# Chart-format evidence

The user-facing specification is [VSB_FORMAT.md](../../docs/VSB_FORMAT.md); the tested ImHex pattern is [vividstasis_vsb.hexpat](../../patterns/vividstasis_vsb.hexpat).

| Artifact | Evidence |
| --- | --- |
| `corpus_validation.json` | All 805 files parsed and byte-identically re-encoded; per-file SHA-256, payload-end offsets, note/modifier counts, observed IDs/types/trailer lengths |
| `crypto_validation.json` | Independent RSA/SHA-1 checks: 803 valid, one unsigned, one digest mismatch; structural boundaries retained |
| `stats_validation.json` | All 803 caches audited against full-file SHA-1: 723 match, 78 stale, two orphan; four charts lack caches |
| `imhex_validation.json` | Actual ImHex 1.38.1 PatternLanguage evaluation: 805/805 passed; runtime and pattern SHA-256 identities recorded |
| `imhex_synthetic_validation.json` | Eight real-runtime synthetic tests, with input hex, including all extra types and malformed-input rejection |
| `mod_ids.json` | Static global/easing/object-specific registration catalog, source-line evidence, duplicate registrations and effective maps |
| `mod_id_validation.json` | All 503 observed custom modifier/object pairs resolved against the static effective maps |
| `generate_mod_ids.py` | Reproduces the static mapping catalog and [readable table](../../docs/chart_mod_ids.md) |

All analysis reads the original charts and extracted code; no game executables or gimmick callbacks were run. Format tests and RSA verification do not prove the semantic purpose of every opaque marker or visual-effect property. Source charts were not modified.

The corpus parser and its seven directed tests are in [tools/](../../tools/). The generated ImHex runtime lived under `/tmp/vsb-plcli-build/` and was compiled from the existing local ImHex source cache, without modifying that cache. Runtime paths in reports record the validation environment, not a portable installation requirement.
