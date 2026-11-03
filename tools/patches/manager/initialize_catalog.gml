
global.custom_chart_song_ids = [];
    for (var fill = array_length(global.song_list); fill <= @@highest_id@@; fill++) {
        global.song_list[fill] = getGenericInvalidSong(fill);
    }
    global.custom_audio_restore_pending = false;
