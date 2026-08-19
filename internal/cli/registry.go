package cli

type commandHandler func(args []string) error

type commandEntry struct {
	name    string
	aliases []string
	handler commandHandler
}

var commandRegistry = []commandEntry{
	{name: "init", handler: cmdInit},
	{name: "scan", aliases: []string{"reality-check"}, handler: cmdScan},
	{name: "check", handler: cmdCheck},
	{name: "fix", handler: cmdFix},
	{name: "validate", handler: cmdValidate},
	{name: "prepare-release", handler: cmdPrepareRelease},
	{name: "packs", handler: cmdPacks},
	{name: "ask", handler: cmdAsk},
	{name: "ask-my-suppliers", handler: cmdAskMySuppliers},
	{name: "attest", handler: cmdAttest},
	{name: "view", handler: cmdView},
	{name: "sock", handler: cmdSock},
	{name: "doctor", handler: cmdDoctor},
	{name: "demo", handler: cmdDemo},
	{name: "export", handler: cmdExport},
	{name: "share", handler: cmdShare},
	{name: "drift", handler: cmdDrift},
	{name: "pathway", handler: cmdPathway},
	{name: "research", handler: cmdResearch},
	{name: "completion", handler: cmdCompletion},
}

var commandByName map[string]commandHandler

func init() {
	commandByName = make(map[string]commandHandler, len(commandRegistry)+4)
	for _, e := range commandRegistry {
		commandByName[e.name] = e.handler
		for _, a := range e.aliases {
			commandByName[a] = e.handler
		}
	}
}

func RegisteredCommandNames() []string {
	out := make([]string, len(commandRegistry))
	for i, e := range commandRegistry {
		out[i] = e.name
	}
	return out
}

func lookupCommand(name string) (commandHandler, bool) {
	h, ok := commandByName[name]
	return h, ok
}