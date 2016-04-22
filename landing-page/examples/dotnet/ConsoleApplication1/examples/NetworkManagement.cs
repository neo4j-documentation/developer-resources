using System;
using System.Collections.Generic;
using System.Linq;
using Neo4j.Driver.V1;

class NetworkManagement
{
    public static void NetworkManagementMain(string[] args)
    {
        using (var driver = GraphDatabase.Driver(new Uri("bolt://localhost:7687"), AuthTokens.Basic("neo4j", "neo4j")))
        {
            var data = new List<string[]>
            {
                new[] {"CRM", "Database VM"},
                new[] {"Database VM", "Server 2"},
                new[] {"Server 2", "SAN"},
                new[] {"Server 1", "SAN"},
                new[] {"Webserver VM", "Server 1"},
                new[] {"Public Website", "Webserver VM"},
                new[] {"Public Website", "Webserver VM"}
            };
            const string loadCypher =
                "UNWIND {servers} AS row MERGE(s1: Service { name: row[0]}) MERGE(s2: Service { name: row[1]}) MERGE(s1) -[:DEPENDS_ON]->(s2)";
            using (var session = driver.Session())
            {
                var result = session.Run(loadCypher, new {servers = data});
                result.ToList();
            }

            //Impact Analysis
            //Find all upstreams impacted by outage of Server 1.
            using (var session = driver.Session())
            {
                var result = session.Run(
                    "MATCH (n:Service)<-[:DEPENDS_ON *]-(dependent:Service) " +
                    "WHERE n.name = 'Server 1' " +
                    "RETURN dependent.name AS name");
                Console.WriteLine("Impacted by outage of Server 1");
                foreach (var record in result)
                {
                    Console.WriteLine($"\t{record["name"]}");
                }
            }

            //Dependency Analysis
            //Find all dependencies of the public website.
            using (var session = driver.Session())
            {
                var result = session.Run(
                    "MATCH (n:Service)-[:DEPENDS_ON *]->(downstream) " +
                    "WHERE n.name = 'Public Website' " +
                    "RETURN downstream.name AS name");
                Console.WriteLine("Dependencies of Public Website");
                foreach (var record in result)
                {
                    Console.WriteLine($"\t{record["name"]}");
                }
            }

            //Statistics
            //Find the most depended-upon component.
            using (var session = driver.Session())
            {
                var result = session.Run(
                    "MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service) " +
                    "RETURN n.name AS service, count(DISTINCT dependent) AS dependents " +
                    "ORDER BY dependents DESC " +
                    "LIMIT 1"
                    );
                Console.WriteLine($"Most depended-upon component is {result.Single()["service"].As<string>()}");
            }
        }
    }
}