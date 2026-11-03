if (show_difficulties && difficulty_panel_alpha > 0 && struct_get_fallback(song, "is_custom_chart", false)) {
    if (difficulty_panel_surf == undefined || !surface_exists(difficulty_panel_surf)) {
        difficulty_panel_surf = surface_create(208, 75);
    }
    surface_target(difficulty_panel_surf);
    draw_clear_alpha(c_black, 1);
    draw_set_alpha(1);
    draw_set_font(global.default_font);
    draw_set_halign(fa_left);
    var custom_rows = array_length(difficulties);
    var custom_spacing = min(18, 70 / max(1, custom_rows));
    for (var ci = 0; ci < custom_rows; ci++) {
        var choice = difficulties[ci];
        var custom_y = 2 + ci * custom_spacing;
        if (ci == selected_difficulty) {
            draw_set_color(make_color_rgb(70, 25, 80));
            draw_rectangle(1, custom_y, 206, custom_y + custom_spacing - 1, false);
        }
        draw_set_color(choice.id == 5 ? c_fuchsia : c_white);
        draw_text(4, custom_y, choice.name);
        draw_set_halign(fa_right);
        draw_text(203, custom_y, "Level " + string(choice.value));
        draw_set_halign(fa_left);
    }
    surface_untarget();
    draw_set_alpha(difficulty_panel_alpha);
    draw_surface(difficulty_panel_surf, round(difficulty_panel_x), round(difficulty_panel_y));
} else 