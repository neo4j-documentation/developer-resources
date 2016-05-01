// npm install neo4j-driver
var neo4j = require('neo4j-driver').v1;

var driver = neo4j.driver("bolt://localhost", neo4j.auth.basic("neo4j", "<password>"));
var session = driver.session();
var queryCount = 0;

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
    .run(insertQuery)
    .then(function(result) {
        query(transitiveQuery, {name: "Hank"}, "Transitive closure: ", "other");
        query(targetingQuery, {}, "Investigation targeting: ", "n");
        query(insightsQuery, {ssn: 993632634}, "Associated accounts: ", "acct");
    })
    .catch(function(error) {
        console.log(error);
    });