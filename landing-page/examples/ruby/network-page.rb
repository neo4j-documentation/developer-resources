
# gem install neo4j-core
require 'neo4j-core'
session = Neo4j::Session.open(:server_db, 'http://localhost:7474', basic_auth: {username: 'neo4j', password: '<password>'})

# Insert data

insert_query = """
UNWIND {pairs} AS pair
MERGE (s1:Service {name: pair[0]})
MERGE (s2:Service {name: pair[1]})
MERGE (s1)-[:DEPENDS_ON]->(s2);
"""

data = [["CRM", "Database VM"], ["Database VM", "Server 2"],
        ["Server 2", "SAN"], ["Server 1", "SAN"], ["Webserver VM", "Server 1"],
        ["Public Website", "Webserver VM"], ["Public Website", "Webserver VM"]]

session.query(insert_query, pairs: data)

# Impact Analysis

impact_query = """
MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service)
WHERE n.name = {service_name}
RETURN dependent.name AS dependent_service
"""

response = session.query(impact_query, service_name: 'Server 1')
puts "Dependent services: "
response.each do |row|
  puts row[:dependent_service]
end
puts "--------------------"

# Dependency Analysis

dependency_query = """
MATCH (n:Service)-[:DEPENDS_ON*]->(downstream:Service)
WHERE n.name = {service_name}
RETURN downstream.name AS downstream_service
"""

response = session.query(dependency_query, service_name: 'Public Website')
puts "Downstream services: "
response.each do |row|
  puts row[:downstream_service]
end
puts "---------------------"

# Statistics

stats_query = """
MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service)
RETURN n.name AS service, count(DISTINCT dependent) AS dependents
ORDER BY dependents DESC
LIMIT 1
"""

puts "Service with most dependent services: "
response = session.query(stats_query)
response.each do |row|
  puts row[:service] + " with " + row[:dependents].to_s + " dependencies"
end