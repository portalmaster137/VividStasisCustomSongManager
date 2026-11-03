if (struct_get_fallback(song, "is_custom_chart", false)) {
    var custom_wanted_diff = selected_difficulty;
    difficulties = [];
    for (var ci = 0; ci < array_length(song.allowed_difficulties); ci++) {
        var custom_id = song.allowed_difficulties[ci];
        if (select_difficulties || custom_id == custom_wanted_diff) array_push(difficulties, custom_id);
    }
    if (array_length(difficulties) == 0) difficulties = [song.allowed_difficulties[0]];
    selected_difficulty = 0;
    for (var ci = 0; ci < array_length(difficulties); ci++) {
        if (difficulties[ci] == custom_wanted_diff) { selected_difficulty = ci; break; }
    }
} else 