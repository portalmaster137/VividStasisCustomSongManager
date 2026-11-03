if (diff == 5 && struct_get_fallback(global.song_list[song_id], "is_custom_chart", false)) {
    draw_set_font(global.default_font);
    draw_set_color(c_fuchsia);
    draw_set_halign(fa_center);
    draw_text(11, 1, "A");
    draw_text(11, 12, diff_value);
    draw_set_halign(fa_left);
} else draw_sprite(diff_sprite, diff_index, 2, 2);