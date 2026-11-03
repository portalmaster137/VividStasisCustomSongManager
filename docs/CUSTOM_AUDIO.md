# Adding new audio for a custom chart

The first implementation should **append a named sound resource and its OGG payload to `data.win`'s built-in audio group**, then register a new catalog entry that points to that sound. This follows the representation already used by Tutorial's audio and avoids introducing another audio-group file or a different playback API. It is a proposed patch route supported by static evidence; newly imported audio has not yet been tested in the running game.

## What the game actually uses

The [VSD reader](../extraction/main/CodeEntries/gml_GlobalScript_v1_vsd_reader.gml) resolves three resource names after reading a song record:

```gml
song.audio_id = asset_get_index("music_chart_" + song.chart_id);
song.jacket = asset_get_index("song_" + song.chart_id);
song.preview_id = asset_get_index("preview_" + song.chart_id);
```

For a chart folder named `custom_demo`, the conventional main sound name is therefore `music_chart_custom_demo`. This is a registered GameMaker sound asset, not a path to a loose audio file. A missing main sound produces a warning and leaves an invalid ID; jacket and preview have generic fallbacks.

[start_song](../extraction/main/CodeEntries/gml_GlobalScript_start_song.gml) assigns the selected sound to `global.loadaudio`, using `song_get_info` so difficulty-specific metadata such as Encore overrides can apply. The [gameplay controller Create event](../extraction/main/CodeEntries/gml_Object_cc_Create_0.gml), lines 59–67, chooses a backend:

```gml
if (global.op_use_gamemaker_audio) {
    playback = audio_play_sound(global.loadaudio, 1, false, global.op_music_volume);
    audio_pause_sound(playback);
} else {
    precise_audio_set_volume(global.op_music_volume);
    precise_audio_load_sound(global.loadaudio);
}
```

The [controller Step event](../extraction/main/CodeEntries/gml_Object_cc_Step_1.gml) has corresponding timing, seek and speed branches. Its native branch obtains seconds from `precise_audio_get_time()` and converts them to chart milliseconds. A replacement loader must preserve those operations as well as starting playback; playing a loose stream alone does not establish compatibility.

The extension declaration is in [vividstasis_optimization](../extraction/main/resources/Extensions/00006_vividstasis_optimization.json). Its declarations and the GML call establish the interface used by this build, but do not establish the native implementation's internal resource lookup or support for newly appended sounds. No native DLL behavior was executed or reversed in this pass.

## Sound resource versus audio payload

A sound involves several distinct references:

| Part | Purpose |
| --- | --- |
| `Data.Sounds` entry | Named asset returned by `asset_get_index`; includes flags, volume, pitch and group references |
| `Data.EmbeddedAudio` entry | Encoded audio bytes stored in the main archive for the built-in group |
| `AudioFile` / `AudioID` | Reference/index of the payload within its group; this is not the sound asset ID |
| `AudioGroup` / `GroupID` | Which group owns the payload |
| Optional external group archive | Payload storage for non-built-in groups, with paths defined by the archive's group metadata |

The [extracted sound table](../extraction/main/metadata/Sounds.jsonl) contains `music_chart_tutorial` at sound index **309**, referring to embedded payload **290**, group **0**. Its flags are `IsCompressed | Regular` (102), and its reported duration is 147.73 seconds. This illustrates why a sound index must not be substituted for a payload index.

The supplied importer is a useful implementation reference: [`ImportSingleSound.csx`](</home/porta/Code/UndertaleModTool/CLI/Scripts/Resource Importers/ImportSingleSound.csx>). It creates an `UndertaleEmbeddedAudio`, registers an `UndertaleSound`, and sets group/payload references. For an embedded OGG kept compressed, it uses `IsCompressed | Regular`; for an OGG decoded on load, it also sets `IsEmbedded`. These flag names should be used as implemented by UndertaleModTool, rather than guessed from ordinary English meanings.

## Concrete import recipe for the first patch

Prepare Ogg Vorbis audio, using the exact timeline expected by the chart. An `.ogg` filename alone does not prove the contained codec is Vorbis. Preserve leading silence and do not trim or normalize timing during import. The osu converter copies hit-object timestamps; it does not extract or modify audio.

The following `.csx` is an **unexecuted implementation template**, adapted to the API shown by the supplied importer. It appends a new resource, refuses a duplicate name, and uses the built-in group. Replace the input path before use:

```csharp
using System;
using System.IO;
using UndertaleModLib;
using UndertaleModLib.Models;

EnsureDataLoaded();
string path = "/absolute/path/to/custom_demo.ogg";
string name = "music_chart_custom_demo";
foreach (var existing in Data.Sounds)
    if (existing?.Name?.Content == name)
        throw new Exception("Sound already exists: " + name);

int groupId = Data.GetBuiltinSoundGroupID();
if (groupId < 0 || groupId >= Data.AudioGroups.Count)
    throw new Exception("Expected a built-in audio group in this build");

var payload = new UndertaleEmbeddedAudio {
    Data = File.ReadAllBytes(path)
};
int payloadId = Data.EmbeddedAudio.Count;
Data.EmbeddedAudio.Add(payload);
var sound = new UndertaleSound {
    Name = Data.Strings.MakeString(name),
    Type = Data.Strings.MakeString(".ogg"),
    File = Data.Strings.MakeString("custom_demo.ogg"),
    Flags = UndertaleSound.AudioEntryFlags.IsCompressed
          | UndertaleSound.AudioEntryFlags.Regular,
    Effects = 0,
    Volume = 1.0f,
    Pitch = 1.0f,
    AudioID = payloadId,
    AudioFile = payload,
    GroupID = groupId,
    AudioGroup = Data.AudioGroups[groupId]
};
Data.Sounds.Add(sound);
ScriptMessage("Added " + name + " as sound index " + (Data.Sounds.Count - 1));
```

This imports bytes; it does not validate the codec or establish the correct handling of duration metadata in this tool/build. Reopen the output and check `audio_sound_length` in-game. The built-in importer is a starting point, not proof that every runtime-specific field is satisfied.

Run the eventual import script against a clean archive, saving a separate output:

```sh
/home/porta/Code/UndertaleModTool/CLI/UndertaleModCli load \
  /path/to/test-game/data.original.win \
  -s /path/to/import_custom_audio.csx \
  -o /path/to/test-game/data.audio.win
```

Then apply the catalog/pack GML patch to `data.audio.win`, producing the test copy's final `data.win`, or combine the import and code changes in one reviewed script. Always use explicit intermediate/output paths. The [patching guide](PATCHING_GAME.md) covers the general build workflow.

Append assets rather than replacing a stock sound or inserting entries before existing assets. Preserve all original sounds and payload references. Rebuild from the clean original each time; the duplicate-name guard deliberately prevents importing the same asset twice.

## Connect the imported music to the chart

Use the [registration guide's](CHART_REGISTRATION.md) end-of-`load_song_information()` injection and custom pack hook. In its example, replace the reused Tutorial audio with:

```gml
custom.chart_id = "custom_demo";
custom.audio_id = asset_get_index("music_chart_custom_demo");
if (custom.audio_id == -1) {
    show_error("Custom song audio was not imported", true);
}
```

Here `custom` means the complete song struct created with `getGenericSong(new_id)`; adapt the local variable name to the actual patch. Set its descriptive metadata, difficulty values, stable numeric ID and unlock fields as described in that guide. Register it before highscore/menu initialization, and add its ID to the custom pack. If using a VSD record instead, the reader resolves this same sound automatically from `chart_id`, but pack membership is still required.

Place charts at `Charts/custom_demo/OPENING.vsb`, `MIDDLE.vsb`, and `FINALE.vsb` for the three visible base difficulties. Add `ENCORE.vsb` only when the entry exposes Encore. The audio and all these charts must share a timeline. The VSB contains notes and BPM events, not an audio filename or payload.

For the initial integration, retain generic jacket and preview resources. To add a dedicated menu preview later, import a second sound named `preview_custom_demo` and assign `custom.preview_id = asset_get_index("preview_custom_demo")` for an injected record. The normal VSD path resolves it automatically. A preview is separate from gameplay music: successfully hearing it does not prove full-song/native playback works. The [song selector](../extraction/main/CodeEntries/gml_Object_o_songselect_main_Create_0.gml) passes the selected `preview_id` to `play_preview`.

## Why use the built-in group first?

The game already has custom group paths: external audio is not universally named `audiogroupN.dat`. The [resource loader Create event](../extraction/main/CodeEntries/gml_Object_obj_resource_loader_Create_0.gml) queues requested groups that are not loaded, and its [Step event](../extraction/main/CodeEntries/gml_Object_obj_resource_loader_Step_0.gml) calls `audio_group_load`. Adding a group would require its payload archive, correct group-local IDs, path metadata and a load/readiness lifecycle before playback. The existence of this generic loader does not automatically schedule a newly added group. Embedding the first custom song in the built-in group avoids those additional integration points, at the cost of a larger main archive and potential memory impact.

The shipped importer also supports external OGG resources. That is a possible later approach, but the native precise-audio backend's handling of such resources remains unverified. A dynamic `audio_create_stream` loader would require an explicit gameplay/backend patch and resource cleanup; it should not be treated as interchangeable with this resource-import recipe.

## Acceptance checks for the eventual patch

First reopen the saved archive with UndertaleModTool and confirm the new sound name, built-in group, payload index/reference, flags and unchanged original entries. Extract the new payload and compare its hash with the input OGG. Confirm the catalog lookup returns the new sound asset ID, rather than its payload index or `-1`.

In a copied game/profile, check menu selection, duration display, initial playback, pause/resume, retry, end of song and timing against notes. Test GameMaker audio and precise audio separately. A pass on one backend establishes only that backend. Check an original song as a regression check. Avoid stock score/rating submissions while authoring, as described in the registration guide.

The remaining decision after that test is concrete: if native playback accepts the appended sound, keep the ordinary pipeline; if it fails while GameMaker audio works, investigate the native lookup or introduce a custom-song backend override covering all timing/control branches. This investigation establishes the archive representation and GML integration points; it does not yet establish native compatibility, a compiled patch, or playable new audio.
