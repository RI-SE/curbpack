# Packs update channel & watchlist refresh

Embedded packs (`cra-baseline`, `medtech-iec62304`, `house-policy`) ship inside the binary. Pack rule changes should prefer **JSON data PRs**, not binary releases.

## Offline / air-gap

```bash
# Export-like layout (or copy from this repo's packs/ directory)
mkdir -p /media/usb/curbpack-packs/{cra-baseline,medtech-iec62304,house-policy}
cp packs/cra-baseline/pack.json /media/usb/curbpack-packs/cra-baseline/
cp packs/medtech-iec62304/pack.json /media/usb/curbpack-packs/medtech-iec62304/
cp packs/house-policy/pack.json /media/usb/curbpack-packs/house-policy/
cp packs/_watchlist.json /media/usb/curbpack-packs/

# On the air-gapped machine
curbpack packs import /media/usb/curbpack-packs
export CURBPACK_PACKS_DIR="$PWD/.github/curbpack/packs"
curbpack check
```

Import prerequisites (fail closed): each pack must pass `ValidatePack`, set `assurance_class`, and avoid claim-adjacent theater names/descriptions. Successful import writes a `.curbpack-pack.sha256` sidecar next to each `pack.json`.

`CURBPACK_PACKS_DIR` overrides embedded JSON when files are present.

## Online update (pin required)

Network pack updates are **off by default**. Both URL and sha256 pin are required:

```bash
curbpack packs update
# prints instructions when CURBPACK_PACKS_URL is unset

CURBPACK_PACKS_URL=https://example.invalid/packs/bundle.json \
CURBPACK_PACKS_SHA256=<64-hex-chars> \
curbpack packs update
```

Without `CURBPACK_PACKS_SHA256`, the CLI refuses the fetch (fail closed). Watchlist entries are **informational only** and never fail `validate`.

## Watchlist refresh

1. Edit `packs/_watchlist.json` (or imported copy).
2. Bump `updated` date.
3. Import or rebuild the binary to embed.
4. Confirm with `curbpack packs list`.
