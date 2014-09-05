package types

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"fmt"
)

type ArrayString struct {
	Val []string
}

func (as *ArrayString) Scan(value interface{}) error {
	if value == nil {
		return ErrScanOnNil
	}

	switch value.(type) {
	case []string:
		as.Val = value.([]string)
		return nil
	case CypherValue:
		cv := value.(CypherValue)
		if cv.Type == CypherArrayString {
			as.Val = cv.Val.([]string)
			return nil
		}
	}
	return errors.New(fmt.Sprintf("cq: invalid Scan value for %T: %T", as, value))
}

func (as ArrayString) Value() (driver.Value, error) {
	b, err := json.Marshal(CypherValue{CypherArrayString, as.Val})
	return b, err
}
