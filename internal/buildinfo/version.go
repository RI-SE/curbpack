package buildinfo

// Version is the single source of truth for tool version metadata.
// Release builds override via -ldflags "-X github.com/afelin/curbpack/internal/buildinfo.Version=...".
var Version = "0.5.4"
