/*
Data in next comment should be saved ad c:/temp/services.csv
*/

/*
CRM,Database VM
Database VM,Server 2
Server 2, SAN
Server 1,SAN
Webserver VM,Server 1
Public Website,Webserver VM
Public Website,Database VM
*/

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

    const string loadCypher = @"LOAD CSV FROM 'file://localhost/c:/temp/services.csv' as row
    MERGE(s1: Service { name: row[0]})
    MERGE(s2: Service { name: row[1]})
    MERGE(s1) -[:DEPENDS_ON]->(s2);";
    ((IRawGraphClient)gc).ExecuteCypher(new CypherQuery(loadCypher, null, CypherResultMode.Set));


    //Impact Analysis
    //Find all upstreams impacted by outage of Server 1.
    var impacted = gc.Cypher
    	.Match("(n:Service)<-[:DEPENDS_ON *]-(dependent:Service)")
    	.Where((Entity n) => n.Name == "Server 1")
    	.Return(dependent => dependent.As<Entity>().Name)
    	.Results;

    Console.WriteLine("Impacted by outage of Server 1");
    foreach (var name in impacted)
    	Console.WriteLine($"\t{name}");

    //Dependency Analysis
    //Find all dependencies of the public website.
    var dependencies = gc.Cypher
    	.Match("(n:Service)-[:DEPENDS_ON *]->(downstream)")
    	.Where((Entity n) => n.Name == "Public Website")
    	.Return(downstream => downstream.As<Entity>().Name)
    	.Results;

    Console.WriteLine("Dependencies of Public Website");
    foreach (var name in dependencies)
    	Console.WriteLine($"\t{name}");

    //Statistics
    //Find the most depended-upon component.
    var mostDepended = gc.Cypher
    		.Match("(n:Service)<-[:DEPENDS_ON *]-(dependent)")
    		.Return(n => new
    		{
    			Entity = n.As<Entity>(),
    			Dependents = n.CountDistinct()
    		})
    		.OrderByDescending("Dependents")
    		.Limit(1)
    		.Results
    		.Single();

    Console.WriteLine($"Most depended-upon component is {mostDepended.Entity.Name}");
}

public class Entity
{
    [JsonProperty("name")]
    public string Name { get; set; }
}
