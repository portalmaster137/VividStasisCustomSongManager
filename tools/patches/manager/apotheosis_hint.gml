
if (struct_exists(song, "custom_apotheosis") && difficulties[selected_difficulty].id == 3) {
    draw_set_default();
    draw_set_alpha(image_alpha);
    draw_set_font(global.default_font);
    draw_set_halign(fa_left);
    draw_text_outlined(4, 168, custom_apotheosis_active ? "TAB: switch to ENCORE" : "TAB: switch to APOTHEOSIS", c_white, c_black);
}
