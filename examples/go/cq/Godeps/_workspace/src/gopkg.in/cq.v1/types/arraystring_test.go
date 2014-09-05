package types_test

import (
	"errors"
	. "gopkg.in/check.v1"
	_ "gopkg.in/cq.v1"
	"gopkg.in/cq.v1/types"
)

func (s *TypesSuite) TestQueryArrayStringParam(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query(types.ArrayString{[]string{"1", "2", "3"}})
	c.Assert(err, IsNil)

	rows.Next()
	var test types.ArrayString
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, DeepEquals, []string{"1", "2", "3"})
}

func (s *TypesSuite) TestQueryStringArrayParam(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query([]string{"1", "2", "3"})
	c.Assert(err, IsNil)

	rows.Next()
	var test types.ArrayString
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, DeepEquals, []string{"1", "2", "3"})
}

func (s *TypesSuite) TestQueryArrayString(c *C) {
	rows := prepareAndQuery("return ['1','2','3']")
	rows.Next()
	var test types.ArrayString
	err := rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, DeepEquals, []string{"1", "2", "3"})
}

func (s *TypesSuite) TestQueryBadStringArray(c *C) {
	rows := prepareAndQuery("return [1,2,'asdf']")
	rows.Next()
	var test types.ArrayString
	err := rows.Scan(&test)
	c.Assert(err, DeepEquals, errors.New("sql: Scan error on column index 0: cq: invalid Scan value for *types.ArrayString: []types.CypherValue"))
}

func (s *TypesSuite) TestQueryNullStringArray(c *C) {
	rows := prepareAndQuery("return null")
	rows.Next()
	var test types.ArrayString
	err := rows.Scan(&test)
	c.Assert(err, DeepEquals, errors.New("sql: Scan error on column index 0: cq: scan value is null"))
}
