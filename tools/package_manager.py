#!/usr/bin/env python3
"""Archive the native PyInstaller executable with usage instructions and a checksum."""
import argparse
import hashlib
from pathlib import Path
import shutil
import tarfile
import tempfile
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', required=True, choices=('linux-x64', 'windows-x64'))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    name = 'VividstasisSongManager'
    executable = root / 'dist' / (name + ('.exe' if args.platform == 'windows-x64' else ''))
    if not executable.is_file(): parser.error(f'Missing built executable: {executable}')
    release = root / 'release'; release.mkdir(exist_ok=True)
    label = name + '-' + args.platform
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary) / label; folder.mkdir()
        shutil.copy2(executable, folder / executable.name)
        shutil.copy2(root / 'docs' / 'EXECUTABLE_BUILDS.md', folder / 'README.md')
        digest = hashlib.sha256(executable.read_bytes()).hexdigest()
        (folder / 'SHA256SUMS').write_text(f'{digest}  {executable.name}\n', encoding='utf-8')
        if args.platform == 'windows-x64':
            output = release / (label + '.zip')
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
                for path in folder.iterdir(): archive.write(path, path.relative_to(folder.parent))
        else:
            # tar preserves the executable permission, unlike raw artifact upload.
            (folder / executable.name).chmod(0o755)
            output = release / (label + '.tar.gz')
            with tarfile.open(output, 'w:gz') as archive: archive.add(folder, arcname=label)
    print(output)


if __name__ == '__main__':
    main()
