
# gem install neo4j-core
require 'neo4j-core'
session = Neo4j::Session.open(:server_db, 'http://localhost:7474', basic_auth: {username: 'neo4j', password: '<password>'})

# Insert data
insert_query = """
CREATE (hank:Person {name:'Hank'}),
(abby:Person {name:'Abby'}),
(max:Person {name:'Max'}),
(sophie:Person {name: 'Sophie'}),
(jane:Person {name: 'Jane'}),
(bill:Person {name: 'Bill'}),
(ssn993632634:SSN {number: 993632634, name: 'SSN 993632634'}),
(ssn123456789:SSN {number: 123456789, name: 'SSN 123456789'}),
(ssn523252364:SSN {number: 523252364, name: 'SSN 523252364'}),
(chase:Account {bank: 'Chase', number: 1523, name: 'Chase 1523'}),
(bofa:Account {bank: 'Bank of America', number: 4634, name: 'BofA 4634'}),
(cayman:Account {bank: 'Cayman', number: 863, name: 'Cayman 863'}),
(bill)-[:HAS_SSN]->(ssn523252364),
(bill)-[:HAS_ACCOUNT]->(bofa),
(jane)-[:HAS_SSN]->(ssn123456789),
(jane)-[:HAS_ACCOUNT]->(chase),
(hank)-[:HAS_ACCOUNT]->(cayman),
(abby)-[:HAS_ACCOUNT]->(cayman),
(abby)-[:HAS_SSN]->(ssn993632634),
(sophie)-[:HAS_SSN]->(ssn993632634),
(max)-[:HAS_SSN]->(ssn993632634)
"""
session.query(insert_query)

# Transitive Closure

transitive_query = """
MATCH (n:Person)-[*]-(o)
WHERE n.name = {name}
RETURN DISTINCT o.name AS other
"""

response = session.query(transitive_query, name: 'Hank')
puts "Suspicious entities: "
response.each do |row|
  puts row[:other]
end
puts "---------------------"
# Investigation Targeting

targeting_query = """
MATCH (n:Person)-[*]-(o)
WITH n, count(DISTINCT o) AS size
WHERE size > 2
RETURN n.name AS target
"""

response = session.query(targeting_query)
puts "Investigation targets: "
response.each do |row|
  puts row[:target]
end
puts "----------------------"

# Fast Insights

connecting_paths_query = """
MATCH (ssn:SSN)<-[:HAS_SSN]-(:Person)-[:HAS_ACCOUNT]->(acct:Account)
WHERE ssn.number = 993632634
RETURN acct.bank + ' ' + str(acct.number) AS account
"""

response = session.query(connecting_paths_query, name1: 'Joe', name2: 'Billy')
puts "Accounts: "
response.each do |row|
  puts row[:account]
end