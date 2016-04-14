
# pip install py2neo

from py2neo import Graph
graph = Graph("http://neo4j:<password>@localhost:7474/db/data/")

# Insert data
insert_query = '''
UNWIND {pairs} AS pair
MERGE (s1:Service {name: pair[0]})
MERGE (s2:Service {name: pair[1]})
MERGE (s1)-[:DEPENDS_ON]->(s2);
'''

data = [["CRM", "Database VM"], ["Database VM", "Server 2"],
       ["Server 2", "SAN"], ["Server 1", "SAN"], ["Webserver VM", "Server 1"],
       ["Public Website", "Webserver VM"], ["Public Website", "Webserver VM"]]

graph.cypher.execute(insert_query, {"pairs": data })

# Impact Analysis

impact_query = '''
MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service)
WHERE n.name = {service_name}
RETURN collect(dependent.name) AS dependent_services
'''

results = graph.cypher.execute(impact_query, {"service_name": "Server 1"})
for record in results:
    print(record)


# Dependency Analysis

dependency_query = """
MATCH (n:Service)-[:DEPENDS_ON*]->(downstream:Service)
WHERE n.name = {service_name}
RETURN collect(downstream.name) AS downstream_services
"""

results = graph.cypher.execute(dependency_query, {"service_name": "Public Website"})
for record in results:
    print(record)

# Statistics

stats_query = """
MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service)
RETURN n.name AS service, count(DISTINCT dependent) AS dependents
ORDER BY dependents DESC
LIMIT 1
"""

results = graph.cypher.execute(stats_query)
for record in results:
    print(record)