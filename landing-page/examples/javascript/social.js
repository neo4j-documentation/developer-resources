
// npm install --save neo4j
var neo4j = require('neo4j');
var db = new neo4j.GraphDatabase('http://neo4j:<password>@localhost:7474');


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

function query(query, params, column, cb) {
    function callback(err, results) {
        if (err || !results) throw err;
        if (!column) cb(results)
        else results.forEach(function(row) { cb(row[column]) });
    };
    db.cypher({ query: query, params: params}, callback);
}

query(insertQuery, {pairs: data}, null, function () {
    query(foafQuery, {name: "Joe"},"name", console.log); 
    query(commonFriendsQuery, {name1: "Joe", name2:"Sally"},"friend",console.log);
    query(connectingPathsQuery, {name1: "Joe", name2:"Billy"}, "names", 
          function(res) { console.log(res)});
});
