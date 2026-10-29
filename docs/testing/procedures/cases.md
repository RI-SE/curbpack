# Carried cases

Repository state [R1](0_controlled_repo_setup.md). Pack input [PF-01](1_pack_template_instantiation.md): pack ids `cra-baseline`, `house-policy`, and `medtech-iec62304` from `curbpack.json` `packs`, loaded under that file's `packs_dir`.

Each id below is a carried case. The expected status is `pass`. The suite process exits 0 when every carried case is `pass`.

The `checks` array is the array in `docs/reference/test-packs/claims/<id>.json`.

## CRA-ANNEX-VII-MANUAL

Expected status: pass

```json
[
  {
    "check": "exist",
    "args": {
      "paths": [
        "docs/annex-vii/user_manual_security.md"
      ]
    }
  },
  {
    "check": "contents",
    "args": {
      "path": "docs/annex-vii/user_manual_security.md",
      "probes": [
        {
          "kind": "size",
          "bytes": 150,
          "op": ">="
        },
        {
          "kind": "headers",
          "headers": [
            "# User Manual \u2014 Security",
            "## Secure Configuration",
            "## Product Disposal"
          ]
        },
        {
          "kind": "token"
        }
      ]
    }
  }
]
```

## CRA-ANNEX-VII-RISK

Expected status: pass

```json
[
  {
    "check": "exist",
    "args": {
      "paths": [
        "docs/annex-vii/risk_assessment.md",
        "README.md"
      ]
    }
  },
  {
    "check": "contents",
    "args": {
      "path": "docs/annex-vii/risk_assessment.md",
      "probes": [
        {
          "kind": "size",
          "bytes": 200,
          "op": ">="
        },
        {
          "kind": "headers",
          "headers": [
            "# Risk Assessment",
            "## Product Overview",
            "## Identified Risks"
          ]
        },
        {
          "kind": "token"
        }
      ]
    }
  }
]
```

## CRA-ANNEX-VII-SUPPORT

Expected status: pass

```json
[
  {
    "check": "exist",
    "args": {
      "paths": [
        "docs/annex-vii/support_period.md"
      ]
    }
  },
  {
    "check": "contents",
    "args": {
      "path": "docs/annex-vii/support_period.md",
      "probes": [
        {
          "kind": "size",
          "bytes": 120,
          "op": ">="
        },
        {
          "kind": "headers",
          "headers": [
            "# Support Period",
            "## End of Support"
          ]
        },
        {
          "kind": "token"
        }
      ]
    }
  }
]
```

## CRA-ART14-PATH

Expected status: pass

```json
[
  {
    "check": "exist",
    "args": {
      "paths": [
        "docs/incident/art14-path.md"
      ]
    }
  },
  {
    "check": "contents",
    "args": {
      "path": "docs/incident/art14-path.md",
      "probes": [
        {
          "kind": "size",
          "bytes": 200,
          "op": ">="
        },
        {
          "kind": "headers",
          "headers": [
            "# Art 14 reporting path",
            "## Reporting clock (CRA Art 14)",
            "## Handling clock (not this file)",
            "## Named owner",
            "## Rehearsal dated artifact"
          ]
        },
        {
          "kind": "token"
        }
      ]
    }
  }
]
```

## HOUSE-ANTI-PLACEHOLDER

Expected status: pass

```json
[
  {
    "check": "contents",
    "args": {
      "paths": [
        "SECURITY.md",
        ".well-known/security.txt"
      ],
      "probes": [
        {
          "kind": "placeholder"
        }
      ]
    }
  }
]
```

## HOUSE-SECURITY-MD

Expected status: pass

```json
[
  {
    "check": "exist",
    "args": {
      "paths": [
        "SECURITY.md"
      ]
    }
  },
  {
    "check": "contents",
    "args": {
      "path": "SECURITY.md",
      "probes": [
        {
          "kind": "size",
          "bytes": 80,
          "op": ">="
        },
        {
          "kind": "words",
          "n": 20,
          "op": ">="
        },
        {
          "kind": "headers",
          "headers": [
            "# Security"
          ]
        }
      ]
    }
  }
]
```

## HOUSE-SECURITY-TXT

Expected status: pass

```json
[
  {
    "check": "exist",
    "args": {
      "paths": [
        ".well-known/security.txt"
      ]
    }
  },
  {
    "check": "contents",
    "args": {
      "path": ".well-known/security.txt",
      "probes": [
        {
          "kind": "size",
          "bytes": 40,
          "op": ">="
        },
        {
          "kind": "words",
          "n": 5,
          "op": ">="
        }
      ]
    }
  }
]
```

# Outside claims

These ids are named here so the check arguments match the claim file. Each id is in [outside.md](../outside.md). Neither is a pass. Neither has expected status `pass`.

## HOUSE-SECRET-PATHS

Outside. Not a pass.

```json
[
  {
    "check": "contents",
    "args": {
      "paths": [
        "README.md",
        "SECURITY.md",
        ".well-known/security.txt",
        ".env",
        ".env.local",
        "credentials.json",
        "service-account.json",
        "id_rsa"
      ],
      "probes": [
        {
          "kind": "pattern",
          "pattern": "(?i)(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH )?PRIVATE KEY-----|api[_-]?key\\s*[:=]\\s*['\\\"]?[a-zA-Z0-9]{20,})"
        }
      ]
    }
  }
]
```
