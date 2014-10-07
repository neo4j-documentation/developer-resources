package cq

import (
	"database/sql"
	"log"
	"testing"
	. "gopkg.in/check.v1"
)

// This file is meant to hold integration tests where cq must be imported

type DriverSuite struct{}

var _ = Suite(&DriverSuite{})

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

func (s *DriverSuite) TestDbQuery(c *C) {
	db := testConn()
	rows, err := db.Query("return 1")
	c.Assert(err, IsNil)

	if rows == nil {
		c.Fatal("rows shouldn't be nil")
	}
}

func (s *DriverSuite) TestDbExec(c *C) {
	db := testConn()
	result, err := db.Exec("return 1")
	c.Assert(err, IsNil)

	if result == nil {
		c.Fatal("result should not be nil")
	}
}

func (s *DriverSuite) TestQuerySimple(c *C) {
	rows := prepareAndQuery("return 1")
	hasNext := rows.Next()
	if !hasNext {
		c.Fatal("no next!")
	}

	var test int
	err := rows.Scan(&test)
	c.Assert(err, IsNil)

	if test != 1 {
		c.Fatal("test != 1")
	}
}

func (s *DriverSuite) TestQuerySimpleFloat(c *C) {
	rows := prepareAndQuery("return 1.2")
	rows.Next()
	var test float64
	err := rows.Scan(&test)
	c.Assert(err, IsNil)

	if test != 1.2 {
		c.Fatal("test != 1.2")
	}
}

func (s *DriverSuite) TestQueryFloatParam(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query(1234567910.891)
	rows.Next()
	var test float64
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test, Equals, 1234567910.891)
}

func (s *DriverSuite) TestQuerySimpleString(c *C) {
	rows := prepareAndQuery("return '123'")
	rows.Next()
	var test string
	err := rows.Scan(&test)
	c.Assert(err, IsNil)

	if test != "123" {
		c.Fatal("test != '123';", test)
	}
}

func (s *DriverSuite) TestQueryStringParam(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query("123")
	rows.Next()
	var test string
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test, Equals, "123")
}

func (s *DriverSuite) TestQueryArrayByteParam(c *C) {
	c.Skip("byte arrays don't work yet")
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query([]byte("123"))
	rows.Next()
	var test []byte
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(string(test), DeepEquals, string([]byte("123")))
}

func (s *DriverSuite) TestQuerySimpleBool(c *C) {
	rows := prepareAndQuery("return true")
	rows.Next()
	var test bool
	err := rows.Scan(&test)
	c.Assert(err, IsNil)

	if test != true {
		c.Fatal("test != true;", test)
	}
}

func (s *DriverSuite) TestQueryBoolParam(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query(true)
	rows.Next()
	var test bool
	err = rows.Scan(&test)
	c.Assert(err, IsNil)

	if test != true {
		c.Fatal("test != true;", test)
	}
}

func (s *DriverSuite) TestQueryBoolFalseParam(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query(false)
	rows.Next()
	var test bool
	err = rows.Scan(&test)
	c.Assert(err, IsNil)

	if test != false {
		c.Fatal("test != true;", test)
	}
}

func (s *DriverSuite) TestQueryIntParam(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query(123)
	c.Assert(err, IsNil)

	rows.Next()
	var test int
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test, Equals, 123)
}

func (s *DriverSuite) TestQueryNullString(c *C) {
	rows := prepareAndQuery("return null")
	rows.Next()
	var nullString sql.NullString
	err := rows.Scan(&nullString)
	c.Assert(err, IsNil)
	c.Assert(nullString.Valid, Equals, false)
}

func (s *DriverSuite) TestScanNullInt64(c *C) {
	rows := prepareAndQuery("return 123456789")
	rows.Next()
	var nullInt64 sql.NullInt64
	err := rows.Scan(&nullInt64)
	c.Assert(err, IsNil)
	c.Assert(nullInt64.Valid, Equals, true)
	c.Assert(nullInt64.Int64, Equals, int64(123456789))
}

func (s *DriverSuite) TestScanBigInt64(c *C) {
	rows := prepareAndQuery("return 123456789101112")
	rows.Next()
	var i64 int64
	err := rows.Scan(&i64)
	c.Assert(err, IsNil)
	c.Assert(i64, Equals, int64(123456789101112))
}

func (s *DriverSuite) TestScanBigInt64FloatBug(c *C) {
	rows := prepareAndQuery("return 23371710262672408")
	rows.Next()
	var i64 int64
	err := rows.Scan(&i64)
	c.Assert(err, IsNil)
	c.Assert(i64, Equals, int64(23371710262672408))
}

func (s *DriverSuite) TestExecNilRows(c *C) {
	db := testConn()
	db.Exec("...")
}
