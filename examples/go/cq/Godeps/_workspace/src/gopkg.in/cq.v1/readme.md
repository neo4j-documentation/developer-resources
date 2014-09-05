# cq - cypher queries for database/sql
A database/sql implementation for Cypher. I've released v1. I plan to change the API in the near future, but v1 will remain supported for some time.

If you'd like to use the new [gopkg.in](http://godoc.org/gopkg.in/docs.v1) semantic versioning system:

```go
import "gopkg.in/cq.v1"
```

[![Build Status](https://travis-ci.org/go-cq/cq.svg?branch=master)](https://travis-ci.org/go-cq/cq)
[![Coverage Status](https://img.shields.io/coveralls/go-cq/cq.svg)](https://coveralls.io/r/go-cq/cq?branch=master)
[![Waffle](https://badge.waffle.io/go-cq/cq.png?label=ready)](https://waffle.io/go-cq/cq)
[![Gitter chat](https://badges.gitter.im/go-cq/cq.png)](https://gitter.im/go-cq/cq)

Thanks to [Baron](http://twitter.com/xaprb), [Mike](http://twitter.com/mikearpaia), and [Jason](https://github.com/jmcvetta) for the ideas/motivation to start on this project. Cypher is close enough to SQL that it seems to fit pretty well in the idiomatic database/sql implementation.

#### Other Go drivers for Neo4j that support Cypher
* [Neoism](https://github.com/jmcvetta/neoism) (a careful/complete REST API implementation)
* [GonormCypher](https://github.com/marpaia/GonormCypher) (a port of AnormCypher, to get up and running quickly)
* [neo4j-go](https://github.com/jakewins/neo4j-go) (Jake's experimental Cypher driver)

## usage
See the [excellent database/sql tutorial](http://go-database-sql.org/index.html) from [VividCortex](https://vividcortex.com/), as well as the [package documentation for database/sql](http://golang.org/pkg/database/sql/) for an introduction to the idiomatic go database access.

You can (and should) use parameters, but the placeholders must be numbers in sequence, e.g. `{0}`, `{1}`, `{2}`, and then you must put them in order in the calls to `Query`/`Exec`. If you'd like to use named parameters, you can use the [sqlx](https://github.com/jmoiron/sqlx) library along with cq. Please let me know if any issues arise from using sqlx with cq--it is not thoroughly tested.

## [minimum viable snippet](http://blog.fogus.me/2012/08/23/minimum-viable-snippet/)

```go
package main

import (
	"database/sql"
	"log"
	
	_ "gopkg.in/cq.v1"
)

func main() {
	db, err := sql.Open("neo4j-cypher", "http://localhost:7474")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	stmt, err := db.Prepare(`
		match (n:User)-[:FOLLOWS]->(m:User) 
		where n.screenName = {0} 
		return m.screenName as friend
		limit 10
	`)
	if err != nil {
		log.Fatal(err)
	}
	defer stmt.Close()

	rows, err := stmt.Query("wefreema")
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()

	var friend string
	for rows.Next() {
		err := rows.Scan(&friend)
		if err != nil {
			log.Fatal(err)
		}
		log.Println(friend)
	}
}
```

## transactional API
The transactional API using `db.Begin()` is optimized for sending many queries to the [transactional Cypher endpoint](http://docs.neo4j.org/chunked/milestone/rest-api-transactional.html), in that it will batch them up and send them in chunks by default. Currently only supports `stmt.Exec()` within a transaction, will work on supporting `stmt.Query()` next and queueing up results.

#### transactional API example
```go
func main() {
	db, err := sql.Open("neo4j-cypher", "http://localhost:7474")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	tx, err := db.Begin()
	if err != nil {
		log.Fatal(err)
	}
	
	stmt, err := tx.Prepare("create (:User {screenName:{0}})")	
	if err != nil {
		log.Fatal(err)
	}
	
	stmt.Exec("wefreema")
	stmt.Exec("JnBrymn")
	stmt.Exec("technige")
	
	err := tx.Commit()
	if err != nil {
		log.Fatal(err)
	}
}
```

## types subpackage

database/sql out of the box doesn't implement many types to pass in as parameters or Scan() out of rows. Custom Cypher types are implemented in the `cq/types` subpackage (`import "gopkg.in/cq.v1/types"`). These custom types allow users of cq to `Scan()` types out of results, as well as pass types in as parameters.

| Go type			| Can be <br/>query parameter?	| cq wrapper, for Scan	| CypherType uint8 |
|:------------------ |:------------------:|:--------------------- | --------------------- |
| `nil`						| yes						| `CypherValue`				| `CypherNull`						|
| `bool`						| yes						| use go `bool`				| `CypherBoolean`					|
| `string`					| yes						| use go `string`				| `CypherString`					|
| `int`						| yes						| use go `int`					| `CypherInt`					|
| `int64`					| yes						| use go `int64`				| `CypherInt64`					|
| `float64`					| yes						| use go `float64`			| `CypherFloat64`					|
| `time.Time`				| yes						| `NullTime`			| `NullTime`					|
| `types.Node`				| no						| `Node`							| `CypherNode`						|
| `types.Relationship`	| no						| `Relationship`				| `CypherRelationship`			|
| `types.CypherValue`	| yes						| `CypherValue`				| `CypherValueType`			|
| N/A							| no						| not implemented				| `CypherPath`						|
| `[]string`				| yes						| `ArrayString`				| `CypherArrayString` |
| `[]int`					| yes						| `ArrayInt`					| `CypherArrayInt` |
| `[]int64`					| yes						| `ArrayInt64`					| `CypherArrayInt64` |
| `[]float64`				| yes						| `ArrayFloat64`				| `CypherArrayFloat64`	|
| `[]types.CypherValue`	| yes						| `ArrayCypherValue`			| `CypherArrayCypherValue`	|
| `map[string]string`	| yes						| `MapStringString`			| `CypherMapStringString`			|
| `map[string]types.CypherValue`| yes			| `MapStringCypherValue`	| `CypherMapStringCypherValue`				|

## transactional API benchmarks
Able to get sustained times of 20k+ cypher statements per second, even with multiple nodes per create... on a 2011 vintage macbook.

```
(master ✓) wes-macbook:cq go test -bench=".*Transaction.*" -test.benchtime=10s
PASS
BenchmarkTransactional10SimpleCreate	  100000	    150630 ns/op
BenchmarkTransactional100SimpleCreate	  500000	     39202 ns/op
BenchmarkTransactional1000SimpleCreate	 1000000	     27320 ns/op
BenchmarkTransactional10000SimpleCreate	  500000	     28524 ns/op
ok  	github.com/wfreeman/cq	79.973s
```

## thanks
Thanks to issue reporters and [contributors](https://github.com/go-cq/cq/graphs/contributors)!

## license

MIT license. See license file.

