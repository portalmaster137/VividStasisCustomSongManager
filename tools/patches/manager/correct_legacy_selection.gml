var custom_diffs = struct_get_fallback(song, "custom_difficulties", [true, true, true, true]);
if (!custom_diffs[difficulty]) {
    for (var cd = 0; cd < 4; cd++) { if (custom_diffs[cd]) { difficulty = cd; break; } }
}
