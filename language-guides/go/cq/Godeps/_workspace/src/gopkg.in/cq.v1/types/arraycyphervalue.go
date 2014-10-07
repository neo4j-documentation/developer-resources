package types

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"fmt"
)

type ArrayCypherValue struct {
	Val []CypherValue
}

func (acv *ArrayCypherValue) Scan(value interface{}) error {
	if value == nil {
		return ErrScanOnNil
	}

	switch value.(type) {
	case []CypherValue:
		acv.Val = value.([]CypherValue)
		return nil
	case CypherValue:
		cv := value.(CypherValue)
		if cv.Type == CypherArrayCypherValue {
			acv.Val = cv.Val.([]CypherValue)
			return nil
		}
	}
	return errors.New(fmt.Sprintf("cq: invalid Scan value for %T: %T", acv, value))
}

func (acv ArrayCypherValue) Value() (driver.Value, error) {
	b, err := json.Marshal(CypherValue{CypherArrayCypherValue, acv.Val})
	return b, err
}
