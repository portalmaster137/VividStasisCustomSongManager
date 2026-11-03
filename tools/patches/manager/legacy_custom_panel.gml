if (can_select_difficulty && struct_get_fallback(song, "is_custom_chart", false)) {
    var custom_count = array_length(song.allowed_difficulties);
    for (var ci = 0; ci < custom_count; ci++) {
        var custom_d = song.allowed_difficulties[ci];
        var custom_x = (320 / (custom_count + 1)) * (ci + 1);
        draw_set_halign(fa_center);
        draw_set_font(global.default_font);
        draw_set_color(custom_d == difficulty ? c_fuchsia : c_white);
        draw_text(custom_x, 141, difficulties[custom_d]);
        draw_text(custom_x, 153, struct_get(song, $"difficulty_display_{custom_d + 1}"));
    }
    draw_set_halign(fa_left);
} else 