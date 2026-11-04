"""Install the pinned UndertaleModTool CLI into a manager workspace."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tempfile
import urllib.request
import zipfile
from manager_backend import Cancelled

VERSION = '0.9.2.0'
RELEASE = f'https://github.com/UnderminersTeam/UndertaleModTool/releases/download/{VERSION}'
ASSETS = {'Windows': f'{RELEASE}/UTMT_CLI_v{VERSION}-Windows.zip',
          'Linux': f'{RELEASE}/UTMT_CLI_v{VERSION}-Ubuntu.zip'}
DOWNLOAD_LIMIT = 512 * 1024 * 1024
EXTRACT_LIMIT = 2 * 1024 ** 3


def _cancelled(cancel):
    if cancel and cancel(): raise Cancelled('CLI setup cancelled')


def install_cli(workspace, progress=None, cancel=None):
    progress = progress or (lambda message: None)
    system = platform.system()
    if system not in ASSETS: raise ValueError('Automatic CLI setup supports Windows and Linux; choose a CLI manually on this OS.')
    _cancelled(cancel)
    workspace = Path(workspace).resolve()
    tools = workspace / 'tools'; tools.mkdir(parents=True, exist_ok=True)
    destination = tools / f'UndertaleMTCLI-{VERSION}-{system.lower()}'
    executable_name = 'UndertaleModCli.exe' if system == 'Windows' else 'UndertaleModCli'
    url = ASSETS[system]
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink(): raise ValueError('CLI install directory must not be a symlink')
        try:
            manifest = json.loads((destination/'cli-install.json').read_text())
            executable = destination / executable_name
            if manifest['url'] != url or hashlib.sha256(executable.read_bytes()).hexdigest() != manifest['executable_sha256']:
                raise ValueError('Installed CLI differs from its setup manifest')
        except (OSError, ValueError, KeyError) as exc:
            raise ValueError(f'Existing CLI installation is incomplete or modified: {destination}. Choose a manual CLI or remove this tool directory and retry.') from exc
        progress('Using the existing UndertaleModTool CLI ' + VERSION)
        return executable
    with tempfile.TemporaryDirectory(prefix='.cli-setup-', dir=tools) as temporary:
        temporary = Path(temporary)
        archive_path = temporary/'cli.zip'
        progress(f'Downloading UndertaleModTool CLI {VERSION} for {system}')
        request = urllib.request.Request(url, headers={'User-Agent': 'Vividstasis-Song-Manager'})
        digest = hashlib.sha256(); received = 0
        with urllib.request.urlopen(request, timeout=30) as response, archive_path.open('wb') as output:
            while True:
                _cancelled(cancel)
                chunk = response.read(1024 * 1024)
                if not chunk: break
                received += len(chunk)
                if received > DOWNLOAD_LIMIT: raise ValueError('CLI archive exceeds the download size limit')
                output.write(chunk); digest.update(chunk)
                progress(f'Downloaded {received // (1024 * 1024)} MiB')
        _cancelled(cancel)
        progress('Checking and extracting CLI archive')
        extracted = temporary/'extracted'; extracted.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            size, names = 0, set()
            for info in archive.infolist():
                name = info.filename; parts = name.split('/')
                if (name.casefold() in names or name.startswith('/') or '\\' in name or ':' in name
                        or any(part in ('.', '..') for part in parts)
                        or any(not part for part in parts[:-1]) or not name
                        or (not info.is_dir() and not parts[-1])):
                    raise ValueError(f'Unsafe archive path: {name}')
                if info.flag_bits & 1 or (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('Encrypted entries and symlinks are unsupported')
                names.add(name.casefold()); size += info.file_size
                if size > EXTRACT_LIMIT: raise ValueError('CLI archive exceeds the extraction size limit')
            for info in archive.infolist():
                _cancelled(cancel)
                path = extracted/info.filename
                if info.is_dir(): path.mkdir(parents=True, exist_ok=True); continue
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, path.open('wb') as output:
                    while True:
                        _cancelled(cancel)
                        chunk = source.read(1024 * 1024)
                        if not chunk: break
                        output.write(chunk)
                if system == 'Linux': path.chmod(0o755 if info.external_attr >> 16 & 0o111 else 0o644)
        candidates = list(extracted.rglob(executable_name))
        if len(candidates) != 1: raise ValueError(f'Expected one {executable_name} in the downloaded archive')
        executable = candidates[0]
        if system == 'Linux': executable.chmod(0o755)
        _cancelled(cancel)
        progress('Verifying CLI version')
        try:
            result = subprocess.run([str(executable), '--version'], stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, timeout=30, check=True)
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError('Downloaded CLI could not run on this system. Check its runtime requirements or choose a compatible CLI manually.') from exc
        if VERSION not in result.stdout: raise ValueError('Downloaded CLI reported an unexpected version: ' + result.stdout.strip())
        _cancelled(cancel)
        payload = executable.parent
        manifest = dict(version=VERSION, url=url, archive_sha256=digest.hexdigest(),
                        executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
        (payload/'cli-install.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
        # Publish only after the complete distribution has extracted and verified.
        if destination.exists(): raise ValueError('Another CLI installation completed; retry setup to reuse it')
        payload.rename(destination)
    progress('CLI tool ready')
    return destination/executable_name
