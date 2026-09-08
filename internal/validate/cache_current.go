package validate

import (
	"fmt"
	"strings"
	"time"

	"github.com/afelin/curbpack/internal/clock"
	"github.com/afelin/curbpack/internal/config"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/packs"
)

// LoadCurrent verifies immutable evidence and recomputes input identity before
// reusing it for a full-scope request. Historical aliases cannot satisfy this.
func LoadCurrent(root string, requested []string) (ir.Evaluation, ir.RunReceipt, error) {
	e, r, err := LoadLatest(root)
	if err != nil {
		return e, r, err
	}
	if e.SchemaVersion != ir.EvaluationSchemaVersion || e.Identity.Scope.Mode != "full" {
		return e, r, fmt.Errorf("cached evaluation is not a current full-scope contract")
	}
	asOf, source, err := clock.EvaluationAsOf("")
	if err != nil {
		return e, r, err
	}
	if (r.AsOfSource != "explicit" || source == "SOURCE_DATE_EPOCH") && e.AsOf != asOf.Format(time.RFC3339) {
		return e, r, fmt.Errorf("cached as_of differs from request")
	}
	ids, err := config.ResolvePackIDs(root, requested)
	if err != nil {
		return e, r, err
	}
	pack, _, sources, err := packs.ComposeSnapshot(ids)
	if err != nil {
		return e, r, err
	}
	now, err := captureInputs(root, pack, sources, false, nil)
	if err != nil {
		return e, r, err
	}
	if !equivalentInputs(e.Identity, now) {
		return e, r, fmt.Errorf("cached evaluation inputs differ from request")
	}
	return e, r, nil
}

// VerifyResultInputs refuses publishing a supplied evaluation after its inputs
// have changed, including scaffolds created by a later recipe step.
func VerifyResultInputs(root string, res Result) error {
	ids := strings.Split(res.Evaluation.PackID, ",")
	pack, _, sources, err := packs.ComposeSnapshot(ids)
	if err != nil {
		return err
	}
	changed := map[string]struct{}{}
	for _, p := range res.Evaluation.Identity.Scope.ChangedPaths {
		changed[p] = struct{}{}
	}
	current, err := captureInputs(root, pack, sources, res.Evaluation.Identity.Scope.Mode == "diff", changed)
	if err != nil {
		return err
	}
	if !equivalentInputs(current, res.Evaluation.Identity) {
		return fmt.Errorf("evaluation inputs changed before publication; rerun check/share on the prepared tree")
	}
	return nil
}
