// javac -cp neo4j-java-driver*.jar:. Network.java
// java -cp neo4j-java-driver*.jar:. Network

import org.neo4j.driver.v1.*;
import static org.neo4j.driver.v1.Values.parameters;

import java.util.List;
import static java.util.Arrays.asList;
import static java.util.Collections.singletonMap;

public class Social {

    public static void main(String...args) {
        
        Config noSSL = Config.build().withEncryptionLevel(Config.EncryptionLevel.NONE).toConfig();
        Driver driver = GraphDatabase.driver("bolt://localhost",AuthTokens.basic("neo4j","test"),noSSL); // <password>
        try (Session session = driver.session()) {

              List data = 
              asList(asList("Jim","Mike"),asList("Jim","Billy"),asList("Anna","Jim"),
              asList("Anna","Mike"),asList("Sally","Anna"),asList("Joe","Sally"),
              asList("Joe","Bob"),asList("Bob","Sally"));
    
              String insertQuery = "UNWIND {pairs} as pair " +
               "MERGE (p1:Person {name:pair[0]}) " +
               "MERGE (p2:Person {name:pair[1]}) " +
               "MERGE (p1)-[:KNOWS]-(p2);";
      
               session.run(insertQuery,singletonMap("pairs",data)).consume();
          
               StatementResult result;
            
               String foafQuery = 
               " MATCH (person:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf) "+
               " WHERE person.name = {name} " +
               "   AND NOT (person)-[:KNOWS]-(foaf) " +
               " RETURN foaf.name AS name ";
               result = session.run(foafQuery, parameters("name","Joe"));
               while (result.hasNext()) System.out.println(result.next().get("name"));
      
               String commonFriendsQuery =
               "MATCH (user:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf:Person) " +
               " WHERE user.name = {from} AND foaf.name = {to} " +
               " RETURN friend.name AS friend";
               result = session.run(commonFriendsQuery, parameters("from","Joe","to","Sally"));
               while (result.hasNext()) System.out.println(result.next().get("friend"));
      
               String connectingPathsQuery =
               "MATCH path = shortestPath((p1:Person)-[:KNOWS*..6]-(p2:Person)) " +
               " WHERE p1.name = {from} AND p2.name = {to} " +
               " RETURN [n IN nodes(path) | n.name] as names";
               result = session.run(connectingPathsQuery, parameters("from","Joe","to","Billy"));
               while (result.hasNext()) System.out.println(result.next().get("names"));

        }
    }
}