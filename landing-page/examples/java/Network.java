
// javac Network.java
// java -cp /path/to/neo4j-jdbc-2.3-SNAPSHOT-jar-with-dependencies.jar:. Network

import java.sql.*;
import static java.util.Arrays.asList;
import java.util.List;

public class Network {

    public static void query(Connection con, 
                            String query, String[] columns, Object...params)
                      throws SQLException {
        try (PreparedStatement pst = con.prepareStatement(query)) {
            for (int i=0;i<params.length;i++) 
                pst.setObject(i + 1, params[i]);
            ResultSet rs = pst.executeQuery();
            int count = 0;
            while (rs.next()) {
                for (int i=0;i<columns.length;i++) 
                    System.out.print(rs.getString(columns[i])+"\t");
               System.out.println();
            }
        }
    }
    public static void main(String...args) throws SQLException {
        Connection con = DriverManager
             .getConnection("jdbc:neo4j://localhost:7474/","neo4j","<password>");

        List data = 
          asList(asList("CRM", "Database VM"), asList("Database VM", "Server 2"),
          asList("Server 2", "SAN"), asList("Server 1", "SAN"), asList("Webserver VM", "Server 1"),
          asList("Public Website", "Webserver VM"), asList("Public Website", "Webserver VM"));

        String insertQuery = "UNWIND {1} AS pair " +
        "MERGE (s1:Service {name: pair[0]}) " +
        "MERGE (s2:Service {name: pair[1]}) " +
        "MERGE (s1)-[:DEPENDS_ON]->(s2) ";
        
        try {
            PreparedStatement pst = con.prepareStatement(insertQuery);
            pst.setObject(1, data);
            pst.executeUpdate();
            pst.close();
    
            String impactQuery = 
            "MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service) " +
            "WHERE n.name = {1} " +
            "RETURN collect(dependent.name) AS dependent_services";

            query(con, impactQuery, new String[] {"dependent_services"}, "Server 1");

            String dependencyQuery =
            "MATCH (n:Service)-[:DEPENDS_ON*]->(downstream:Service) " +
            "WHERE n.name = {1} " +
            "RETURN collect(downstream.name) AS downstream_services ";
            
            query(con, dependencyQuery, new String[] {"downstream_services"}, "Public Website");

            String statsQuery =
            "MATCH (n:Service)<-[:DEPENDS_ON*]-(dependent:Service) " +
            "RETURN n.name AS service, count(DISTINCT dependent) AS dependents " +
            "ORDER BY dependents DESC " +
            "LIMIT 1";
            query(con, statsQuery, new String[]{"dependents"});
        } finally {
            con.close();
        }
    }
}