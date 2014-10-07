package types

import (
	"bytes"
	"database/sql/driver"
	"encoding/json"
	"errors"
	"fmt"
	"reflect"
	"strconv"
	"strings"
)

type CypherType uint8

var (
	ErrScanOnNil = errors.New("cq: scan value is null")
)

// supported types
const (
	CypherNull CypherType = iota
	CypherBoolean
	CypherString
	CypherInt64
	CypherInt
	CypherFloat64
	CypherArrayInt
	CypherArrayInt64
	CypherArrayByte
	CypherArrayFloat64
	CypherArrayString
	CypherArrayCypherValue
	CypherMapStringString
	CypherMapStringCypherValue
	CypherNode
	CypherRelationship
	CypherPath
	CypherValueType
)

func (v *CypherValue) Scan(value interface{}) error {
	if v == nil {
		return ErrScanOnNil
	}
	if value == nil {
		v.Val = nil
		v.Type = CypherNull
		return nil
	}

	switch value.(type) {
	case bool:
		v.Type = CypherBoolean
		v.Val = value
		return nil
	case string:
		v.Type = CypherString
		v.Val = value
		return nil
	case int:
		if value.(int) > ((1 << 31) - 1) {
			v.Type = CypherInt64
			v.Val = int64(value.(int))
			return nil
		}
		v.Type = CypherInt
		v.Val = value
		return nil
	case []byte:
		err := json.Unmarshal(value.([]byte), &v)
		if err != nil {
			return err
		}
	case []int:
		v.Type = CypherArrayInt
		v.Val = value.([]int)
		return nil
	case []string:
		v.Type = CypherArrayString
		v.Val = value.([]string)
		return nil
	}

	return errors.New(fmt.Sprintf("cq: invalid Scan value for %T: %T", v, value))
}

type CypherValue struct {
	Type CypherType
	Val  interface{}
}

func (cv *CypherValue) Value() (driver.Value, error) {
	//fmt.Println("Value() cv:", cv)
	switch cv.Type {
	case CypherInt:
		return cv.Val.(int), nil
	case CypherFloat64:
		return cv.Val.(float64), nil
	}
	b, err := json.Marshal(cv)
	return b, err
}

func (c *CypherValue) UnmarshalJSON(b []byte) error {
	if len(b) > 0 && bytes.HasPrefix(b, []byte("{\"Type\"")) {
		start := bytes.Index(b, []byte(":"))
		end := bytes.Index(b, []byte(","))
		if start > 0 && end > 0 {
			t, err := strconv.Atoi(string(b[start+1 : end]))
			if err != nil {
				return err
			}
			c.Type = CypherType(t)
			switch c.Type {
			case CypherString:
				var s string
				err := json.Unmarshal(b[end+7:len(b)-1], &s)
				if err != nil {
					return err
				}
				c.Val = s
				return nil
			case CypherFloat64:
				var f float64
				err := json.Unmarshal(b[end+7:len(b)-1], &f)
				if err != nil {
					return err
				}
				c.Val = f
				return nil
			case CypherInt64:
				var i int64
				err := json.Unmarshal(b[end+7:len(b)-1], &i)
				if err != nil {
					return err
				}
				c.Val = i
				return nil
			case CypherInt:
				var i int
				err := json.Unmarshal(b[end+7:len(b)-1], &i)
				if err != nil {
					return err
				}
				c.Val = i
				return nil
			case CypherArrayInt:
				var ai = []int{}
				err := json.Unmarshal(b[end+7:len(b)-1], &ai)
				if err != nil {
					return err
				}
				c.Val = ai
				return nil
			case CypherArrayInt64:
				var ai = []int64{}
				err := json.Unmarshal(b[end+7:len(b)-1], &ai)
				if err != nil {
					return err
				}
				c.Val = ai
				return nil
			case CypherArrayFloat64:
				var af = []float64{}
				err := json.Unmarshal(b[end+7:len(b)-1], &af)
				if err != nil {
					return err
				}
				c.Val = af
				return nil
			case CypherArrayString:
				var as = []string{}
				// need to refactor this to avoid hardcoding
				err := json.Unmarshal(b[end+7:len(b)-1], &as)
				if err != nil {
					return err
				}
				c.Val = as
				return nil
			case CypherMapStringString:
				var mss = map[string]string{}
				// need to refactor this to avoid hardcoding
				err := json.Unmarshal(b[end+7:len(b)-1], &mss)
				if err != nil {
					return err
				}
				c.Val = mss
				return nil
			case CypherMapStringCypherValue:
				var msc = map[string]CypherValue{}
				// need to refactor this to avoid hardcoding
				err := json.Unmarshal(b[end+7:len(b)-1], &msc)
				if err != nil {
					return err
				}
				c.Val = msc
				return nil
			}
		}
	}
	//fmt.Println("parsing raw cypher value (unwrapped)...")
	var err error
	str := string(b)
	switch str {
	case "null":
		c.Val = nil
		c.Type = CypherNull
		return nil
	case "true":
		c.Val = true
		c.Type = CypherBoolean
		return nil
	case "false":
		c.Val = false
		c.Type = CypherBoolean
		return nil
	}
	if len(b) > 0 {
		switch b[0] {
		case byte('"'):
			c.Val = strings.Trim(str, "\"")
			c.Type = CypherString
			return nil
		case byte('{'):
			var mss = map[string]string{}
			err = json.Unmarshal(b, &mss)
			if err == nil {
				c.Val = mss
				c.Type = CypherMapStringString
				return nil
			}
			var mscv = map[string]CypherValue{}
			err = json.Unmarshal(b, &mscv)
			if err == nil {
				c.Val = mscv
				c.Type = CypherMapStringCypherValue
				return nil
			}
		case byte('['):
			var ai = []int{}
			err = json.Unmarshal(b, &ai)
			if err == nil {
				c.Val = ai
				c.Type = CypherArrayInt
				return nil
			}
			var af = []float64{}
			err = json.Unmarshal(b, &af)
			if err == nil {
				c.Val = af
				c.Type = CypherArrayFloat64
				return nil
			}
			var as = []string{}
			err = json.Unmarshal(b, &as)
			if err == nil {
				c.Val = as
				c.Type = CypherArrayString
				return nil
			}
			var acv = []CypherValue{}
			err = json.Unmarshal(b, &acv)
			if err == nil {
				c.Val = acv
				c.Type = CypherArrayCypherValue
				return nil
			}
			return nil
		}
	}
	c.Val, err = strconv.Atoi(str)
	if err == nil {
		c.Type = CypherInt
		return nil
	}
	c.Val, err = strconv.ParseInt(str, 10, 64)
	if err == nil {
		c.Type = CypherInt64
		return nil
	}
	c.Val, err = strconv.ParseFloat(str, 64)
	if err == nil {
		c.Type = CypherFloat64
		return nil
	}
	ai := []int{}
	err = json.Unmarshal(b, &ai)
	if err == nil {
		c.Val = ai
		c.Type = CypherArrayInt
		return nil
	}
	c.Val = b
	c.Type = CypherValueType
	//json.Unmarshal(b, &c.Val)
	return nil
}

func (cv CypherValue) ConvertValue(v interface{}) (driver.Value, error) {
	if driver.IsValue(v) {
		return v, nil
	}

	if svi, ok := v.(driver.Valuer); ok {
		sv, err := svi.Value()
		if err != nil {
			return nil, err
		}
		if !driver.IsValue(sv) {
			return nil, fmt.Errorf("non-Value type %T returned from Value", sv)
		}
		return sv, nil
	}

	rv := reflect.ValueOf(v)
	switch rv.Kind() {
	case reflect.Slice:
		b := CypherValue{}
		switch v.(type) {
		case []int:
			b.Type = CypherArrayInt
			b.Val = v
		case []int64:
			b.Type = CypherArrayInt64
			b.Val = v
		case []float64:
			b.Type = CypherArrayFloat64
			b.Val = v
		case []string:
			b.Type = CypherArrayString
			b.Val = v
		}
		return b.Value()
	case reflect.Map:
		b := CypherValue{}
		switch v.(type) {
		case map[string]string:
			b.Type = CypherMapStringString
			b.Val = v
		case map[string]CypherValue:
			b.Type = CypherMapStringCypherValue
			b.Val = v
		}
		return b.Value()
	case reflect.Ptr:
		// indirect pointers
		if rv.IsNil() {
			return nil, nil
		}
		return CypherValue{}.ConvertValue(rv.Elem().Interface())
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		return rv.Int(), nil
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32:
		return int64(rv.Uint()), nil
	case reflect.Uint64:
		u64 := rv.Uint()
		if u64 >= 1<<63 {
			return nil, fmt.Errorf("uint64 values with high bit set are not supported")
		}
		return int64(u64), nil
	case reflect.Float32, reflect.Float64:
		return rv.Float(), nil
	}
	return nil, fmt.Errorf("unsupported type %T, a %s", v, rv.Kind())
}
