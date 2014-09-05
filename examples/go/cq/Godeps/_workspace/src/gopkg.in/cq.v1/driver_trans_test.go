package cq

import (
	"log"
	"time"

	. "gopkg.in/check.v1"
	//	_ "gopkg.in/cq.v1"
)

// This file is meant to hold integration tests where cq must be imported as _
// and is for testing transactions. Some of these are going to be long tests...

type TransactionSuite struct{}

var _ = Suite(&TransactionSuite{})

func clearTestRecords() {
	db := testConn()
	_, err := db.Exec("match (n:`TestRollback~~~~`) delete n")
	if err != nil {
		log.Fatal(err)
	}
	_, err = db.Exec("match (n:`TestCommit~~~~`) delete n")
	if err != nil {
		log.Fatal(err)
	}
}

func (s *TransactionSuite) SetUpTest(c *C) {
	clearTestRecords()
}

func (s *TransactionSuite) TearDownTest(c *C) {
	clearTestRecords()
}

func (s *TransactionSuite) TestTransactionRollback1(c *C) {
	testTransactionRollbackN(c, 1)
}
func (s *TransactionSuite) TestTransactionRollback7(c *C) {
	testTransactionRollbackN(c, 7)
}
func (s *TransactionSuite) TestTransactionRollback100(c *C) {
	testTransactionRollbackN(c, 100)
}
func (s *TransactionSuite) TestTransactionRollback1000(c *C) {
	testTransactionRollbackN(c, 1000)
}
func (s *TransactionSuite) TestTransactionRollback7777(c *C) {
	testTransactionRollbackN(c, 7777)
}

func testTransactionRollbackN(c *C, n int) {
	db := testConn()
	tx, err := db.Begin()
	c.Assert(err, IsNil)

	for i := 0; i < n; i++ {
		_, err := tx.Exec("create (:`TestRollback~~~~`)")
		c.Assert(err, IsNil)
	}

	err = tx.Rollback()
	c.Assert(err, IsNil)

	rows, err := db.Query("match (n:`TestRollback~~~~`) return count(1)")
	c.Assert(err, IsNil)
	defer rows.Close()

	rows.Next()

	var count int
	err = rows.Scan(&count)
	c.Assert(err, IsNil)

	if count > 0 {
		c.Fatal("rollback doesn't work")
	}
}

func (s *TransactionSuite) TestTransactionExecCommit1(c *C) {
	testTransactionExecCommitN(c, 1, 0)
}
func (s *TransactionSuite) TestTransactionExecCommit77(c *C) {
	testTransactionExecCommitN(c, 77, 0)
}
func (s *TransactionSuite) TestTransactionExecCommit100(c *C) {
	testTransactionExecCommitN(c, 100, 0)
}
func (s *TransactionSuite) TestTransactionExecCommit1000(c *C) {
	testTransactionExecCommitN(c, 1000, 0)
}
func (s *TransactionSuite) TestTransactionExecCommit7777(c *C) {
	testTransactionExecCommitN(c, 7777, 0)
}
func (s *TransactionSuite) TestTransactionExecCommit1Rec2Secs(c *C) {
	testTransactionExecCommitN(c, 1, 2*time.Second)
}

func testTransactionExecCommitN(c *C, n int, delay time.Duration) {
	db := testConn()
	tx, err := db.Begin()
	c.Assert(err, IsNil)

	for i := 0; i < n; i++ {
		_, err := tx.Exec("create (:`TestCommit~~~~` {id:{0}})", i)
		c.Assert(err, IsNil)
	}

	time.Sleep(delay)

	err = tx.Commit()
	c.Assert(err, IsNil)

	rows, err := db.Query("match (n:`TestCommit~~~~`) return n.id order by n.id")
	c.Assert(err, IsNil)
	defer rows.Close()

	var count int
	var i int
	for rows.Next() {
		if i > n {
			c.Fatal("i shouldn't be > n")
		}
		err = rows.Scan(&count)
		c.Assert(err, IsNil)
		i++
	}
	c.Assert(i, Equals, n)
}

func (s *TransactionSuite) TestTxBadCypherError(c *C) {
	db := testConn()
	tx, err := db.Begin()
	c.Assert(err, IsNil)

	for i := 0; i < 1000; i++ {
		_, err := tx.Exec("create (:`TestCommit~~~~` {id:{0}})")
		if i%100 != 99 {
			c.Assert(err, IsNil)
		} else {
			if err == nil {
				c.Fatal(err)
			}
		}
	}
	err = tx.Commit()
	if err == nil {
		c.Fatal(err)
	}
}
