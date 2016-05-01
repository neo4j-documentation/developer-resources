
using System;
using System.Collections.Generic;
using System.Linq;
using Neo4jClient;
using Neo4jClient.Cypher;
using Newtonsoft.Json;

//Use this for Console Apps
internal class Program
{
    private static void Main(string[] args)
    {
        var s = new Social();
        s.Setup();

        var friendsOfFriends = s.FriendsOfAFriend(new Person {Name = "Joe"});
        Console.WriteLine($"Joe's friends (of friends)");
        foreach (var fof in friendsOfFriends)
        {
            Console.WriteLine($"\t{fof.Name}");
        }

        Console.WriteLine();

        var commonFriends = s.CommonFriends(new Person {Name = "Joe"}, new Person {Name = "Sally"});
        Console.WriteLine("Joe and Sally's common friends");
        foreach (var friend in commonFriends)
        {
            Console.WriteLine($"\t{friend.Name}");
        }

        Console.WriteLine();

        var connectingNames = s.ConnectingPaths(new Person {Name = "Joe"}, new Person {Name = "Billy"});
        Console.WriteLine("Path to Billy");
        foreach (var name in connectingNames)
        {
            Console.WriteLine($"\t{name}");
        }
    }
}

public class Social
{
    private readonly IGraphClient _graphClient;

    public Social()
    {
        _graphClient = new GraphClient(new Uri("http://localhost:7474/db/data"), "user", "pass");
        _graphClient.Connect();
    }

    public void Setup()
    {
        var people = new List<string[]>
        {
            new[] {"Jim", "Mike"}, new[] {"Jim", "Billy"}, new[] {"Anna", "Jim"},
            new[] {"Anna", "Mike"}, new[] {"Sally", "Anna"}, new[] {"Joe", "Sally"},
            new[] {"Joe", "Bob"}, new[] {"Bob", "Sally"}
        };

        _graphClient.Cypher
            .Unwind(people, "pair")
            .Merge("(u1:Person { name: pair[0] })")
            .Merge("(u2:Person { name: pair[1] })")
            .Merge("(u1)-[:KNOWS]->(u2)")
            .ExecuteWithoutResults();
    }

    public IEnumerable<Person> FriendsOfAFriend(Person person)
    {
        /*
            MATCH (p:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf)
            WHERE p.name = {p1}
            AND NOT (p)-[:KNOWS]-(foaf)
            RETURN foaf
        */

        var query = _graphClient.Cypher
            .Match("(p:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf)")
            .Where((Person p) => p.Name == person.Name)
            .AndWhere("NOT (p)-[:KNOWS]-(foaf)")
            .Return(foaf => foaf.As<Person>());
        return query.Results;
    }

    public IEnumerable<Person> CommonFriends(Person person1, Person person2)
    {
        /*
            MATCH (p:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf:Person)
            WHERE p.name = {p1}
            AND foaf.name = {p2}
            RETURN friend
        */

        var query = _graphClient.Cypher
            .Match("(p:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf:Person)")
            .Where((Person p) => p.Name == person1.Name)
            .AndWhere((Person foaf) => foaf.Name == person2.Name)
            .Return(friend => friend.As<Person>());

        return query.Results;
    }

    public IEnumerable<string> ConnectingPaths(Person person1, Person person2)
    {
        /*
            MATCH path = shortestPath((p1:Person)-[:KNOWS*..6]-(p2:Person))
            WHERE p1.name = {p1}
            AND p2.name = {p2}
            RETURN [n IN nodes(path) | n.name]
        */

        var query = _graphClient.Cypher
            .Match("path = shortestPath((p1:Person)-[:KNOWS*..6]-(p2:Person))")
            .Where((Person p1) => p1.Name == person1.Name)
            .AndWhere((Person p2) => p2.Name == person2.Name)
            .Return(() => Return.As<IEnumerable<string>>("[n IN nodes(path) | n.name]"));

        return query.Results.Single();
    }
}
public class Person
{
    //This is required to make the serializer treat the 'C#' naming style as 'Java' in the DB
    [JsonProperty("name")]
    public string Name { get; set; }
}