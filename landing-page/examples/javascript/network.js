// npm install neo4j-driver
var neo4j = require('neo4j-driver').v1;

var driver = neo4j.driver("bolt://localhost", neo4j.auth.basic("neo4j", "<password>"));
var session = driver.session();
var queryCount = 0;

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

function query(query, params, message, column) {
    session
        .run(query, params)
        .then(function(result) {
            console.log(message);
            result.records.forEach(function(record) {
                if (column === 'dependents') {
                    console.log(record.get(column).toInt());
                } else {
                    console.log(record.get(column));
                }
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
        query(impactQuery, {service_name: "Server 1"}, "Dependent services: ", "dependent_services");
        query(dependencyQuery, {service_name: "Public Website"}, "Downstream services: ", "downstream_services");
        query(statsQuery, {}, "Dependents: ", "dependents");
    })
    .catch(function(error) {
        console.log(error);
    });