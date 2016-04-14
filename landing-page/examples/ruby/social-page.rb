
# gem install neo4j-core
require 'neo4j-core'
session = Neo4j::Session.open(:server_db, 'http://localhost:7474', basic_auth: {username: 'neo4j', password: '<password>'})

# Insert data
insert_query = """
UNWIND {pairs} as pair
MERGE (p1:Person {name:pair[0]})
MERGE (p2:Person {name:pair[1]})
MERGE (p1)-[:KNOWS]-(p2);
"""

data = [["Jim","Mike"],["Jim","Billy"],["Anna","Jim"],
          ["Anna","Mike"],["Sally","Anna"],["Joe","Sally"],
          ["Joe","Bob"],["Bob","Sally"]]

session.query(insert_query, pairs: data)

# Friends of a friend

foaf_query = """
MATCH (person:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf) 
WHERE person.name = {name}
  AND NOT (person)-[:KNOWS]-(foaf)
RETURN foaf.name AS name
"""

response = session.query(foaf_query, name: 'Joe')
response.each do |row|
  puts row[:name]
end

# Common friends

common_friends_query = """
MATCH (user:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf:Person)
WHERE user.name = {user} AND foaf.name = {foaf}
RETURN friend.name AS friend
"""

response = session.query(common_friends_query, user: 'Joe', foaf: 'Sally')
response.each do |row|
  puts row[:friend]
end

# Connecting paths

connecting_paths_query = """
MATCH path = shortestPath((p1:Person)-[:KNOWS*..6]-(p2:Person))
WHERE p1.name = {name1} AND p2.name = {name2}
RETURN path
"""

response = session.query(connecting_paths_query, name1: 'Joe', name2: 'Billy')
response.each do |row|
  puts row
end