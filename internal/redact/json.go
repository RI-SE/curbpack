package redact

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
)

// JSON scrubs decoded string values and keys using an explicitly supplied
// context. It preserves JSON numbers and refuses key collisions. Use this for
// derived crossing formats, never to rewrite signed or canonical evidence.
func JSON(raw []byte, ctx Context) ([]byte, error) {
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	var value any
	if err := dec.Decode(&value); err != nil {
		return nil, err
	}
	var extra any
	if err := dec.Decode(&extra); err != io.EOF {
		return nil, fmt.Errorf("expected one JSON value")
	}
	var scrub func(any) (any, error)
	scrub = func(v any) (any, error) {
		switch x := v.(type) {
		case string:
			return String(x, ctx), nil
		case []any:
			for i, item := range x {
				clean, err := scrub(item)
				if err != nil {
					return nil, err
				}
				x[i] = clean
			}
			return x, nil
		case map[string]any:
			out := map[string]any{}
			for key, item := range x {
				cleanKey := String(key, ctx)
				if _, exists := out[cleanKey]; exists {
					return nil, fmt.Errorf("redaction collapses JSON keys")
				}
				clean, err := scrub(item)
				if err != nil {
					return nil, err
				}
				out[cleanKey] = clean
			}
			return out, nil
		default:
			return v, nil
		}
	}
	clean, err := scrub(value)
	if err != nil {
		return nil, err
	}
	return json.MarshalIndent(clean, "", "  ")
}

// JSONLooksClean checks decoded JSON, including escaped home paths. Evidence is
// verified in place; callers must not replace canonical bytes with scrubbed JSON.
func JSONLooksClean(raw []byte, ctx Context) error {
	clean, err := JSON(raw, ctx)
	if err != nil {
		return err
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	var value any
	if err := dec.Decode(&value); err != nil {
		return err
	}
	normalized, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	if !bytes.Equal(normalized, clean) {
		return fmt.Errorf("JSON contains home-path, PEM or configured secret material")
	}
	return nil
}
