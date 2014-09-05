package types_test

import (
	"database/sql"
	"log"
	"testing"
	. "gopkg.in/check.v1"
	_ "gopkg.in/cq.v1"
	"gopkg.in/cq.v1/types"
)

type TypesSuite struct{}

var _ = Suite(&TypesSuite{})

func Test(t *testing.T) {
	TestingT(t)
}

func testConn() *sql.DB {
	db, err := sql.Open("neo4j-cypher", "http://localhost:7474/")
	if err != nil {
		log.Fatal(err)
	}
	return db
}

func prepareTest(query string) *sql.Stmt {
	db := testConn()
	stmt, err := db.Prepare(query)
	if err != nil {
		log.Fatal(err)
	}
	return stmt
}

func prepareAndQuery(query string) *sql.Rows {
	stmt := prepareTest(query)
	rows, err := stmt.Query()
	if err != nil {
		log.Fatal(err)
	}
	return rows
}

func (s *TypesSuite) TestQueryCypherValueNull(c *C) {
	rows := prepareAndQuery("return null")
	rows.Next()
	var test types.CypherValue
	err := rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Type, Equals, types.CypherNull)
	c.Assert(test.Val, Equals, nil)
}

func (s *TypesSuite) TestQueryCypherValueBoolean(c *C) {
	rows := prepareAndQuery("return true")
	rows.Next()
	var test types.CypherValue
	err := rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Type, Equals, types.CypherBoolean)
	c.Assert(test.Val, Equals, true)
}

func (s *TypesSuite) TestQueryCypherValueString(c *C) {
	rows := prepareAndQuery("return 'asdf'")
	rows.Next()
	var test types.CypherValue
	err := rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Type, Equals, types.CypherString)
	c.Assert(test.Val, Equals, "asdf")
}

func (s *TypesSuite) TestQueryCypherValueInt64(c *C) {
	rows := prepareAndQuery("return 9223372000000000000")
	rows.Next()
	var test types.CypherValue
	err := rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, Equals, int64(9223372000000000000))
	c.Assert(test.Type, Equals, types.CypherInt64)
}

func (s *TypesSuite) TestQueryCypherValueInt(c *C) {
	rows := prepareAndQuery("return 1234567890")
	rows.Next()
	var test types.CypherValue
	err := rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Type, Equals, types.CypherInt)
	c.Assert(test.Val, Equals, 1234567890)
}

func (s *TypesSuite) TestQueryCypherValueIntArray(c *C) {
	rows := prepareAndQuery("return [1,2,2345678910]")
	rows.Next()
	var test types.CypherValue
	err := rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Type, Equals, types.CypherArrayInt)
	c.Assert(test.Val.([]int), DeepEquals, []int{1, 2, 2345678910})
}
