# Patching Vividstasis for custom charts

For the automated audio + osu chart + original archive workflow, use [the custom-song builder](BUILD_CUSTOM_SONG.md).

This guide describes the expected workflow once the chart-registration and audio edits are ready. The game is a GameMaker VM build, and the supplied `data.win` can be edited with the UndertaleModTool CLI already used for extraction. The extraction is **not** a reconstructed GameMaker project: it lacks original project/source files, so this workflow patches compiled resources in `data.win` and does not rebuild the game's runner or a full project.

The examples below are a workflow template. They have not yet been used to build or launch a modified game.

## Prepare a clean working copy

Keep the installed game untouched. Copy the whole game directory to a separate test directory, then preserve the original archive and hash it:

```sh
cp -a /path/to/Vividstasis /path/to/Vividstasis-chart-test
cd /path/to/Vividstasis-chart-test
cp data.win data.original.win
sha256sum data.win data.original.win
```

Use the CLI version tested for extraction (`0.9.2.0`, commit `f43e12c445c37d50dc6244caa12ccab232983f3f`) and keep each patch input in the writable research workspace. Work on a fresh copy of `data.win` for each build; this makes failures easy to roll back and prevents cumulative edits from obscuring which patch caused a problem.

## Apply GML changes

For a small code replacement, UndertaleModCli's `replace` command accepts a resource name and a GML file. The CLI imports and compiles that code into the GameMaker VM resource:

```sh
cli=/path/to/UndertaleModTool/CLI/UndertaleModCli
"$cli" replace data.original.win \
  -c 'gml_GlobalScript_load_song_information=/path/to/load_song_information.gml' \
  -o data.win
```

Use the code resource names from `extraction/main/metadata/code_index.json` and follow the source's decompiled naming where it is accepted by the CLI. The CLI help also describes `UMT_REPLACE_ALL`, but avoid it for ordinary chart patches: it replaces every matching code resource and makes accidental broad changes easier. For multiple code edits, prefer one reviewed `.csx` patch script or build separate intermediate archives; confirm the CLI's exact replacement-option behavior before relying on repeated `-c` flags.

If a change is easier to express as an UndertaleModTool C# script, use `load` with `-s` and an explicit output path:

```sh
"$cli" load data.original.win \
  -s /path/to/patch_custom_charts.csx \
  -o data.win
```

The script runs against the loaded `UndertaleData`; use the shipped UndertaleModTool scripts and API version as the reference for import, compile, and resource lookup APIs. For edits to multiple code entries or structured resources, a script is often easier to review than a long shell command. Capture CLI output to a log and treat compiler warnings/errors as a failed build until understood.

Do not pass `-f` unless intentionally replacing an existing output. Do not use the original installed `data.win` as the output path.

See [adding custom audio](CUSTOM_AUDIO.md) for embedding a new music resource and connecting it to a registered song.

## Add the chart files

The runtime looks up `Charts/<chart_id>/<difficulty>.vsb` under the game's working directory. Copy the authored VSBs into the test copy at that exact path, using the chart ID and standard difficulty basenames selected by the registration code (normally `OPENING`, `MIDDLE`, `FINALE`, and optionally `ENCORE`). Keep chart metadata/stats alongside the corresponding VSB if desired; stats are a regenerable cache, not a registration mechanism. See [the chart registration guide](CHART_REGISTRATION.md) and [the VSB format guide](VSB_FORMAT.md).

The current loader resolves music through GameMaker's registered sound resources. A loose OGG beside a chart is not automatically discovered. If the patch uses an existing in-game sound, no audio import is needed for the first test. New music requires a separate resource-import/loader change, and that should be validated independently from chart registration.

## Check the build before launching

1. Confirm `data.original.win` still has the original SHA-256 recorded in [the extraction report](../extraction/README.md).
2. Confirm the patched archive exists and is nonempty; ask the CLI to parse it:

   ```sh
   "$cli" info data.win
   ```

3. Re-run a targeted `dump` of changed code/resources into a new temporary directory and inspect the exported result. The CLI dump workflow is recorded in [reproduce.sh](../extraction/reproduce.sh).
4. Validate each VSB with the local parser and, when available, the ImHex pattern:

   ```sh
   python /path/to/VividStasisDecomp/tools/vsb.py decode Charts/custom_demo/OPENING.vsb -o /tmp/opening.json
   ```

   `decode` parses one file and emits its notes/metadata as JSON. The corpus validator accepts a directory and writes a report; for example, validate the game chart tree with `python /path/to/VividStasisDecomp/tools/vsb.py validate Charts -o /tmp/chart_validation.json`.

5. Record the output archive hash, patch inputs, CLI version, command, and logs beside the test build. The hash is for identifying this exact build, not for proving it is safe or correct.

Only then launch the copied game and test the full path: boot, custom pack visibility, each intended difficulty, audio playback, chart load, results, and return to menu. Start with a disposable profile or back up the profile separately; chart registration can affect unlock, score, rating, and network code. A dedicated custom-chart mode should keep custom scores separate from the game's stock leaderboard flow.

## Roll back and iterate

If the test build fails, discard its `data.win` and recreate the copy from `data.original.win`, then reapply the patch with one change at a time. Keep the original executable, archive, profile, and user data untouched. Once the patch is stable, retain the exact patch script/GML inputs and build instructions so the output can be regenerated; do not treat a patched `data.win` as a maintainable source project.

## Practical limits

- UndertaleModTool edits the GameMaker data archive; it does not rebuild the native executable or missing original project.
- This game's native extensions/audio behavior and the proposed registration hooks have not yet been tested in a patched runtime.
- Chart registration alone does not import new audio, isolate score submission, or guarantee every result/rating path is local. Those behaviors must be explicitly handled in the patch and checked during testing.
- A patched `data.win` may not be accepted by future game updates or external integrity checks. Keep a clean, version-matched original for each patch build.
