package sourceurl

import "testing"

func TestHostAllowed(t *testing.T) {
	if !HostAllowed("eur-lex.europa.eu") {
		t.Fatal("eur-lex should be allowed")
	}
	if HostAllowed("evil.example") {
		t.Fatal("evil.example must be refused")
	}
	if HostAllowed("") {
		t.Fatal("empty host must be refused")
	}
}

func TestValidateHTTPSAllowlist(t *testing.T) {
	if err := Validate("https://eur-lex.europa.eu/eli/reg/2024/2847"); err != nil {
		t.Fatal(err)
	}
}

func TestValidateRefuseNonHTTPS(t *testing.T) {
	if err := Validate("http://eur-lex.europa.eu/x"); err == nil {
		t.Fatal("expected non-https refuse")
	}
}

func TestValidateRefuseUnknownHost(t *testing.T) {
	if err := Validate("https://example.com/doc"); err == nil {
		t.Fatal("expected host refuse")
	}
}

func TestValidateEmpty(t *testing.T) {
	if err := Validate("  "); err == nil {
		t.Fatal("expected empty refuse")
	}
}
