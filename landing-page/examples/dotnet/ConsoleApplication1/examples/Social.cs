using System;
using System.Collections.Generic;
using System.Linq;
using Neo4j.Driver.V1;

class SocialProgram
{
    private static void SocialMain(string[] args)
    {
        using (var s = new Social())
        {
            s.Setup();

            var friendsOfFriends = s.FriendsOfAFriend("Joe");
            Console.WriteLine($"Joe's friends (of friends)");
            foreach (var fof in friendsOfFriends)
            {
                Console.WriteLine($"\t{fof["foaf"].As<INode>()["name"].As<string>()}");
            }

            Console.WriteLine();

            var commonFriends = s.CommonFriends("Joe", "Sally");
            Console.WriteLine("Joe and Sally's common friends");
            foreach (var friend in commonFriends)
            {
                Console.WriteLine($"\t{friend["friend"].As<string>()}");
            }

            Console.WriteLine();

            var connectingNames = s.ConnectingPaths("Joe", "Billy");
            Console.WriteLine("Path to Billy");
            foreach (var record in connectingNames)
            {
                var path = record["path"].As<IPath>();
                foreach (var friend in path.Nodes)
                {
                    Console.WriteLine($"\t{friend["name"].As<string>()}");
                }
            }
        }
    }
}

public class Social :IDisposable
{
    private readonly IDriver _driver;

    public Social()
    {
        _driver = GraphDatabase.Driver(new Uri("bolt://localhost:7687"), AuthTokens.Basic("neo4j", "neo4j"));
    }

    public void Setup()
    {
        var peopleList = new List<string[]>
        {
            new[] {"Jim", "Mike"}, new[] {"Jim", "Billy"}, new[] {"Anna", "Jim"},
            new[] {"Anna", "Mike"}, new[] {"Sally", "Anna"}, new[] {"Joe", "Sally"},
            new[] {"Joe", "Bob"}, new[] {"Bob", "Sally"}
        };

        using (var session = _driver.Session())
        {
            var result = session.Run(
                "UNWIND {people} AS pair " +
                "MERGE (u1:Person { name: pair[0] }) " +
                "MERGE (u2:Person { name: pair[1] }) " +
                "MERGE (u1)-[:KNOWS]->(u2)", new {people = peopleList});
            result.ToList();
        }
    }

    public List<IRecord> FriendsOfAFriend(string personName)
    {
        using (var session = _driver.Session())
        {
            var result = session.Run(
                "MATCH (p:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf)" +
                "WHERE p.name = {p1}" +
                "AND NOT (p) -[:KNOWS]-(foaf)" +
                "RETURN foaf", 
                new {p1 = personName});

            return result.ToList();
        }
    }

    public List<IRecord> CommonFriends(string personName1, string personName2)
    {
        using (var session = _driver.Session())
        {
            var result = session.Run(
                "MATCH (p:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf:Person)" +
                "WHERE p.name = {p1}" +
                "AND foaf.name = {p2}" +
                "RETURN friend.name AS friend",
                new { p1 = personName1, p2 = personName2 });

            return result.ToList();
        }
    }

    public List<IRecord> ConnectingPaths(string personName1, string personName2)
    {
        using (var session = _driver.Session())
        {
            var result = session.Run(
                "MATCH path = shortestPath((p1:Person)-[:KNOWS*..6]-(p2:Person))" +
                "WHERE p1.name = {p1}" +
                "AND p2.name = {p2}" +
                "RETURN path",
                new { p1 = personName1, p2 = personName2 });

            return result.ToList();
        }
    }

    public void Dispose()
    {
        _driver?.Dispose();
    }
}