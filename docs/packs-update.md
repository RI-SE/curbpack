# Packs update channel & watchlist refresh

Embedded packs (`cra-baseline`, `medtech-iec62304`) ship inside the binary. Pack rule changes should prefer **JSON data PRs**, not binary releases.

## Offline / air-gap

```bash
# Export-like layout (or copy from this repo's packs/ directory)
mkdir -p /media/usb/cyberready-packs/cra-baseline
cp packs/cra-baseline/pack.json /media/usb/cyberready-packs/cra-baseline/
cp packs/medtech-iec62304/pack.json /media/usb/cyberready-packs/medtech-iec62304/
cp packs/_watchlist.json /media/usb/cyberready-packs/

# On the air-gapped machine
cyberready packs import /media/usb/cyberready-packs
export CYBERREADY_PACKS_DIR="$PWD/.github/cyberready/packs"
cyberready validate
```

`CYBERREADY_PACKS_DIR` overrides embedded JSON when files are present.

## Online stub

```bash
cyberready packs update
# prints instructions when CYBERREADY_PACKS_URL is unset

CYBERREADY_PACKS_URL=https://example.invalid/packs/bundle.json cyberready packs update
```

No signed CDN is required for P0/P1. Watchlist entries are **informational only** and never fail `validate`.

## Watchlist refresh

1. Edit `packs/_watchlist.json` (or imported copy).
2. Bump `updated` date.
3. Import or rebuild the binary to embed.
4. Confirm with `cyberready packs list`.
