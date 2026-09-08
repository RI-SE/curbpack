package review_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/review"
)

func TestHistoricalReportDigestSurvivesAuditExtension(t *testing.T) {
	raw, err := os.ReadFile(filepath.Join("testdata", "report_before_pack_audit.json"))
	if err != nil {
		t.Fatal(err)
	}
	var rep review.Report
	if err := json.Unmarshal(raw, &rep); err != nil {
		t.Fatal(err)
	}
	if rep.Audit != nil {
		t.Fatal("fixture must predate the audit extension")
	}
	const historical = "7e7a8de08bef231703953f1457468682d8967ae44448815b3e34e05cb706a2b4"
	if rep.RecordDigest != historical || review.ComputeRecordDigest(rep) != historical {
		t.Fatal("historical digest bytes changed")
	}
}
