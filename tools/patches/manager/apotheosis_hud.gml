if (global.df_load == "APOTHEOSIS") {
    draw_set_font(global.default_font);
    draw_set_alpha(mod_uialpha);
    draw_set_color(c_fuchsia);
    draw_text(274, 167, "APOTHEOSIS");
} else {
    draw_sprite(sp_newdifficultyindicator, diffsp, 274, 167);
    draw_sprite_ext(sp_newdifficultylevel, diffsp, 278, 171, 1, 1, 0, c_black, 0.3 * mod_uialpha);
    draw_sprite_ext(sp_newdifficultylevel, diffsp, 277, 170, 1, 1, 0, c_white, mod_uialpha);
}
