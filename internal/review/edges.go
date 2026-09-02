package review

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
)

const reviewStateApproved = "approved"

// ReviewedAgainst records pack/classifier/method versions at human review time.
type ReviewedAgainst struct {
	PackVersions      json.RawMessage `json:"pack_versions"`
	ClassifierVersion string          `json:"classifier_version"`
	MethodVersion     string          `json:"method_version"`
}

// Edge is one human-approved mapping from a gate to a review finding (Shared Frame §6 TO).
type Edge struct {
	GateID          string          `json:"gate_id"`
	FindingID       string          `json:"finding_id"`
	Source          string          `json:"source"`
	ReviewedBy      string          `json:"reviewed_by"`
	ReviewedAt      string          `json:"reviewed_at"`
	ReviewState     string          `json:"review_state"`
	ReviewedAgainst ReviewedAgainst `json:"reviewed_against"`
}

type edgeWire struct {
	GateID          string          `json:"gate_id"`
	FindingID       string          `json:"finding_id"`
	Source          string          `json:"source"`
	ReviewedBy      string          `json:"reviewed_by"`
	ReviewedAt      string          `json:"reviewed_at"`
	ReviewState     string          `json:"review_state"`
	ReviewedAgainst ReviewedAgainst `json:"reviewed_against"`
}

type edgesFileEnvelope struct {
	Edges []json.RawMessage `json:"edges"`
}

// LoadEdgesFile reads {"edges":[...]} from path. Refuses symlinks and oversize files.
func LoadEdgesFile(path string) ([]Edge, error) {
	path = strings.TrimSpace(path)
	if path == "" {
		return nil, fmt.Errorf("edges file path empty")
	}
	st, err := os.Lstat(path)
	if err != nil {
		return nil, fmt.Errorf("edges file: %w", err)
	}
	if st.Mode()&os.ModeSymlink != 0 {
		return nil, fmt.Errorf("edges file refuses symlink: %s", path)
	}
	if !st.Mode().IsRegular() {
		return nil, fmt.Errorf("edges file must be a regular file: %s", path)
	}
	if st.Size() > MaxPriorReportBytes {
		return nil, fmt.Errorf("edges file exceeds size cap: %s", path)
	}
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("edges file: %w", err)
	}
	defer f.Close()
	data, err := io.ReadAll(io.LimitReader(f, MaxPriorReportBytes+1))
	if err != nil {
		return nil, fmt.Errorf("edges file: %w", err)
	}
	if int64(len(data)) > MaxPriorReportBytes {
		return nil, fmt.Errorf("edges file exceeds size cap: %s", path)
	}
	dec := json.NewDecoder(bytes.NewReader(data))
	dec.DisallowUnknownFields()
	var env edgesFileEnvelope
	if err := dec.Decode(&env); err != nil {
		return nil, fmt.Errorf("edges file: not valid JSON: %w", err)
	}
	if dec.More() {
		return nil, fmt.Errorf("edges file: trailing JSON after envelope")
	}
	out := make([]Edge, 0, len(env.Edges))
	for i, raw := range env.Edges {
		e, err := decodeEdgeWire(raw)
		if err != nil {
			return nil, fmt.Errorf("edges[%d]: %w", i, err)
		}
		out = append(out, e)
	}
	return out, nil
}

func decodeEdgeWire(raw json.RawMessage) (Edge, error) {
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.DisallowUnknownFields()
	var w edgeWire
	if err := dec.Decode(&w); err != nil {
		return Edge{}, fmt.Errorf("%w", err)
	}
	if dec.More() {
		return Edge{}, fmt.Errorf("trailing JSON in edge object")
	}
	return Edge(w), nil
}

// ValidateEdges refuses non-approved, incomplete, or report-inconsistent edges.
func ValidateEdges(rep Report, edges []Edge) error {
	if len(edges) == 0 {
		return fmt.Errorf("edges: empty slice refused")
	}
	findingIDs := make(map[string]struct{}, len(rep.Findings))
	for _, f := range rep.Findings {
		findingIDs[f.ID] = struct{}{}
	}
	for i, e := range edges {
		if strings.TrimSpace(e.GateID) == "" {
			return fmt.Errorf("edges[%d]: gate_id required", i)
		}
		if strings.TrimSpace(e.FindingID) == "" {
			return fmt.Errorf("edges[%d]: finding_id required", i)
		}
		if _, ok := findingIDs[e.FindingID]; !ok {
			return fmt.Errorf("edges[%d]: finding_id %q not in report findings", i, e.FindingID)
		}
		if strings.TrimSpace(e.Source) == "" {
			return fmt.Errorf("edges[%d]: source required", i)
		}
		if strings.TrimSpace(e.ReviewedBy) == "" {
			return fmt.Errorf("edges[%d]: reviewed_by required", i)
		}
		if strings.TrimSpace(e.ReviewedAt) == "" {
			return fmt.Errorf("edges[%d]: reviewed_at required", i)
		}
		if e.ReviewState != reviewStateApproved {
			return fmt.Errorf("edges[%d]: review_state must be %q (got %q)", i, reviewStateApproved, e.ReviewState)
		}
		if err := validateReviewedAgainst(i, e.ReviewedAgainst); err != nil {
			return err
		}
	}
	return nil
}

func validateReviewedAgainst(i int, ra ReviewedAgainst) error {
	if len(bytes.TrimSpace(ra.PackVersions)) == 0 || bytes.Equal(bytes.TrimSpace(ra.PackVersions), []byte("null")) {
		return fmt.Errorf("edges[%d]: reviewed_against.pack_versions required", i)
	}
	if strings.TrimSpace(ra.ClassifierVersion) == "" {
		return fmt.Errorf("edges[%d]: reviewed_against.classifier_version required", i)
	}
	if strings.TrimSpace(ra.MethodVersion) == "" {
		return fmt.Errorf("edges[%d]: reviewed_against.method_version required", i)
	}
	return nil
}

// AttachEdges copies rep, sets Edges, and recomputes record_digest.
func AttachEdges(rep Report, edges []Edge) (Report, error) {
	if err := ValidateEdges(rep, edges); err != nil {
		return Report{}, err
	}
	out := rep
	out.Edges = append([]Edge(nil), edges...)
	out.RecordDigest = computeRecordDigest(out)
	return out, nil
}
