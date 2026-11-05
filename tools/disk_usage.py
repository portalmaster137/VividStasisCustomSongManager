"""Read-only storage measurements for the desktop manager."""
import os
from pathlib import Path
import shutil
import stat

from manager_backend import Cancelled


def format_bytes(size):
    value = float(size)
    for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB'):
        if value < 1024 or unit == 'TiB':
            return f'{value:,.0f} {unit}' if unit == 'B' else f'{value:,.2f} {unit}'
        value /= 1024


def measure(path, cancel):
    """Sum logical file sizes without following symbolic links or junctions."""
    size, errors = 0, 0
    pending = [Path(path)]
    while pending:
        if cancel():
            raise Cancelled('Disk space scan cancelled.')
        current = pending.pop()
        try:
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0):
                continue
            if stat.S_ISDIR(info.st_mode):
                with os.scandir(current) as entries:
                    pending.extend(Path(entry.path) for entry in entries)
            else:
                size += info.st_size
        except OSError:
            errors += 1
    return size, errors


def scan_usage(workspace, state, progress, cancel):
    workspace = Path(workspace)
    categories = [('Song library', 'library'), ('Clean backup', 'original'),
                  ('Conversion cache', 'cache'), ('Build files and logs', 'builds'),
                  ('Rollback and transaction files', 'transactions')]
    rows = []
    for label, name in categories:
        path = workspace / name
        progress('Measuring ' + label.lower() + '...')
        size, errors = measure(path, cancel) if path.exists() else (0, 0)
        rows.append((label, str(path), size, errors))
    known = {name for _, name in categories}
    other_size = other_errors = 0
    for path in workspace.iterdir():
        if path.name not in known:
            size, errors = measure(path, cancel)
            other_size += size
            other_errors += errors
    rows.append(('Other workspace files', str(workspace), other_size, other_errors))
    rows.append(('Workspace total', str(workspace), sum(r[2] for r in rows), sum(r[3] for r in rows)))
    paths = [workspace]
    for label, key in [('Original game', 'original'), ('Playable game copy', 'destination')]:
        if state.get(key):
            path = Path(state[key])
            progress('Measuring ' + label.lower() + '...')
            size, errors = measure(path, cancel)
            rows.append((label, str(path), size, errors))
            paths.append(path)
    drives = []
    for path in paths:
        try:
            usage = shutil.disk_usage(path)
            drives.append(f'{path}: {format_bytes(usage.free)} free of {format_bytes(usage.total)}')
        except OSError as exc:
            drives.append(f'{path}: free space unavailable ({exc})')
    return rows, drives
