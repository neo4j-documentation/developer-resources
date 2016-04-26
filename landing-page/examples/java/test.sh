echo "You have to have a Neo4j server running with neo4j:<password> set as credentials"

export CLASSPATH=neo4j-java-driver-1.0.0.jar:.
rm *.class
javac [SFN]*.java
java -cp $CLASSPATH Social
java -cp $CLASSPATH Fraud
java -cp $CLASSPATH Network
