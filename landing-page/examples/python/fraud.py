# pip install neo4j-driver

from neo4j.v1 import GraphDatabase, basic_auth

driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth("neo4j", "<password>"))
session = driver.session()

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

session.run(insert_query)

# Transitive Closure

transitive_query = '''
MATCH (n:Person)-[*]-(o)
WHERE n.name = {name}
RETURN DISTINCT o AS other
'''

results = session.run(transitive_query, parameters={"name": "Hank"})
for record in results:
    print(record["other"])


# Investigation Targeting

targeting_query = """
MATCH (n:Person)-[*]-(o)
WITH n, count(DISTINCT o) AS size
WHERE size > 2
RETURN n
"""

results = session.run(targeting_query)
for record in results:
    print(record["n"])

# Fast Insights

insights_query = """
MATCH (ssn:SSN)<-[:HAS_SSN]-(:Person)-[:HAS_ACCOUNT]->(acct:Account)
WHERE ssn.number = {flagged_ssn}
RETURN acct
"""

results = session.run(insights_query, parameters={"flagged_ssn": 993632634})
for record in results:
    print(record["acct"])


session.close()
