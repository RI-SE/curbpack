package cli

import "io"

type ioDiscard struct{}

func (ioDiscard) Write(p []byte) (int, error) { return len(p), nil }

var _ io.Writer = ioDiscard{}
