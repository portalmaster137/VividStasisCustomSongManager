#!/usr/bin/env python3
"""Build a Vividstasis custom-song overlay from clean game data, audio and 4K/6K .osu."""

from patch_templates import render_patch
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
DEFAULT_CLI = './UndertaleMTCLI'


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


def make_compiler_preamble(work):
    return render_patch('shared/compiler_preamble.csx', work_cs=cs(work))


def make_asset_import(audio, chart_id, cover=None):
    cover_import = '' if cover is None else render_patch(
        'single/cover_import.csx', chart_id=chart_id, cover_cs=cs(cover),
    )
    return render_patch(
        'shared/import_audio.csx', chart_id=chart_id,
        audio_cs=cs(audio), cover_import=cover_import,
    )


def make_script(audio, work, chart_id, title, artist, designer, bpm, level, cover=None):
    register = render_patch('single/register.gml',
        title_gml=gml(title),
        artist_gml=gml(artist),
        chart_id=chart_id,
        jacket_assignment=f'custom.jacket = asset_get_index("song_{chart_id}");' if cover else '',
        initial_bpm=format(bpm / 2, '.12g'),
        level=level,
        level_display=format(level, 'g'),
        designer_gml=gml(designer),
    )
    pack = render_patch('single/pack.gml')
    launch = render_patch('single/launch.gml')
    cleanup = render_patch('single/cleanup.gml')
    return make_compiler_preamble(work) + make_asset_import(audio, chart_id, cover) + render_patch('single/apply_patches.csx',
        work_cs=cs(work),
        register_cs=cs(register),
        pack_cs=cs(pack),
        launch_cs=cs(launch),
        cleanup_cs=cs(cleanup),
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio', type=Path)
    p.add_argument('osu', type=Path)
    p.add_argument('data', type=Path)
    p.add_argument('-o', '--output-dir', type=Path, required=True, help='New overlay directory (must not exist)')
    p.add_argument('--cli', type=Path, default=Path(DEFAULT_CLI))
    p.add_argument('--chart-id', default='custom_demo')
    p.add_argument('--cover', type=Path, help='Cover image; resized and center-cropped to 100x100')
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
        if a.cli.is_dir():
            a.cli = a.cli / 'UndertaleModCli'
        for path in (a.audio, a.osu, a.data, a.cli, *([a.cover] if a.cover else [])):
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
        cover = None
        if a.cover:
            cover = build / 'cover.png'
            with (build / 'cover.log').open('w') as log:
                subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(a.cover.resolve()),
                                '-vf', 'scale=100:100:force_original_aspect_ratio=increase,crop=100:100,setsar=1',
                                '-frames:v', '1', '-pix_fmt', 'rgba', str(cover)],
                               stdout=log, stderr=subprocess.STDOUT, check=True)
        meta = metadata(text)
        script = build / 'patch.csx'
        script.write_text(make_script(ogg, build, a.chart_id, a.title or meta.get('Title', a.osu.stem), a.artist or meta.get('Artist', 'Unknown'), a.designer or meta.get('Creator', 'Unknown'), bpm, a.level, cover))
        staged = a.output_dir / 'data.pending.win'
        print('Importing audio and compiling registration patches (see build/patch.log)...', flush=True)
        with (build / 'patch.log').open('w') as log:
            subprocess.run([str(a.cli.resolve()), 'load', str(a.data.resolve()), '-s', str(script), '-o', str(staged)], stdout=log, stderr=subprocess.STDOUT, check=True)
        if not (build / 'patch-applied.txt').exists() or not staged.is_file():
            raise ValueError('CLI did not complete patching; inspect build/patch.log')
        cover_verify = '' if cover is None else render_patch('single/verify_cover.csx',
            value=a.chart_id,
            cover_cs=cs(cover),
        )
        verify = build / 'verify.csx'
        verify.write_text(render_patch('single/verify.csx',
            value=a.chart_id,
            ogg_cs=cs(ogg),
            cover_verify=cover_verify,
            build_cs=cs(build),
        ))
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
        report = dict(source_sha256=source_hash, output_sha256=sha256(a.output_dir / 'data.win'), chart_id=a.chart_id, records=count, source_bpm=bpm, bumper_holds=a.bumper_holds, cover_sha256=sha256(cover) if cover else None, audio_backend='GameMaker', results='skipped for custom song', runtime_tested=False)
        (a.output_dir / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
        print(f'Built {a.output_dir}. Copy data.win and Charts/ into a COPY of the complete game; open Custom Charts. All three base difficulties contain the same input chart.')
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        p.exit(1, f'Build failed: {exc}\nAny partial output is incomplete; inspect its build logs and use a new output directory.\n')


if __name__ == '__main__':
    main()
