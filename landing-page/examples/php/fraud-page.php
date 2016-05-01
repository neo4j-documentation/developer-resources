
<?php
/**
 * To install Neo4j-PHP-Client, we use Composer
 *
 * $ curl -sS https://getcomposer.org/installer | php
 * $ php composer.phar require graphaware/neo4j-php-client
 *
 */

require __DIR__.'/vendor/autoload.php';

use GraphAware\Neo4j\Client\ClientBuilder;

// change to your hostname, port, username, password
$neo4j_url = "bolt://neo4j:password@localhost";

// setup connection
$client = ClientBuilder::create()
    ->addConnection('default', $neo4j_url)
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
$client->run($insert_query);


// transitive closure: query
$transitive_query = <<<EOQ
MATCH (n:Person)-[*]-(o)
WHERE n.name = {name}
RETURN labels(o), o
EOQ;

// transitive closure: build and execute query
$params = ['name' => 'Hank'];
$result = $client->run($transitive_query, $params);

foreach ($result->records() as $record) {
  print_r($record->values());
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
$result = $client->run($investigation_targeting_query);

echo "The following people are suspicious:" . PHP_EOL;

foreach ($result->records() as $record) {
  echo $record->get('n')->value('name') . PHP_EOL;
}


// fast insights: query
$fast_insights_query = <<<EOQ
MATCH (ssn:SSN)<-[:HAS_SSN]-(:Person)-[:HAS_ACCOUNT]->(acct:Account)
WHERE ssn.number = {ssn}
RETURN acct
EOQ;

// fast insights: build and execute query
$params = ['ssn' => 993632634];
$result = $client->run($fast_insights_query, $params);

echo "Accounts owned by this SSN:" . PHP_EOL;

foreach ($result->records() as $record) {
  echo "\t" . sprintf('%s@%s', $record->get('acct')->value('number'), $record->get('acct')->value('bank')) . PHP_EOL;
}
