echo "You have to have a Neo4j server running with neo4j:<password> set as credentials"

javac [SFN]*.java
java -cp neo4j-jdbc.jar:. Social
java -cp neo4j-jdbc.jar:. Fraud
java -cp neo4j-jdbc.jar:. Network


