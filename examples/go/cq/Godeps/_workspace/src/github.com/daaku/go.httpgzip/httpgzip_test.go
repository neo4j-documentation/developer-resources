package httpgzip_test

import (
	"bytes"
	"github.com/daaku/go.httpgzip"
	"io/ioutil"
	"net/http"
	"net/http/httptest"
	"testing"
)

func stubHandler(response string) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(response))
	})
}

func TestWithoutGzip(t *testing.T) {
	const resp = "hello"
	handler := httpgzip.NewHandler(stubHandler(resp))
	writer := httptest.NewRecorder()
	handler.ServeHTTP(writer, &http.Request{Method: "GET"})
	if writer.Body == nil {
		t.Fatal("expected a body")
	}
	if l := writer.Body.Len(); l != len(resp) {
		t.Fatalf("invalid body length, got %d", l)
	}
}

func TestWithGzip(t *testing.T) {
	handler := httpgzip.NewHandler(stubHandler("hello"))
	writer := httptest.NewRecorder()
	handler.ServeHTTP(writer, &http.Request{
		Method: "GET",
		Header: http.Header{
			"Accept-Encoding": []string{"gzip"},
		},
	})
	if writer.Body == nil {
		t.Fatal("expected a body")
	}
	if l := writer.Body.Len(); l != 29 {
		t.Fatalf("invalid body length, got %d", l)
	}
}

func TestWithGzipReal(t *testing.T) {
	const raw = "hello"
	handler := httpgzip.NewHandler(stubHandler(raw))
	server := httptest.NewServer(handler)
	defer server.Close()
	resp, err := http.Get(server.URL)
	if err != nil {
		t.Fatalf("failed http request: %s", err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if string(body) != raw {
		t.Fatalf(`did not find expected "%s" but got "%s" instead`, raw, resp)
	}
}

func TestWithGzipDoubleWrite(t *testing.T) {
	handler := httpgzip.NewHandler(
		http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write(bytes.Repeat([]byte("foo"), 1000))
			w.Write(bytes.Repeat([]byte("bar"), 1000))
		}))
	writer := httptest.NewRecorder()
	handler.ServeHTTP(writer, &http.Request{
		Method: "GET",
		Header: http.Header{
			"Accept-Encoding": []string{"gzip"},
		},
	})
	if writer.Body == nil {
		t.Fatal("expected a body")
	}
	if l := writer.Body.Len(); l != 54 {
		t.Fatalf("invalid body length, got %d", l)
	}
}
