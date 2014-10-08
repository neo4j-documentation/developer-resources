(ns neocons-example.handler
  (:require [clojure.string                   :refer [blank?]]
            [clojurewerkz.neocons.rest        :as nr]
            [clojurewerkz.neocons.rest.cypher :as cy]
            [compojure.core                   :refer [GET defroutes]]
            [compojure.handler                :as handler]
            [ring.util.response               :as resp]
            [ring.middleware.json             :as rj]
            [compojure.route                  :as route]))


(def conn (nr/connect "http://localhost:7474/db/data/"))


(def graph-query "MATCH (m:Movie)<-[:ACTED_IN]-(a:Person)
                  RETURN m.title as movie, collect(a.name) as cast
                  LIMIT {limit};")

(defn get-graph
  [limit]
  (let   [lim      (if (some? limit)
                     (Integer/parseInt limit)
                     100)
          result   (cy/tquery conn graph-query {:limit lim})
          nodes    (map (fn [{:strs [cast movie]}]
                          (concat [{:title movie
                                    :label :movie}]
                                  (map (fn [x] {:title x
                                                :label :actor})
                                       cast)))
                        result)
          nodes        (distinct (apply concat nodes))
          nodes-index  (into {} (map-indexed #(vector %2 %1) nodes))
          links        (map (fn [{:strs [cast movie]}]
                              (let [target   (nodes-index {:title movie :label :movie})]
                                (map (fn [x]
                                       {:target target
                                        :source (nodes-index {:title x :label :actor})})
                                     cast)))
                            result)]
    {:nodes nodes :links (flatten links)}))


(def search-query "MATCH (movie:Movie) WHERE movie.title =~ {title} RETURN movie;")

(defn get-search
  [q]
  (if (blank? q)
    []
    (let  [result  (cy/tquery conn search-query {:title (str "(?i).*" q ".*")})]
      (map (fn [x] {:movie (:data (x "movie"))}) result))))


(def title-query "MATCH (movie:Movie {title:{title}})
                  OPTIONAL MATCH (movie)<-[r]-(person:Person)
                  RETURN movie.title as title,
                         collect({name:person.name,
                                  job:head(split(lower(type(r)),'_')),
                                  role:r.roles}) as cast LIMIT 1;")

(defn get-movie
  [title]
  (let [[result]   (cy/tquery conn title-query {:title title})]
    result))


(defroutes app-routes
  (GET "/" [] (resp/redirect "index.html"))
  (GET "/graph" [limit] (resp/response
                         (get-graph limit)))
  (GET "/search" [q] (resp/response
                      (get-search q)))
  (GET "/movie/:title" [title] (resp/response (get-movie title)))
  (route/resources "/")
  (route/not-found "Not Found"))


(def app
  (-> app-routes
      (handler/site)
      (rj/wrap-json-response)))
