# Custom Song Manager

The desktop manager creates editable song packages, selects a set of songs, and rebuilds a playable game copy from a clean backup.

Install the Python dependencies and launch from the workspace root:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python tools/song_manager.py
```

FFmpeg and UndertaleModTool CLI are also required. The default CLI location is `./UndertaleMTCLI`; both its containing directory and its executable can be configured. Only the original game build analyzed in this workspace is supported.

During setup select the complete original game directory and a separate new destination. The manager copies the game and preserves `<workspace>/original/data.win.backup`. Existing backups are verified and reused, never overwritten. Every build starts from that backup. Keep your profile backed up separately; the game's save location can be outside its installation directory.

Use **Auto Import osz…** to create a library song from an osu! archive. The manager inspects the archive in the background, then shows its supported 4K/6K mania charts and lists incompatible charts separately. Assign up to five source charts to different difficulty slots; leave unwanted charts set to Skip. Each slot has an editable level (default 4) and a 6K bumper-hold policy (default reject).

Choose the audio track in the required dropdown. The first assigned chart's `AudioFilename` is suggested when it matches an archive track; every row also shows its referenced audio so you can compare sources. You can change the suggestion, and the chosen track supplies the entire imported song. Optionally choose a cover image from the archive. Title and artist default from the first assigned chart; a unique package ID is suggested automatically. Existing library entries are replaced only after confirmation. A validation error keeps the import dialog's choices for correction.

Import copies the chosen audio, cover and charts into the editable library before closing the archive. It does not install them into the game immediately; use the regular review/build action afterward. Export the resulting song as `.vsc` when a portable package is needed.

Create a song by choosing audio, an optional jacket, and one or more 4K or 6K osu!mania charts. Assign each chart to OPENING, MIDDLE, FINALE, ENCORE, or APOTHEOSIS, and set its level, designer and bumper-hold policy. APOTHEOSIS is directly selectable for custom songs in the game; it does not require an ENCORE chart or a keybind toggle. The normal lane conversion remains unchanged. Use audio matching the chart's timeline. Cover images become 100×100 square jackets.

Import/export uses `.vsc` ZIP archives containing `data.toml` and referenced audio, cover and chart files. Package IDs are stable lowercase identifiers. Updating a library song with the same ID preserves its game ID; unrelated songs must use different IDs. Imported packages are copied into the local library so editing them does not change the original archive.

Select songs in the library, review the pending changes, then commit the rebuild. The manager stages and verifies its output before installation. Unchecking a song removes it from the next build; it does not delete the library package. The previous successful installation is retained for rollback, including its custom chart files. An empty selection restores the stock archive and removes manager-owned custom chart folders.

The two restore actions have separate purposes: **Restore previous build** returns to the previous complete manager installation, while **RESTORE (clean game)** restores the pristine archive and removes manager-installed custom chart files. Both retain library packages and stable ID assignments. Restores run in the background and require confirmation.

**Delete song** removes the selected editable library package after confirmation and deselects it. It does not immediately delete files from the installed game. An installed song whose package was deleted remains listed as pending removal until the next committed build or clean restore. Export a `.vsc` first if you want to retain a portable copy.

Custom songs use GameMaker audio and return to the stock freeplay selector without entering stock results. A custom score system is not included. Source packages can contain any nonempty subset of OPENING, MIDDLE, FINALE, ENCORE, and APOTHEOSIS, including an APOTHEOSIS-only song; only supplied slots should be exposed in-game. The custom-only APOTHEOSIS selection uses internal difficulty ID 5, preserving the stock PRELUDE ID 4. It follows the custom-song playback route and skips stock results.

By default, manager data is stored in `.song-manager` beside the project. Use `python tools/song_manager.py --workspace /path/to/workspace` to choose another location.

The manager's state, package library, build logs and ID assignments belong together. Preserve that workspace when moving the manager or game copy. Reserved numeric IDs are not recycled when songs are deselected.

Automated package, converter and transaction tests pass. They include interruption recovery, backup preservation, ID stability and rollback. Successful builds retain one previous installation snapshot; large staged archives are discarded while diagnostic scripts and logs remain.

A real two-song archive build, sparse chart slots, removal rebuild, asset-cache reuse and byte-identical previous-build rollback also passed; see [the evidence](../analysis/chart_manager/backend_smoke.json).

The UI requires PySide6. Its installation could not be completed in the development environment because PyPI DNS was unavailable; window interaction and gameplay checks must be performed on a machine with that dependency installed.

Example package metadata:

```toml
format_version = 1
id = "my_song"
title = "My Song"
artist = "Artist"
audio = "audio.mp3"
jacket = "jacket.png"

[charts.opening]
file = "charts/opening.osu"
level = 4.0
designer = "Mapper"
bumper_holds = "reject"

[charts.encore]
file = "charts/encore.osu"
level = 12.0
designer = "Mapper"
bumper_holds = "both"

# Optional directly selectable custom difficulty; ENCORE is not required.
[charts.apotheosis]
file = "charts/apotheosis.osu"
level = 14.0
designer = "Mapper"
bumper_holds = "both"
```

Chart type is auto-detected from `CircleSize`. 4K columns map directly to the four normal lanes and preserve holds. Bumper policies apply only to 6K charts. In the manager, the Type column shows 4K or 6K and bumper controls are disabled for 4K; switching back to 6K restores the existing policy selection. No package mode field is required.

Direct APOTHEOSIS build verification is recorded in [the standalone build evidence](../analysis/chart_manager/direct_apotheosis_smoke/manifest.json). Custom confirmation, song rows, transition and gameplay labels support APOTHEOSIS. Secondary stock pack-summary counters and the level-overview detail table retain their four-base-difficulty layout. Gameplay and visual layout still require in-game verification.
