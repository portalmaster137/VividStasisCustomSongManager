"""Custom-song manager: stable IDs, verified multi-song builds, recoverable installs.

The game installation is never edited until a clean-source archive has been
compiled, reopened, and verified. A write-ahead journal preserves previous bytes.
"""
from __future__ import annotations
import contextlib
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
# Existing converter/package helpers are also executable scripts using local imports.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from custom_songs import Package, DIFFICULTIES
    from osu_to_vsb import convert
    from vsb import parse_chart
    from patch_custom_song import SOURCE_SHA256, cs, gml, make_script, sha256
except ModuleNotFoundError:
    from tools.custom_songs import Package, DIFFICULTIES
    from tools.osu_to_vsb import convert
    from tools.vsb import parse_chart
    from tools.patch_custom_song import SOURCE_SHA256, cs, gml, make_script, sha256

class Cancelled(RuntimeError):
    pass


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.pending-' + uuid.uuid4().hex)
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=True)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def make_multi_script(songs, work, highest_id):
    """One audio/cover import batch and one code compilation for the entire set."""
    work = Path(work)
    first = songs[0]
    for song in songs:
        if 'apotheosis' in song['charts'] and 'encore' not in song['charts']:
            raise ValueError('APOTHEOSIS requires an ENCORE chart in the same song')
    # Reuse the tested import primitives, enclosing each import in its own scope.
    templates = [make_script(s['audio'], work, s['chart_id'], s['title'], s['artist'], '', s['bpm'], 1, s.get('cover')) for s in songs]
    preamble = templates[0].split('string name = "music_chart_', 1)[0]
    audio_imports = []
    for template in templates:
        segment = 'string name = "music_chart_' + template.split('string name = "music_chart_', 1)[1].split('string loader = ', 1)[0]
        audio_imports.append('{\n' + segment + '\n}')
    register = f'''\nglobal.custom_chart_song_ids = [];
    for (var fill = array_length(global.song_list); fill <= {highest_id}; fill++) {{
        global.song_list[fill] = getGenericInvalidSong(fill);
    }}
    global.custom_audio_restore_pending = false;
'''
    for i, song in enumerate(songs):
        v = f'custom_song_{i}'
        available = ['true' if d in song['charts'] else 'false' for d in DIFFICULTIES]
        register += f'''\n    var {v} = getGenericSong({song['song_id']});
    {v}.name = {gml(song['title'])};
    {v}.formatted_name = {v}.name;
    {v}.artist = {gml(song['artist'])};
    {v}.jacket_artist = {gml(song.get('jacket_artist', 'Unknown'))};
    {v}.chart_id = "{song['chart_id']}";
    {v}.audio_id = asset_get_index("music_chart_{song['chart_id']}");
    {v}.preview_id = {v}.audio_id;
    {f'{v}.jacket = asset_get_index("song_{song["chart_id"]}");' if song.get('cover') else ''}
    {v}.bpm_display = "{song['bpm'] / 2:.12g}";
    {v}.version = "6.2.2";
    {v}.has_encore = {'true' if 'encore' in song['charts'] else 'false'};
    {v}.is_published = true;
    {v}.invalid = false;
    {v}.sort_artists = [{v}.artist];
    {v}.is_custom_chart = true;
    {v}.custom_difficulties = [{', '.join(available)}];
    {v}.allowed_difficulties = [{', '.join(str(j) for j,d in enumerate(DIFFICULTIES) if d in song["charts"])}];
'''
        for j, diff in enumerate(DIFFICULTIES, 1):
            chart = song['charts'].get(diff)
            level = float(chart['level']) if chart else 0
            display = str(math.floor(level)) + ('+' if level % 1 >= .5 else '') if chart else '--'
            designer = chart.get('designer', 'Unknown') if chart else ''
            register += f'    {v}.difficulty_constant_{j} = {level:.12g};\n    {v}.difficulty_display_{j} = {gml(display)};\n    {v}.note_designer_{j} = {gml(designer)};\n'
        if 'apotheosis' in song['charts']:
            alternate = song['charts']['apotheosis']
            level = float(alternate['level'])
            display = str(math.floor(level)) + ('+' if level % 1 >= .5 else '')
            register += f'    {v}.custom_apotheosis = {{level: {level:.12g}, display: {gml(display)}, designer: {gml(alternate.get("designer", "Unknown"))}}};\n'
        register += f'    global.song_list[{song["song_id"]}] = {v};\n    array_push(global.custom_chart_song_ids, {song["song_id"]});\n'
    pack = '''if (arg0 == -1) {
        array_push(global.song_packs, {name: "Custom Charts",
            songs: global.custom_chart_song_ids, color1: 16777215,
            color2: 16724480, description: "Local custom song library."});
    }
    '''
    launch = '''
    if (variable_global_exists("custom_audio_restore_pending") && global.custom_audio_restore_pending) {
        global.op_use_gamemaker_audio = global.custom_audio_previous;
        global.custom_audio_restore_pending = false;
    }
    var custom_start_song = global.song_list[arg0];
    if (struct_get_fallback(custom_start_song, "is_custom_chart", false)) {
        if (arg1 < 0 || arg1 > 3 || !custom_start_song.custom_difficulties[arg1]) {
            for (var cd = 0; cd < 4; cd++) {
                if (custom_start_song.custom_difficulties[cd]) { arg1 = cd; break; }
            }
        }
        if (arg1 == 3 && struct_exists(custom_start_song, "custom_apotheosis") && struct_get_fallback(arg2, "custom_apotheosis", false)) {
            arg2.force_chart = "APOTHEOSIS";
        }
        global.custom_audio_previous = global.op_use_gamemaker_audio;
        global.custom_audio_restore_pending = true;
        global.op_use_gamemaker_audio = true;
        arg2.actually_skip_results = true;
        arg2.clear_room = scene_songselect_old;
        arg2.fail_room = scene_songselect_old;
        arg2.quit_room = scene_songselect_old;
        arg2.gameplay_room = scene_gameplay;
    }
    '''
    cleanup = '''
if (variable_global_exists("custom_audio_restore_pending") && global.custom_audio_restore_pending) {
    global.op_use_gamemaker_audio = global.custom_audio_previous;
    global.custom_audio_restore_pending = false;
}
'''
    # Filtering inside the shared insertion helper also covers Encore fallback.
    filter_code = '''if (struct_get_fallback(song_list[arg2[0]], "is_custom_chart", false) && !song_list[arg2[0]].custom_difficulties[arg2[1]]) return;
            '''
    correction = '''var custom_diffs = struct_get_fallback(song, "custom_difficulties", [true, true, true, true]);
if (!custom_diffs[difficulty]) {
    for (var cd = 0; cd < 4; cd++) { if (custom_diffs[cd]) { difficulty = cd; break; } }
}
'''
    next_old = '''if (difficulty == maxd)
                    {
                        difficulty = 0;
                    }
                    else
                    {
                        difficulty++;
                    }'''
    previous_old = '''if (difficulty == 0)
                    {
                        difficulty = maxd;
                    }
                    else
                    {
                        difficulty--;
                    }'''
    next_new = '''repeat (4) {
                        difficulty = (difficulty + 1) % (maxd + 1);
                        if (custom_diffs[difficulty]) break;
                    }'''
    previous_new = '''repeat (4) {
                        difficulty = (difficulty + maxd) % (maxd + 1);
                        if (custom_diffs[difficulty]) break;
                    }'''
    apotheosis_metadata = '''
    if (struct_get_fallback(song, "is_custom_chart", false) && arg1 == 3 && struct_exists(song, "custom_apotheosis") && struct_get_fallback(arg2, "custom_apotheosis", false)) {
        global.songdifficulty = song.custom_apotheosis.display;
        global.songdifficultyconstant = song.custom_apotheosis.level;
        global.note_designer = song.custom_apotheosis.designer;
    }
    '''
    apotheosis_toggle = '''
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
'''
    apotheosis_hint = '''
if (struct_exists(song, "custom_apotheosis") && difficulties[selected_difficulty].id == 3) {
    draw_set_default();
    draw_set_alpha(image_alpha);
    draw_set_font(global.default_font);
    draw_set_halign(fa_left);
    draw_text_outlined(4, 168, custom_apotheosis_active ? "TAB: switch to ENCORE" : "TAB: switch to APOTHEOSIS", c_white, c_black);
}
'''
    apotheosis_transition = '''
        case "APOTHEOSIS":
            diff_str = "APOTHEOSIS";
            diff_num = "Level " + song.custom_apotheosis.display;
            chart_designer = song.custom_apotheosis.designer;
            jacket_designer = struct_get_fallback(song, "jacket_artist", "Unknown");
            diff_col = 16711858;
            break;
'''
    finish = f'''
string loader = "gml_GlobalScript_load_song_information";
Queue(loader, ReplaceOnce(Read(loader), "file_text_close(artists_file);", "file_text_close(artists_file);" + {cs(register)}));
string packs = "gml_GlobalScript_create_song_packs";
Queue(packs, ReplaceOnce(Read(packs), "var all_songs = [];", {cs(pack)} + "var all_songs = [];"));
string start = "gml_GlobalScript_start_song";
string startSource = ReplaceOnce(Read(start), "global.boundary_shatter = false;\\n    var song", {cs(launch)} + "global.boundary_shatter = false;\\n    var song");
startSource = ReplaceOnce(startSource, "if (force_chart != undefined)", {cs(apotheosis_metadata)} + "if (force_chart != undefined)");
Queue(start, startSource);
string transition = "gml_Object_o_transitionsong_Alarm_0";
Queue(transition, ReplaceOnce(Read(transition), {cs('case "PRELUDE":')}, {cs(apotheosis_transition)} + {cs('case "PRELUDE":')}));
string clean = "gml_Object_cc_CleanUp_0";
Queue(clean, Read(clean) + {cs(cleanup)});
string select = "gml_GlobalScript_refresh_song_objects";
Queue(select, ReplaceOnce(Read(select), "var chk = floor", {cs(filter_code)} + "var chk = floor"));
string confirm = "gml_Object_o_songselect_confirm_Step_0";
string confirmation = ReplaceOnce(Read(confirm), "if (active)", {cs(correction)} + "if (active)");
confirmation = ReplaceOnce(confirmation, {cs(next_old)}, {cs(next_new)});
confirmation = ReplaceOnce(confirmation, {cs(previous_old)}, {cs(previous_new)});
Queue(confirm, confirmation);
string draw = "gml_Object_o_songselect_confirm_Draw_64";
Queue(draw, ReplaceOnce(Read(draw), "var unlocked = global.unlocked_songs[song.song_id][i];", "if (struct_get_fallback(song, \\"is_custom_chart\\", false) && !song.custom_difficulties[i]) continue;\\n        var unlocked = global.unlocked_songs[song.song_id][i];"));
string modernCreate = "gml_Object_o_songselect_newconfirm_Create_0";
string modernCreateSource = ReplaceOnce(Read(modernCreate), "selected_difficulty = clamp(selected_difficulty, 0, array_length(difficulties) - 1);", {cs('if (struct_get_fallback(song, "is_custom_chart", false)) {\n            var custom_wanted_diff = selected_difficulty;\n            selected_difficulty = 0;\n            for (var ci = 0; ci < array_length(difficulties); ci++) {\n                if (difficulties[ci] == custom_wanted_diff) { selected_difficulty = ci; break; }\n            }\n        } else {\n            selected_difficulty = clamp(selected_difficulty, 0, array_length(difficulties) - 1);\n        }')});
Queue(modernCreate, modernCreateSource + {cs(chr(10)+'custom_apotheosis_active = false;'+chr(10))});
string modernStep = "gml_Object_o_songselect_newconfirm_Step_0";
string modernStepSource = ReplaceOnce(Read(modernStep), {cs('illustrator = song_get_info(song, "jacket_artist", selected_difficulty);')}, {cs('illustrator = song_get_info(song, "jacket_artist", struct_get_fallback(song, "is_custom_chart", false) ? difficulties[selected_difficulty].id : selected_difficulty);')});
modernStepSource = ReplaceOnce(modernStepSource, "global.unlocked_songs[song.song_id][selected_difficulty]", {cs('global.unlocked_songs[song.song_id][struct_get_fallback(song, "is_custom_chart", false) ? difficulties[selected_difficulty].id : selected_difficulty]')});
modernStepSource = ReplaceOnce(modernStepSource, "illustrator = song_get_info", {cs(apotheosis_toggle)} + "illustrator = song_get_info");
Queue(modernStep, modernStepSource);
string mainSelect = "gml_Object_o_songselect_main_Create_0";
Queue(mainSelect, ReplaceOnce(Read(mainSelect), "start_song(selected_song.song_id, confirm_menu.selected_difficulty);", {cs('var custom_actual_difficulty = confirm_menu.selected_difficulty;\n    var custom_start_args = {};\n    if (struct_get_fallback(selected_song, "is_custom_chart", false)) {\n        custom_actual_difficulty = confirm_menu.difficulties[confirm_menu.selected_difficulty].id;\n        if (custom_actual_difficulty == 3 && struct_exists(selected_song, "custom_apotheosis") && confirm_menu.custom_apotheosis_active) {\n            custom_start_args.force_chart = "APOTHEOSIS";\n            custom_start_args.custom_apotheosis = true;\n        }\n    }\n    start_song(selected_song.song_id, custom_actual_difficulty, custom_start_args);')}));
foreach (string modernDraw in new[] {{ "gml_Object_o_songselect_newconfirm_Draw_0", "gml_Object_o_songselect_newconfirm_Draw_64" }}) {{
    string render = ReplaceOnce(Read(modernDraw), {cs('charter = struct_get(song, $"note_designer_{difficulty + 1}");')}, {cs('charter = (difficulty == 3 && custom_apotheosis_active) ? song.custom_apotheosis.designer : struct_get(song, $"note_designer_{difficulty + 1}");')});
    render = ReplaceOnce(render, {cs('struct_get(song, $"difficulty_display_{i + 1}")')}, {cs('((i == 3 && custom_apotheosis_active) ? song.custom_apotheosis.display : struct_get(song, $"difficulty_display_{i + 1}"))')});
    render = render.Replace({cs('format_score(global.highscores.normal[song.song_id][i].score)')}, {cs('((i == 3 && custom_apotheosis_active) ? "--" : format_score(global.highscores.normal[song.song_id][i].score))')});
    render = ReplaceOnce(render, {cs('get_grade_string(get_score_grade(global.highscores.normal[song.song_id][i].score))')}, {cs('((i == 3 && custom_apotheosis_active) ? "" : get_grade_string(get_score_grade(global.highscores.normal[song.song_id][i].score)))')});
    int enums = render.IndexOf("\\nenum ", StringComparison.Ordinal);
    render = enums < 0 ? render + {cs(apotheosis_hint)} : render.Insert(enums, {cs(apotheosis_hint)});
    Queue(modernDraw, render);
}}
imports.Import();
File.WriteAllText(Path.Combine({cs(work)}, "patch-applied.txt"), "Compiled all custom song patches");
'''
    return preamble + '\n'.join(audio_imports) + finish


def make_verify_script(songs, work):
    text = '''using System;
using System.IO;
using System.Linq;
using UndertaleModLib;
using UndertaleModLib.Decompiler;
EnsureDataLoaded();
var context = new GlobalDecompileContext(Data);
string Read(string name) {
    var code = Data.Code.ByName(name);
    if (code == null) throw new Exception("Missing saved code " + name);
    return new Underanalyzer.Decompiler.DecompileContext(context, code, Data.ToolInfo.DecompilerSettings).DecompileToString();
}
'''
    expected_audio = ', '.join(cs('music_chart_'+s['chart_id']) for s in songs)
    expected_covers = ', '.join(cs('song_'+s['chart_id']) for s in songs if s.get('cover'))
    text += f'''var expectedAudio = new string[] {{ {expected_audio} }};
var expectedCovers = new string[] {{ {expected_covers} }};
if (!Data.Sounds.Where(s => s?.Name?.Content?.StartsWith("music_chart_custom_manager_", StringComparison.Ordinal) == true).Select(s => s.Name.Content).OrderBy(s => s).SequenceEqual(expectedAudio.OrderBy(s => s))) throw new Exception("Saved audio selection differs");
if (!Data.Sprites.Where(s => s?.Name?.Content?.StartsWith("song_custom_manager_", StringComparison.Ordinal) == true).Select(s => s.Name.Content).OrderBy(s => s).SequenceEqual(expectedCovers.OrderBy(s => s))) throw new Exception("Saved jacket selection differs");
'''
    for song in songs:
        cid = song['chart_id']
        text += f'''{{
var sound = Data.Sounds.ByName("music_chart_{cid}");
if (sound == null || sound.GroupID != 0 || sound.AudioFile == null || !sound.AudioFile.Data.SequenceEqual(File.ReadAllBytes({cs(song['audio'])}))) throw new Exception("Audio verification failed: {cid}");
if (!Read("gml_GlobalScript_load_song_information").Contains("music_chart_{cid}")) throw new Exception("Missing song registration: {cid}");
}}
'''
        if song.get('cover'):
            text += f'''{{
var sprite = Data.Sprites.ByName("song_{cid}");
if (sprite == null || sprite.Width != 100 || sprite.Height != 100 || sprite.Textures.Count != 1) throw new Exception("Invalid saved cover: {cid}");
var page = sprite.Textures[0].Texture;
if (page == null || page.SourceWidth != 100 || page.SourceHeight != 100 || page.TexturePage == null) throw new Exception("Invalid saved texture page");
using var output = new MemoryStream();
page.TexturePage.TextureData.Image.SavePng(output);
if (!output.ToArray().SequenceEqual(File.ReadAllBytes({cs(song['cover'])}))) throw new Exception("Saved cover differs: {cid}");
}}
'''
    markers = {
        'gml_Object_o_transitionsong_Alarm_0': ['case \"APOTHEOSIS\":', 'song.custom_apotheosis.display', 'song.custom_apotheosis.designer', 'jacket_designer = struct_get_fallback'],
        'gml_GlobalScript_load_song_information': ['custom_chart_song_ids', 'custom_difficulties'],
        'gml_GlobalScript_create_song_packs': ['Custom Charts'],
        'gml_GlobalScript_start_song': ['custom_apotheosis', 'APOTHEOSIS', 'custom_audio_previous', 'custom_difficulties', 'arg2.clear_room = scene_songselect_old;', 'arg2.quit_room = scene_songselect_old;', 'arg2.fail_room = scene_songselect_old;'],
        'gml_Object_cc_CleanUp_0': ['custom_audio_restore_pending'],
        'gml_GlobalScript_refresh_song_objects': ['custom_difficulties'],
        'gml_Object_o_songselect_confirm_Step_0': ['custom_diffs'],
        'gml_Object_o_songselect_confirm_Draw_64': ['custom_difficulties'],
        'gml_Object_o_songselect_newconfirm_Create_0': ['custom_wanted_diff', 'custom_apotheosis_active'],
        'gml_Object_o_songselect_newconfirm_Step_0': ['difficulties[selected_difficulty].id', 'custom_apotheosis_active', 'keyboard_check_pressed'],
        'gml_Object_o_songselect_newconfirm_Draw_0': ['TAB: switch to APOTHEOSIS', 'custom_apotheosis_active'],
        'gml_Object_o_songselect_newconfirm_Draw_64': ['TAB: switch to APOTHEOSIS', 'custom_apotheosis_active'],
        'gml_Object_o_songselect_main_Create_0': ['custom_actual_difficulty', 'difficulties[confirm_menu.selected_difficulty].id'],
    }
    for name, expected in markers.items():
        text += '{\nstring source = Read(' + cs(name) + ');\n'
        for marker in expected:
            text += 'if (!source.Contains(' + cs(marker) + ')) throw new Exception(' + cs('Missing saved patch ' + name + ':' + marker) + ');\n'
        text += f'File.WriteAllText(Path.Combine({cs(work)}, {cs("verified_"+name+".gml")}), source);\n}}\n'
    text += f'File.WriteAllText(Path.Combine({cs(work)}, "verified.txt"), "Saved archive reopened; all imported assets and compiled patches verified");\n'
    return text


class Manager:
    def __init__(self, workspace):
        self.workspace = Path(workspace).expanduser().resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.library = self.workspace / 'library'; self.library.mkdir(exist_ok=True)
        self.state_path = self.workspace / 'state.json'
        self.journal_path = self.workspace / 'transaction.json'
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else dict(version=1, configured=False, assignments={}, tombstones=[], selected_ids=[], installed_ids=[], installed_files={})
        if self.journal_path.exists():
            self.recover()
        # Migrate workspaces created by early manager prototypes without touching
        # their existing source backup or reusing a modified game archive.
        if self.state.get('configured') and Path(self.state['backup']).name != 'data.win.backup':
            with self._lock():
                backup = self.workspace/'original'/'data.win.backup'
                self._immutable_backup(Path(self.state['backup']),backup)
                self.state['backup']=str(backup);self._save()

    def _save(self):
        atomic_json(self.state_path, self.state)

    @contextlib.contextmanager
    def _lock(self):
        with (self.workspace / '.manager.lock').open('a+b') as stream:
            if os.name == 'posix':
                import fcntl
                try: fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError: raise RuntimeError('Another manager operation is active')
            else:
                import msvcrt
                stream.seek(0); stream.write(b'0'); stream.flush(); stream.seek(0)
                try: msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError: raise RuntimeError('Another manager operation is active')
            try:
                if self.state_path.exists(): self.state = json.loads(self.state_path.read_text())
                yield
            finally:
                if os.name == 'posix': fcntl.flock(stream, fcntl.LOCK_UN)
                else:
                    stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)

    def select(self, ids):
        with self._lock():
            self.state['selected_ids'] = list(dict.fromkeys(ids)); self._save()

    def setup(self, original, destination, cli):
        with self._lock():
            if self.state.get('configured'):
                raise ValueError('This workspace is already configured; use a new workspace to change game copies')
            original = Path(original).expanduser().resolve()
            if original.is_file(): original = original.parent
            destination = Path(destination).expanduser().resolve()
            cli = Path(cli).expanduser().resolve()
            if cli.is_dir(): cli = cli / ('UndertaleModCli.exe' if os.name == 'nt' else 'UndertaleModCli')
            if not cli.is_file(): raise ValueError('UndertaleModCli executable not found')
            source = original / 'data.win'
            if not source.is_file() or not (original / 'VIVIDSTASIS.exe').is_file(): raise ValueError('Choose a complete Vividstasis game folder')
            if destination == original or destination.is_relative_to(original) or original.is_relative_to(destination):
                raise ValueError('Original and destination folders must be separate, non-nested game folders')
            if destination == self.workspace or self.workspace.is_relative_to(destination): raise ValueError('Game destination must not contain the manager workspace')
            if destination.exists() and (not destination.is_dir() or any(destination.iterdir())): raise ValueError('Destination must be a new or empty directory')
            if sha256(source) != SOURCE_SHA256: raise ValueError('Unsupported original data.win; exact clean Vividstasis 6.2.2.2 build required')
            backupdir = self.workspace / 'original'; backupdir.mkdir(exist_ok=True)
            backup = backupdir / 'data.win.backup'
            self._immutable_backup(source,backup)
            shutil.copytree(original, destination, dirs_exist_ok=True)
            if sha256(destination / 'data.win') != SOURCE_SHA256: raise ValueError('Copied game archive failed verification')
            self.state.update(configured=True, original=str(original), destination=str(destination), cli=str(cli), source_sha256=SOURCE_SHA256, archive_sha256=SOURCE_SHA256, backup=str(backup), installed_files={}, installed_ids=[])
            self._save()
            return copy.deepcopy(self.state)

    @staticmethod
    def _immutable_backup(source,backup):
        if backup.exists():
            if not backup.is_file() or sha256(backup)!=SOURCE_SHA256:
                raise ValueError('Existing data.win.backup is not pristine; it will not be overwritten')
            return
        temporary = backup.with_name('.data.win.backup.pending-'+uuid.uuid4().hex)
        try:
            shutil.copy2(source,temporary)
            if sha256(temporary)!=SOURCE_SHA256:raise ValueError('Pristine backup copy failed verification')
            # A hardlink creates the permanent name exclusively; never overwrite.
            os.link(temporary,backup)
        finally:
            if temporary.exists():temporary.unlink()

    def validate_setup(self):
        if not self.state.get('configured'): raise ValueError('Set up a separate game copy first')
        destination = Path(self.state['destination'])
        if not (destination / 'VIVIDSTASIS.exe').is_file(): raise ValueError('Configured game copy is missing its executable')
        if not Path(self.state['cli']).is_file(): raise ValueError('Configured UndertaleModCli executable is missing')
        if sha256(Path(self.state['backup'])) != SOURCE_SHA256: raise ValueError('Pristine source backup has changed')
        if sha256(destination / 'data.win') != self.state.get('archive_sha256', SOURCE_SHA256):
            raise ValueError('Game copy data.win changed outside this manager; refusing to overwrite it')
        for relative, digest in self.state.get('installed_files', {}).items():
            path = self._target(relative)
            if not path.is_file() or sha256(path) != digest: raise ValueError('Installed manager file changed or disappeared: ' + relative)
        return True

    def _target(self, relative):
        destination = Path(self.state['destination']).resolve()
        result = (destination / relative).resolve()
        if not result.is_relative_to(destination): raise ValueError('Unsafe install path')
        return result

    def _packages(self, ids):
        result = []
        for ident in dict.fromkeys(ids):
            path = (self.library / ident).resolve()
            if path.parent != self.library or not path.is_dir(): raise ValueError('Unknown library song: ' + str(ident))
            package = Package(path)
            if package.metadata['id'] != ident: raise ValueError('Library directory and package IDs disagree')
            result.append(package)
        return result

    @staticmethod
    def _fingerprint(package):
        refs = {package.metadata['audio']}
        if package.metadata.get('jacket'):refs.add(package.metadata['jacket'])
        refs.update(chart['file'] for chart in package.charts.values())
        files = {name:sha256(package.asset(name)) for name in sorted(refs)}
        canonical = json.dumps(dict(metadata=package.metadata,files=files),sort_keys=True,ensure_ascii=True,separators=(',',':')).encode()
        return hashlib.sha256(canonical).hexdigest()

    fingerprint = _fingerprint

    def review(self, ids):
        with self._lock():
            packages = self._packages(ids)
            active = {p.metadata['id'] for p in packages}
            installed = set(self.state.get('installed_ids',[]))
            fingerprints = {p.metadata['id']:self._fingerprint(p) for p in packages}
            old = self.state.get('package_fingerprints',{})
            changed = sorted(i for i in active & installed if old.get(i)!=fingerprints[i])
            return dict(selected_ids=[p.metadata['id'] for p in packages], additions=sorted(active-installed),removals=sorted(installed-active),changed=changed,unchanged=sorted((active & installed)-set(changed)),package_fingerprints=fingerprints,songs=[dict(id=p.metadata['id'], title=p.metadata['title'], artist=p.metadata['artist'], difficulties=list(p.charts), assignment=self.state.get('assignments',{}).get(p.metadata['id'])) for p in packages], original=self.state.get('original'), destination=self.state.get('destination'), configured=self.state.get('configured',False))

    def _assign(self, packages):
        assignments = self.state.setdefault('assignments', {})
        next_id = max([206] + [a['song_id'] for a in assignments.values()]) + 1
        for package in packages:
            ident = package.metadata['id']
            if ident not in assignments:
                # Names derive from the persistent numeric ID, not package text.
                assignments[ident] = dict(song_id=next_id, chart_id=f'custom_manager_{next_id}')
                next_id += 1
        active = {p.metadata['id'] for p in packages}
        self.state['tombstones'] = sorted(set(assignments) - set(self.state.get('installed_ids', [])))
        self._save()  # reserve IDs even if conversion or compilation later fails

    @staticmethod
    def _cancel(cancel):
        if cancel and cancel(): raise Cancelled('Build cancelled; installed game was not changed')

    def _run(self, command, log, cancel=None):
        env = dict(os.environ, DOTNET_PROCESSOR_COUNT='4')
        with Path(log).open('w') as stream:
            process = subprocess.Popen([str(x) for x in command], stdout=stream, stderr=subprocess.STDOUT, env=env)
            try:
                while process.poll() is None:
                    self._cancel(cancel); time.sleep(.15)
                if process.returncode: raise RuntimeError(f'Command failed ({process.returncode}); see {log}')
            except BaseException:
                process.terminate()
                try: process.wait(timeout=10)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
                raise

    def _normalized_asset(self, source, kind, output, log, cancel):
        source_digest = sha256(source)
        settings = dict(version=1,kind=kind,audio_codec='libvorbis',audio_quality=6,cover_size=100)
        key = hashlib.sha256(json.dumps([source_digest,settings],sort_keys=True).encode()).hexdigest()
        cache = self.workspace/'cache'; cache.mkdir(exist_ok=True)
        payload = cache/(key+('.ogg' if kind=='audio' else '.png'))
        metadata = cache/(key+'.json')
        valid = False
        if payload.is_file() and metadata.is_file():
            try:valid = sha256(payload)==json.loads(metadata.read_text())['sha256']
            except (ValueError,KeyError,OSError):pass
        if valid:
            Path(log).write_text('Reused verified normalized asset '+key+'\n')
        else:
            temporary = payload.with_name(key+'.pending'+payload.suffix)
            if temporary.exists():temporary.unlink()
            command=['ffmpeg','-nostdin','-v','error','-i',source]
            command += ['-map','0:a:0','-vn','-c:a','libvorbis','-q:a','6'] if kind=='audio' else ['-vf','scale=100:100:force_original_aspect_ratio=increase,crop=100:100,setsar=1','-frames:v','1','-pix_fmt','rgba']
            try:
                self._run(command+[temporary],log,cancel)
                if sha256(source)!=source_digest:raise ValueError('Source asset changed during normalization')
                os.replace(temporary,payload)
            finally:
                if temporary.exists():temporary.unlink()
            atomic_json(metadata,dict(sha256=sha256(payload),source_sha256=source_digest,settings=settings))
        self._cancel(cancel)
        shutil.copy2(payload,output)

    def build(self, ids, progress=None, cancel=None):
        progress = progress or (lambda _: None)
        with self._lock():
            self.validate_setup(); self._cancel(cancel)
            packages = self._packages(ids)
            if not packages: return self._restore_stock(progress)
            self._assign(packages)
            fingerprints = {p.metadata['id']:self._fingerprint(p) for p in packages}
            stage = self.workspace / 'builds' / uuid.uuid4().hex; stage.mkdir(parents=True)
            (stage/'.manager-owned').write_text('Vividstasis song manager build\n')
            try:
                prepared = []
                files = {}
                if not shutil.which('ffmpeg'): raise ValueError('ffmpeg is required to convert audio and jackets')
                for package in packages:
                    self._cancel(cancel)
                    ident = package.metadata['id']; assignment = self.state['assignments'][ident]
                    progress('Converting ' + package.metadata['title'])
                    work = stage / ident; work.mkdir()
                    audio = work / 'audio.ogg'
                    self._normalized_asset(package.asset(package.metadata['audio']),'audio',audio,work/'audio.log',cancel)
                    cover = None
                    if package.metadata.get('jacket'):
                        cover = work / 'cover.png'
                        self._normalized_asset(package.asset(package.metadata['jacket']),'cover',cover,work/'cover.log',cancel)
                    charts = {}; bpm = None
                    for difficulty, chart in package.charts.items():
                        payload, chart_bpm, count = convert(package.asset(chart['file']).read_text(encoding='utf-8-sig'),chart.get('bumper_holds','reject'))
                        decoded = parse_chart(payload)
                        if not any(n['type'] != 3 for b in decoded['blocks'] if b['tag'] == 0xC0 for n in b['notes']): raise ValueError(f'{ident}/{difficulty}: chart has no playable notes')
                        if bpm is None: bpm = chart_bpm
                        outfile = work / (difficulty.upper()+'.vsb'); outfile.write_bytes(payload)
                        relative = f"Charts/{assignment['chart_id']}/{difficulty.upper()}.vsb"
                        files[relative] = outfile
                        charts[difficulty] = dict(chart, records=count, source_bpm=chart_bpm)
                    prepared.append(dict(id=ident,title=package.metadata['title'],artist=package.metadata['artist'],jacket_artist=package.metadata.get('jacket_artist','Unknown'),audio=audio,cover=cover,charts=charts,bpm=bpm,**assignment))
                progress('Compiling all selected songs into one clean archive')
                script = stage / 'patch.csx'; script.write_text(make_multi_script(prepared,stage,max(a['song_id'] for a in self.state['assignments'].values())))
                archive = stage / 'data.pending.win'
                self._run([self.state['cli'],'load',self.state['backup'],'-s',script,'-o',archive],stage/'patch.log',cancel)
                if not (stage/'patch-applied.txt').is_file() or not archive.is_file(): raise RuntimeError('CLI did not complete patching; see '+str(stage/'patch.log'))
                progress('Reopening the saved archive and verifying every song')
                verify = stage / 'verify.csx'; verify.write_text(make_verify_script(prepared,stage))
                self._run([self.state['cli'],'load',archive,'-s',verify],stage/'verify.log',cancel)
                if not (stage/'verified.txt').is_file(): raise RuntimeError('Saved archive verification did not complete')
                self._cancel(cancel)
                if sha256(Path(self.state['backup'])) != SOURCE_SHA256: raise RuntimeError('Pristine backup changed during build')
                for package in packages:
                    if self._fingerprint(Package(package.root)) != fingerprints[package.metadata['id']]:
                        raise ValueError('Library song changed during build: '+package.metadata['id'])
                files['data.win'] = archive
                report = dict(package_fingerprints=fingerprints,selected_ids=[p.metadata['id'] for p in packages],songs=[{k:v for k,v in s.items() if k not in ('audio','cover')} for s in prepared],source_sha256=SOURCE_SHA256,output_sha256=sha256(archive),runtime_tested=False)
                atomic_json(stage/'manifest.json',report)
                newstate = copy.deepcopy(self.state)
                newstate.update(package_fingerprints=fingerprints,tombstones=sorted(set(self.state['assignments']) - set(report['selected_ids'])),selected_ids=report['selected_ids'],installed_ids=report['selected_ids'],installed_files={r:sha256(p) for r,p in files.items() if r!='data.win'},archive_sha256=report['output_sha256'],last_build=str(stage))
                progress('Installing the verified build (transaction in progress)')
                self._install(files,newstate)
                progress('Build installed and verified')
                return report
            except BaseException:
                self._prune()
                raise

    def _install(self, desired, newstate):
        """Snapshot all affected paths, journal, replace each file, then commit state."""
        self.validate_setup()
        transaction = self.workspace / 'transactions' / uuid.uuid4().hex
        transaction.mkdir(parents=True)
        (transaction/'.manager-owned').write_text('Vividstasis song manager transaction\n')
        old_files = self.state.get('installed_files',{})
        removed = set(old_files) - set(desired)
        # Stats are generated caches belonging to our reserved chart folders.
        for rel in list(old_files):
            if rel.endswith('.vsb'):
                stats = str(Path(rel).with_suffix('.stats'))
                if self._target(stats).is_file(): removed.add(stats)
        operations=[]
        for relative in sorted(set(desired) | removed, key=lambda r:(r=='data.win',r)):
            target = self._target(relative)
            if target.exists() and relative not in old_files and relative != 'data.win' and relative not in removed:
                raise ValueError('Install would overwrite an unmanaged file: '+relative)
            operations.append(dict(relative=relative,source=str(desired[relative]) if relative in desired else None,existed=target.exists(),before=str(transaction/'before'/relative)))
        previous_state = copy.deepcopy(self.state)
        previous_state.pop('previous_installation',None)
        before_paths = {op['relative']:op['before'] for op in operations if op['existed'] and (op['relative']=='data.win' or op['relative'] in old_files)}
        newstate['previous_installation'] = dict(state=previous_state,files=before_paths)
        journal=dict(version=1,phase='preparing',directory=str(transaction),old_state=copy.deepcopy(self.state),new_state=newstate,operations=operations)
        atomic_json(self.journal_path,journal)
        try:
            for op in operations:
                if op['existed']:
                    target=self._target(op['relative']); before=Path(op['before']);before.parent.mkdir(parents=True,exist_ok=True)
                    try: os.link(target,before)
                    except OSError: shutil.copy2(target,before)
                    op['before_sha256']=sha256(before)
                if op['source']:op['after_sha256']=sha256(Path(op['source']))
            journal['phase']='installing';atomic_json(self.journal_path,journal)
            for op in operations:
                target=self._target(op['relative'])
                if op['source']:
                    self._replace(Path(op['source']),target)
                    if sha256(target)!=op['after_sha256']:raise RuntimeError('Installed file verification failed: '+op['relative'])
                elif target.exists():target.unlink()
            # The state commit and the journal commit can be interrupted independently;
            # recovery rolls back until phase=committed is durably recorded.
            atomic_json(self.state_path,newstate)
            journal['phase']='committed';atomic_json(self.journal_path,journal)
            self.state=newstate
            self.journal_path.unlink()
            self._prune()
            for op in operations:
                if not op['source']:
                    try:self._target(op['relative']).parent.rmdir()
                    except OSError:pass
        except BaseException:
            self._recover_journal(journal)
            raise

    @staticmethod
    def _replace(source,target):
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_name('.'+target.name+'.manager-'+uuid.uuid4().hex)
        try:
            shutil.copy2(source,temporary)
            with temporary.open('rb') as stream:os.fsync(stream.fileno())
            os.replace(temporary,target)
        finally:
            if temporary.exists():temporary.unlink()

    def _recover_journal(self,journal):
        if journal['phase']=='committed':
            self.state=journal['new_state'];atomic_json(self.state_path,self.state)
        elif journal['phase']=='installing':
            self.state=journal['old_state']
            for op in reversed(journal['operations']):
                target=self._target(op['relative'])
                if op['existed']:
                    before=Path(op['before'])
                    if not before.is_file() or sha256(before)!=op['before_sha256']:raise RuntimeError('Recovery backup missing or changed; do not launch the game')
                    self._replace(before,target)
                elif target.exists():target.unlink()
            atomic_json(self.state_path,self.state)
        if self.journal_path.exists():self.journal_path.unlink()
        self._prune()

    def _prune(self):
        # Only touch UUID directories explicitly created by this manager. Retain
        # small build logs, scripts and manifests, but not multi-GB saved archives.
        if self.journal_path.exists():return
        builds=self.workspace/'builds'
        for directory in builds.iterdir() if builds.exists() else []:
            if directory.is_symlink() or not directory.is_dir() or len(directory.name)!=32 or any(c not in '0123456789abcdef' for c in directory.name):continue
            if (directory/'.manager-owned').is_file():
                archive=directory/'data.pending.win'
                if archive.is_file() and not archive.is_symlink():archive.unlink()
        transactions=self.workspace/'transactions'
        keep=set()
        for value in self.state.get('previous_installation',{}).get('files',{}).values():
            path=Path(value).resolve()
            if path.is_relative_to(transactions.resolve()):keep.add(path.relative_to(transactions.resolve()).parts[0])
        for directory in transactions.iterdir() if transactions.exists() else []:
            if directory.is_symlink() or not directory.is_dir() or len(directory.name)!=32 or any(c not in '0123456789abcdef' for c in directory.name):continue
            if directory.name not in keep and (directory/'.manager-owned').is_file():shutil.rmtree(directory)

    def recover(self,progress=None):
        with self._lock():
            if self.journal_path.exists():
                journal=json.loads(self.journal_path.read_text())
                self._recover_journal(journal)
                if progress:progress('Recovered the previous complete game installation')
            return copy.deepcopy(self.state)

    def _restore_stock(self,progress):
        progress('Restoring the pristine game archive')
        newstate=copy.deepcopy(self.state)
        newstate.update(package_fingerprints={},installed_ids=[],selected_ids=[],installed_files={},archive_sha256=SOURCE_SHA256,tombstones=sorted(self.state.get('assignments',{})))
        self._install({'data.win':Path(self.state['backup'])},newstate)
        progress('Original archive restored; stable song IDs retained')
        return dict(restored=True,source_sha256=SOURCE_SHA256)

    def restore_clean(self,progress=None):
        with self._lock():
            self.validate_setup()
            return self._restore_stock(progress or (lambda _:None))

    def rollback(self,progress=None):
        progress = progress or (lambda _:None)
        with self._lock():
            self.validate_setup()
            previous = self.state.get('previous_installation')
            if not previous: raise ValueError('No previous successful installation is available')
            desired = {rel:Path(path) for rel,path in previous['files'].items()}
            target_state = copy.deepcopy(previous['state'])
            target_state['backup'] = self.state['backup']
            target_state['assignments'] = copy.deepcopy(self.state['assignments'])
            target_state['tombstones'] = sorted(set(target_state['assignments']) - set(target_state.get('installed_ids',[])))
            for relative,path in desired.items():
                expected = target_state['archive_sha256'] if relative=='data.win' else target_state['installed_files'][relative]
                if not path.is_file() or sha256(path)!=expected:raise ValueError('Previous installation snapshot changed: '+relative)
            progress('Restoring the previous complete installation')
            self._install(desired,target_state)
            progress('Previous installation restored; stable IDs retained')
            return dict(restored=True,installed_ids=self.state['installed_ids'])

    def launch(self):
        self.validate_setup()
        executable=Path(self.state['destination'])/'VIVIDSTASIS.exe'
        command=[str(executable)]
        if os.name!='nt':
            wine=shutil.which('wine')
            if not wine:raise ValueError('Wine is required to launch this Windows game on this platform')
            command=[wine,str(executable)]
        return subprocess.Popen(command,cwd=self.state['destination'])
