
# pip install py2neo

from py2neo import Graph
graph = Graph("http://neo4j:<password>@localhost:7474/db/data/")

# Insert data
insert_query = '''
UNWIND {pairs} as pair
MERGE (p1:Person {name:pair[0]})
MERGE (p2:Person {name:pair[1]})
MERGE (p1)-[:KNOWS]-(p2);
'''

data = [["Jim","Mike"],["Jim","Billy"],["Anna","Jim"],
          ["Anna","Mike"],["Sally","Anna"],["Joe","Sally"],
          ["Joe","Bob"],["Bob","Sally"]]

graph.cypher.execute(insert_query, {"pairs": data })

# Friends of a friend

foaf_query = '''
MATCH (person:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf) 
WHERE person.name = {name}
  AND NOT (person)-[:KNOWS]-(foaf)
RETURN foaf.name AS name
'''

results = graph.cypher.execute(foaf_query, {"name": "Joe"})
for record in results:
    print(record)


# Common friends

common_friends_query = """
MATCH (user:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf:Person)
WHERE user.name = {user} AND foaf.name = {foaf}
RETURN friend.name AS friend
"""

results = graph.cypher.execute(common_friends_query, {"user": "Joe", "foaf": "Sally"})
for record in results:
    print(record)

# Connecting paths

connecting_paths_query = """
MATCH path = shortestPath((p1:Person)-[:KNOWS*..6]-(p2:Person))
WHERE p1.name = {name1} AND p2.name = {name2}
RETURN path
"""

results = graph.cypher.execute(connecting_paths_query, {"name1": "Joe", "name2": "Billy"})
for record in results:
    print(record)