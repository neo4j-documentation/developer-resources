package types

import (
	"fmt"
	"time"
)

type NullTime struct {
	Time  time.Time
	Valid bool
}

func (nt *NullTime) Scan(value interface{}) error {
	if value == nil {
		nt.Valid = false
		return nil
	}

	switch value.(type) {
	// do we need to handle int64 too?
	case int:
		nt.Time = time.Unix(0, int64(value.(int)*1000000))
		nt.Valid = true
		return nil
	case CypherValue:
		cv := value.(CypherValue)
		if cv.Type == CypherInt64 {
			nt.Time = time.Unix(0, cv.Val.(int64)*1000000)
			nt.Valid = true
			return nil
		}
	default:
		fmt.Println(value)
	}
	nt.Valid = false
	return nil
}
