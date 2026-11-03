if (struct_get_fallback(selected_song, "is_custom_chart", false)) {
    var custom_footer_id = use_focus_diff ? focus_difficulty : songs[cursor_pos][1];
    var custom_footer_names = ["OPENING", "MIDDLE", "FINALE", "ENCORE", "PRELUDE", "APOTHEOSIS"];
    draw_set_font(global.default_font);
    draw_set_color(custom_footer_id == 5 ? c_fuchsia : c_white);
    draw_set_halign(fa_right);
    draw_text(205, round(top_y) + 16, custom_footer_names[custom_footer_id]);
    draw_set_halign(fa_left);
} else {
