var expectedAudio = new string[] { @@expected_audio@@ };
var expectedCovers = new string[] { @@expected_covers@@ };
if (!Data.Sounds.Where(s => s?.Name?.Content?.StartsWith("music_chart_custom_manager_", StringComparison.Ordinal) == true).Select(s => s.Name.Content).OrderBy(s => s).SequenceEqual(expectedAudio.OrderBy(s => s))) throw new Exception("Saved audio selection differs");
if (!Data.Sprites.Where(s => s?.Name?.Content?.StartsWith("song_custom_manager_", StringComparison.Ordinal) == true).Select(s => s.Name.Content).OrderBy(s => s).SequenceEqual(expectedCovers.OrderBy(s => s))) throw new Exception("Saved jacket selection differs");
