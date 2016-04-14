
<?php
/**
 * To install Neoclient, we use Composer
 * 
 * $ curl -sS https://getcomposer.org/installer | php
 * $ php composer.phar require neoxygen/neoclient
 *
 */

use Neoxygen\NeoClient\ClientBuilder;

require __DIR__.'/vendor/autoload.php';

// change to your hostname, port, username, password
$neo4j_url = "http://neo4j:password@localhost:7474";

// setup connection
$cnx = parse_url($neo4j_url);
$neo4j = ClientBuilder::create()
    ->addConnection('default', $cnx['scheme'], $cnx['host'], $cnx['port'], true, $cnx['user'], $cnx['pass'])
    ->setAutoFormatResponse(true)
    ->setDefaultTimeout(20)
    ->build();

// setup data
$insert_query = <<<EOQ
CREATE (hank:Person {name:'Hank'}),
(abby:Person {name:'Abby'}),
(max:Person {name:'Max'}),
(sophie:Person {name: 'Sophie'}),
(jane:Person {name: 'Jane'}),
(bill:Person {name: 'Bill'}),
(ssn993632634:SSN {number: 993632634}),
(ssn123456789:SSN {number: 123456789}),
(ssn523252364:SSN {number: 523252364}),
(chase:Account {bank: 'Chase', number: 1523}),
(bofa:Account {bank: 'Bank of America', number: 4634}),
(cayman:Account {bank: 'Cayman', number: 863}),
(bill)-[:HAS_SSN]->(ssn523252364),
(bill)-[:HAS_ACCOUNT]->(bofa),
(jane)-[:HAS_SSN]->(ssn123456789),
(jane)-[:HAS_ACCOUNT]->(chase),
(hank)-[:HAS_ACCOUNT]->(cayman),
(abby)-[:HAS_ACCOUNT]->(cayman),
(abby)-[:HAS_SSN]->(ssn993632634),
(sophie)-[:HAS_SSN]->(ssn993632634),
(max)-[:HAS_SSN]->(ssn993632634)
EOQ;

// insert data
$neo4j->sendCypherQuery($insert_query);


// transitive closure: query
$transitive_query = <<<EOQ
MATCH (n:Person)-[*]-(o)
WHERE n.name = {name}
RETURN labels(o), o
EOQ;

// transitive closure: build and execute query
$params = ['name' => 'Hank'];
$results = $neo4j->sendCypherQuery($transitive_query, $params)->getResult()->getTableFormat();

foreach ($results as $result) {
  print_r($result);
}
print "\n";

// investigation targeting: query
$investigation_targeting_query = <<<EOQ
MATCH (n:Person)-[*]-(o)
WITH n, count(DISTINCT o) AS size
WHERE size > 2
RETURN n
EOQ;

// investigation targeting: build and execute query
$results = $neo4j->sendCypherQuery($investigation_targeting_query)->getResult()->getTableFormat();

print "The following people are suspicious:\n";

foreach ($results as $result) {
  print "\t" . $result['n']['name'] . "\n";
}
print "\n";


// fast insights: query
$fast_insights_query = <<<EOQ
MATCH (ssn:SSN)<-[:HAS_SSN]-(:Person)-[:HAS_ACCOUNT]->(acct:Account)
WHERE ssn.number = {ssn}
RETURN acct
EOQ;

// fast insights: build and execute query
$params = ['ssn' => 993632634];
$results = $neo4j->sendCypherQuery($fast_insights_query, $params)->getResult()->getTableFormat();

print "Accounts owned by this SSN:\n";

foreach ($results as $result) {
  print "\t" . $result['acct']['number'] . " @ " . $result['acct']['bank'] . "\n";
}
