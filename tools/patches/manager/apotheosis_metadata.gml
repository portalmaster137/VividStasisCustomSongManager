
    if (struct_get_fallback(song, "is_custom_chart", false) && arg1 == 3 && struct_exists(song, "custom_apotheosis") && struct_get_fallback(arg2, "custom_apotheosis", false)) {
        global.songdifficulty = song.custom_apotheosis.display;
        global.songdifficultyconstant = song.custom_apotheosis.level;
        global.note_designer = song.custom_apotheosis.designer;
    }
    