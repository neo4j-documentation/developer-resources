
// npm install --save neo4j
var neo4j = require('neo4j');
var db = new neo4j.GraphDatabase('http://neo4j:<password>@localhost:7474');


var insertQuery = 
  "UNWIND {pairs} AS pair \
   MERGE (s1:Service {name: pair[0]}) \
   MERGE (s2:Service {name: pair[1]}) \
   MERGE (s1)-[:DEPENDS_ON]->(s2);";

var impactQuery = 
  "MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service) \
   WHERE n.name = {service_name} \
   RETURN collect(dependent.name) AS dependent_services";

var dependencyQuery = 
  "MATCH (n:Service)-[:DEPENDS_ON*]->(downstream:Service) \
   WHERE n.name = {service_name} \
   RETURN collect(downstream.name) AS downstream_services";

var statsQuery =
  "MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service) \
   RETURN n.name AS service, count(DISTINCT dependent) AS dependents \
   ORDER BY dependents DESC \
   LIMIT 1";

var data = 
  [["CRM", "Database VM"], ["Database VM", "Server 2"],
   ["Server 2", "SAN"], ["Server 1", "SAN"], ["Webserver VM", "Server 1"],
   ["Public Website", "Webserver VM"], ["Public Website", "Webserver VM"]];


function query(query, params, column, cb) {
    function callback(err, results) {
        if (err || !results) throw err;
        if (!column) cb(results)
        else results.forEach(function(row) { cb(row[column]) });
    };
    db.cypher({ query: query, params: params}, callback);
}

query(insertQuery, {pairs: data}, null, function () {
    query(impactQuery, {service_name: "Server 1"},"dependent_services", console.log); 
    query(dependencyQuery, {service_name: "Public Website"},"downstream_services",console.log);
    query(statsQuery, null, "dependents", 
          function(res) { console.log(res)});
});
