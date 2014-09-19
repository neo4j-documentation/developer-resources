function dir_and_adoc {
  mkdir -p $1
  if [ ! -f "$1/$1.adoc" ]; then
     sed -e "s/Guide Title/$1/" ../guide_template.adoc > $1/$1.adoc
  else
	 echo  "$1/$1.adoc already exists"
  fi
}

mkdir -p neo4j-in-production
cd neo4j-in-production
dir_and_adoc guide-cloud-deployment
dir_and_adoc guide-sizing-and-hardware-calculator
dir_and_adoc guide-performance-tuning
dir_and_adoc guide-clustering-neo4j
dir_and_adoc guide-ha
cd ..

exit

mkdir -p what-is-neo4j
cd what-is-neo4j
dir_and_adoc graph-database
dir_and_adoc property-graph
dir_and_adoc graph-db-vs-rdbms
dir_and_adoc graph-db-vs-nosql
cd ..

mkdir -p cypher-query-language
cd cypher-query-language
dir_and_adoc guide-cypher-basics
dir_and_adoc guide-build-a-recommendation-engine
dir_and_adoc cypher-ref-card
cd ..

mkdir -p working-with-data
cd working-with-data
dir_and_adoc guide-create-your-dataset
dir_and_adoc guide-importing-data-and-etl
dir_and_adoc guide-neo4j-browser
dir_and_adoc guide-neo4j-browser-data-visualization
dir_and_adoc gists-and-examples
cd ..

mkdir -p build-a-graph-data-model
cd build-a-graph-data-model
dir_and_adoc guide-intro-to-graph-modeling
cd ..

mkdir -p choosing-your-language
cd choosing-your-language
dir_and_adoc guide-neo4j-with-java
dir_and_adoc guide-neo4j-with-javascript
dir_and_adoc guide-neo4j-with-python
dir_and_adoc guide-neo4j-with-dotnet
dir_and_adoc guide-neo4j-with-php
dir_and_adoc guide-neo4j-with-r
dir_and_adoc guide-neo4j-with-clojure
dir_and_adoc guide-neo4j-with-ruby
dir_and_adoc guide-neo4j-with-go
dir_and_adoc guide-neo4j-with-scala
dir_and_adoc guide-neo4j-with-groovy
cd ..

mkdir -p neo4j-ecosystem
cd neo4j-ecosystem
dir_and_adoc documentation
dir_and_adoc language-drivers
dir_and_adoc libraries
dir_and_adoc visualization-tools
cd ..
