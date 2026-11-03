"""Portable custom-song packages and editable local library."""
import json
import os
import re
import shutil
import tempfile
import tomllib
import zipfile
from pathlib import Path

DIFFICULTIES = ('opening', 'middle', 'finale', 'encore')
PACKAGE_DIFFICULTIES = DIFFICULTIES + ('apotheosis',)
LIMIT = 1024 ** 3


def metadata_text(metadata):
    def scalar(v):
        if isinstance(v, bool): return str(v).lower()
        if isinstance(v, (int, float)): return repr(v)
        return json.dumps(str(v), ensure_ascii=False)
    lines = [f'{json.dumps(str(k))} = {scalar(v)}' for k, v in metadata.items() if not isinstance(v, dict)]
    for difficulty, chart in metadata.get('charts', {}).items():
        lines += ['', f'[charts.{difficulty}]']
        lines += [f'{json.dumps(str(k))} = {scalar(v)}' for k, v in chart.items()]
    return '\n'.join(lines) + '\n'


def write_metadata(path, metadata):
    Path(path).write_text(metadata_text(metadata), encoding='utf-8')


class Package:
    def __init__(self, path):
        self.path = Path(path)
        self._temporary = None
        if self.path.is_dir():
            self.root = self.path
        else:
            self._temporary = tempfile.TemporaryDirectory(prefix='vsc-')
            self.root = Path(self._temporary.name)
            with zipfile.ZipFile(self.path) as archive:
                names = set()
                size = 0
                for entry in archive.infolist():
                    name = entry.filename
                    parts = name.replace('\\', '/').split('/')
                    if any(not part for part in parts[:-1]) or (not entry.is_dir() and not parts[-1]) or name in names or name.startswith(('/', '\\')) or '..' in parts or '.' in parts or ':' in name or '\\' in name:
                        raise ValueError('Unsafe or duplicate archive path')
                    if entry.flag_bits & 1 or (entry.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ValueError('Encrypted entries and symlinks are unsupported')
                    names.add(name)
                    size += entry.file_size
                    if size > LIMIT: raise ValueError('Package exceeds 1 GiB')
                archive.extractall(self.root)
        with (self.root / 'data.toml').open('rb') as stream:
            self.metadata = tomllib.load(stream)
        self.charts = self.metadata.get('charts', {})
        self.validate()

    def close(self):
        if self._temporary is not None:
            self._temporary.cleanup()
            self._temporary = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    def asset(self, value):
        if not isinstance(value, str) or Path(value).is_absolute() or "\\" in value or ':' in value:
            raise ValueError('Asset paths must be relative package paths')
        if any(part in ('', '.', '..') for part in value.split('/')):
            raise ValueError('Asset paths must be canonical relative paths')
        path = (self.root / value).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file():
            raise ValueError(f'Missing or unsafe asset: {value}')
        return path

    def validate(self):
        import math
        from osu_to_vsb import convert
        m = self.metadata
        self.charts = m.get('charts', {})
        if type(m.get('format_version')) is not int or m.get('format_version') != 1: raise ValueError('Unsupported package format version')
        if not isinstance(m.get('id'), str) or not re.fullmatch('[a-z][a-z0-9_]{0,63}', m.get('id', '')): raise ValueError('Invalid song ID')
        for field in ('title', 'artist', 'audio'):
            if not isinstance(m.get(field), str) or not m[field]: raise ValueError(f'Missing {field}')
        self.asset(m['audio'])
        if m.get('jacket'): self.asset(m['jacket'])
        if not isinstance(self.charts, dict) or not self.charts or set(self.charts) - set(PACKAGE_DIFFICULTIES): raise ValueError('Invalid difficulty set')
        if 'apotheosis' in self.charts and 'encore' not in self.charts:
            raise ValueError('APOTHEOSIS requires an ENCORE chart to toggle from')
        for name, chart in self.charts.items():
            if not isinstance(chart, dict) or not isinstance(chart.get('file'), str):
                raise ValueError(f'Missing chart file for {name}')
            if not isinstance(chart.get('designer', ''), str):
                raise ValueError('Chart designer must be text')
            level = chart.get('level')
            if isinstance(level, bool) or not isinstance(level, (float, int)) or not math.isfinite(level) or not 0 < level <= 100:
                raise ValueError(f'Invalid level for {name}')
            mode = chart.get('bumper_holds', 'reject')
            if mode not in ('reject', 'start', 'both'): raise ValueError('Invalid bumper hold policy')
            convert(self.asset(chart['file']).read_text(encoding='utf-8-sig'), mode)
        return self

    def export(self, destination):
        self.validate()
        assets = {'data.toml', self.metadata['audio']}
        if self.metadata.get('jacket'): assets.add(self.metadata['jacket'])
        assets.update(c['file'] for c in self.charts.values())
        destination = Path(destination)
        if destination.exists(): raise FileExistsError(destination)
        with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
            staged = Path(temporary) / 'package.vsc'
            with zipfile.ZipFile(staged, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
                for name in sorted(assets):
                    if name == 'data.toml': archive.writestr(name, metadata_text(self.metadata))
                    else: archive.write(self.asset(name), name)
            os.link(staged, destination)

    def install_library(self, library, replace=False):
        self.validate()
        library = Path(library)
        library.mkdir(parents=True, exist_ok=True)
        target = library / self.metadata['id']
        if target.is_symlink(): raise ValueError('Library target must not be a symlink')
        if target.exists() and not replace: raise FileExistsError(target)
        with tempfile.TemporaryDirectory(dir=library) as temporary:
            staged = Path(temporary) / 'song'
            staged.mkdir()
            assets = {'data.toml', self.metadata['audio']}
            if self.metadata.get('jacket'): assets.add(self.metadata['jacket'])
            assets.update(c['file'] for c in self.charts.values())
            for name in assets:
                source = self.asset(name)
                destination = staged / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            write_metadata(staged / 'data.toml', self.metadata)
            old = library / ('.old-' + self.metadata['id'])
            if old.exists() or old.is_symlink(): raise ValueError('Previous library update needs recovery')
            if target.exists(): target.rename(old)
            try: staged.rename(target)
            except BaseException:
                if old.exists(): old.rename(target)
                raise
            if old.exists(): shutil.rmtree(old)
        return target


def delete_library_song(library, ident):
    """Remove one local package; installed game assets and ID assignments stay intact."""
    library = Path(library).resolve()
    if not isinstance(ident, str) or not re.fullmatch('[a-z][a-z0-9_]{0,63}', ident):
        raise ValueError('Invalid song ID')
    target = library / ident
    if target.is_symlink() or not target.is_dir() or target.resolve().parent != library:
        raise ValueError('Unknown or unsafe library song')
    # Rename before removal so the package disappears from library scans atomically.
    with tempfile.TemporaryDirectory(prefix='.delete-', dir=library) as temporary:
        staged = Path(temporary) / ident
        target.rename(staged)
        try:
            shutil.rmtree(staged)
        except BaseException:
            if staged.exists(): staged.rename(target)
            raise
