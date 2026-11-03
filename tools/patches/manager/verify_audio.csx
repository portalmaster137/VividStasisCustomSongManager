{
var sound = Data.Sounds.ByName("music_chart_@@cid@@");
if (sound == null || sound.GroupID != 0 || sound.AudioFile == null || !sound.AudioFile.Data.SequenceEqual(File.ReadAllBytes(@@audio@@))) throw new Exception("Audio verification failed: @@cid@@");
if (!Read("gml_GlobalScript_load_song_information").Contains("music_chart_@@cid@@")) throw new Exception("Missing song registration: @@cid@@");
}
