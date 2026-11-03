string name = "music_chart_@@chart_id@@";
if (Data.Sounds.Any(s => s?.Name?.Content == name)) throw new Exception("Sound already registered");
int group = Data.GetBuiltinSoundGroupID();
if (group != 0) throw new Exception("Unexpected built-in group");
var payload = new UndertaleEmbeddedAudio { Data = File.ReadAllBytes(@@audio_cs@@) };
int payloadId = Data.EmbeddedAudio.Count;
Data.EmbeddedAudio.Add(payload);
Data.Sounds.Add(new UndertaleSound {
    Name = Data.Strings.MakeString(name), Type = Data.Strings.MakeString(".ogg"),
    File = Data.Strings.MakeString("@@chart_id@@.ogg"),
    Flags = UndertaleSound.AudioEntryFlags.IsCompressed | UndertaleSound.AudioEntryFlags.Regular,
    Volume = 1.0f, Pitch = 1.0f, Effects = 0, AudioID = payloadId,
    AudioFile = payload, AudioGroup = Data.AudioGroups[group], GroupID = group
});
@@cover_import@@
