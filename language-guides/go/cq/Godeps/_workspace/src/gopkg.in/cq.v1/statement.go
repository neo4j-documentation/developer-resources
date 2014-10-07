package cq

import (
	"bytes"
	"database/sql/driver"
	"encoding/json"
	"errors"
	"io"
	"io/ioutil"
	"net/http"
	"strconv"

	"gopkg.in/cq.v1/types"
)

type rows struct {
	stmt   *cypherStmt
	result *cypherResult
	pos    int
}

type cypherStmt struct {
	c     *conn
	query *string
}

type cypherResult struct {
	Columns         []string              `json:"columns"`
	Data            [][]types.CypherValue `json:"data"`
	ErrorMessage    string                `json:"message"`
	ErrorException  string                `json:"exception"`
	ErrorFullname   string                `json:"fullname"`
	ErrorStacktrace []string              `json:"stacktrace"`
}

type cypherRequest struct {
	Query  *string                `json:"query"`
	Params map[string]interface{} `json:"params,omitempty"`
}

func (stmt *cypherStmt) Close() error {
	stmt.query = nil
	return nil
}

func (stmt *cypherStmt) Exec(args []driver.Value) (driver.Result, error) {
	if stmt.c.transaction != nil {
		err := stmt.c.transaction.query(stmt.query, args)
		// TODO add counts and error support
		return nil, err
	}
	rows, err := stmt.Query(args)
	if rows != nil {
		defer rows.Close()
	}
	// TODO add counts and error support
	return nil, err
}

func (stmt *cypherStmt) NumInput() int {
	return -1 // avoid sanity check
}

func (stmt *cypherStmt) Query(args []driver.Value) (driver.Rows, error) {
	if stmt.c.transaction != nil {
		return nil, errors.New("transactions only support Exec")
	}
	// this only happens outside of a transaction
	cyphReq := cypherRequest{
		Query:  stmt.query,
		Params: makeArgsMap(args),
	}

	var buf bytes.Buffer
	err := json.NewEncoder(&buf).Encode(cyphReq)
	if err != nil {
		return nil, err
	}
	req, err := http.NewRequest("POST", stmt.c.cypherURL, &buf)
	if err != nil {
		return nil, err
	}
	setDefaultHeaders(req)
	res, err := client.Do(req)
	defer res.Body.Close()
	if err != nil {
		return nil, err
	}
	cyphRes := cypherResult{}
	err = json.NewDecoder(res.Body).Decode(&cyphRes)
	io.Copy(ioutil.Discard, res.Body)
	res.Body.Close()
	if err != nil {
		return nil, err
	}
	if cyphRes.ErrorMessage != "" {
		return nil, errors.New("Cypher error: " + cyphRes.ErrorMessage)
	}
	return &rows{stmt, &cyphRes, 0}, nil
}

func (rs *rows) Close() error {
	rs.result = nil
	return nil
}

func (rs *rows) Columns() []string {
	return rs.result.Columns
}

func (rs *rows) Next(dest []driver.Value) error {
	// TODO handle transaction
	if len(rs.result.Data) <= rs.pos {
		return io.EOF
	}
	for i := 0; i < len(dest); i++ {
		dest[i] = rs.result.Data[rs.pos][i].Val
	}
	rs.pos++
	return nil
}

func makeArgsMap(args []driver.Value) map[string]interface{} {
	argsmap := make(map[string]interface{})
	for idx, e := range args {
		switch e.(type) {
		case []byte:
			cv := types.CypherValue{}
			err := json.Unmarshal(e.([]byte), &cv)
			if err == nil {
				argsmap[strconv.Itoa(idx)] = cv.Val
				continue
			}
		}
		argsmap[strconv.Itoa(idx)] = e
	}
	return argsmap
}

func (cs cypherStmt) ColumnConverter(idx int) driver.ValueConverter {
	return types.CypherValue{}
}
