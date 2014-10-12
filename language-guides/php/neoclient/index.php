<?php
use Silex\Application,
    Symfony\Component\HttpFoundation\Request,
    Symfony\Component\HttpFoundation\JsonResponse,
    Neoxygen\NeoClient\Client,
    Neoxygen\NeoClient\Formatter\ResponseFormatter;

require __DIR__.'/vendor/autoload.php';

$app = new Application();

$neo4j = new Client();
$neo4j->addConnection('default', 'http', 'localhost', 7474)
    ->build();

$app->get('/', function () {
    return file_get_contents(__DIR__.'/static/index.html');
});

$app->get('/graph', function (Request $request) use ($neo4j) {
    $formatter = new ResponseFormatter();
    $limit = $request->get('limit', 50);
    $params = ['limit' => $limit];
    $q = 'MATCH (m:Movie)<-[r:ACTED_IN]-(p:Person) RETURN m,r,p LIMIT {limit}';
    $apiResponse = $neo4j->sendCypherQuery($q, $params, null, array('row', 'graph'));

    $nodes = [];
    $edges = [];
    $nodesPositions = [];

    $result = $formatter->format($apiResponse);
    $i = 0;
    foreach ($result->getNodes() as $node){
        $prop = ($node->getLabel() === 'Movie') ? 'title' : 'name';
        $nodes[] = [
            'title' => $node->getProperty($prop),
            'label' => $node->getLabel()
        ];
        $nodesPositions[$node->getId()] = $i;
        $i++;
    }

    foreach ($result->getRelationships() as $rel){
        $edges[] = [
            'source' => $nodesPositions[$rel->getStartNode()->getId()],
            'target' => $nodesPositions[$rel->getEndNode()->getId()]
        ];
    }

    $data = [
        'nodes' => $nodes,
        'links' => $edges
    ];

    $response = new JsonResponse();
    $response->setData($data);

    return $response;
});

$app->get('/search', function (Request $request) use ($neo4j) {
    $searchTerm = $request->get('q');
    $term = '(?i).*'.$searchTerm.'.*';
    $query = 'MATCH (m:Movie) WHERE m.title =~ {term} RETURN m';
    $params = ['term' => $term];

    $apiResponse = $neo4j->sendCypherQuery($query, $params, null, array('graph'));
    $formatter = new ResponseFormatter();
    $result = $formatter->format($apiResponse);
    $movies = [];
    foreach ($result->getNodes() as $movie){
        $movies[] = ['movie' => $movie->getProperties()];
    }

    $response = new JsonResponse();
    $response->setData($movies);

    return $response;
});

$app->get('/movie/{title}', function ($title) use ($neo4j) {
    $q = 'MATCH (m:Movie) WHERE m.title = {title} OPTIONAL MATCH p=(m)<-[r]-(a:Person) RETURN m,p';
    $params = ['title' => $title];

    $apiResponse = $neo4j->sendCypherQuery($q, $params, null, array('graph'));
    $formatter = new ResponseFormatter();
    $result = $formatter->format($apiResponse);

    $movie = $result->getSingleNodeByLabel('Movie');
    $mov = [
        'title' => $movie->getProperty('title'),
        'cast' => []
        ];

    foreach ($movie->getInboundRelationships() as $rel){
        $actor = $rel->getStartNode()->getProperty('name');
        $relType = explode('_', strtolower($rel->getType()));
        $job = $relType[0];
        $cast = [
            'job' => $job,
            'name' => $actor
        ];
        if (array_key_exists('roles', $rel->getProperties())){
            $cast['role'] = implode(',', $rel->getProperties()['roles']);
        } else {
            $cast['role'] = null;
        }
        $mov['cast'][] = $cast;
    }

    $response = new JsonResponse();
    $response->setData($mov);

    return $response;
});

$app->run();