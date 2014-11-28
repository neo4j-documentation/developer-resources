#!/usr/bin/env python


import json

from bottle import get, run, request, response, static_file
from py2neo.neo4j import GraphDatabaseService, CypherQuery


graph = GraphDatabaseService()


@get("/")
def get_index():
    return static_file("index.html", root="static")


@get("/graph")
def get_graph():
    query = CypherQuery(graph, "MATCH (m:Movie)<-[:ACTED_IN]-(a:Person) "
                               "RETURN m.title as movie, collect(a.name) as cast "
                               "LIMIT {limit}")
    results = query.execute(limit=request.query.get("limit", 100))
    nodes = []
    rels = []
    i = 0
    for movie, cast in results.data:
        nodes.append({"title": movie, "label": "movie"})
        target = i
        i += 1
        for name in cast:
            actor = {"title": name, "label": "actor"}
            try:
                source = nodes.index(actor)
            except ValueError:
                nodes.append(actor)
                source = i
                i += 1
            rels.append({"source": source, "target": target})
    return {"nodes": nodes, "links": rels}


@get("/search")
def get_search():
    try:
        q = request.query["q"]
    except KeyError:
        return []
    else:
        query = CypherQuery(graph, "MATCH (movie:Movie) "
                                   "WHERE movie.title =~ {title} "
                                   "RETURN movie")
        results = query.execute(title="(?i).*" + q + ".*")
        response.content_type = "application/json"
        return json.dumps([{"movie": row["movie"].get_cached_properties()} for row in results.data])


@get("/movie/<title>")
def get_movie(title):
    query = CypherQuery(graph, "MATCH (movie:Movie {title:{title}}) "
                               "OPTIONAL MATCH (movie)<-[r]-(person:Person) "
                               "RETURN movie.title as title,"
                               "collect([person.name, head(split(lower(type(r)),'_')), r.roles]) as cast "
                               "LIMIT 1")
    results = query.execute(title=title)
    row = results.data[0]
    return {"title": row["title"],
            "cast": [dict(zip(("name", "job", "role"), member)) for member in row["cast"]]}


if __name__ == "__main__":
    run(port=8080)
