// Create indexes
CREATE CONSTRAINT ON (m:Movie) ASSERT m.id IS UNIQUE;
CREATE CONSTRAINT ON (g:Genre) ASSERT g.id IS UNIQUE;
CREATE CONSTRAINT ON (c:Character) ASSERT c.id IS UNIQUE;
CREATE CONSTRAINT ON (a:Actor) ASSERT a.id IS UNIQUE;


// Movie titles
LOAD CSV WITH HEADERS FROM "https://raw.githubusercontent.com/neo4j-contrib/developer-resources/movies-csv/scraping/all-movies.csv" AS line

MERGE (m:Movie {id: line.Id})
ON CREATE SET m.title = line.Title, m.releaseDate = line.ReleaseDate;

// Genres
LOAD CSV WITH HEADERS FROM "https://raw.githubusercontent.com/neo4j-contrib/developer-resources/movies-csv/scraping/all-genres.csv" AS line

MERGE (m:Movie {id: line.MovieId})
MERGE (g:Genre {id: line.GenreId})
ON CREATE SET g.name = line.GenreName

MERGE (m)-[:HAS_GENRE]->(g);

// Casts
LOAD CSV WITH HEADERS FROM "https://raw.githubusercontent.com/neo4j-contrib/developer-resources/movies-csv/scraping/all-casts.csv" AS line

MERGE (m:Movie {id: line.MovieId})

MERGE (a:Actor {id: line.ActorId})
ON CREATE SET a.name = line.ActorName

MERGE (a)-[:ACTED_IN {character: line.Character}]-(m);

// Key words
LOAD CSV WITH HEADERS FROM "https://raw.githubusercontent.com/neo4j-contrib/developer-resources/movies-csv/scraping/all-keywords.csv" AS line

MERGE (k:Keyword {id: line.KeyWordId})
ON CREATE SET k.name = line.KeyWord

MERGE (m:Movie {id: line.MovieId})

MERGE (m)-[:HAS_KEYWORD]->(k)
