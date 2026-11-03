# Custom song cover images

Supply `--cover /path/to/image.jpg` to `tools/patch_custom_song.py`. The cover is embedded in `data.win`, so no separate image needs to be installed. Without that argument, the builder retains the generic jacket.

The [VSD reader](../extraction/main/CodeEntries/gml_GlobalScript_v1_vsd_reader.gml) looks up `song_<chart_id>` and falls back to `song_generic`. Our injected catalog record explicitly assigns the same named sprite to its `jacket` field. This field is then used by the game's existing song display and gameplay launch code.

The [generic jacket](../extraction/main/resources/Sprites/00524_song_generic.json) is a single-frame 100×100 sprite with origin (0, 0). The builder matches that shape. FFmpeg preserves the source aspect ratio while enlarging/shrinking to cover a square, then crops the center to 100×100 and writes an RGBA PNG. Use a square source if all of its edges must be visible. Animated inputs contribute only the first frame.

Import appends a new embedded texture, texture-page item, and sprite named `song_<chart_id>`. It uses a dedicated texture page instead of repacking the original atlases, and adds the texture/sprite references to the texture group containing `song_generic`. Sprite format and playback fields follow the generic jacket. Existing artwork is preserved.

After saving, the builder reopens the archive and verifies the jacket dimensions, frame count, texture reference and exact embedded PNG bytes. It also retains the usual imported-audio and compiled-code checks. The normalized cover is available at `build/cover.png` and its SHA-256 is recorded in the manifest.

A synthetic complete build with a cover passed compilation, serialization, reopening, image-byte comparison and code checks. Its manifest is retained in [the build evidence](../analysis/custom_song_build/cover/manifest.json). In-game cover appearance has not been checked here. The cover importer does not alter rendering helpers. The builder now uses the stock freeplay return room; see [the builder guide](BUILD_CUSTOM_SONG.md) for the exit-path correction.
