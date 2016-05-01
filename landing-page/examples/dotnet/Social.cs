use 

var client = new GraphClient(new Uri("http://user:<password>@localhost:7474/db/data"));

var users = {{"Jim","Mike"},{"Jim","Billy"},{"Anna","Jim"},
{"Anna","Mike"},{"Sally","Anna"},{"Joe","Sally"},
{"Joe","Bob"},{"Bob","Sally"}};

graphClient.Cypher
    .Unwind(users, “pair”)
    .Merge("(u1:User { name: pair[0] })")
    .Merge("(u2:User { name: pair[1] })")
    .Merge("(u1)-[:KNOWS]->(u2)")
    .ExecuteWithoutResults();
}

public class User
{
    public string Name { get; set; }
}

var joe = new User { Name = "joe" };

graphClient.Cypher
    .Match("(user:User)-[:KNOWS]-(friend)-[:KNOWS]-(foaf)")
    .Where((User user) => user.Name == “Joe”)
    .Return(foaf => foaf.As<User>())
    .Results;

