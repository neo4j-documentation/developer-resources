package cq

import (
	"database/sql/driver"
	"log"
	. "gopkg.in/check.v1"
)

type StatementSuite struct{}

var _ = Suite(&StatementSuite{})

func prepareStmtTest(query string) driver.Stmt {
	db := openTest()
	if db == nil {
		log.Fatal("can't connect to test db: ", testURL)
	}
	stmt, err := db.Prepare(query)
	if err != nil {
		log.Print(err)
	}
	return stmt
}

func (s *StatementSuite) TestQuerySimple(c *C) {
	stmt := prepareStmtTest("return 1")
	rows, err := stmt.Query([]driver.Value{})
	c.Assert(err, IsNil)
	dest := make([]driver.Value, 1)

	err = rows.Next(dest)
	c.Assert(err, IsNil)

	if rows.Columns()[0] != "1" {
		c.Fatal("column doesn't match")
	}

	err = rows.Next(dest)
	if err == nil {
		c.Fatal("doesn't end after first row")
	}
}
