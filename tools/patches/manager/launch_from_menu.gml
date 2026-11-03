var custom_actual_difficulty = confirm_menu.selected_difficulty;
if (struct_get_fallback(selected_song, "is_custom_chart", false)) {
    custom_actual_difficulty = confirm_menu.difficulties[confirm_menu.selected_difficulty].id;
}
start_song(selected_song.song_id, custom_actual_difficulty);
