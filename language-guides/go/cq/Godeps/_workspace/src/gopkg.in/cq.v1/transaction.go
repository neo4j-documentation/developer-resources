package cq

import (
	"bytes"
	"database/sql/driver"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"time"
)

type transactionResponse struct {
	Commit      string `json:"commit"`
	Transaction struct {
		Expires string
	}
	Errors   []commitError `json:"errors"`
	location string
}

type cypherTransactionStatement struct {
	Statement  *string                `json:"statement"`
	Parameters map[string]interface{} `json:"parameters"`
}

type cypherTransaction struct {
	Statements     []cypherTransactionStatement `json:"statements"`
	commitURL      string
	transactionURL string
	expiration     time.Time
	c              *conn
	rows           []*rows
	keepAlive      *time.Timer
}

type commitError struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

type commitResponse struct {
	Errors []commitError `json:"errors"`
}

func (c *conn) Begin() (driver.Tx, error) {
	if c.transactionURL == "" {
		return nil, ErrTransactionsNotSupported
	}
	transResponse, err := getTransactionResponse(c.transactionURL, cypherTransaction{})
	if err != nil {
		return nil, err
	}
	exp, err := time.Parse(time.RFC1123Z, transResponse.Transaction.Expires)
	if err != nil {
		log.Println(err, c)
		err = nil
	}
	commitURL, err := url.Parse(transResponse.Commit)
	if err != nil {
		return nil, err
	}
	commitURL.Scheme = c.scheme
	commitURL.User = c.userInfo

	transactionURL, err := url.Parse(transResponse.location)
	if err != nil {
		return nil, err
	}
	transactionURL.Scheme = c.scheme
	transactionURL.User = c.userInfo

	c.transaction = &cypherTransaction{
		commitURL:      commitURL.String(),
		transactionURL: transactionURL.String(),
		c:              c,
		expiration:     exp,
	}
	c.transaction.updateKeepAlive()
	return c.transaction, nil
}

func (tx *cypherTransaction) query(query *string, args []driver.Value) error {
	stmt := cypherTransactionStatement{
		Statement:  query,
		Parameters: makeArgsMap(args),
	}
	tx.Statements = append(tx.Statements, stmt)
	if len(tx.Statements) >= 100 {
		err := tx.exec()
		if err != nil {
			return err
		}
	}
	return nil
}

func (tx *cypherTransaction) exec() error {
	trans, err := getTransactionResponse(tx.transactionURL, *tx)
	if err != nil {
		return err
	}

	tx.expiration, err = time.Parse(time.RFC1123Z, trans.Transaction.Expires)
	if err != nil {
		log.Print(err, tx)
		err = nil
	}
	tx.updateKeepAlive()

	tx.Statements = tx.Statements[:0]

	if len(trans.Errors) > 0 {
		return errors.New("exec errors: " + fmt.Sprintf("%q", trans))
	}
	if err != nil {
		return err
	}
	return nil
}

func (tx *cypherTransaction) Commit() error {
	if tx.Statements == nil {
		return nil	
	}
	var buf bytes.Buffer
	err := json.NewEncoder(&buf).Encode(tx)
	if err != nil {
		return err
	}
	req, err := http.NewRequest("POST", tx.commitURL, &buf)
	if err != nil {
		return err
	}
	setDefaultHeaders(req)
	res, err := client.Do(req)
	defer res.Body.Close()
	if err != nil {
		return err
	}
	commit := commitResponse{}
	json.NewDecoder(res.Body).Decode(&commit)
	io.Copy(ioutil.Discard, res.Body)
	res.Body.Close()
	if err != nil {
		return err
	}
	if len(commit.Errors) > 0 {
		return errors.New("commit errors: " + fmt.Sprintf("%q", commit))
	}
	tx.c.transaction = nil
	if tx.keepAlive != nil {
		tx.keepAlive.Stop()
	}
	return nil
}

func (tx *cypherTransaction) Rollback() error {
	req, err := http.NewRequest("DELETE", tx.transactionURL, nil)
	if err != nil {
		return err
	}
	setDefaultHeaders(req)
	res, err := client.Do(req)
	if err != nil {
		return err
	}
	commit := commitResponse{}
	json.NewDecoder(res.Body).Decode(&commit)
	io.Copy(ioutil.Discard, res.Body)
	res.Body.Close()
	if err != nil {
		return err
	}
	if len(commit.Errors) > 0 {
		return errors.New("rollback errors: " + fmt.Sprintf("%q", commit))
	}
	tx.c.transaction = nil
	if tx.keepAlive != nil {
		tx.keepAlive.Stop()
	}

	return nil
}

func getTransactionResponse(url string, cypherTransReq cypherTransaction) (*transactionResponse, error) {
	var buf bytes.Buffer
	json.NewEncoder(&buf).Encode(cypherTransReq)
	req, err := http.NewRequest("POST", url, &buf)
	if err != nil {
		return nil, err
	}
	setDefaultHeaders(req)
	res, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	transResponse := transactionResponse{}
	json.NewDecoder(res.Body).Decode(&transResponse)
	io.Copy(ioutil.Discard, res.Body)
	res.Body.Close()
	transResponse.location = res.Header.Get("Location")
	return &transResponse, nil
}

// updateKeepAlive cancels the current timer, if it is set, and
// schedules a timer to send a keepalive message before the transaction expires.
func (tx *cypherTransaction) updateKeepAlive() {
	if tx.keepAlive != nil {
		tx.keepAlive.Stop()
	}
	dur := getDurToKeepAlive(tx.expiration)
	tx.keepAlive = time.AfterFunc(dur, func() { sendKeepAlive(tx.transactionURL) })
}

// sendKeepAlive sends an empty Cypher transactional statement
// to the URL given. It parses the response and schedules a new
// call to itself halfway to the next timeout
func sendKeepAlive(txURL string) {
	trans, err := getTransactionResponse(txURL, cypherTransaction{Statements: []cypherTransactionStatement{}})
	if err != nil {
		return
	}
	if len(trans.Errors) > 0 {
		return
	}
	exp, err := time.Parse(time.RFC1123Z, trans.Transaction.Expires)
	if err != nil {
		return
	}
	dur := getDurToKeepAlive(exp)
	time.AfterFunc(dur, func() { sendKeepAlive(txURL) })
}

// getDurToKeepAlive gets the difference between now and the expiration
// and returns the duration until the halfway point
func getDurToKeepAlive(t time.Time) time.Duration {
	dur := -1 * time.Since(t)
	if dur < time.Second*1 {
		dur = time.Second * 1
	}
	dur /= 2
	return dur
}
