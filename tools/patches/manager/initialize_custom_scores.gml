// Preserve the stock load_highscores bytecode, including its nested factory.
// Recompiling {score: ...} incorrectly targets the legacy builtin.score in
// this toolchain. Clone an actual stock record and address members by string.
for (var custom_score_i = 0; custom_score_i < array_length(global.song_list); custom_score_i++) {
    if (!struct_get_fallback(global.song_list[custom_score_i], "is_custom_chart", false)) continue;
    var custom_score_record = variable_clone(global.highscores.normal[custom_score_i][0]);
    variable_struct_set(custom_score_record, "score", 0);
    variable_struct_set(custom_score_record, "game_score", 0);
    variable_struct_set(custom_score_record, "game_perc", 0);
    variable_struct_set(custom_score_record, "max_combo", 0);
    variable_struct_set(custom_score_record, "lamp", 0);
    global.highscores.normal[custom_score_i][5] = custom_score_record;
    global.highscores_at_load.normal[custom_score_i][5] = variable_clone(custom_score_record);
}
