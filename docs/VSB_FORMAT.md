# Vividstasis binary chart format (`.vsb`, VSC version 1)

The supplied charts are **unencrypted, uncompressed, little-endian tagged streams**. A five-byte header is followed by note records, optional visual/gameplay modifiers, a chart terminator, and usually a 384-byte RSA signature. Timestamps are stored directly in milliseconds; modifiers use the game's beat grid. There is no note-count field or offset table.

The format below is recovered from the extracted reader, writer, and gameplay consumers and checked against **all 805 `.vsb` files** in this distribution. A separate Python parser decoded and re-encoded every file byte for byte. The accompanying [ImHex pattern](../patterns/vividstasis_vsb.hexpat) describes the actual tagged grammar, including optional fields, all supported extra-value types, modifier commands, and unsigned files.

For adding an authored chart to a playable song entry, see [chart registration and the launch path](CHART_REGISTRATION.md). A valid VSB alone does not register a menu entry or audio resource.

## Evidence and scope

The primary sources are the shipped game's decompiled GML, not assumptions based on chart filenames:

| Source | What it establishes |
| --- | --- |
| [read_binary_chart](../extraction/main/CodeEntries/gml_GlobalScript_read_binary_chart.gml), lines 12–24 | Header bytes and version dispatch |
| [V1ChartReader](../extraction/main/CodeEntries/gml_GlobalScript_v1_chart_reader.gml), lines 22–176 | Tagged note/extra/modifier grammar and defaults |
| [V1ChartWriter](../extraction/main/CodeEntries/gml_GlobalScript_v1_chart_writer.gml), lines 1–124 | Canonical field order, hold endpoints, exact payload types |
| [chart_enums](../extraction/main/CodeEntries/gml_GlobalScript_chart_enums.gml), lines 1–30 | Extra-value tag to GameMaker buffer-type mapping |
| [LoadSong](../extraction/main/CodeEntries/gml_GlobalScript_LoadSong.gml), lines 18–89 | Disk note types, lanes, milliseconds, BPM handling |
| [mod_setup](../extraction/main/CodeEntries/gml_GlobalScript_mod_setup.gml) and [base gimmick](../extraction/main/CodeEntries/gml_Object_obj_base_gimmick_Create_0.gml) | Easing/mod IDs, proxy targets, modifier time units |
| [chart_sign](../extraction/main/CodeEntries/gml_GlobalScript_chart_sign.gml), lines 22–50 | Signature size and verification bypass in this build |
| [LoadSongData](../extraction/main/CodeEntries/gml_GlobalScript_LoadSongData.gml), lines 290–345 | `.stats` cache format and checksum handling |

GameMaker's [buffer documentation](https://manual.gamemaker.io/monthly/en/GameMaker_Language/GML_Reference/Buffers/buffer_read.htm) confirms the little-endian numeric representation and NUL-terminated buffer strings. Corpus parsing independently confirms byte widths and boundaries. This write-up applies to version 1 in the supplied distribution; other chart versions are not established.

## Primitive representation

| Name | Representation |
| --- | --- |
| `u8`, `s8` | One-byte unsigned / two's-complement signed integer |
| `u32`, `s32` | Four-byte little-endian integer |
| `f16`, `f32` | IEEE-754 binary16 / binary32, little endian |
| `bool` | One byte: `00` false, `01` true |
| `stringz` | NUL-terminated byte string, not length-prefixed or UTF-16; decode text as UTF-8 |
| Tag | One byte interpreted according to the current enclosing section |

Fields are packed without alignment. `f32` is four bytes even when the decompiler displays `read(8)`: **8 is the GameMaker `buffer_f32` type identifier, not a byte count**. Likewise, `read(11)` means a buffer string, `read(2)` means signed eight-bit integer, and `read(10)` means a one-byte boolean. GameMaker's `buffer_f64` is type 9; the chart extra mapper does not select it. Never scan for a tag byte inside a numeric value or string; payload bytes can equal structural tags.

## Overall layout

| Offset | Size | Meaning |
| --- | --- | --- |
| `0x00` | 3 | ASCII `VSC` (`56 53 43`) |
| `0x03` | 1 | Format version: `01` |
| `0x04` | 1 | Reserved / required zero: `00` |
| `0x05` | Variable | Top-level sections |
| Variable | 1 | `FF`: end of chart payload |
| Immediately after `FF` | 384 or 0 | RSA signature, or no trailer for an unsigned chart |

The usual writer output is:

```text
56 53 43 01 00
C0  [notes...]  C1
[E0  [modifier configuration/list...]  E1]
FF
[384-byte signature]
```

Top-level tags are `C0` (note section), `E0` (modifier section), and `FF` (stop). Neither section has a byte length or record count. The reader can encounter multiple sections, although the writer emits one note section and at most one modifier section.

The first `FF` reached **through structural parsing** terminates the payload. It is not the first literal `FF` anywhere in the file and is not necessarily the last byte of the file.

## Note section: `C0 … C1`

Each note begins with `A0`, contains tagged fields, and ends with `A1`. The canonical writer emits:

```text
A0 A2 <type:u8> A3 <lane:u8> A4 <time:f32>
   [A6 <extra entries...> A7]
A1
```

| Tag | Following payload | Meaning |
| --- | --- | --- |
| `A0` | None | Begin note |
| `A1` | None | End note |
| `A2` | `u8` | Disk note type |
| `A3` | `u8` | Lane |
| `A4` | `f32` | Absolute timestamp in milliseconds |
| `A6` | Extra entries terminated by `A7` | Replace this note's extra dictionary |
| `A7` | None | End extra dictionary; only meaningful inside `A6` |
| `C1` | None | End note section; only meaningful between notes |

A simple canonical note is 11 bytes; a canonical hold with one `s32`/`f32` extra is 19 bytes. These sizes are conveniences, **not fixed record sizes**. The reader initializes `type=0`, `lane=0`, `time=0`, `extra={}`; fields may be absent or reordered, and later repetitions overwrite earlier values. Repeated `A6` groups replace the extra dictionary rather than merging it. A decoder should preserve field order and duplicate fields when lossless editing matters.

### Disk note types

| Value | Meaning in this build | Lane | Extra ID `1` |
| --- | --- | --- | --- |
| `0` | Chip/tap note | `0..3`, left to right | Unused by observed consumer |
| `1` | Normal bumper | `0..2` | Unused |
| `2` | Hold | `0..3` | Absolute hold-end timestamp in ms |
| `3` | BPM change | Ignored; `0` in corpus | New BPM; absent value is ignored |
| `4` | Opaque marker, ignored by gameplay/statistics loaders | `0` in corpus | No extras observed; original purpose unknown |
| `5` | No case in current gameplay loader | Not established | Not observed in corpus |
| `6` | Chip mine | `0..3` | Unused |
| `7` | Bumper mine | `0..2` | Unused |
| `8` | Timing/precision bumper | `0..2` | Unused |

Bumper lane `0` uses key pair `0/1`, lane `1` uses `1/2`, and lane `2` uses `2/3` ([input_handler](../extraction/main/CodeEntries/gml_GlobalScript_input_handler.gml), lines 257–267). Do not infer only two bumper lanes from the stats keys `leftBumpers` and `rightBumpers`: that cache groups every nonzero bumper lane on the right.

Disk note types are not the same enum as the runtime note renderer. The loader maps disk types `0,1,2,6,7,8` to runtime types `0,4,3,5,6,7` respectively.

For holds, the writer stores `min(time,endTime)` as the note time and `max(time,endTime)` as extra ID `1`. The end timestamp is absolute, not a duration. Hold scoring subdivisions are derived at load time; they are not separate serialized hold-piece records.

The chart does not contain its song ID, difficulty name, audio filename, display title, or a separate initial-BPM header. Those are supplied by surrounding game data and the path. Gameplay initializes its timing BPM to external `bpm_display * 2`, then type `3` records replace that timing BPM directly. Therefore the modifier beat grid should not automatically be interpreted as conventional musical quarter notes.

### Extra dictionary: `A6 … A7`

Each entry is `<type-tag:u8> <id:u8> <value>`. There is no extra-entry count or per-entry length. IDs and types are separate bytes.

| Type tag | Value type | Bytes after ID | Observed here? |
| --- | --- | --- | --- |
| `B0` | `u8` | 1 | Reader-supported |
| `B1` | `s8` | 1 | Reader-supported |
| `B2` | `u32` | 4 | Reader-supported |
| `B3` | `s32` | 4 | **141,264 entries** |
| `B4` | No mapping | Unknown / invalid for this parser | Not observed |
| `B5` | `f16` | 2 | Reader-supported |
| `B6` | `f32` | 4 | **25,306 entries** |
| `B7` | `bool` | 1 | Reader-supported; GameMaker type 10 |
| `B8` | `stringz` | Through terminating NUL | Reader-supported |
| `A7` | End dictionary | No ID or value follows | Terminator |

The included writer uses `B6` for hold endpoints and BPM values, but many shipped files use `B3`. Hard-coding every extra as a float produces incorrect charts. Only extra ID `1` occurs in this corpus: 161,559 hold-end values and 5,011 BPM values. There are 5,319 type-3 records in total, so some BPM records lack a value; the gameplay loader ignores those records. The generic reader supports other IDs but their gameplay semantics are not established.

## Modifiers: `E0 … E1`

The default configuration is one proxy and object name `obj_base_gimmick`. Configuration fields are tagged and optional:

| Tag | Payload | Meaning |
| --- | --- | --- |
| `E0` | Modifier fields | Begin modifier section |
| `E1` | None | End modifier section |
| `E4` | `u8` | Proxy count |
| `E5` | `stringz` | Gimmick object name |
| `E2` | Modifier records terminated by `E3` | Begin modifier command list |
| `E3` | None | End modifier command list |
| `E9` | Fixed 19-byte payload below | Tween/property command |
| `EC` | Two floats plus string | Per-frame function command |

Canonical order is `E0 E4 count [E5 object] [E2 records E3] E1`. The object name controls resolution of chart-specific mod IDs and named per-frame callbacks. It is a GameMaker object name, not embedded executable code.

### Tween command `E9`: 20 bytes including tag

Offsets below are relative to the `E9` byte:

| Relative offset | Size | Field | Meaning |
| --- | --- | --- | --- |
| `0x00` | 1 | `E9` | Record tag |
| `0x01` | 4 | `b:f32` | Start beat |
| `0x05` | 4 | `d:f32` | Duration in beats |
| `0x09` | 1 | `e:u8` | Easing ID |
| `0x0A` | 4 | `v1:f32` | Initial value |
| `0x0E` | 4 | `v2:f32` | Final value |
| `0x12` | 1 | `mi:u8` | Modifier ID |
| `0x13` | 1 | `p:s8` | Signed target/proxy selector |

`p >= 0` indexes the proxy array. Negative values address the gameplay controller with the modifier property prefixed by `mod_`; `-1` is the only negative value observed. Treating `FF` here as unsigned 255 or as the end-chart tag is wrong.

The gimmick handler starts the tween when the beat counter reaches `b`. It converts duration to milliseconds using `d * 60000 / BPM_at_start`, rather than serializing duration in milliseconds. Some modifier names trigger callbacks or effects instead of a simple numeric property assignment.

Global modifier IDs have bit 7 clear; IDs with bit 7 set are resolved through the selected gimmick object's `extraMods` table. Ordinary extra-mod registration starts at `0x81`. **There is no universal name for a chart-specific byte.** The [mod/easing catalog](chart_mod_ids.md) and [machine-readable mapping](../analysis/chart_format/mod_ids.json) give 74 globals, 19 easing IDs, and per-object registrations with source lines. The ImHex pattern labels globals and leaves object-specific values numeric.

### Per-frame command `EC`

```text
EC <begin_beat:f32> <end_beat:f32> <function_name:stringz>
```

Size is `10 + UTF8_byte_length(function_name)` bytes including tag and NUL. Both times are absolute beats; the second float is **not** a duration. The named method is looked up in the selected gimmick object's `funcs` dictionary. The handler invokes it every frame when `begin_beat < current_beat < end_beat`, passing the current beat. No function body is stored in the chart.

## Signature trailer and real-world exceptions

In 804 files, the chart-ending `FF` is followed immediately by a 384-byte signature, with **no padding**. The remaining file is structurally unsigned. The signature is a big-endian RSA-3072 integer using public exponent **17**, PKCS#1 v1.5 encoding, and SHA-1 of all chart payload bytes from the initial `V` through the final `FF`, inclusive. The public modulus and an independent verifier are in [verify_vsb_signatures.py](../tools/verify_vsb_signatures.py).

Do not round the chart length up to a four-byte boundary. Despite the helper name `binary_pad`, the shipped files have no such padding and their total lengths span every residue modulo four.

Corpus verification found:

| Result | Count | Detail |
| --- | --- | --- |
| Valid signatures | 803 | RSA envelope and payload digest both match |
| Structurally unsigned | 1 | `nulctrlex/SHATTER.vsb` ends exactly at chart `FF` |
| Signature digest mismatch | 1 | `plauditefull/SHATTER.vsb` has a valid RSA/SHA-1 envelope but its digest does not match the current payload |

For the mismatching file, the signed SHA-1 is `447b79a7fa23b269e2cbbd165944c18c9854f3d4`, while the current payload hashes to `e27585545d30c455e0846486bb66aa4e6039a4b6`. This establishes a mismatch, not its cause.

**This supplied game build bypasses signature checking:** `rsa_verify` immediately returns true. The [VM assembly](../extraction/main/Assembly/00318_gml_GlobalScript_chart_sign.asm), lines 211–215, corroborates the decompiled early return. This is specific to this build and should not be generalized to other releases. The ImHex pattern displays the trailer but does not cryptographically verify it.

## `.stats` companions

`.stats` is a plain INI cache with a `[stats]` section. The `checksum` value is a lowercase hexadecimal SHA-1 of the **entire `.vsb` file, including the signature**, which differs from the signature's payload-only digest. The game regenerates stats when the hash differs or refresh is forced. Missing numeric keys default to zero.

Values are typically quoted decimal strings, for example `holdNotes="179.000000"`. Keys written by the current code are:

```text
checksum, bumpers, holdNotes, holdPieces, leftBumpers, rightBumpers,
normalNotes, noteCount, multiNoteCount, multiHoldNoteCount,
peakDensity, lowestDensity, averageDensity, peakBeatDensity,
jackStat, chainStat, hasMods
```

Older caches omit keys and can contain non-finite textual values such as `-nan(ind)`. `noteCount` reflects derived gameplay/scoring counts, including hold subdivisions, rather than the number of binary note records. Treat stats as optional, potentially stale derived data, not a source of record boundaries or authoritative note counts.

Of 803 caches, 723 have matching checksums, 78 have stale sibling checksums, and two have no sibling chart (`collab_beyond/FINALE`, `dragon/ENCORE`). Four charts have no cache (`00/MIDDLE`, `dracula/FINALE`, `lockedout/MIDDLE`, `untechnical/ENCORE`). Details are in [stats_validation.json](../analysis/chart_format/stats_validation.json).

## Worked byte example

The first record of `Charts/00/OPENING.vsb` is a BPM event:

```text
00: 56 53 43 01 00    header
05: C0                begin notes
06: A0                begin record
07: A2 03             type = BPM
09: A3 00             lane = 0 (unused)
0B: A4 00 00 00 00    time = 0.0 ms
10: A6                begin extras
11: B6 01 00 00 22 43 extra ID 1 = f32 162.0 BPM
17: A7                end extras
18: A1                end record
```

A complete canonical unsigned chart containing just that event is:

```text
56 53 43 01 00 C0 A0 A2 03 A3 00 A4 00 00 00 00
A6 B6 01 00 00 22 43 A7 A1 C1 FF
```

## Using the artifacts and reproducing validation

In ImHex, open a `.vsb`, open `patterns/vividstasis_vsb.hexpat` in the Pattern Editor, and evaluate it. The pattern uses the standard `std.mem`, `std.sys`, and `type.float16` includes shipped with ImHex. Expand `chart.sections` to inspect notes and modifiers, and `chart.rsa_signature` when present. It supports the verified version-1 grammar and intentionally rejects unknown structural tags and unsupported trailer sizes rather than guessing payload lengths.

The Python helper provides an independent decoder with offsets and a byte-for-byte encoder:

```bash
python tools/vsb.py decode vividstasis/Charts/00/OPENING.vsb -o /tmp/opening.json
python tools/vsb.py validate vividstasis/Charts -o analysis/chart_format/corpus_validation.json
python tools/verify_vsb_signatures.py
python tools/validate_chart_stats.py
python -m unittest discover -s tools -p test_vsb.py -v
```

The decoder retains note-field ordering, duplicate fields, and opaque trailing bytes. Its JSON output includes derived note values as a convenience; the encoder uses the ordered `fields` representation. The current encoder is validated byte-for-byte on this corpus, not promised to preserve every possible IEEE signaling-NaN encoding in arbitrary files. Unknown tags fail explicitly. The game reader is more permissive in some unknown-tag paths, but does not supply a general length with which another parser could safely skip an unknown payload.

Real ImHex PatternLanguage validation can be repeated using a standalone `plcli` build:

```bash
python tools/validate_vsb_pattern.py \
  --runtime /path/to/plcli \
  --includes /path/to/ImHex-Patterns/includes
```

The runtime used here was built out of tree from the locally available **ImHex 1.38.1** PatternLanguage sources, without running the game. Pattern-language behavior and include APIs were checked against its local sources and the official [data-type](https://docs.werwolv.net/pattern-language/core-language/data-types) and [control-flow](https://docs.werwolv.net/pattern-language/core-language/control-flow) documentation.

The corpus has **873,225 note/event records, 254,323 tween commands, and 45 per-frame commands**. All 805 charts decoded and re-encoded identically, and the actual ImHex 1.38.1 PatternLanguage runtime evaluated the pattern successfully on all 805 files. Eight additional ImHex tests exercised extra types absent from the corpus, repeated/default fields, signed targets, and rejection of invalid/truncated inputs. All 503 observed object-specific mod-ID/object pairs resolve against the static catalog. Reader-supported extra types absent from the corpus were exercised with synthetic tests, together with default/reordered/repeated fields, strings, signed targets, truncated payloads, and unknown-tag rejection. Exact per-file hashes, boundaries, counts, signature results, and ImHex evaluation outcomes are retained under [analysis/chart_format/](../analysis/chart_format/).

The remaining semantic uncertainty is primarily the original purpose of ignored type-4 markers. Mod IDs are cataloged by their code names and object-specific registration order; this document does not claim a physical interpretation for every visual-effect parameter.
