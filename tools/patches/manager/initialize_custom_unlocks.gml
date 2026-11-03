if (struct_get_fallback(global.song_list[i], "is_custom_chart", false)) {
    for (var custom_d = 0; custom_d < 6; custom_d++) su[custom_d] = global.song_list[i].custom_difficulties[custom_d];
}
