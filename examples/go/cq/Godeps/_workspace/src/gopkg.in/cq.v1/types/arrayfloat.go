package types

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"fmt"
)

type ArrayFloat64 struct {
	Val []float64
}

func (af *ArrayFloat64) Scan(value interface{}) error {
	if value == nil {
		return ErrScanOnNil
	}

	switch value.(type) {
	case []float64:
		af.Val = value.([]float64)
		return nil
	case CypherValue:
		cv := value.(CypherValue)
		if cv.Type == CypherArrayFloat64 {
			af.Val = cv.Val.([]float64)
			return nil
		}
	}
	return errors.New(fmt.Sprintf("cq: invalid Scan value for %T: %T", af, value))
}

func (af ArrayFloat64) Value() (driver.Value, error) {
	b, err := json.Marshal(CypherValue{CypherArrayFloat64, af.Val})
	return b, err
}
