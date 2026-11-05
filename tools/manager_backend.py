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
from patch_templates import render_patch
try:
    from custom_songs import Package, DIFFICULTIES, DIFFICULTY_IDS
    from osu_to_vsb import convert
    from vsb import parse_chart
    from patch_custom_song import SOURCE_SHA256, cs, gml, make_compiler_preamble, make_asset_import, sha256
except ModuleNotFoundError:
    from tools.custom_songs import Package, DIFFICULTIES, DIFFICULTY_IDS
    from tools.osu_to_vsb import convert
    from tools.vsb import parse_chart
    from tools.patch_custom_song import SOURCE_SHA256, cs, gml, make_compiler_preamble, make_asset_import, sha256

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
    preamble = make_compiler_preamble(work)
    audio_imports = [
        '{\n' + make_asset_import(song['audio'], song['chart_id'], song.get('cover')) + '\n}'
        for song in songs
    ]
    register = render_patch('manager/initialize_catalog.gml',
        highest_id=highest_id,
    )
    for i, song in enumerate(songs):
        v = f'custom_song_{i}'
        available = ['true' if any(engine_id == i and d in song['charts'] for d,engine_id in DIFFICULTY_IDS.items()) else 'false' for i in range(6)]
        register += render_patch('manager/register_song.gml',
            v=v,
            song_id=song['song_id'],
            title_gml=gml(song['title']),
            artist_gml=gml(song['artist']),
            jacket_artist_gml=gml(song.get('jacket_artist', 'Unknown')),
            chart_id=song['chart_id'],
            jacket_assignment=f'{v}.jacket = asset_get_index("song_{song["chart_id"]}");' if song.get('cover') else '',
            initial_bpm=format(song['bpm'] / 2, '.12g'),
            has_encore='true' if 'encore' in song['charts'] else 'false',
            available_difficulties=', '.join(available),
            allowed_difficulties=', '.join(str(engine_id) for d,engine_id in DIFFICULTY_IDS.items() if d in song['charts']),
        )
        for diff, engine_id in DIFFICULTY_IDS.items():
            j = engine_id + 1
            chart = song['charts'].get(diff)
            level = float(chart['level']) if chart else 0
            display = str(math.floor(level)) + ('+' if level % 1 >= .5 else '') if chart else '--'
            designer = chart.get('designer', 'Unknown') if chart else ''
            register += render_patch('manager/register_difficulty.gml',
                v=v,
                slot=j,
                level=format(level, '.12g'),
                display_gml=gml(display),
                designer_gml=gml(designer),
            )
        if 'apotheosis' in song['charts']:
            alternate = song['charts']['apotheosis']
            level = float(alternate['level'])
            display = str(math.floor(level)) + ('+' if level % 1 >= .5 else '')
            register += render_patch(
                'manager/register_apotheosis.gml', variable=v,
                level=format(level, '.12g'), display=gml(display),
                designer=gml(alternate.get('designer', 'Unknown')),
            )
        register += render_patch('manager/publish_song.gml',
            song_id=song["song_id"],
            v=v,
        )
    pack = render_patch('manager/pack.gml')
    launch = render_patch('manager/launch.gml')
    cleanup = render_patch('manager/cleanup.gml')
    # Filtering inside the shared insertion helper also covers Encore fallback.
    filter_code = render_patch('manager/filter_difficulties.gml')
    correction = render_patch('manager/correct_legacy_selection.gml')
    next_old = render_patch('manager/legacy_next_anchor.gml')
    previous_old = render_patch('manager/legacy_previous_anchor.gml')
    next_new = render_patch('manager/legacy_next.gml')
    previous_new = render_patch('manager/legacy_previous.gml')
    apotheosis_metadata = render_patch('manager/apotheosis_metadata.gml')
    apotheosis_transition = render_patch('manager/apotheosis_transition.gml')
    finish = render_patch('manager/apply_patches.csx',
        register_cs=cs(register),
        pack_cs=cs(pack),
        launch_cs=cs(launch),
        apotheosis_metadata_cs=cs(apotheosis_metadata),
        apotheosis_transition_cs=cs(apotheosis_transition),
        cleanup_cs=cs(cleanup),
        filter_code_cs=cs(filter_code),
        correction_cs=cs(correction),
        next_old_cs=cs(next_old),
        next_new_cs=cs(next_new),
        previous_old_cs=cs(previous_old),
        previous_new_cs=cs(previous_new),
        work_cs=cs(work),
    )
    return preamble + '\n'.join(audio_imports) + finish


def make_verify_script(songs, work):
    text = render_patch('manager/verify_preamble.csx')
    expected_audio = ', '.join(cs('music_chart_'+s['chart_id']) for s in songs)
    expected_covers = ', '.join(cs('song_'+s['chart_id']) for s in songs if s.get('cover'))
    text += render_patch('manager/verify_selection.csx',
        expected_audio=expected_audio,
        expected_covers=expected_covers,
    )
    for song in songs:
        cid = song['chart_id']
        text += render_patch('manager/verify_audio.csx',
            cid=cid,
            audio=cs(song['audio']),
        )
        if song.get('cover'):
            text += render_patch('manager/verify_cover.csx',
                cid=cid,
                cover=cs(song['cover']),
            )
    markers = {
        'gml_Object_o_transitionsong_Alarm_0': ['case "APOTHEOSIS":', 'song.custom_apotheosis.display', 'song.custom_apotheosis.designer', 'jacket_designer = struct_get_fallback'],
        'gml_GlobalScript_load_song_information': ['custom_chart_song_ids', 'custom_difficulties', 'difficulty_constant_6'],
        'gml_GlobalScript_create_song_packs': ['Custom Charts'],
        'gml_GlobalScript_start_song': ['custom_has_apotheosis', 'APOTHEOSIS', 'arg1 == 5', 'song.difficulty_display_6', 'custom_audio_previous', 'arg2.clear_room = scene_songselect_old;'],
        'gml_Object_initiategame_Other_10': ['custom_score_record', 'global.highscores_at_load.normal[custom_score_i][5]'],
        'gml_GlobalScript_define_options': ['custom_score_record'],
        'gml_Object_o_profile_select_2023boot_Step_0': ['custom_score_record'],
        'gml_GlobalScript_process_song_unlocks': ['custom_difficulties', 'custom_d < 6'],
        'gml_Object_cc_CleanUp_0': ['custom_audio_restore_pending'],
        'gml_GlobalScript_refresh_song_objects': ['allowed_difficulties', 'custom_d != 5', 'APOTHEOSIS'],
        'gml_Object_o_songselect_confirm_Step_0': ['custom_diffs', 'allowed_difficulties'],
        'gml_Object_o_songselect_confirm_Draw_64': ['allowed_difficulties'],
        'gml_Object_o_songselect_newconfirm_Create_0': ['custom_wanted_diff', 'APOTHEOSIS'],
        'gml_Object_o_songselect_newconfirm_Step_0': ['difficulties[selected_difficulty].id'],
        'gml_Object_o_songselect_newconfirm_Draw_0': ['custom_spacing', 'choice.id == 5'],
        'gml_Object_o_songselect_newconfirm_Draw_64': ['custom_spacing', 'choice.id == 5'],
        'gml_Object_o_songselect_main_Create_0': ['custom_actual_difficulty', 'difficulties[confirm_menu.selected_difficulty].id', 'APOTHEOSIS'],
        'gml_Object_o_songselect_main_Other_25': ['!struct_get_fallback(selected_song, "is_custom_chart", false)'],
        'gml_Object_o_songselect_main_Draw_0': ['custom_footer_id'],
        'gml_Object_o_songobject_main_Other_25': ['[APOTHEOSIS]', 'min(diff, 3)'],
        'gml_Object_cc_Draw_0': ['global.df_load == "APOTHEOSIS"'],
    }
    for name, expected in markers.items():
        text += '{\nstring source = Read(' + cs(name) + ');\n'
        for marker in expected:
            text += 'if (!source.Contains(' + cs(marker) + ')) throw new Exception(' + cs('Missing saved patch ' + name + ':' + marker) + ');\n'
        text += f'File.WriteAllText(Path.Combine({cs(work)}, {cs("verified_"+name+".gml")}), source);\n}}\n'
    text += render_patch('manager/verify_stock_scores.csx', work_cs=cs(work))
    text += render_patch('manager/verify_done.csx',
        work_cs=cs(work),
    )
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
            # Windows requires a writable descriptor for fsync/_commit.
            # Flush before copying metadata, which may make the file read-only.
            with source.open('rb') as incoming, temporary.open('wb') as stream:
                shutil.copyfileobj(incoming, stream)
                stream.flush()
                os.fsync(stream.fileno())
            shutil.copystat(source,temporary)
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
