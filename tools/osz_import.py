"""Inspect an osu! archive and create a validated custom-song package."""
from pathlib import Path
import shutil
import tempfile
import zipfile
from custom_songs import LIMIT, PACKAGE_DIFFICULTIES, Package, write_metadata
from osu_to_vsb import detect_key_count

AUDIO_EXTENSIONS = {'.mp3', '.ogg', '.wav', '.flac', '.m4a', '.aac', '.opus'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'}


def chart_metadata(text):
    values, section = {}, ''
    for raw in text.lstrip('\ufeff').splitlines():
        line = raw.strip()
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
        elif section in ('Metadata', 'General') and ':' in line:
            key, value = line.split(':', 1)
            values[key.strip()] = value.strip()
    return values


class OszArchive:
    def __init__(self, path):
        self._temporary = tempfile.TemporaryDirectory(prefix='vivid-osz-')
        self.root = Path(self._temporary.name)
        self.audio, self.images, self.charts, self.rejected = [], [], [], []
        try:
            with zipfile.ZipFile(path) as archive:
                names, size = set(), 0
                for info in archive.infolist():
                    name = info.filename
                    parts = name.split('/')
                    normalized = name.casefold()
                    if (normalized in names or any(part in ('.', '..') for part in parts) or name.startswith('/') or '\\' in name or ':' in name
                            or any(part in ('', '.', '..') for part in parts[:-1])
                            or (not info.is_dir() and not parts[-1])):
                        raise ValueError(f'Unsafe or duplicate archive path: {name}')
                    if info.flag_bits & 1 or (info.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ValueError('Encrypted archive entries and symlinks are unsupported')
                    names.add(normalized)
                    size += info.file_size
                    if size > LIMIT: raise ValueError('OSZ archive exceeds 1 GiB uncompressed')
                archive.extractall(self.root)
            for file in sorted(self.root.rglob('*')):
                if not file.is_file(): continue
                name = file.relative_to(self.root).as_posix()
                extension = file.suffix.lower()
                if extension in AUDIO_EXTENSIONS: self.audio.append(name)
                elif extension in IMAGE_EXTENSIONS: self.images.append(name)
                elif extension == '.osu':
                    try:
                        text = file.read_text(encoding='utf-8-sig')
                        keys = detect_key_count(text)
                        data = chart_metadata(text)
                        audio = (file.parent / data.get('AudioFilename', '').replace('\\', '/')).resolve()
                        audio_ref = audio.relative_to(self.root).as_posix() if audio.is_relative_to(self.root) else ''
                        self.charts.append(dict(file=name, keys=keys, title=data.get('Title', file.stem),
                                                artist=data.get('Artist', 'Unknown'), creator=data.get('Creator', ''),
                                                version=data.get('Version', file.stem), audio=audio_ref))
                    except (ValueError, OSError, UnicodeError) as exc:
                        self.rejected.append((name, str(exc)))
            if not self.audio: raise ValueError('No supported audio tracks found in OSZ archive')
            if not self.charts: raise ValueError('No supported 4K or 6K osu!mania charts found in OSZ archive')
        except BaseException:
            self.close()
            raise

    def close(self):
        self._temporary.cleanup()

    def __enter__(self): return self
    def __exit__(self, *args): self.close()

    def create_package(self, destination, audio, assignments, *, ident, title=None, artist=None, jacket=None):
        """Publish only a fully validated package; assignments map difficulty to source and settings."""
        destination = Path(destination)
        if destination.exists(): raise FileExistsError(destination)
        if audio not in self.audio: raise ValueError('Choose an audio track from this archive')
        if not assignments or set(assignments) - set(PACKAGE_DIFFICULTIES):
            raise ValueError('Choose charts and valid difficulty slots')
        known = {chart['file']: chart for chart in self.charts}
        if any(spec.get('file') not in known for spec in assignments.values()):
            raise ValueError('Choose supported charts from this archive')
        if jacket is not None and jacket not in self.images: raise ValueError('Choose a cover from this archive')
        first = known[next(iter(assignments.values()))['file']]
        with tempfile.TemporaryDirectory(prefix='.osz-package-', dir=destination.parent) as temporary:
            stage = Path(temporary)/'package'; stage.mkdir()
            audio_name = 'audio' + Path(audio).suffix.lower()
            shutil.copyfile(self.root/audio, stage/audio_name)
            metadata = dict(format_version=1, id=ident, title=title or first['title'],
                            artist=artist or first['artist'], audio=audio_name, charts={})
            if jacket:
                metadata['jacket'] = 'jacket' + Path(jacket).suffix.lower()
                shutil.copyfile(self.root/jacket, stage/metadata['jacket'])
            (stage/'charts').mkdir()
            for difficulty, spec in assignments.items():
                name = f'charts/{difficulty}.osu'
                shutil.copyfile(self.root/spec['file'], stage/name)
                metadata['charts'][difficulty] = dict(file=name, level=spec.get('level', 4),
                    designer=spec.get('designer', known[spec['file']]['creator']),
                    bumper_holds=spec.get('bumper_holds', 'reject'))
            write_metadata(stage/'data.toml', metadata)
            with Package(stage): pass
            stage.rename(destination)
        return Package(destination)
