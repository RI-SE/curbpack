package validate

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/outwrite"
	"github.com/afelin/curbpack/internal/pathjail"
)

// writeEvaluationCache persists canonical evaluation + run receipt, and keeps
// legacy latest_failure / latest_result aliases via the GateFailurePayload adapter.
// Each file is replaced only after its complete contents have been written and synced.
// The alias set is not a multi-file transaction.
func writeEvaluationCache(root string, writer *outwrite.ExclusiveLock, eval ir.Evaluation, receipt ir.RunReceipt, legacy ir.GateFailurePayload, action string) error {
	const rel = ".github/curbpack/cache"
	dir, _, err := pathjail.Join(root, rel)
	if err != nil {
		return fmt.Errorf("cache directory: %w", err)
	}
	if writer == nil {
		writer, err = outwrite.Acquire(root)
		if err != nil {
			return fmt.Errorf("cache lock: %w", err)
		}
		defer writer.Release()
	} else if err := writer.Holds(root); err != nil {
		return err
	}

	if err = outwrite.EnsureDir(root, dir); err != nil {
		return fmt.Errorf("create cache: %w", err)
	}

	evalBytes, err := ir.MarshalCanonical(eval)
	if err != nil {
		return fmt.Errorf("marshal evaluation: %w", err)
	}
	receiptBytes, err := ir.MarshalReceipt(receipt)
	if err != nil {
		return err
	}
	evalDigest, receiptDigest := hashBytes(evalBytes), hashBytes(receiptBytes)
	if receipt.EvaluationDigest != evalDigest {
		return fmt.Errorf("receipt does not bind evaluation")
	}
	pointerBytes, err := json.MarshalIndent(CachePointer{SchemaVersion: cachePointerSchema, EvaluationDigest: evalDigest, ReceiptDigest: receiptDigest}, "", "  ")
	if err != nil {
		return err
	}

	legacyBytes, err := json.MarshalIndent(legacy, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal legacy payload: %w", err)
	}
	legacyBytes = append(legacyBytes, '\n')

	files := []struct {
		name string
		body []byte
	}{
		{"latest_evaluation.json", evalBytes},
		{"latest_receipt.json", receiptBytes},
		{"latest_failure.json", legacyBytes},
		{"latest_result.json", legacyBytes},
		{"latest_action_report.md", []byte(action)},
	}
	// Publish immutable objects first. Interrupted writes leave only unreferenced
	// objects; the authoritative pointer advances last, by one atomic rename.
	if err := writeImmutableCache(root, "evaluations/"+evalDigest+".json", evalBytes); err != nil {
		return err
	}
	if err := writeImmutableCache(root, "receipts/"+receiptDigest+".json", receiptBytes); err != nil {
		return err
	}
	files = append(files, struct {
		name string
		body []byte
	}{"latest.json", append(pointerBytes, '\n')})
	// Preflight all destinations before replacing any alias.
	for _, file := range files {
		path, _, err := pathjail.Join(root, rel+"/"+file.name)
		if err != nil {
			return fmt.Errorf("cache %s: %w", file.name, err)
		}
		if st, err := os.Lstat(path); err == nil && !st.Mode().IsRegular() {
			return fmt.Errorf("cache %s: destination must be a regular file", file.name)
		} else if err != nil && !os.IsNotExist(err) {
			return err
		}
	}
	for _, file := range files {
		if err := writeCacheFile(root, rel+"/"+file.name, file.body); err != nil {
			return fmt.Errorf("cache %s: %w", file.name, err)
		}
	}
	return nil
}

func writeCacheFile(root, rel string, body []byte) error {
	path, _, err := pathjail.Join(root, rel)
	if err != nil {
		return err
	}
	return outwrite.WriteFile(root, path, body, 0644)
}

func writeImmutableCache(root, rel string, data []byte) error {
	path, _, err := SafeJoin(root, ".github/curbpack/cache/"+rel)
	if err != nil {
		return err
	}
	if st, err := os.Lstat(path); err == nil {
		if !st.Mode().IsRegular() {
			return fmt.Errorf("immutable object is not a regular file")
		}
		prior, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		if !bytes.Equal(prior, data) {
			return fmt.Errorf("immutable cache object integrity mismatch: %s", rel)
		}
		return nil
	} else if !os.IsNotExist(err) {
		return err
	}
	return outwrite.WriteFile(root, path, data, 0644)
}
