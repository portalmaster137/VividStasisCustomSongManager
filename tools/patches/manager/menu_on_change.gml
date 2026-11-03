diff_opt.on_change = function(arg0)
            {
                if (struct_get_fallback(song, "is_custom_chart", false)) arg0 = difficulties[arg0].id;