# Custom-song patcher build evidence

The patcher was run against the exact unaltered main archive using a generated five-second 440 Hz WAV and a synthetic 6K chart containing a left bumper, a normal hold and a right bumper. FFmpeg converted the input to Ogg Vorbis. UndertaleModTool compiled all four modified code entries, saved a new archive, reopened it, compared embedded audio with the transcoded input and decompiled each modified entry to verify its patch marker.

The original archive hash was checked before and after. All three emitted VSB files parsed and re-encoded identically. Seven existing VSB unit checks also passed. The manifest and chart-validation report are retained here; the full synthetic overlay and generated code/logs were written to `/tmp/vivid-patcher-verified` during development and may be removed by the host.

No game process was launched. Playback, selector behavior, backend restoration and clear/fail/quit routing still require in-game checks. The generated overlay is a development fixture, not a user's song.
