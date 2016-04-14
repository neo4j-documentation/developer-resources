
# pip install py2neo

from py2neo import Graph
graph = Graph("http://neo4j:<password>@localhost:7474/db/data/")

# tag::setup[]
# Insert data
insert_query = '''
CREATE (hank:Person {name:"Hank"}),
(abby:Person {name:"Abby"}),
(max:Person {name:"Max"}),
(sophie:Person {name: "Sophie"}),
(jane:Person {name: "Jane"}),
(bill:Person {name: "Bill"}),
(ssn993632634:SSN {number: 993632634}),
(ssn123456789:SSN {number: 123456789}),
(ssn523252364:SSN {number: 523252364}),
(chase:Account {bank: "Chase", number: 1523}),
(bofa:Account {bank: "Bank of America", number: 4634}),
(cayman:Account {bank: "Cayman", number: 863}),
(bill)-[:HAS_SSN]->(ssn523252364),
(bill)-[:HAS_ACCOUNT]->(bofa),
(jane)-[:HAS_SSN]->(ssn123456789),
(jane)-[:HAS_ACCOUNT]->(chase),
(hank)-[:HAS_ACCOUNT]->(cayman),
(abby)-[:HAS_ACCOUNT]->(cayman),
(abby)-[:HAS_SSN]->(ssn993632634),
(sophie)-[:HAS_SSN]->(ssn993632634),
(max)-[:HAS_SSN]->(ssn993632634)
'''

graph.cypher.execute(insert_query)
# end:setup[]

# Transitive Closure

transitive_query = '''
MATCH (n:Person)-[*]-(o)
WHERE n.name = {name}
RETURN DISTINCT o AS other
'''

results = graph.cypher.execute(transitive_query, {"name": "Hank"})
for record in results:
    print(record)


# Investigation Targeting

targeting_query = """
MATCH (n:Person)-[*]-(o)
WITH n, count(DISTINCT o) AS size
WHERE size > 2
RETURN n
"""

results = graph.cypher.execute(targeting_query)
for record in results:
    print(record)

# Fast Insights

insights_query = """
MATCH (ssn:SSN)<-[:HAS_SSN]-(:Person)-[:HAS_ACCOUNT]->(acct:Account)
WHERE ssn.number = 993632634
RETURN acct
"""

results = graph.cypher.execute(insights_query)
for record in results:
    print(record)
