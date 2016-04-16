// npm install neo4j-driver
var neo4j = require('neo4j-driver').v1;

var driver = neo4j.driver("bolt://localhost", neo4j.auth.basic("neo4j", "<password>"));
var session = driver.session();
var queryCount = 0;

var insertQuery =
    "UNWIND {pairs} as pair \
     MERGE (p1:Person {name:pair[0]}) \
     MERGE (p2:Person {name:pair[1]}) \
     MERGE (p1)-[:KNOWS]-(p2)";

var foafQuery =
    "MATCH (person:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf) \
     WHERE person.name = {name} \
      AND NOT (person)-[:KNOWS]-(foaf) \
     RETURN foaf.name AS name";

var commonFriendsQuery =
    "MATCH (user:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf:Person) \
     WHERE user.name = {name1} AND foaf.name = {name2} \
     RETURN friend.name AS friend";

var connectingPathsQuery =
    "MATCH path = shortestPath((p1:Person)-[:KNOWS*..6]-(p2:Person)) \
     WHERE p1.name = {name1} AND p2.name = {name2} \
     RETURN [n IN nodes(path) | n.name] as names";

var data = [["Jim","Mike"],["Jim","Billy"],["Anna","Jim"],
    ["Anna","Mike"],["Sally","Anna"],["Joe","Sally"],
    ["Joe","Bob"],["Bob","Sally"]];


function query(query, params, message, column) {
    session
        .run(query, params)
        .then(function(result) {
            console.log(message);
            result.records.forEach(function(record) {
                console.log(record.get(column));
            });

            queryCount += 1;
            if (queryCount > 2) {
                session.close();
                process.exit();
            }
        })
        .catch(function(error){
            console.log(error);
        });
}

session
    .run(insertQuery, {pairs: data})
    .then(function(result) {
        query(foafQuery, {name: "Joe"}, "Friends of friends of Joe: ", "name");
        query(commonFriendsQuery, {name1: "Joe", name2: "Sally"}, "Common friends", "friend");
        query(connectingPathsQuery, {name1: "Joe", name2:"Billy"}, "Connecting paths: ", "names");
    })
    .catch(function(error) {
        console.log(error);
    });