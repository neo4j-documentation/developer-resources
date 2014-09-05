package types

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"fmt"
)

type MapStringCypherValue struct {
	Val map[string]CypherValue
}

func (msc *MapStringCypherValue) Scan(value interface{}) error {
	if value == nil {
		return ErrScanOnNil
	}

	switch value.(type) {
	case map[string]CypherValue:
		msc.Val = value.(map[string]CypherValue)
		return nil
	case CypherValue:
		cv := value.(CypherValue)
		if cv.Type == CypherMapStringString {
			msc.Val = cv.Val.(map[string]CypherValue)
			return nil
		}
	}
	return errors.New(fmt.Sprintf("cq: invalid Scan value for %T: %T", msc, value))
}

func (msc MapStringCypherValue) Value() (driver.Value, error) {
	b, err := json.Marshal(CypherValue{CypherMapStringCypherValue, msc.Val})
	return b, err
}
