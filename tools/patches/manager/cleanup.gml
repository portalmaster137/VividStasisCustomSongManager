
if (variable_global_exists("custom_audio_restore_pending") && global.custom_audio_restore_pending) {
    global.op_use_gamemaker_audio = global.custom_audio_previous;
    global.custom_audio_restore_pending = false;
}
