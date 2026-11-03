# Build a custom-song patch

Run this script from the research workspace with Python 3.11+, FFmpeg with `libvorbis`, and the supplied UndertaleModTool CLI:

```sh
python tools/patch_custom_song.py \
  /path/to/music.mp3 \
  /path/to/chart.osu \
  /path/to/unaltered/data.win \
  --output-dir /path/to/new-custom-song-build \
  --chart-id my_song \
  --bump-both
```

`--output-dir` must not already exist. The input archive must match the SHA-256 of the original analyzed build; other releases are rejected. The script reads the original and checks that its hash is unchanged after building. It never overwrites input files. Audio formats supported by the installed FFmpeg can be used; the selected first audio stream is converted to Ogg Vorbis without deliberate trimming or timing shifts.

The osu file must be 6K mania. Lanes 1/6 become left/right bumper taps, and lanes 2–5 become normal notes/holds. Bumper holds reject by default; select `--bump-start` or `--bump-both` to convert them. `--reject-bump-holds` explicitly selects rejection. See [converter details](OSU_CONVERTER.md).

Title, artist and chart designer come from osu metadata. Override them with `--title`, `--artist` and `--designer`. `--level` sets the displayed difficulty constant (default 4). `--chart-id` accepts lowercase ASCII letters, digits and underscores, starting with a letter. `--cli` overrides the UndertaleModCli executable path or its containing directory. The default is `./UndertaleMTCLI`.

## Output and installation

A completed output contains:

- `data.win`: compiled registration/pack/playback patches and embedded new audio.
- `Charts/<chart-id>/OPENING.vsb`, `MIDDLE.vsb`, `FINALE.vsb`: three copies of the supplied chart, so every exposed base difficulty has a playable file.
- `manifest.json`: source/output hashes and conversion settings.
- `build/`: generated import and verification scripts, input OGG, patched and re-exported GML, and CLI logs.

Copy **both `data.win` and `Charts/`** into a copy of the complete original game directory. Merge `Charts/` with the existing directory, preserving stock charts. The output is an overlay: the game still needs its original executable, DLLs, registry, other charts and supporting files. A lone `data.win` cannot contain the externally loaded charts without a separate chart-loader redesign.

Launch the copied game and select the **Custom Charts** pack (also included in All Songs). The new entry is registered before unlock and highscore initialization, using a new ID after the stock catalog. The same audio resource supplies the menu preview. A generic jacket is used unless `--cover /path/to/image.png` is supplied. Cover images are resized and center-cropped to 100×100, preserving their aspect ratio before cropping, and embedded as a new `song_<chart-id>` sprite on its own texture page. Existing artwork is preserved. PNG, JPEG and other still-image formats readable by FFmpeg are supported; animated inputs use the first frame. The three visible difficulties play the same converted chart; this version accepts one song and one chart per clean build.

## Playback behavior

The patch temporarily selects GameMaker audio for the custom song and restores the previous setting in gameplay cleanup. It keeps ordinary song playback on the user's existing backend. This avoids depending on unverified native precise-audio resource lookup. The custom song skips the normal results room and returns to song select on clear/failure/quit; this avoids the stock results score/rating submission path. It does not implement a custom score system or promise that the rest of the game's profile/network behavior is disabled.

The custom song's initial BPM metadata uses half the osu source BPM, matching this build's doubling convention. Converted BPM events use the source BPM directly. Audio must match the chart's original timeline, including leading silence. Hitsounds, inherited scroll-speed changes and storyboard elements are not converted.

## Build validation and limits

The script transcodes audio, compiles targeted GML changes through UndertaleModTool's `CodeImportGroup`, saves to `data.pending.win`, then reopens that saved archive. It compares the imported audio bytes and decompiles all four changed code entries to confirm patch markers survived serialization. Only after those checks does it publish `data.win` and write a manifest. Missing or ambiguous patch anchors abort the build. Logs and partial files remain for diagnosis after failure; use a fresh output directory for another attempt.

An end-to-end synthetic build was compiled and serialized against the original archive during development. Archive checks do not establish running-game behavior. The build has not been launched in-game here: check menu visibility, playback/synchronization, pause/resume, retry, clear/failure and return to menu in your copied game before using a real profile.

For the underlying investigation, see [song registration](CHART_REGISTRATION.md), [audio resources](CUSTOM_AUDIO.md), and [general patching](PATCHING_GAME.md).

The exit destination now matches the stock `start_song` destination, `scene_songselect_old`. Earlier builds forced `scene_songselect`, a different selector whose `obj_tempEffect` mixes the game's tracked surface helper with a raw reset. That can leave the tracked stack stale and cause the reported unbalanced-surface error. Rebuild from the unaltered archive with this script and replace the previous output. Compilation and saved-code checks verify the corrected destinations; in-game clear/fail/quit checks are still needed.
