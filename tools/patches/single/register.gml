
    var custom_id = getNewSongId();
    var custom = getGenericSong(custom_id);
    custom.name = @@title_gml@@;
    custom.formatted_name = custom.name;
    custom.artist = @@artist_gml@@;
    custom.chart_id = "@@chart_id@@";
    custom.audio_id = asset_get_index("music_chart_@@chart_id@@");
    custom.preview_id = custom.audio_id;
    @@jacket_assignment@@
    custom.bpm_display = "@@initial_bpm@@";
    custom.version = "6.2.2";
    custom.has_encore = false;
    custom.is_published = true;
    custom.invalid = false;
    custom.sort_artists = [custom.artist];
    custom.is_custom_chart = true;
    for (var slot = 1; slot <= 3; slot++) {
        struct_set(custom, $"difficulty_constant_{slot}", @@level@@);
        struct_set(custom, $"difficulty_display_{slot}", "@@level_display@@");
        struct_set(custom, $"note_designer_{slot}", @@designer_gml@@);
    }
    global.song_list[custom_id] = custom;
    global.custom_chart_song_id = custom_id;
    global.custom_audio_restore_pending = false;
