#!/usr/bin/env python


import json

from bottle import get, run, request, response, static_file
from py2neo import Graph


graph = Graph()


@get("/")
def get_index():
    return static_file("index.html", root="static")


@get("/graph")
def get_graph():
    results = graph.cypher.execute(
        "MATCH (m:Movie)<-[:ACTED_IN]-(a:Person) "
        "RETURN m.title as movie, collect(a.name) as cast "
        "LIMIT {limit}", {"limit": 100})
    nodes = []
    rels = []
    i = 0
    for movie, cast in results:
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
        results = graph.cypher.execute(
            "MATCH (movie:Movie) "
            "WHERE movie.title =~ {title} "
            "RETURN movie", {"title": "(?i).*" + q + ".*"})
        response.content_type = "application/json"
        return json.dumps([{"movie": row.movie.properties} for row in results])


@get("/movie/<title>")
def get_movie(title):
    results = graph.cypher.execute(
        "MATCH (movie:Movie {title:{title}}) "
        "OPTIONAL MATCH (movie)<-[r]-(person:Person) "
        "RETURN movie.title as title,"
        "collect([person.name, head(split(lower(type(r)),'_')), r.roles]) as cast "
        "LIMIT 1", {"title": title})
    row = results[0]
    return {"title": row.title,
            "cast": [dict(zip(("name", "job", "role"), member)) for member in row.cast]}


if __name__ == "__main__":
    run(port=8080)
