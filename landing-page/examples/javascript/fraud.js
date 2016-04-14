
// npm install --save neo4j
var neo4j = require('neo4j');
var db = new neo4j.GraphDatabase('http://neo4j:<password>@localhost:7474');


var insertQuery = 
    "CREATE (hank:Person {name:'Hank'}), \
    (abby:Person {name:'Abby'}), \
    (max:Person {name:'Max'}), \
    (sophie:Person {name: 'Sophie'}), \
    (jane:Person {name: 'Jane'}), \
    (bill:Person {name: 'Bill'}), \
    (ssn993632634:SSN {number: 993632634}), \
    (ssn123456789:SSN {number: 123456789}), \
    (ssn523252364:SSN {number: 523252364}), \
    (chase:Account {bank: 'Chase', number: 1523}), \
    (bofa:Account {bank: 'Bank of America', number: 4634}), \
    (cayman:Account {bank: 'Cayman', number: 863}), \
    (bill)-[:HAS_SSN]->(ssn523252364), \
    (bill)-[:HAS_ACCOUNT]->(bofa), \
    (jane)-[:HAS_SSN]->(ssn123456789), \
    (jane)-[:HAS_ACCOUNT]->(chase), \
    (hank)-[:HAS_ACCOUNT]->(cayman), \
    (abby)-[:HAS_ACCOUNT]->(cayman), \
    (abby)-[:HAS_SSN]->(ssn993632634), \
    (sophie)-[:HAS_SSN]->(ssn993632634), \
    (max)-[:HAS_SSN]->(ssn993632634)";

var transitiveQuery = 
    "MATCH (n:Person)-[*]-(o) \
    WHERE n.name = {name} \
    RETURN DISTINCT o AS other";
        
var targetingQuery =
    "MATCH (n:Person)-[*]-(o) \
    WITH n, count(DISTINCT o) AS size \
    WHERE size > 2 \
    RETURN n";

var insightsQuery =
    "MATCH (ssn:SSN)<-[:HAS_SSN]-(:Person)-[:HAS_ACCOUNT]->(acct:Account) \
    WHERE ssn.number = {ssn} \
    RETURN acct";

function query(query, params, column, cb) {
    function callback(err, results) {
        if (err || !results) throw err;
        if (!column) cb(results)
        else results.forEach(function(row) { cb(row[column]) });
    };
    db.cypher({ query: query, params: params}, callback);
}

query(insertQuery, {}, null, function () {
    query(transitiveQuery, {name: "Hank"},"other", console.log); 
    query(targetingQuery, {},"other",console.log);
    query(insightsQuery, {ssn: 993632634}, "acct", 
          function(res) { console.log(res)});
});
