package types

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"fmt"
)

type MapStringString struct {
	Val map[string]string
}

func (mss *MapStringString) Scan(value interface{}) error {
	if value == nil {
		return ErrScanOnNil
	}

	switch value.(type) {
	case map[string]string:
		mss.Val = value.(map[string]string)
		return nil
	case CypherValue:
		cv := value.(CypherValue)
		if cv.Type == CypherMapStringString {
			mss.Val = cv.Val.(map[string]string)
			return nil
		}
	}
	return errors.New(fmt.Sprintf("cq: invalid Scan value for %T: %T", mss, value))
}

func (mss MapStringString) Value() (driver.Value, error) {
	b, err := json.Marshal(CypherValue{CypherMapStringString, mss.Val})
	return b, err
}
