if (struct_get_fallback(song, "is_custom_chart", false)) {
            var custom_wanted_diff = selected_difficulty;
            selected_difficulty = 0;
            for (var ci = 0; ci < array_length(difficulties); ci++) {
                if (difficulties[ci] == custom_wanted_diff) { selected_difficulty = ci; break; }
            }
        } else {
            selected_difficulty = clamp(selected_difficulty, 0, array_length(difficulties) - 1);
        }