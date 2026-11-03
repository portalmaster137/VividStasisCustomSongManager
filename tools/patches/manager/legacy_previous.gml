if (struct_get_fallback(song, "is_custom_chart", false)) {
    var custom_pos = 0;
    var custom_count = array_length(song.allowed_difficulties);
    for (var ci = 0; ci < custom_count; ci++) {
        if (song.allowed_difficulties[ci] == difficulty) custom_pos = ci;
    }
    difficulty = song.allowed_difficulties[(custom_pos + custom_count - 1) % custom_count];
} else {
    if (difficulty == 0) difficulty = maxd; else difficulty--;
}
