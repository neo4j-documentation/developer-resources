package main

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strconv"

	"github.com/daaku/go.httpgzip"
	"github.com/jmoiron/sqlx"
	_ "gopkg.in/cq.v1"
	"gopkg.in/cq.v1/types"
)

type MovieResult struct {
	Movie `json:"movie"`
}

type Movie struct {
	Released int      `json:"released"`
	Title    string   `json:"title,omitempty"`
	Tagline  string   `json:"tagline,omitempty"`
	Cast     []Person `json:"cast,omitempty"`
}

type Person struct {
	Job  string   `json:"job"`
	Role []string `json:"role"`
	Name string   `json:"name"`
}

type D3Response struct {
	Nodes []Node `json:"nodes"`
	Links []Link `json:"links"`
}

type Node struct {
	Title string `json:"title"`
	Label string `json:"label"`
}

type Link struct {
	Source int `json:"source"`
	Target int `json:"target"`
}

var (
	neo4jURL = "http://localhost:7474"
)

func defaultHandler(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "text/html")
	body, _ := ioutil.ReadFile("public/index.html")
	w.Write(body)
}

func searchHandler(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	query := req.URL.Query()["q"][0]
	cypher := `MATCH (movie:Movie) 
				 WHERE movie.title =~ {0} 
				 RETURN movie.title as title, movie.tagline as tagline, movie.released as released`
	db, err := sqlx.Connect("neo4j-cypher", neo4jURL)
	if err != nil {
		log.Println("error connecting to neo4j:", err)
	}
	defer db.Close()

	movies := []Movie{}
	param := "(?i).*" + query + ".*"
	err = db.Select(&movies, cypher, param)
	if err != nil {
		log.Println("error querying search:", err)
	}

	movieResults := []MovieResult{}
	for _, x := range movies {
		movieResults = append(movieResults, MovieResult{x})
	}

	err = json.NewEncoder(w).Encode(movieResults)
	if err != nil {
		log.Println("error writing search response:", err)
	}
}

func movieHandler(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	query := req.URL.Path[len("/movie/"):]
	cypher := `MATCH (movie:Movie {title:{0}})
				  OPTIONAL MATCH (movie)<-[r]-(person:Person)
				  WITH movie.title as title,
						 collect({name:person.name,
						 job:head(split(lower(type(r)),'_')),
						 role:r.roles}) as cast 
				  LIMIT 1
				  UNWIND cast as c 
				  RETURN title, c.name as name, c.job as job, c.role as role`
	db, err := sqlx.Connect("neo4j-cypher", neo4jURL)
	if err != nil {
		log.Println("error connecting to neo4j:", err)
	}
	defer db.Close()

	rows, err := db.Query(cypher, query)
	if err != nil {
		log.Println("error querying movie:", err)
	}
	defer rows.Close()

	movie := Movie{}
	for rows.Next() {
		name := ""
		job := ""
		role := types.CypherValue{}
		err = rows.Scan(&movie.Title, &name, &job, &role)
		if err != nil {
			log.Println("error scanning row:", err)
			break
		}
		switch role.Val.(type) {
		case []string:
			movie.Cast = append(movie.Cast, Person{Name: name, Job: job, Role: role.Val.([]string)})
		default: // handle nulls or unexpected stuff
			movie.Cast = append(movie.Cast, Person{Name: name, Job: job})
		}
	}

	err = json.NewEncoder(w).Encode(movie)
	if err != nil {
		log.Println("error writing movie response:", err)
	}
}

func graphHandler(w http.ResponseWriter, req *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	limits := req.URL.Query()["limit"]
	limit := 50
	var err error
	if len(limits) > 0 {
		limit, err = strconv.Atoi(limits[0])
		if err != nil {
			limit = 50
		}
	}
	cypher := `MATCH (m:Movie)<-[:ACTED_IN]-(a:Person)
				  RETURN m.title as movie, collect(a.name) as cast
				  LIMIT {0} `
	db, err := sqlx.Connect("neo4j-cypher", neo4jURL)
	if err != nil {
		log.Println("error connecting to neo4j:", err)
	}
	defer db.Close()

	rows, err := db.Query(cypher, limit)
	if err != nil {
		log.Println("error querying graph:", err)
	}
	defer rows.Close()

	d3Resp := D3Response{}
	for rows.Next() {
		title := ""
		actors := []string{}
		err = rows.Scan(&title, &actors)
		if err != nil {
			log.Println("error scanning graph:", err)
		}
		d3Resp.Nodes = append(d3Resp.Nodes, Node{Title: title, Label: "movie"})
		movIdx := len(d3Resp.Nodes) - 1
		for _, actor := range actors {
			idx := -1
			for i, node := range d3Resp.Nodes {
				if actor == node.Title && node.Label == "actor" {
					idx = i
					break
				}
			}
			if idx == -1 {
				d3Resp.Nodes = append(d3Resp.Nodes, Node{Title: actor, Label: "actor"})
				d3Resp.Links = append(d3Resp.Links, Link{Source: len(d3Resp.Nodes) - 1, Target: movIdx})
			} else {
				d3Resp.Links = append(d3Resp.Links, Link{Source: idx, Target: movIdx})
			}
		}
	}

	err = json.NewEncoder(w).Encode(d3Resp)
	if err != nil {
		log.Println("error writing graph response:", err)
	}
}

func init() {
	if os.Getenv("GRAPHENEDB_URL") != "" {
		neo4jURL = os.Getenv("GRAPHENEDB_URL")
	}
}

func main() {
	serveMux := http.NewServeMux()
	serveMux.HandleFunc("/", defaultHandler)
	serveMux.HandleFunc("/search", searchHandler)
	serveMux.HandleFunc("/movie/", movieHandler)
	serveMux.HandleFunc("/graph", graphHandler)

	panic(http.ListenAndServe(":"+os.Getenv("PORT"), httpgzip.NewHandler(serveMux)))
}
