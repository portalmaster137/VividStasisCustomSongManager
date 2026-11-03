
    if (variable_global_exists("custom_audio_restore_pending") && global.custom_audio_restore_pending) {
        global.op_use_gamemaker_audio = global.custom_audio_previous;
        global.custom_audio_restore_pending = false;
    }
    var custom_start_song = global.song_list[arg0];
    if (struct_get_fallback(custom_start_song, "is_custom_chart", false)) {
        if (arg1 < 0 || arg1 > 3 || !custom_start_song.custom_difficulties[arg1]) {
            for (var cd = 0; cd < 4; cd++) {
                if (custom_start_song.custom_difficulties[cd]) { arg1 = cd; break; }
            }
        }
        if (arg1 == 3 && struct_exists(custom_start_song, "custom_apotheosis") && struct_get_fallback(arg2, "custom_apotheosis", false)) {
            arg2.force_chart = "APOTHEOSIS";
        }
        global.custom_audio_previous = global.op_use_gamemaker_audio;
        global.custom_audio_restore_pending = true;
        global.op_use_gamemaker_audio = true;
        arg2.actually_skip_results = true;
        arg2.clear_room = scene_songselect_old;
        arg2.fail_room = scene_songselect_old;
        arg2.quit_room = scene_songselect_old;
        arg2.gameplay_room = scene_gameplay;
    }
    