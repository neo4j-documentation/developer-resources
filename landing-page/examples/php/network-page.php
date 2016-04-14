
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
UNWIND {pairs} as pair
MERGE (s1:Service {name:pair[0]})
MERGE (s2:Service {name:pair[1]})
MERGE (s1)-[:DEPENDS_ON]-(s2);
EOQ;

// network data to insert
$data = [["CRM","Database VM"],["Database VM","Server 2"],["Server 2","SAN"],
          ["Server 1","SAN"],["Webserver VM","Server 1"],["Public Website","Webserver VM"],
          ["Public Website","Database VM"]];

// insert data
$neo4j->sendCypherQuery($insert_query, ["pairs" => $data]);


// impact analysis: query
$impact_query = <<<EOQ
MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service)
WHERE n.name = {service}
RETURN dependent
EOQ;

// impact analysis: build and execute query
$params = ['service' => 'Server 1'];
$results = $neo4j->sendCypherQuery($impact_query, $params)->getResult()->getTableFormat();

print "Services impacted by Server 1 outage:\n";
foreach ($results as $result) {
  print "\t" . $result['dependent']['name'] . "\n";
}
print "\n";


// dependency analysis: query
$dependency_analysis_query = <<<EOQ
MATCH (n:Service)-[:DEPENDS_ON*]->(downstream:Service)
WHERE n.name = {service}
RETURN downstream
EOQ;

// dependency analysis: build and execute query
$params = ['service' => 'Public Website'];
$results = $neo4j->sendCypherQuery($dependency_analysis_query, $params)->getResult()->getTableFormat();

print "The following services depend upon Public Website, either directly or indirectly:\n";

foreach ($results as $result) {
  print "\t" . $result['downstream']['name'] . "\n";
}
print "\n";


// statistics: query
$statistics_query = <<<EOQ
MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service)
RETURN n, count(DISTINCT dependent) AS dependents
ORDER BY dependents DESC
LIMIT 1
EOQ;

// statistics: build and execute query
$results = $neo4j->sendCypherQuery($statistics_query)->getResult()->getTableFormat();

foreach ($results as $result) {
  print $result['n']['name'] . ' is the most depended-upon component with ' . $result['dependents'] . ' dependents' . "\n";
}
