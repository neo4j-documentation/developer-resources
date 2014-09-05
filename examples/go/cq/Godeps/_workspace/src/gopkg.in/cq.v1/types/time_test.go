package types_test

import (
	"time"

	. "gopkg.in/check.v1"
	_ "gopkg.in/cq.v1"
	"gopkg.in/cq.v1/types"
)

func (s *TypesSuite) TestScanTime(c *C) {
	stmt := prepareTest("with {0} as test return test")
	rows, err := stmt.Query(1395967804 * 1000)
	c.Assert(err, IsNil)

	rows.Next()
	var test types.NullTime
	err = rows.Scan(&test)
	c.Assert(err, IsNil)
	c.Assert(test.Valid, Equals, true)
	c.Assert(test.Time, DeepEquals, time.Unix(0, 1395967804*1000*1000000))
}
