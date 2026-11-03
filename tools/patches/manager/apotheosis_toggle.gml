
if (struct_exists(song, "custom_apotheosis")) {
    var custom_encore_selected = difficulties[selected_difficulty].id == 3;
    if (!custom_encore_selected) custom_apotheosis_active = false;
    if (custom_encore_selected && keyboard_check_pressed(vk_tab)) {
        custom_apotheosis_active = !custom_apotheosis_active;
        play_se(sfx_songsel_diff);
    }
    for (var ca = 0; ca < array_length(difficulties); ca++) {
        if (difficulties[ca].id == 3) {
            difficulties[ca].name = custom_apotheosis_active ? "APOTHEOSIS" : "ENCORE";
            difficulties[ca].value = custom_apotheosis_active ? song.custom_apotheosis.display : song.difficulty_display_4;
            difficulties[ca].charter = custom_apotheosis_active ? song.custom_apotheosis.designer : song.note_designer_4;
            diff_opt.choices[ca] = difficulties[ca].name;
        }
    }
    diff_names[3] = custom_apotheosis_active ? "APOTHEOSIS" : "ENCORE";
}
