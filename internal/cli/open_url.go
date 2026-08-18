package cli

import (
	"github.com/afelin/curbpack/internal/platform"
	"github.com/afelin/curbpack/internal/research"
)

func openAllowlistedURL(raw string) error {
	if err := research.ValidateSourceURL(raw); err != nil {
		return err
	}
	return platform.OpenURL(raw)
}
