package validate

import (
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
	receiptBytes, err := json.MarshalIndent(receipt, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal receipt: %w", err)
	}
	receiptBytes = append(receiptBytes, '\n')
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
