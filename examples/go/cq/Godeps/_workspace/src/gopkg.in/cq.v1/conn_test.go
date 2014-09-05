package cq

import (
	"database/sql/driver"
	"flag"
	"log"
	. "gopkg.in/check.v1"
)

type ConnSuite struct{}

var (
	_       = Suite(&ConnSuite{})
	testURL = flag.String("testdb", "http://localhost:7474/", "the base url for the test db")
)

//func Test(t *testing.T) {
//	TestingT(t)
//}

func openTest() driver.Conn {
	db, err := Open(*testURL)
	if err != nil {
		log.Println("can't connect to db.")
		return nil
	}
	return db
}

func (s *ConnSuite) TestOpen(c *C) {
	db := openTest()
	if db == nil {
		c.Fatal("can't connect to test db: ", *testURL)
	}
}

func (s *ConnSuite) TestPrepareNoParams(c *C) {
	db := openTest()
	if db == nil {
		c.Fatal("can't connect to test db: ", *testURL)
	}
	stmt, err := db.Prepare("match (n) return n limit 1")
	c.Assert(err, IsNil)
	if stmt == nil {
		c.Fatal("stmt is nil")
	}
}

func (s *ConnSuite) TestBadURL(c *C) {
	db, err := Open("")
	if err == nil {
		c.Fatal("err was nil!")
	}
	if db != nil {
		c.Fatal("db should be nil:", db)
	}
}
