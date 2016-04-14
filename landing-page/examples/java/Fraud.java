
// javac Fraud.java
// java -cp /path/to/neo4j-jdbc-2.3-SNAPSHOT-jar-with-dependencies.jar:. Fraud

import java.sql.*;

public class Fraud {

    public static void query(Connection con, 
                            String query, String[] columns, Object...params)
                      throws SQLException {
        try (PreparedStatement pst = con.prepareStatement(query)) {
            for (int i=0;i<params.length;i++) 
                pst.setObject(i + 1, params[i]);
            ResultSet rs = pst.executeQuery();
            while (rs.next()) {
                for (int i=0;i<columns.length;i++) 
                    System.out.print(rs.getObject(columns[i])+"\t");
                System.out.println();
            }
        }
    }
    public static void main(String...args) throws SQLException {
        Connection con = DriverManager
             .getConnection("jdbc:neo4j://localhost:7474/","neo4j","<password>");

        String insertQuery = 
            "CREATE (hank:Person {name:'Hank'})," +
            "(abby:Person {name:'Abby'})," +
            "(max:Person {name:'Max'})," +
            "(sophie:Person {name: 'Sophie'})," +
            "(jane:Person {name: 'Jane'})," +
            "(bill:Person {name: 'Bill'})," +
            "(ssn993632634:SSN {number: 993632634})," +
            "(ssn123456789:SSN {number: 123456789})," +
            "(ssn523252364:SSN {number: 523252364})," +
            "(chase:Account {bank: 'Chase', number: 1523})," +
            "(bofa:Account {bank: 'Bank of America', number: 4634})," +
            "(cayman:Account {bank: 'Cayman', number: 863})," +
            "(bill)-[:HAS_SSN]->(ssn523252364)," +
            "(bill)-[:HAS_ACCOUNT]->(bofa)," +
            "(jane)-[:HAS_SSN]->(ssn123456789)," +
            "(jane)-[:HAS_ACCOUNT]->(chase)," +
            "(hank)-[:HAS_ACCOUNT]->(cayman)," +
            "(abby)-[:HAS_ACCOUNT]->(cayman)," +
            "(abby)-[:HAS_SSN]->(ssn993632634)," +
            "(sophie)-[:HAS_SSN]->(ssn993632634)," +
            "(max)-[:HAS_SSN]->(ssn993632634)";
        try {
            PreparedStatement pst = con.prepareStatement(insertQuery);
            pst.executeUpdate();
            pst.close();
    
            String transitiveQuery = 
            " MATCH (n:Person)-[*]-(o) " +
            " WHERE n.name = {1} "+
            " RETURN o ";
            query(con, transitiveQuery, new String[] {"o"}, "Hank");

            String targetingQuery =
            "MATCH (n:Person)-[*]-(o) " +
            " WITH n, count(DISTINCT o) AS size " +
            " WHERE size > 2 " +
            " RETURN n";
            query(con, targetingQuery, null);

            String insightsQuery =
            "MATCH (ssn:SSN)<-[:HAS_SSN]-(:Person)-[:HAS_ACCOUNT]->(acct:Account) "+
            " WHERE ssn.number = {1} "+
            " RETURN acct";
            query(con, insightsQuery, new String[] {"acct"}, 993632634);
        } finally {
            con.close();
        }
    }
}