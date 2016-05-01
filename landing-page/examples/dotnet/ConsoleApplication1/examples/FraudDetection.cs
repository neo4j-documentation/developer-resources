using System;
using System.Linq;
using Neo4j.Driver.V1;

namespace ConsoleApplication1
{
    class FraudDetection
    {
        public static void FraudDetectionMain(string[] args)
        {
            using (var driver = GraphDatabase.Driver(new Uri("bolt://localhost:7687"), AuthTokens.Basic("neo4j", "neo4j")))
            {
                // setup
                var statementText =
                    "CREATE (hank:Person {name:'Hank'})," +
                    "(abby:Person {name:'Abby'})," +
                    "(max:Person {name:'Max'})," +
                    "(sophie:Person {name: 'Sophie'})," +
                    "(jane:Person {name: 'Jane'})," +
                    "(bill:Person {name: 'Bill'})," +
                    "(ssn993632634:SSN {number: 993632634})," +
                    "(ssn123456789:SSN {number: 123456789})," +
                    "(ssn523252364:SSN {number: 523252364})," +
                    "(chase:Account {bank: 'Chase', number: 1523})," +
                    "(bofa:Account {bank: 'Bank of America', number: 4634})," +
                    "(cayman:Account {bank: 'Cayman', number: 863})," +
                    "(bill)-[:HAS_SSN]->(ssn523252364)," +
                    "(bill)-[:HAS_ACCOUNT]->(bofa)," +
                    "(jane)-[:HAS_SSN]->(ssn123456789)," +
                    "(jane)-[:HAS_ACCOUNT]->(chase)," +
                    "(hank)-[:HAS_ACCOUNT]->(cayman)," +
                    "(abby)-[:HAS_ACCOUNT]->(cayman)," +
                    "(abby)-[:HAS_SSN]->(ssn993632634)," +
                    "(sophie)-[:HAS_SSN]->(ssn993632634)," +
                    "(max)-[:HAS_SSN]->(ssn993632634)";

                using (var session = driver.Session())
                {
                    var result = session.Run(statementText);
                    result.ToList();
                }

                //Transitive Closure
                using (var session = driver.Session())
                {
                    var result = session.Run("MATCH (n:Person)-[*]-(o) WHERE n.name = 'Hank' RETURN o");
                    Console.WriteLine("Transitive Closure");
                    foreach (var record in result)
                    {
                        var node = record["o"].As<INode>();
                        if (node.Labels.Contains("Person"))
                        {
                            Console.WriteLine($"\tPerson: {node["name"]}");
                        }
                        else if (node.Labels.Contains("Account"))
                        {
                            Console.WriteLine($"\tACCOUNT: {node["bank"]}, {node["number"]}");
                        }
                        else // ssn
                        {
                            Console.WriteLine($"\tSSN: {node["number"]}");
                        }
                    }
                }

                //Investigation Targeting
                using (var session = driver.Session())
                {
                    var result = session.Run(
                            "MATCH (n: Person) -[*]- (o) WITH n, count(DISTINCT o) AS size WHERE size > 2 RETURN n");
                    Console.WriteLine("Investigation Targeting");
                    foreach (var record in result)
                    {
                        Console.WriteLine($"\t{record["n"].As<INode>()["name"]}");
                    }
                }

                //Fast Insights
                using (var session = driver.Session())
                {
                    var result = session.Run(
                        "MATCH (ssn: SSN) <-[:HAS_SSN]-(:Person)-[:HAS_ACCOUNT]->(acct: Account) WHERE ssn.number = 993632634 RETURN acct");
                    Console.WriteLine("Fast Insights");
                    foreach (var record in result)
                    {
                        Console.WriteLine($"\t{record["acct"].As<INode>()["number"]}");
                    }
                }
            }
        }
    }
}
