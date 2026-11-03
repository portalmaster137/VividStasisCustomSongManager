# Converting 4K or 6K osu!mania charts

Run from the research workspace with Python 3 (no third-party packages):

```sh
python tools/osu_to_vsb.py input.osu OPENING.vsb
python tools/osu_to_vsb.py input.osu OPENING.vsb --bump-start
python tools/osu_to_vsb.py input.osu OPENING.vsb --bump-both
```

Bumper holds are rejected by default; `--reject-bump-holds` selects that behavior explicitly. The three switches are mutually exclusive. Existing output files are refused unless `--force` is supplied.

Source lanes 1 and 6 become normal bumper notes on VSB lanes 0 and 2 (left and right). Source lanes 2–5 become VSB lanes 0–3, preserving taps and holds. `--bump-start` emits one bumper at the hold start; `--bump-both` emits bumpers at both endpoints. This can introduce overlapping bumper notes; the converter does not remove or adjust them.

Timestamps and absolute hold endpoints are preserved in milliseconds and stored as VSB float32 values. Uninherited timing points become BPM events. Inherited timing points (scroll velocity), hitsounds, samples, breaks, storyboard, audio and visual assets are not converted. Playback rate mods and osu!mania judgment settings are not transferred.

The output is an unsigned version-1 VSB with no gimmick modifiers or stats cache. This supplied build bypasses signature verification. It has not been tested in the running game. Copy the output into the registered chart directory and difficulty filename; see [registration](CHART_REGISTRATION.md) and [patching](PATCHING_GAME.md). The converter prints the first source BPM; this build initializes its internal BPM using twice the catalog `bpm_display`, so set that metadata to half the source BPM. BPM events then use source BPM values directly. Audio must use the same timeline as the source chart, including any leading silence.

Chart type is auto-detected from `CircleSize`. 4K columns map directly to the four normal lanes and preserve holds. Bumper policies apply only to 6K charts. In the manager, the Type column shows 4K or 6K and bumper controls are disabled for 4K; switching back to 6K restores the existing policy selection. No package mode field is required.
