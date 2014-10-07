package types

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"fmt"
)

type ArrayInt struct {
	Val []int
}

func (ai *ArrayInt) Scan(value interface{}) error {
	if value == nil {
		return ErrScanOnNil
	}

	switch value.(type) {
	case []int:
		ai.Val = value.([]int)
		return nil
	case CypherValue:
		cv := value.(CypherValue)
		if cv.Type == CypherArrayInt {
			ai.Val = cv.Val.([]int)
			return nil
		}
	}
	return errors.New(fmt.Sprintf("cq: invalid Scan value for %T: %T", ai, value))
}

func (ai ArrayInt) Value() (driver.Value, error) {
	b, err := json.Marshal(CypherValue{CypherArrayInt, ai.Val})
	return b, err
}

type ArrayInt64 struct {
	Val []int64
}

func (ai *ArrayInt64) Scan(value interface{}) error {
	if value == nil {
		return ErrScanOnNil
	}

	switch value.(type) {
	case []int:
		iv := value.([]int)
		ai.Val = []int64{}
		for _, v := range iv {
			ai.Val = append(ai.Val, int64(v))
		}
		return nil
	case []int64:
		ai.Val = value.([]int64)
		return nil
	case CypherValue:
		cv := value.(CypherValue)
		if cv.Type == CypherArrayInt64 {
			ai.Val = cv.Val.([]int64)
			return nil
		}
	}
	return errors.New(fmt.Sprintf("cq: invalid Scan value for %T: %T", ai, value))
}

func (ai ArrayInt64) Value() (driver.Value, error) {
	b, err := json.Marshal(CypherValue{CypherArrayInt64, ai.Val})
	return b, err
}
