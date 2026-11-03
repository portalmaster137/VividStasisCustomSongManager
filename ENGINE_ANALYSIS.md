# Vividstasis engine investigation

Static inspection on 2026-11-03. No game executables were launched or modified.

## Findings

The game uses **GameMaker, from the GameMaker Studio 2 / modern GameMaker lineage**, with game logic present as VM bytecode. Subsequent extraction with UndertaleModCli 0.9.2.0 detects format/runtime version **2024.14.1.0**; this can be inferred from format features and does not independently establish the exact runner build. See [the extraction](extraction/README.md).

- `vividstasis/VIVIDSTASIS.exe` is an x86-64 Windows GUI PE executable, 7,998,464 bytes. Embedded strings include `Made with GameMaker`, `YoYoGames`, and source paths containing `GameMaker/Runner/GMS2-Runner-Main`.
- Executable SHA-256: `af928313c8add5e94870521f7c7c83dcfcd2b5c66b642c945b6796ba41013ed2`.
- REA PE resource inspection evidence: `ev_0fda2f5b0c52f51c9c57857de5f217e29b88203fd5e4eed3e131bfea776a0cde`. This establishes PE/resource layout; engine identification additionally uses local strings and archive parsing.
- `data.win` is a valid top-level `FORM` container whose declared length matches the 2,764,969,219-byte file. A bounded header walk found the expected GameMaker chunks, including `GEN8`, `EXTN`, `SPRT`, `SCPT`, `OBJT`, `ROOM`, `CODE`, `VARI`, `FUNC`, `STRG`, `TXTR`, and `AUDO`.
- `GEN8` reports WAD/bytecode-format version 17. This is a format value, not GameMaker release 17.
- Its `CODE` chunk starts at file offset 2,008,704, spans 4,510,328 payload bytes, and declares 22,033 code entries. Sample entries contain recognizable GML script names. This supports using a VM decompiler rather than treating the game as a YYC-only native build.

## Distribution structure

| Item | Observed contents / interpretation |
| --- | --- |
| `VIVIDSTASIS.exe` | Native GameMaker runner |
| `data.win` | Main game code and resources: 2,141 sprite entries, 814 objects, 232 rooms, 664 sound entries, 19,375 script-table entries; these are table counts, not necessarily distinct user-authored resources |
| `Charts/` | External files with extensions including `.vsb`, `.stats`, `.vmv`, `.vsc`, `.vsm`, and ZIP archives; custom formats not decoded in this pass |
| `MOVIE/` | MP4 video assets, plus two `.sfk` sidecars |
| `rhythm_onrelease.dat` | `FORM` container containing an `AUDO` chunk; approximately 98.9 MB |
| `update_340_gts.dat` | `FORM` container containing an `AUDO` chunk; approximately 20.7 MB |
| DLLs and `options.ini` | Native extensions, including Steamworks, presence, RSA, dialogs, shell execution, and a game-specific optimization DLL; individual implementation behavior not analyzed |
| `otherside/` | Additional executables and a separate 32,823,152-byte GameMaker archive with 19,435 code entries; its gameplay purpose was not established |
| `ver` | Game version string `6.2.2.2 [F3D3B703]`; not an engine version |

## Open-source tools

1. **[UndertaleModTool](https://github.com/UnderminersTeam/UndertaleModTool)** (GPL-3.0): recommended starting point. Opens GameMaker data files, decompiles GML VM code, exposes assets/objects/rooms, and supports editing and scripted export. Includes UndertaleModLib for custom automation and a CLI usable on Linux; its main GUI targets Windows. Open `vividstasis/data.win` as the initial target. Actual compatibility with this build remains untested.
2. **[Underanalyzer](https://github.com/UnderminersTeam/Underanalyzer)** (MPL-2.0): C# library for GML VM analysis, decompilation, and compilation. Useful for building custom code-analysis/export tooling; not a standalone asset browser.

[Official getting-started instructions](https://underminersteam.github.io/usage/getting-started/) cover stable/nightly builds and opening data files. If stable cannot parse this game's format, try the latest nightly. Work from a copy when editing.

The best next step is to load the main archive with UndertaleModTool/its CLI and export GML plus resource metadata. Native DLL internals would require a separate native-code investigation. The initial static inspection did not perform decompilation or a compatibility test; the subsequent [extraction report](extraction/README.md) records successful CLI exports. In general, decompiled output should not be assumed to reproduce the original project or comments.
