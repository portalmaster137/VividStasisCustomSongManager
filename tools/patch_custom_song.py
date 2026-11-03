#!/usr/bin/env python3
"""Build a Vividstasis custom-song overlay from clean game data, audio and 6K .osu."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from osu_to_vsb import convert
from vsb import parse_chart

SOURCE_SHA256 = '73e98f6c77f66675af9ce5cc52e4710457e4eefc82e91ef245b7d9ba12c15e45'
DEFAULT_CLI = '/home/porta/Code/UndertaleModTool/CLI/UndertaleModCli'


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def cs(value):
    return '@"' + str(value).replace('"', '""') + '"'


def gml(value):
    # chr() avoids GML string interpolation/escape ambiguities for user metadata.
    return ' + '.join(f'chr({ord(c)})' for c in value) or '""'


def metadata(text):
    result = {}
    active = False
    for line in text.lstrip('\ufeff').splitlines():
        if line.startswith('['):
            active = line.strip() == '[Metadata]'
        elif active and ':' in line:
            key, value = line.split(':', 1)
            result[key.strip()] = value.strip()
    return result


def make_script(audio, work, chart_id, title, artist, designer, bpm, level):
    register = f'''
    var custom_id = getNewSongId();
    var custom = getGenericSong(custom_id);
    custom.name = {gml(title)};
    custom.formatted_name = custom.name;
    custom.artist = {gml(artist)};
    custom.chart_id = "{chart_id}";
    custom.audio_id = asset_get_index("music_chart_{chart_id}");
    custom.preview_id = custom.audio_id;
    custom.bpm_display = "{bpm / 2:.12g}";
    custom.version = "6.2.2";
    custom.has_encore = false;
    custom.is_published = true;
    custom.invalid = false;
    custom.sort_artists = [custom.artist];
    custom.is_custom_chart = true;
    for (var slot = 1; slot <= 3; slot++) {{
        struct_set(custom, $"difficulty_constant_{{slot}}", {level});
        struct_set(custom, $"difficulty_display_{{slot}}", "{level:g}");
        struct_set(custom, $"note_designer_{{slot}}", {gml(designer)});
    }}
    global.song_list[custom_id] = custom;
    global.custom_chart_song_id = custom_id;
    global.custom_audio_restore_pending = false;
'''
    pack = '''if (arg0 == -1) {
        array_push(global.song_packs, {name: "Custom Charts",
            songs: [global.custom_chart_song_id], color1: 16777215,
            color2: 16724480, description: "Local authored chart."});
    }
    '''
    launch = '''
    if (variable_global_exists("custom_audio_restore_pending") && global.custom_audio_restore_pending) {
        global.op_use_gamemaker_audio = global.custom_audio_previous;
        global.custom_audio_restore_pending = false;
    }
    if (arg0 == global.custom_chart_song_id) {
        global.custom_audio_previous = global.op_use_gamemaker_audio;
        global.custom_audio_restore_pending = true;
        global.op_use_gamemaker_audio = true;
        arg2.actually_skip_results = true;
        arg2.clear_room = scene_songselect;
        arg2.fail_room = scene_songselect;
        arg2.quit_room = scene_songselect;
        arg2.gameplay_room = scene_gameplay;
    }
    '''
    cleanup = '''
if (variable_global_exists("custom_audio_restore_pending") && global.custom_audio_restore_pending) {
    global.op_use_gamemaker_audio = global.custom_audio_previous;
    global.custom_audio_restore_pending = false;
}
'''
    return f'''using System;
using System.IO;
using System.Linq;
using UndertaleModLib;
using UndertaleModLib.Models;
using UndertaleModLib.Decompiler;
EnsureDataLoaded();
var context = new GlobalDecompileContext(Data);
var imports = new UndertaleModLib.Compiler.CodeImportGroup(Data, null, Data.ToolInfo.DecompilerSettings) {{ MainThreadAction = MainThreadAction }};
string Read(string name) {{
    var code = Data.Code.ByName(name);
    if (code == null) throw new Exception("Missing code: " + name);
    return new Underanalyzer.Decompiler.DecompileContext(context, code, Data.ToolInfo.DecompilerSettings).DecompileToString();
}}
string ReplaceOnce(string source, string anchor, string replacement) {{
    int at = source.IndexOf(anchor, StringComparison.Ordinal);
    if (at < 0 || source.IndexOf(anchor, at + anchor.Length, StringComparison.Ordinal) >= 0)
        throw new Exception("Patch anchor missing or ambiguous: " + anchor);
    return source.Substring(0, at) + replacement + source.Substring(at + anchor.Length);
}}
void Queue(string name, string source) {{
    File.WriteAllText(Path.Combine({cs(work)}, name + ".gml"), source);
    imports.QueueReplace(Data.Code.ByName(name), source);
}}
string name = "music_chart_{chart_id}";
if (Data.Sounds.Any(s => s?.Name?.Content == name)) throw new Exception("Sound already registered");
int group = Data.GetBuiltinSoundGroupID();
if (group != 0) throw new Exception("Unexpected built-in group");
var payload = new UndertaleEmbeddedAudio {{ Data = File.ReadAllBytes({cs(audio)}) }};
int payloadId = Data.EmbeddedAudio.Count;
Data.EmbeddedAudio.Add(payload);
Data.Sounds.Add(new UndertaleSound {{
    Name = Data.Strings.MakeString(name), Type = Data.Strings.MakeString(".ogg"),
    File = Data.Strings.MakeString("{chart_id}.ogg"),
    Flags = UndertaleSound.AudioEntryFlags.IsCompressed | UndertaleSound.AudioEntryFlags.Regular,
    Volume = 1.0f, Pitch = 1.0f, Effects = 0, AudioID = payloadId,
    AudioFile = payload, AudioGroup = Data.AudioGroups[group], GroupID = group
}});
string loader = "gml_GlobalScript_load_song_information";
Queue(loader, ReplaceOnce(Read(loader), "file_text_close(artists_file);", "file_text_close(artists_file);" + {cs(register)}));
string packs = "gml_GlobalScript_create_song_packs";
Queue(packs, ReplaceOnce(Read(packs), "var all_songs = [];", {cs(pack)} + "var all_songs = [];"));
string start = "gml_GlobalScript_start_song";
Queue(start, ReplaceOnce(Read(start), "global.boundary_shatter = false;\\n    var song", {cs(launch)} + "global.boundary_shatter = false;\\n    var song"));
string clean = "gml_Object_cc_CleanUp_0";
Queue(clean, Read(clean) + {cs(cleanup)});
imports.Import();
File.WriteAllText(Path.Combine({cs(work)}, "patch-applied.txt"), "Compiled all custom song patches");
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio', type=Path)
    p.add_argument('osu', type=Path)
    p.add_argument('data', type=Path)
    p.add_argument('-o', '--output-dir', type=Path, required=True, help='New overlay directory (must not exist)')
    p.add_argument('--cli', type=Path, default=Path(DEFAULT_CLI))
    p.add_argument('--chart-id', default='custom_demo')
    p.add_argument('--title')
    p.add_argument('--artist')
    p.add_argument('--designer')
    p.add_argument('--level', type=float, default=4)
    g = p.add_mutually_exclusive_group()
    for option, value in [('bump-start', 'start'), ('bump-both', 'both'), ('reject-bump-holds', 'reject')]:
        g.add_argument('--' + option, dest='bumper_holds', action='store_const', const=value)
    p.set_defaults(bumper_holds='reject')
    a = p.parse_args()
    try:
        if not re.fullmatch('[a-z][a-z0-9_]{0,63}', a.chart_id):
            raise ValueError('--chart-id must start with a lowercase letter and contain only lowercase letters, digits and underscores (max 64)')
        if not 0 < a.level <= 100:
            raise ValueError('--level must be between 0 and 100')
        for path in (a.audio, a.osu, a.data, a.cli):
            if not path.is_file():
                raise ValueError(f'Missing input: {path}')
        if a.output_dir.exists():
            raise ValueError('Output directory already exists; choose a new directory')
        if not shutil.which('ffmpeg'):
            raise ValueError('ffmpeg is required to convert input audio to Ogg Vorbis')
        text = a.osu.read_text(encoding='utf-8-sig')
        chart, bpm, count = convert(text, a.bumper_holds)
        playable = [n for n in parse_chart(chart)['blocks'][0]['notes'] if n['type'] != 3]
        if not playable:
            raise ValueError('Chart contains no playable notes')
        print('Checking original data.win SHA-256...', flush=True)
        source_hash = sha256(a.data)
        if source_hash != SOURCE_SHA256:
            raise ValueError('Unsupported data.win: this patcher requires the exact unaltered build analyzed in this workspace')
        a.output_dir = a.output_dir.resolve()
        a.output_dir.mkdir(parents=True)
        build = a.output_dir / 'build'
        build.mkdir()
        ogg = build / 'audio.ogg'
        with (build / 'audio.log').open('w') as log:
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(a.audio.resolve()), '-map', '0:a:0', '-vn', '-c:a', 'libvorbis', '-q:a', '6', str(ogg)], stdout=log, stderr=subprocess.STDOUT, check=True)
        meta = metadata(text)
        script = build / 'patch.csx'
        script.write_text(make_script(ogg, build, a.chart_id, a.title or meta.get('Title', a.osu.stem), a.artist or meta.get('Artist', 'Unknown'), a.designer or meta.get('Creator', 'Unknown'), bpm, a.level))
        staged = a.output_dir / 'data.pending.win'
        print('Importing audio and compiling registration patches (see build/patch.log)...', flush=True)
        with (build / 'patch.log').open('w') as log:
            subprocess.run([str(a.cli.resolve()), 'load', str(a.data.resolve()), '-s', str(script), '-o', str(staged)], stdout=log, stderr=subprocess.STDOUT, check=True)
        if not (build / 'patch-applied.txt').exists() or not staged.is_file():
            raise ValueError('CLI did not complete patching; inspect build/patch.log')
        verify = build / 'verify.csx'
        verify.write_text(f'''using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UndertaleModLib;
using UndertaleModLib.Decompiler;
EnsureDataLoaded();
var sound = Data.Sounds.ByName("music_chart_{a.chart_id}");
if (sound == null || sound.GroupID != 0 || sound.AudioFile == null)
    throw new Exception("Missing or invalid imported sound");
if (!sound.AudioFile.Data.SequenceEqual(File.ReadAllBytes({cs(ogg)})))
    throw new Exception("Stored audio differs from input payload");
var context = new GlobalDecompileContext(Data);
string Read(string name) {{
    return new Underanalyzer.Decompiler.DecompileContext(context, Data.Code.ByName(name), Data.ToolInfo.DecompilerSettings).DecompileToString();
}}
string[,] expected = {{
    {{"gml_GlobalScript_load_song_information", "music_chart_{a.chart_id}"}},
    {{"gml_GlobalScript_create_song_packs", "Custom Charts"}},
    {{"gml_GlobalScript_start_song", "custom_audio_previous"}},
    {{"gml_Object_cc_CleanUp_0", "custom_audio_restore_pending"}}
}};
for (int i = 0; i < expected.GetLength(0); i++) {{
    string source = Read(expected[i, 0]);
    if (!source.Contains(expected[i, 1])) throw new Exception("Missing compiled patch: " + expected[i, 0]);
    File.WriteAllText(Path.Combine({cs(build)}, "verified_" + expected[i, 0] + ".gml"), source);
}}
File.WriteAllText(Path.Combine({cs(build)}, "verified.txt"), "Saved archive reopened; imported audio and compiled code verified");
''')
        print('Reopening the saved archive to verify audio and compiled code...', flush=True)
        with (build / 'verify.log').open('w') as log:
            subprocess.run([str(a.cli.resolve()), 'load', str(staged), '-s', str(verify)], stdout=log, stderr=subprocess.STDOUT, check=True)
        if not (build / 'verified.txt').is_file():
            raise ValueError('Saved archive verification failed; inspect build/verify.log')
        if sha256(a.data) != source_hash:
            raise ValueError('Source data.win changed during build')
        chartdir = a.output_dir / 'Charts' / a.chart_id
        chartdir.mkdir(parents=True)
        for difficulty in ('OPENING', 'MIDDLE', 'FINALE'):
            (chartdir / (difficulty + '.vsb')).write_bytes(chart)
        staged.rename(a.output_dir / 'data.win')
        report = dict(source_sha256=source_hash, output_sha256=sha256(a.output_dir / 'data.win'), chart_id=a.chart_id, records=count, source_bpm=bpm, bumper_holds=a.bumper_holds, audio_backend='GameMaker', results='skipped for custom song', runtime_tested=False)
        (a.output_dir / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
        print(f'Built {a.output_dir}. Copy data.win and Charts/ into a COPY of the complete game; open Custom Charts. All three base difficulties contain the same input chart.')
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        p.exit(1, f'Build failed: {exc}\nAny partial output is incomplete; inspect its build logs and use a new output directory.\n')


if __name__ == '__main__':
    main()
