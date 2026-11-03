if (struct_get_fallback(song_list[arg2[0]], "is_custom_chart", false) && (arg2[1] < 0 || arg2[1] > 5 || !song_list[arg2[0]].custom_difficulties[arg2[1]])) return;
