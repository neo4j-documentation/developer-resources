package types_test

import (
	"database/sql"

	. "gopkg.in/check.v1"
	_ "gopkg.in/cq.v1"
	"gopkg.in/cq.v1/types"
)

func (s *TypesSuite) TestQueryNode(c *C) {
	conn, err := sql.Open("neo4j-cypher", "http://localhost:7474/")
	c.Assert(err, IsNil)
	stmt, err := conn.Prepare(`create (a:Test {foo:"bar", i:1}) return a`)
	c.Assert(err, IsNil)
	rows, err := stmt.Query()
	c.Assert(err, IsNil)

	rows.Next()
	var test types.Node
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	t1 := types.Node{}
	t1.Properties = map[string]types.CypherValue{}
	t1.Properties["foo"] = types.CypherValue{types.CypherString, "bar"}
	t1.Properties["i"] = types.CypherValue{types.CypherInt, 1}
	c.Assert(test.Properties, DeepEquals, t1.Properties)
	labels, err := test.Labels("http://localhost:7474/")
	c.Assert(err, IsNil)
	c.Assert(labels, DeepEquals, []string{"Test"})
}
