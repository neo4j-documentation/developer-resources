// javac -cp neo4j-java-driver*.jar:. Network.java
// java -cp neo4j-java-driver*.jar:. Network

import org.neo4j.driver.v1.*;
import static org.neo4j.driver.v1.Values.parameters;

import java.util.List;
import static java.util.Arrays.asList;
import static java.util.Collections.singletonMap;

public class Network {

public static void main(String...args) {
    Config noSSL = Config.build().withEncryptionLevel(Config.EncryptionLevel.NONE).toConfig();
    Driver driver = GraphDatabase.driver("bolt://localhost",AuthTokens.basic("neo4j","test"),noSSL); // <password>
    try (Session session = driver.session()) {

        List data = 
          asList(asList("CRM", "Database VM"), asList("Database VM", "Server 2"),
          asList("Server 2", "SAN"), asList("Server 1", "SAN"), asList("Webserver VM", "Server 1"),
          asList("Public Website", "Webserver VM"), asList("Public Website", "Webserver VM"));

          String insertQuery = "UNWIND {pairs} AS pair " +
          "MERGE (s1:Service {name: pair[0]}) " +
          "MERGE (s2:Service {name: pair[1]}) " +
          "MERGE (s1)-[:DEPENDS_ON]->(s2) ";

           session.run(insertQuery,singletonMap("pairs",data)).consume();

           StatementResult result;
        
           String impactQuery = 
           "MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service) " +
           "WHERE n.name = {name} " +
           "RETURN collect(dependent.name) AS dependent_services";

           result = session.run(impactQuery, parameters("name","Server 1"));
           while (result.hasNext()) System.out.println(result.next().get("dependent_services"));

           String dependencyQuery =
           "MATCH (n:Service)-[:DEPENDS_ON*]->(downstream:Service) " +
           "WHERE n.name = {name} " +
           "RETURN collect(downstream.name) AS downstream_services ";

           result = session.run(dependencyQuery, parameters("name","Public Website"));
           while (result.hasNext()) System.out.println(result.next().get("downstream_services"));

           String statsQuery =
           "MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service) " +
           "RETURN n.name AS service, count(DISTINCT dependent) AS dependents " +
           "ORDER BY dependents DESC " +
           "LIMIT 1";

           result = session.run(statsQuery, parameters());
           while (result.hasNext()) {
             Record record = result.next();
             System.out.printf("%s has %s dependents.%n",record.get("service"),record.get("dependents"));
           }
    }
}
}