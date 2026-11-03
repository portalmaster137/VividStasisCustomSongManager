if (variable_global_exists("custom_audio_restore_pending") && global.custom_audio_restore_pending) {
    global.op_use_gamemaker_audio = global.custom_audio_previous;
    global.custom_audio_restore_pending = false;
}
var custom_start_song = global.song_list[arg0];
if (struct_get_fallback(custom_start_song, "is_custom_chart", false)) {
    if (arg1 < 0 || arg1 > 5 || !custom_start_song.custom_difficulties[arg1]) {
        arg1 = custom_start_song.allowed_difficulties[0];
    }
    if (arg1 == 5) arg2.force_chart = "APOTHEOSIS";
    global.custom_audio_previous = global.op_use_gamemaker_audio;
    global.custom_audio_restore_pending = true;
    global.op_use_gamemaker_audio = true;
    arg2.actually_skip_results = true;
    arg2.clear_room = scene_songselect_old;
    arg2.fail_room = scene_songselect_old;
    arg2.quit_room = scene_songselect_old;
    arg2.gameplay_room = scene_gameplay;
}
