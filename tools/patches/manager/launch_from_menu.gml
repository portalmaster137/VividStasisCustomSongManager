var custom_actual_difficulty = confirm_menu.selected_difficulty;
    var custom_start_args = {};
    if (struct_get_fallback(selected_song, "is_custom_chart", false)) {
        custom_actual_difficulty = confirm_menu.difficulties[confirm_menu.selected_difficulty].id;
        if (custom_actual_difficulty == 3 && struct_exists(selected_song, "custom_apotheosis") && confirm_menu.custom_apotheosis_active) {
            custom_start_args.force_chart = "APOTHEOSIS";
            custom_start_args.custom_apotheosis = true;
        }
    }
    start_song(selected_song.song_id, custom_actual_difficulty, custom_start_args);