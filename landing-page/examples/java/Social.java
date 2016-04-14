// javac Social.java
// java -cp /path/to/neo4j-jdbc-2.3-SNAPSHOT-jar-with-dependencies.jar:. Social

import java.sql.*;
import static java.util.Arrays.asList;
import java.util.List;

public class Social {

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
          asList(asList("Jim","Mike"),asList("Jim","Billy"),asList("Anna","Jim"),
          asList("Anna","Mike"),asList("Sally","Anna"),asList("Joe","Sally"),
          asList("Joe","Bob"),asList("Bob","Sally"));

        String insertQuery = "UNWIND {1} as pair " +
         "MERGE (p1:Person {name:pair[0]}) " +
         "MERGE (p2:Person {name:pair[1]}) " +
         "MERGE (p1)-[:KNOWS]-(p2);";

        try {
            PreparedStatement pst = con.prepareStatement(insertQuery);
            pst.setObject(1, data);
            pst.executeUpdate();
            pst.close();
    
            String foafQuery = 
            " MATCH (person:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf) "+
            " WHERE person.name = {1} " +
            "   AND NOT (person)-[:KNOWS]-(foaf) " +
            " RETURN foaf.name AS name ";
            query(con, foafQuery, new String[] {"name"}, "Joe");

            String commonFriendsQuery =
            "MATCH (user:Person)-[:KNOWS]-(friend)-[:KNOWS]-(foaf:Person) " +
            " WHERE user.name = {1} AND foaf.name = {2} " +
            " RETURN friend.name AS friend";
            query(con, commonFriendsQuery, new String[] {"friend"}, "Joe", "Sally");

            String connectingPathsQuery =
            "MATCH path = shortestPath((p1:Person)-[:KNOWS*..6]-(p2:Person)) " +
            " WHERE p1.name = {1} AND p2.name = {2} " +
            " RETURN [n IN nodes(path) | n.name] as names";
            query(con, connectingPathsQuery, new String[] {"names"}, "Joe","Billy");
        } finally {
            con.close();
        }
    }
}