package types_test

import (
	"errors"

	. "gopkg.in/check.v1"
	_ "gopkg.in/cq.v1"
	"gopkg.in/cq.v1/types"
)

func (s *TypesSuite) TestQueryCypherValueArray(c *C) {
	rows := prepareAndQuery("return [1.1,2.1,'asdf']")
	rows.Next()
	var test types.ArrayCypherValue
	err := rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Val, DeepEquals,
		[]types.CypherValue{
			types.CypherValue{types.CypherFloat64, 1.1},
			types.CypherValue{types.CypherFloat64, 2.1},
			types.CypherValue{types.CypherString, "asdf"}})
}

func (s *TypesSuite) TestQueryNullCypherValueArray(c *C) {
	rows := prepareAndQuery("return null")
	rows.Next()
	var test types.ArrayCypherValue
	err := rows.Scan(&test)
	c.Assert(err, DeepEquals, errors.New("sql: Scan error on column index 0: cq: scan value is null"))
}
