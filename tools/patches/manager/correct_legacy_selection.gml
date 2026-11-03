var custom_diffs = struct_get_fallback(song, "custom_difficulties", [true, true, true, true]);
if (difficulty < 0 || difficulty >= array_length(custom_diffs) || !custom_diffs[difficulty]) {
    for (var cd = 0; cd < array_length(custom_diffs); cd++) {
        if (custom_diffs[cd]) { difficulty = cd; break; }
    }
}
