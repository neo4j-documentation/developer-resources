package types_test

import (
	"errors"

	. "gopkg.in/check.v1"
	_ "gopkg.in/cq.v1"
	"gopkg.in/cq.v1/types"
)

func (s *TypesSuite) TestQueryArrayIntParam(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query(types.ArrayInt{[]int{1, 2, 3}})
	c.Assert(err, IsNil)

	rows.Next()
	var test types.ArrayInt
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, DeepEquals, []int{1, 2, 3})
}

func (s *TypesSuite) TestQueryIntArrayParam(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query([]int{1, 2, 3})
	c.Assert(err, IsNil)

	rows.Next()
	var test types.ArrayInt
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, DeepEquals, []int{1, 2, 3})
}

func (s *TypesSuite) TestQueryArrayInt(c *C) {
	rows := prepareAndQuery("return [1,2,3]")
	rows.Next()
	var test types.ArrayInt
	err := rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, DeepEquals, []int{1, 2, 3})
}

func (s *TypesSuite) TestQueryBadIntArray(c *C) {
	rows := prepareAndQuery("return [1,2,'asdf']")
	rows.Next()
	var test types.ArrayInt
	err := rows.Scan(&test)
	c.Assert(err, DeepEquals, errors.New("sql: Scan error on column index 0: cq: invalid Scan value for *types.ArrayInt: []types.CypherValue"))
}

func (s *TypesSuite) TestQueryNullIntArray(c *C) {
	rows := prepareAndQuery("return null")
	rows.Next()
	var test types.ArrayInt
	err := rows.Scan(&test)
	c.Assert(err, DeepEquals, errors.New("sql: Scan error on column index 0: cq: scan value is null"))
}

func (s *TypesSuite) TestQueryIntArrayProperty(c *C) {
	stmt := prepareTest("create (a:Test {prop:{0}}) return a.prop[0], a.prop[1], a.prop[2]")
	rows, err := stmt.Query([]int{1, 2, 3})
	c.Assert(err, IsNil)

	rows.Next()
	var test1, test2, test3 int
	err = rows.Scan(&test1, &test2, &test3)
	c.Assert(err, IsNil)
	c.Assert(test1, Equals, 1)
	c.Assert(test2, Equals, 2)
	c.Assert(test3, Equals, 3)
}

func (s *TypesSuite) TestQueryArrayInt64Param(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query(types.ArrayInt64{[]int64{12345678910, 234567891011, 3456789101112}})
	c.Assert(err, IsNil)

	rows.Next()
	var test types.ArrayInt64
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, DeepEquals, []int64{12345678910, 234567891011, 3456789101112})
}

func (s *TypesSuite) TestQueryInt64ArrayParam(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query([]int64{12345678910, 234567891011, 3456789101112})
	c.Assert(err, IsNil)

	rows.Next()
	var test types.ArrayInt64
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, DeepEquals, []int64{12345678910, 234567891011, 3456789101112})
}

func (s *TypesSuite) TestQueryArrayInt64(c *C) {
	rows := prepareAndQuery("return [12345678910, 234567891011, 3456789101112]")
	rows.Next()
	var test types.ArrayInt64
	err := rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, DeepEquals, []int64{12345678910, 234567891011, 3456789101112})
}

func (s *TypesSuite) TestQueryBadInt64Array(c *C) {
	rows := prepareAndQuery("return [123456789,'asdf']")
	rows.Next()
	var test types.ArrayInt64
	err := rows.Scan(&test)
	c.Assert(err, DeepEquals, errors.New("sql: Scan error on column index 0: cq: invalid Scan value for *types.ArrayInt64: []types.CypherValue"))
}

func (s *TypesSuite) TestQueryNullInt64Array(c *C) {
	rows := prepareAndQuery("return null")
	rows.Next()
	var test types.ArrayInt64
	err := rows.Scan(&test)
	c.Assert(err, DeepEquals, errors.New("sql: Scan error on column index 0: cq: scan value is null"))
}
