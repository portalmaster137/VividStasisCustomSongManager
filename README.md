# Vividstasis Custom Song Manager

A desktop tool for creating, importing and managing custom Vividstasis songs. [tools/song_manager.py](tools/song_manager.py) maintains an editable song library and builds your selected songs into a separate playable copy of the game.

Import 4K or 6K osu!mania charts, assign up to five difficulties per song, add audio and a cover, and share songs as portable `.vsc` packages.

## Requirements

- The complete, unmodified **Vividstasis 6.2.2.2** game installation. Setup checks the original `data.win` hash and rejects unsupported or previously patched archives.
- FFmpeg with the `libvorbis` encoder available on your PATH.
- UndertaleModTool CLI. **Setup CLI Tool** downloads and checks the supported version; you can also select an existing CLI executable or its containing folder.
- For running from source: Python 3.11 or newer and the dependencies in `requirements.txt`.

See [Executable builds](docs/EXECUTABLE_BUILDS.md) for Windows and Linux downloads and build instructions. Packaged executables bundle Python and its dependencies. On Linux, launching the Windows game also requires Wine.

## Launch from source

Run these commands from the repository root. A Python virtual environment is recommended.

```sh
python -m pip install -r requirements.txt
python tools/song_manager.py
```

## Set up a playable game copy

1. Click **Set up game copy…**.
2. Choose the complete original game folder and a separate **new or empty** destination folder for the playable copy.
3. Click **Setup CLI Tool**, or select your existing UndertaleModTool CLI.
4. Click **Create playable copy**.

Setup copies the complete game and preserves a clean archive in the manager workspace. Every build starts from this backup. Back up your game profile separately, since saves can live outside the game folder.

## Add songs to the library

### Import an osu! archive

Click **Auto Import osz…** and choose an `.osz` file. In the import dialog:

1. Choose the audio track and, optionally, a cover image.
2. Assign supported 4K or 6K mania charts to OPENING, MIDDLE, FINALE, ENCORE or APOTHEOSIS. Each difficulty accepts one chart; leave unwanted charts set to Skip.
3. Set each chart's displayed level and, for 6K charts, its bumper-hold policy.
4. Review the title, artist and package ID, then import.

The manager suggests metadata and audio from the first assigned chart. Check the referenced audio shown for each chart: the selected audio track is used for the entire song.

### Create or edit a song

Click **New song**, choose audio and an optional cover, then use **Add chart files…** to add `.osu` charts. Set their difficulty slots, levels, designers and bumper-hold policies, then click **Save song to library**. Select an existing library song to edit it.

Songs can contain any nonempty subset of the five difficulty slots. APOTHEOSIS can be used without ENCORE. Covers are resized and center-cropped to 100 × 100 pixels.

### Share packages

Use **Import .vsc…** to copy packages into your library and **Export .vsc…** to share a saved song. Packages contain the metadata and referenced audio, cover and chart files. Export requires a new filename.

Package IDs identify songs across updates. Replacing a package with the same ID preserves its game ID; use different IDs for unrelated songs.

## Build and play

1. Check the library songs you want installed.
2. Click **Review & build…** to review additions, updates and removals.
3. Click **Build and install**. The manager stages and verifies the build before installing it into the playable copy.
4. Click **Launch game** and open the **Custom Charts** pack.

Saving or importing a library song does not install it immediately. Unchecking a song removes it from the next committed build while keeping its editable package. Building with no songs selected restores the stock archive and removes manager-owned custom chart folders.

- **Restore previous build** restores the previous complete manager installation.
- **RESTORE (clean game)** restores the pristine archive and removes manager-installed custom charts.
- **Delete song…** deletes the editable library package. An installed copy remains until the next build or clean restore; export first if you want to keep a portable copy.

Both restore actions retain the library and reserved song IDs.

## Chart conversion and playback

4K charts map directly to the four normal lanes and preserve holds. For 6K charts, the two outer lanes become left and right bumpers, while the middle four become normal lanes. Choose how outer-lane holds are handled:

- **Reject bumper holds**: reject charts containing them (the default).
- **Start tap**: create a bumper at the hold start.
- **Start and end taps**: create bumpers at both ends.

Bumper controls are disabled for 4K charts. Use audio that matches the chart timeline, including leading silence. Conversion does not transfer osu! scroll-speed changes, hitsounds or storyboard effects.

Custom songs use GameMaker audio and return to song select after playback, skipping the stock results screen. A custom score system is not included. Interactive desktop behavior, playback and visual layout still need verification on the target platform.

## Workspace and further documentation

The default workspace is `.song-manager` beside the project, or beside the executable for packaged builds. It contains the library, clean backup, manager state, build logs and stable ID assignments. Keep it when moving or updating the manager.

Open **Disk Space Usage** to measure the library, clean backup, conversion cache, build files, rollback files and other workspace data. The tab also shows configured game folder sizes and available drive space. Use **Refresh disk usage** to update the figures; scans run in the background and can be cancelled. Sizes are logical file sizes, exclude filesystem overhead and skip links. Unreadable entries are marked as partial measurements. Game folders are separate measurements and may overlap with workspace data; do not add every row together.

To manage another game copy or store data elsewhere, launch with a separate workspace:

```sh
python tools/song_manager.py --workspace /path/to/workspace
```

- [Detailed Song Manager guide](docs/SONG_MANAGER.md)
- [Executable downloads and local builds](docs/EXECUTABLE_BUILDS.md)
- [Command-line single-song builder](docs/BUILD_CUSTOM_SONG.md)
- [Chart registration](docs/CHART_REGISTRATION.md), [custom audio](docs/CUSTOM_AUDIO.md) and [VSB format](docs/VSB_FORMAT.md)
