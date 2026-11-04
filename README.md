# Getting started: custom Vividstasis songs

For the desktop song library, package editor and managed game builds, see [the Song Manager guide](docs/SONG_MANAGER.md). The manager includes **Auto Import osz…** for choosing audio and charts directly from an osu! archive. The command-line workflow below remains available for single-song builds.

Build a custom song from an audio file, a **4K or 6K osu!mania `.osu` chart**, and the unaltered `data.win` supplied with this game build.

## Requirements

- Python 3.11 or newer.
- FFmpeg with the `libvorbis` encoder available on your PATH.
- UndertaleModTool CLI at `./UndertaleMTCLI` (an executable or a directory containing `UndertaleModCli`), relative to the directory you run the command from. Use `--cli /path/to/UndertaleModCli` to override it.
- The original game files. The patcher checks the archive hash and rejects other builds or previously patched archives.

## Build your song

From this directory, run:

```sh
python tools/patch_custom_song.py \
  /path/to/music.mp3 \
  /path/to/chart.osu \
  vividstasis/data.win \
  --output-dir custom-build \
  --chart-id my_song \
  --cover /path/to/cover.jpg \
  --bump-both
```

The optional `--cover` image is embedded as the song jacket, resized and center-cropped to 100×100. Omit it to use the generic jacket.

Choose a new output directory for each build. Title, artist and designer come from the chart; override them with `--title`, `--artist` and `--designer`. Use `--level 8` to set the displayed difficulty.

Source lanes **1 and 6** become left/right bumpers. Lanes **2–5** become the four normal lanes, preserving holds. Choose how bumper holds are converted:

- `--bump-start`: one bumper at the hold start.
- `--bump-both`: bumpers at the start and end.
- `--reject-bump-holds`: reject them; this is the default when no option is given.

Use audio that matches the chart's timeline, including leading silence. The converter does not transfer osu scroll-speed changes, hitsounds or storyboard effects.

## Install and play

1. Make a copy of the **complete original game directory**.
2. Copy `custom-build/data.win` into that copy, replacing its archive.
3. Merge `custom-build/Charts/` into that copy's `Charts/` directory, preserving existing charts.
4. Launch the copied game and open the **Custom Charts** pack.

The three base difficulties contain the same input chart. Custom playback uses GameMaker audio and skips the stock results screen, returning to song select. This version adds one custom song per clean build.

The builder has passed synthetic compilation, saved-archive, audio and chart checks. **In-game playback has not yet been verified here.** Test with a copied game and backed-up profile. Build logs and generated patch code are in `custom-build/build/`.

For more detail, see [the builder guide](docs/BUILD_CUSTOM_SONG.md), [chart registration](docs/CHART_REGISTRATION.md), [custom audio](docs/CUSTOM_AUDIO.md), and [the VSB format](docs/VSB_FORMAT.md).

Chart type is auto-detected from `CircleSize`. 4K columns map directly to the four normal lanes and preserve holds. Bumper policies apply only to 6K charts. In the manager, the Type column shows 4K or 6K and bumper controls are disabled for 4K; switching back to 6K restores the existing policy selection. No package mode field is required.
