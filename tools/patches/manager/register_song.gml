
    var @@v@@ = getGenericSong(@@song_id@@);
    @@v@@.name = @@title_gml@@;
    @@v@@.formatted_name = @@v@@.name;
    @@v@@.artist = @@artist_gml@@;
    @@v@@.jacket_artist = @@jacket_artist_gml@@;
    @@v@@.chart_id = "@@chart_id@@";
    @@v@@.audio_id = asset_get_index("music_chart_@@chart_id@@");
    @@v@@.preview_id = @@v@@.audio_id;
    @@jacket_assignment@@
    @@v@@.bpm_display = "@@initial_bpm@@";
    @@v@@.version = "6.2.2";
    @@v@@.has_encore = @@has_encore@@;
    @@v@@.is_published = true;
    @@v@@.invalid = false;
    @@v@@.sort_artists = [@@v@@.artist];
    @@v@@.is_custom_chart = true;
    @@v@@.custom_has_apotheosis = false;
    @@v@@.custom_difficulties = [@@available_difficulties@@];
    @@v@@.allowed_difficulties = [@@allowed_difficulties@@];
