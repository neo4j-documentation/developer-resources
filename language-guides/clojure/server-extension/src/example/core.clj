(ns example.core
  (:require [clojure.string      :as s]
            [cheshire.core       :as cc])
  (:import (java.util Map)
           (javax.ws.rs Path PathParam Produces GET QueryParam)
           (javax.ws.rs.core Context Response)
           (org.neo4j.cypher.javacompat ExecutionEngine ExecutionResult)
           (org.neo4j.helpers.collection IteratorUtil)))


(def search-query "MATCH (movie:Movie)
  WHERE movie.title =~ {query}
  RETURN {title:movie.title,
          released:movie.released,
          tagline:movie.tagline} as movie;")


(defn do-search
  [^ExecutionEngine engine ^String query]
  (if (s/blank? query)
    {}
    (let [result   (.execute engine search-query {"query" (str "(?i).*" query ".*")})]
      (IteratorUtil/asCollection result))))

(def movie-query "MATCH (m:Movie)<-[:ACTED_IN]-(a:Person)
  RETURN m.title as movie, collect(a.name) as cast LIMIT {1}")


(defn get-graph
  [^ExecutionEngine engine ^Integer limit]
  (let [result       (iterator-seq
                      (.iterator
                       (.execute engine movie-query {"1" limit})))
        nodes        (map (fn [^Map row]
                            [{:title (get row "movie")
                              :label :movie}
                             (map (fn [y] {:title y
                                           :label :actor})
                                  (get row "cast"))])
                          result)
        nodes        (distinct (flatten nodes))
        nodes-index  (into {} (map-indexed #(vector %2 %1) nodes))
        links        (map (fn [^Map row]
                            (let [target   (nodes-index {:title (get row "movie")
                                                         :label :movie})]
                              (map (fn [x] {:target target
                                            :source  (nodes-index {:title x :label :actor})})
                                   (get row "cast"))))
                          result)]
    {:nodes nodes :links (flatten links)}))

(def find-movie-query "MATCH (movie:Movie {title:{title}})
OPTIONAL MATCH (movie)<-[r]-(person:Person)
RETURN movie.title as title,
COLLECT({name:person.name, job:head(split(lower(type(r)),'_')), role:r.roles[0]}) as cast LIMIT 1")

(defn find-movie
  [^ExecutionEngine engine ^String title]
  (if (s/blank? title)
    {}
    (let [result   (.execute engine find-movie-query {"title" title})]
      (IteratorUtil/singleOrNull result))))


(definterface IMovieResource
  (search [^org.neo4j.graphdb.GraphDatabaseService database ^String query])
  (graph [^org.neo4j.graphdb.GraphDatabaseService database ^Integer limit])
  (findMovie [^org.neo4j.graphdb.GraphDatabaseService database ^String title]))


(deftype ^{Path "/"} MovieResource []
         IMovieResource
         (^{GET true
            Produces ["text/plain"]
            Path "/search"}
          search
          [this ^{Context true} database ^{QueryParam "q"} query]
            (require 'example.core)
            (let  [result   (do-search (ExecutionEngine. database) query)]
              (-> result
                  cc/generate-string
                  (Response/ok)
                  .build)))
         (^{GET true
            Produces ["text/plain"]
            Path "/graph"}
          graph
          [this ^{Context true} database ^{QueryParam "limit"} limit]
            (require 'example.core)
            (let  [result  (get-graph (ExecutionEngine. database) limit)]
              (-> result
                  cc/generate-string
                  (Response/ok)
                  .build)))
         (^{GET true
            Produces ["text/plain"]
            Path "/{title}"}
          findMovie
          [this ^{Context true} database ^{PathParam "title"} query]
            (require 'example.core)
            (let  [result   (find-movie (ExecutionEngine. database) query)]
              (-> result
                  cc/generate-string
                  (Response/ok)
                  .build))))
