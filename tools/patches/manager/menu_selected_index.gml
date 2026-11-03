if (struct_get_fallback(song, "is_custom_chart", false)) {
    selected_difficulty = 0;
    for (var ci = 0; ci < array_length(difficulties); ci++) {
        if (difficulties[ci].id == songselect.focus_difficulty) { selected_difficulty = ci; break; }
    }
} else selected_difficulty = songselect.focus_difficulty;