
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
$neo4j_url = "http://neo4j:nods-increment-elbow@54.86.149.98:32826";

// setup connection
$cnx = parse_url($neo4j_url);
$neo4j = ClientBuilder::create()
    ->addConnection('default', $cnx['scheme'], $cnx['host'], $cnx['port'], true, $cnx['user'], $cnx['pass'])
    ->setAutoFormatResponse(true)
    ->setDefaultTimeout(20)
    ->build();

// setup data
$insert_query = <<<EOQ
UNWIND {pairs} as pair
MERGE (p1:Person {name:pair[0]})
MERGE (p2:Person {name:pair[1]})
MERGE (p1)-[:KNOWS]-(p2);
EOQ;

// friend data to insert
$data = [["Jim","Mike"],["Jim","Billy"],["Anna","Jim"],
          ["Anna","Mike"],["Sally","Anna"],["Joe","Sally"],
          ["Joe","Bob"],["Bob","Sally"]];

// insert data
$neo4j->sendCypherQuery($insert_query, ["pairs" => $data]);


// friend of friend: query
$foaf_query = <<<EOQ
MATCH (person:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf)
WHERE person.name = {name}
  AND NOT (person)-[:KNOWS]-(foaf)
RETURN foaf.name AS name
EOQ;

// friend of friend: build and execute query
$params = ['name' => 'Joe'];
$results = $neo4j->sendCypherQuery($foaf_query, $params)->getResult()->getTableFormat();

foreach ($results as $result) {
  print_r( $result );
}


// common friends: query
$common_friends_query = <<<EOQ
MATCH (user:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf:Person)
WHERE user.name = {user} AND foaf.name = {foaf}
RETURN friend.name AS friend
EOQ;

// common friends: build and execute query
$params = ['user' => 'Joe', 'foaf' => 'Sally'];
$results = $neo4j->sendCypherQuery($common_friends_query, $params)->getResult()->getTableFormat();

foreach ($results as $result) {
  print_r( $result );
}


// connecting paths: query
$connecting_paths_query = <<<EOQ
MATCH path = shortestPath((p1:Person)-[:KNOWS*..6]-(p2:Person))
WHERE p1.name = {name1} AND p2.name = {name2}
RETURN [n IN nodes(path) | n.name] as names
EOQ;

// connecting paths: build and execute query
$params = ['name1' => 'Joe', 'name2' => 'Billy'];
$results = $neo4j->sendCypherQuery($connecting_paths_query, $params)->getResult()->getTableFormat();

foreach ($results as $result) {
  print_r( $result );
}
