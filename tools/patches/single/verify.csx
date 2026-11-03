using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UndertaleModLib;
using UndertaleModLib.Decompiler;
EnsureDataLoaded();
var sound = Data.Sounds.ByName("music_chart_@@value@@");
if (sound == null || sound.GroupID != 0 || sound.AudioFile == null)
    throw new Exception("Missing or invalid imported sound");
if (!sound.AudioFile.Data.SequenceEqual(File.ReadAllBytes(@@ogg_cs@@)))
    throw new Exception("Stored audio differs from input payload");
@@cover_verify@@
var context = new GlobalDecompileContext(Data);
string Read(string name) {
    return new Underanalyzer.Decompiler.DecompileContext(context, Data.Code.ByName(name), Data.ToolInfo.DecompilerSettings).DecompileToString();
}
string[,] expected = {
    {"gml_GlobalScript_load_song_information", "music_chart_@@value@@"},
    {"gml_GlobalScript_create_song_packs", "Custom Charts"},
    {"gml_GlobalScript_start_song", "custom_audio_previous"},
    {"gml_GlobalScript_start_song", "arg2.clear_room = scene_songselect_old;"},
    {"gml_GlobalScript_start_song", "arg2.fail_room = scene_songselect_old;"},
    {"gml_GlobalScript_start_song", "arg2.quit_room = scene_songselect_old;"},
    {"gml_Object_cc_CleanUp_0", "custom_audio_restore_pending"}
};
for (int i = 0; i < expected.GetLength(0); i++) {
    string source = Read(expected[i, 0]);
    if (!source.Contains(expected[i, 1])) throw new Exception("Missing compiled patch: " + expected[i, 0]);
    File.WriteAllText(Path.Combine(@@build_cs@@, "verified_" + expected[i, 0] + ".gml"), source);
}
File.WriteAllText(Path.Combine(@@build_cs@@, "verified.txt"), "Saved archive reopened; imported audio and compiled code verified");
