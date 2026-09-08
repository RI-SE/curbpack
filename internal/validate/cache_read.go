package validate

import (
	"encoding/json"
	"fmt"
	"os"
	"regexp"

	"github.com/afelin/curbpack/internal/ir"
)

const cachePointerSchema = "curbpack-cache-pointer:1"

var digestPattern = regexp.MustCompile(`^[0-9a-f]{64}$`)

type CachePointer struct {
	SchemaVersion    string `json:"schema_version"`
	EvaluationDigest string `json:"evaluation_digest"`
	ReceiptDigest    string `json:"receipt_digest"`
}

// LoadLatest reads the convenience pointer and independently verifies both
// immutable objects. Legacy latest_* aliases are never evidence inputs here.
func LoadLatest(root string) (ir.Evaluation, ir.RunReceipt, error) {
	b, err := readCacheObject(root, "latest.json")
	if err != nil {
		return ir.Evaluation{}, ir.RunReceipt{}, err
	}
	var pointer CachePointer
	if err := json.Unmarshal(b, &pointer); err != nil {
		return ir.Evaluation{}, ir.RunReceipt{}, err
	}
	if pointer.SchemaVersion != cachePointerSchema {
		return ir.Evaluation{}, ir.RunReceipt{}, fmt.Errorf("unsupported cache pointer schema")
	}
	return LoadByDigest(root, pointer.EvaluationDigest, pointer.ReceiptDigest)
}

func LoadByDigest(root, evalDigest, receiptDigest string) (ir.Evaluation, ir.RunReceipt, error) {
	if !digestPattern.MatchString(evalDigest) || !digestPattern.MatchString(receiptDigest) {
		return ir.Evaluation{}, ir.RunReceipt{}, fmt.Errorf("cache requires full SHA-256 digests")
	}
	raw, err := readCacheObject(root, "evaluations/"+evalDigest+".json")
	if err != nil {
		return ir.Evaluation{}, ir.RunReceipt{}, err
	}
	if hashBytes(raw) != evalDigest {
		return ir.Evaluation{}, ir.RunReceipt{}, fmt.Errorf("evaluation integrity mismatch")
	}
	evaluation, err := ir.ParseCanonical(raw)
	if err != nil {
		return ir.Evaluation{}, ir.RunReceipt{}, err
	}
	raw, err = readCacheObject(root, "receipts/"+receiptDigest+".json")
	if err != nil {
		return ir.Evaluation{}, ir.RunReceipt{}, err
	}
	if hashBytes(raw) != receiptDigest {
		return ir.Evaluation{}, ir.RunReceipt{}, fmt.Errorf("receipt integrity mismatch")
	}
	receipt, err := ir.ParseReceipt(raw)
	if err != nil {
		return ir.Evaluation{}, ir.RunReceipt{}, err
	}
	if err := ir.ValidateReceipt(receipt, evaluation, evalDigest); err != nil {
		return ir.Evaluation{}, ir.RunReceipt{}, err
	}
	return evaluation, receipt, nil
}

func readCacheObject(root, rel string) ([]byte, error) {
	path, _, err := SafeJoin(root, ".github/curbpack/cache/"+rel)
	if err != nil {
		return nil, err
	}
	st, err := os.Lstat(path)
	if err != nil {
		return nil, err
	}
	if !st.Mode().IsRegular() {
		return nil, fmt.Errorf("cache object is not a regular file")
	}
	return os.ReadFile(path)
}
