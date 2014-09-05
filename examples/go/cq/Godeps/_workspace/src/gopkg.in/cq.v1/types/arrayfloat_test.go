package types_test

import (
	"errors"

	. "gopkg.in/check.v1"
	_ "gopkg.in/cq.v1"
	"gopkg.in/cq.v1/types"
)

func (s *TypesSuite) TestQueryArrayFloat64Param(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query(types.ArrayFloat64{[]float64{1.1, 2.1, 3.1}})
	c.Assert(err, IsNil)

	rows.Next()
	var test types.ArrayFloat64
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, DeepEquals, []float64{1.1, 2.1, 3.1})
}

func (s *TypesSuite) TestQueryFloat64ArrayParam(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query([]float64{1.1, 2.1, 3.1})
	c.Assert(err, IsNil)

	rows.Next()
	var test types.ArrayFloat64
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, DeepEquals, []float64{1.1, 2.1, 3.1})
}

func (s *TypesSuite) TestQueryArrayFloat64(c *C) {
	rows := prepareAndQuery("return [1.1,2.1,3.1]")
	rows.Next()
	var test types.ArrayFloat64
	err := rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, DeepEquals, []float64{1.1, 2.1, 3.1})
}

func (s *TypesSuite) TestQueryBadFloatArray(c *C) {
	rows := prepareAndQuery("return [1.1,2.1,'asdf']")
	rows.Next()
	var test types.ArrayFloat64
	err := rows.Scan(&test)
	c.Assert(err, DeepEquals, errors.New("sql: Scan error on column index 0: cq: invalid Scan value for *types.ArrayFloat64: []types.CypherValue"))
}

func (s *TypesSuite) TestQueryNullFloat64Array(c *C) {
	rows := prepareAndQuery("return null")
	rows.Next()
	var test types.ArrayFloat64
	err := rows.Scan(&test)
	c.Assert(err, DeepEquals, errors.New("sql: Scan error on column index 0: cq: scan value is null"))
}

func (s *TypesSuite) TestQueryFloat64ArrayProperty(c *C) {
	stmt := prepareTest("create (a:Test {prop:{0}}) return a.prop[0], a.prop[1], a.prop[2]")
	rows, err := stmt.Query([]float64{1.1, 2.2, 3.3})
	c.Assert(err, IsNil)

	rows.Next()
	var test1, test2, test3 float64
	err = rows.Scan(&test1, &test2, &test3)
	c.Assert(err, IsNil)
	c.Assert(test1, Equals, 1.1)
	c.Assert(test2, Equals, 2.2)
	c.Assert(test3, Equals, 3.3)
}
