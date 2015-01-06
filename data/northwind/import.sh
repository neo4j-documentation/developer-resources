VERSION=2.1.6
ARCHIVE=neo4j-community-$VERSION-unix.tar.gz
DIR=neo4j-community-$VERSION
DB=northwind.db
if [ ! -f $ARCHIVE ]; then
curl -O http://dist.neo4j.org/$ARCHIVE
tar xvzf $ARCHIVE
fi
rm -rf $DB
$DIR/bin/neo4j-shell -path $DB -file import_csv.cypher | tee import.out

 
