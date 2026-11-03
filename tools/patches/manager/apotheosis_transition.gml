
        case "APOTHEOSIS":
            diff_str = "APOTHEOSIS";
            diff_num = "Level " + song.custom_apotheosis.display;
            chart_designer = song.custom_apotheosis.designer;
            jacket_designer = struct_get_fallback(song, "jacket_artist", "Unknown");
            diff_col = 16711858;
            break;
