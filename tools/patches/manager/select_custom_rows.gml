if (struct_get_fallback(song_list[song], "is_custom_chart", false)) {
    // The four stock filter buttons keep their original meaning. Custom-only
    // APOTHEOSIS rows are always visible so standalone packages remain reachable.
    for (var custom_ci = 0; custom_ci < array_length(song_list[song].allowed_difficulties); custom_ci++) {
        var custom_d = song_list[song].allowed_difficulties[custom_ci];
        if (custom_d != 5 && (custom_d < low_diff || custom_d > high_diff)) continue;
        var custom_artists = song_get_info(song_list[song], "sort_artists", custom_d);
        if (global.sort_type == 4) {
            for (var ca = 0; ca < array_length(custom_artists); ca++) {
                add_song_after_range_check(low_range, high_range, [song, custom_d, array_length(songs), custom_artists[ca]]);
            }
        } else {
            add_song_after_range_check(low_range, high_range, [song, custom_d, array_length(songs)]);
        }
    }
} else 