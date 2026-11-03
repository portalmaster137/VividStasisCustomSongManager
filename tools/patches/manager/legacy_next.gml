if (struct_get_fallback(song, "is_custom_chart", false)) {
    var custom_pos = 0;
    for (var ci = 0; ci < array_length(song.allowed_difficulties); ci++) {
        if (song.allowed_difficulties[ci] == difficulty) custom_pos = ci;
    }
    difficulty = song.allowed_difficulties[(custom_pos + 1) % array_length(song.allowed_difficulties)];
} else {
    if (difficulty == maxd) difficulty = 0; else difficulty++;
}
