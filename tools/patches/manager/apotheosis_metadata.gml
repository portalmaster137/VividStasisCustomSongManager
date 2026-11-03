if (struct_get_fallback(song, "is_custom_chart", false) && arg1 == 5 && song.custom_has_apotheosis) {
    global.songdifficulty = song.difficulty_display_6;
    global.songdifficultyconstant = song.difficulty_constant_6;
    global.note_designer = song.note_designer_6;
}
