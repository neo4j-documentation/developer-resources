package types

import (
	"encoding/json"
	"errors"
)

type Relationship struct {
	Type       string                 `json:"type"`
	SelfURI    string                 `json:"self"`
	Properties map[string]CypherValue `json:"data"`
}

func (r *Relationship) Scan(value interface{}) error {
	if value == nil {
		return ErrScanOnNil
	}

	switch value.(type) {
	case map[string]CypherValue:
		cv := value.(map[string]CypherValue)
		var ok = false
		var inner CypherValue
		inner, ok = cv["data"]
		if ok != true {
			break
		}
		r.Properties = inner.Val.(map[string]CypherValue)
		inner, ok = cv["self"]
		if ok != true {
			break
		}
		r.SelfURI = inner.Val.(string)
		inner, ok = cv["type"]
		if ok != true {
			break
		}
		r.Type = inner.Val.(string)
		return nil
	case []byte:
		err := json.Unmarshal(value.([]byte), &r)
		return err
	}
	return errors.New("cq: invalid Scan value for Relationship")
}
