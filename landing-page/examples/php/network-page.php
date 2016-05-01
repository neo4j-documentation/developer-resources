
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
$client->run($insert_query, ["pairs" => $data]);


// impact analysis: query
$impact_query = <<<EOQ
MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service)
WHERE n.name = {service}
RETURN dependent
EOQ;

// impact analysis: build and execute query
$params = ['service' => 'Server 1'];
$result = $client->run($impact_query, $params);

echo "Services impacted by Server 1 outage:" . PHP_EOL;
foreach ($result->records() as $record) {
  echo "\t" . $record->get('dependent')->value('name') . PHP_EOL;
}


// dependency analysis: query
$dependency_analysis_query = <<<EOQ
MATCH (n:Service)-[:DEPENDS_ON*]->(downstream:Service)
WHERE n.name = {service}
RETURN downstream
EOQ;

// dependency analysis: build and execute query
$params = ['service' => 'Public Website'];
$result = $client->run($dependency_analysis_query, $params);

echo "The following services depend upon Public Website, either directly or indirectly:" . PHP_EOL;

foreach ($result->records() as $record) {
  echo "\t" . $record->get('downstream')->value('name') . PHP_EOL;
}

echo PHP_EOL;


// statistics: query
$statistics_query = <<<EOQ
MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service)
RETURN n, count(DISTINCT dependent) AS dependents
ORDER BY dependents DESC
LIMIT 1
EOQ;

// statistics: build and execute query
$result = $client->run($statistics_query);

foreach ($result->records() as $record) {
  echo sprintf(
    '%s is the most depended-upon component with %d dependents',
    $record->get('n')->value('name'),
    $record->get('dependents')
    ) . PHP_EOL;
}
