using System;
using System.Collections.Generic;
using System.Linq;
using Neo4jClient;
using Neo4jClient.Cypher;
using Newtonsoft.Json;

void Main()
{
    var gc = new GraphClient(new Uri("http://localhost.:7474/db/data"));
    gc.Connect();

    const string createCypher = @"(hank:Person {name:'Hank'}),
(abby:Person {name:'Abby'}),
(max:Person {name:'Max'}),
(sophie:Person {name: 'Sophie'}),
(jane:Person {name: 'Jane'}),
(bill:Person {name: 'Bill'}),
(ssn993632634:SSN {number: 993632634}),
(ssn123456789:SSN {number: 123456789}),
(ssn523252364:SSN {number: 523252364}),
(chase:Account {bank: 'Chase', number: 1523}),
(bofa:Account {bank: 'Bank of America', number: 4634}),
(cayman:Account {bank: 'Cayman', number: 863}),
(bill)-[:HAS_SSN]->(ssn523252364),
(bill)-[:HAS_ACCOUNT]->(bofa),
(jane)-[:HAS_SSN]->(ssn123456789),
(jane)-[:HAS_ACCOUNT]->(chase),
(hank)-[:HAS_ACCOUNT]->(cayman),
(abby)-[:HAS_ACCOUNT]->(cayman),
(abby)-[:HAS_SSN]->(ssn993632634),
(sophie)-[:HAS_SSN]->(ssn993632634),
(max)-[:HAS_SSN]->(ssn993632634)";
    gc.Cypher.Create(createCypher).ExecuteWithoutResults();

    //Transitive Closure
    var transitiveClosure = gc.Cypher
    	.Match("(n:Person)-[*]-(o)")
    	.Where((Entity n) => n.Name == "Hank")
    	.Return(o => o.As<Entity>())
    	.Results;
    
    Console.WriteLine("Transitive Closure");
    foreach (var tc in transitiveClosure)
    	Console.WriteLine($"\t{tc}");

    //Investigation Targeting
    var investigationTargeting = gc.Cypher
    	.Match("(n:Person)-[*]-(o)")
    	.With("n, count(distinct o) AS size")
    	.Where("size > 2")
    	.Return(n => n.As<Entity>())
    	.Results;

    Console.WriteLine("Investigation Targeting");
    foreach (var it in investigationTargeting)
    	Console.WriteLine($"\t{it}");
    
    //Fast Insights
    var fastInsights = gc.Cypher
    	.Match("(ssn:SSN)<-[:HAS_SSN]-(:Person)-[:HAS_ACCOUNT]->(acct:Account)")
    	.Where((Entity ssn) => ssn.Number == 993632634)
    	.Return(acct => acct.As<Entity>())
    	.Results;
    
    Console.WriteLine("Fast Insights");
    foreach (var entity in fastInsights)
    	Console.WriteLine($"\tBank: {entity.Bank}, Number: {entity.Number}");
}

public class Entity
{
    [JsonProperty("name")]
    public string Name { get; set; }

    [JsonProperty("bank")]
    public string Bank { get; set;}

    [JsonProperty("number")]
    public int Number { get; set;}

    public override string ToString()
    {
    	return (string.IsNullOrWhiteSpace(Name)) ? ((string.IsNullOrWhiteSpace(Bank))) ?  Number.ToString() : Bank : Name;
    }
}
