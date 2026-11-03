
    if (variable_global_exists("custom_audio_restore_pending") && global.custom_audio_restore_pending) {
        global.op_use_gamemaker_audio = global.custom_audio_previous;
        global.custom_audio_restore_pending = false;
    }
    if (arg0 == global.custom_chart_song_id) {
        global.custom_audio_previous = global.op_use_gamemaker_audio;
        global.custom_audio_restore_pending = true;
        global.op_use_gamemaker_audio = true;
        // Match start_song's stock freeplay destination. scene_songselect is
        // a different selector with an incompatible surface-effect path.
        arg2.actually_skip_results = true;
        arg2.clear_room = scene_songselect_old;
        arg2.fail_room = scene_songselect_old;
        arg2.quit_room = scene_songselect_old;
        arg2.gameplay_room = scene_gameplay;
    }
    