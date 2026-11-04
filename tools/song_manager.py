#!/usr/bin/env python3
"""PySide6 desktop editor and transactional installer for custom song packages."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import threading
import traceback
import unicodedata

try:
    from PySide6.QtCore import Qt, QThread, Signal, QUrl, QSize
    from PySide6.QtGui import QCloseEvent, QDesktopServices, QPixmap, QIcon
    from PySide6.QtWidgets import (
        QApplication, QAbstractItemView, QComboBox, QDialog, QDialogButtonBox,
        QDoubleSpinBox, QFileDialog, QFormLayout, QHBoxLayout, QHeaderView,
        QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
        QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QSplitter,
        QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
    )
except ImportError as exc:
    raise SystemExit(
        'PySide6 is required for the desktop manager. Install the dependencies:\n'
        '  python -m pip install -r requirements.txt\n'
        'Then run: python tools/song_manager.py\n'
        f'Dependency error: {exc}'
    ) from exc

from osu_to_vsb import detect_key_count
from osz_import import OszArchive
from custom_songs import PACKAGE_DIFFICULTIES, Package, write_metadata, delete_library_song
from manager_backend import Manager, Cancelled

PROJECT = Path(__file__).resolve().parents[1]
AUDIO_FILTER = 'Audio (*.ogg *.mp3 *.wav *.flac *.m4a *.aac *.opus);;All files (*)'
IMAGE_FILTER = 'Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff);;All files (*)'
CHART_FILTER = 'osu! beatmaps (*.osu);;All files (*)'


def identifier(title: str) -> str:
    text = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode().lower()
    text = re.sub('[^a-z0-9_]+', '_', text).strip('_')
    if not text or not text[0].isalpha():
        text = 'song_' + text
    return text[:64]


def unique_identifier(title: str, reserved) -> str:
    base = identifier(title)
    candidate, index = base, 2
    while candidate in reserved:
        suffix = f'_{index}'
        candidate = base[:64 - len(suffix)] + suffix
        index += 1
    return candidate


def osu_metadata(path: Path) -> dict:
    result, section = {}, ''
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
        elif section in ('Metadata', 'General') and ':' in line:
            key, value = line.split(':', 1)
            result[key.strip()] = value.strip()
    return result


class Operation(QThread):
    progress = Signal(str)
    succeeded = Signal(object)
    failed = Signal(str)
    cancelled = Signal(str)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.cancel_requested = threading.Event()

    def run(self):
        try:
            result = self.task(self.progress.emit, self.cancel_requested.is_set)
        except Cancelled as exc:
            self.cancelled.emit(str(exc))
        except Exception:
            self.failed.emit(traceback.format_exc())
        else:
            self.succeeded.emit(result)


class SetupDialog(QDialog):
    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Set up the playable game copy')
        self.resize(700, 260)
        layout = QVBoxLayout(self)
        explanation = QLabel('Choose the original game and a separate new destination. '
                             'Setup copies the complete game and preserves a clean archive for rebuilds.')
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        form = QFormLayout()
        self.original = QLineEdit(str(state.get('original', '')))
        self.destination = QLineEdit(str(state.get('destination', '')))
        self.cli = QLineEdit(str(state.get('cli') or PROJECT / 'UndertaleMTCLI'))
        for label, edit, is_cli in [('Original game folder', self.original, False),
                                    ('Playable copy folder', self.destination, False),
                                    ('UndertaleModTool CLI', self.cli, True)]:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(edit)
            browse = QPushButton('Browse…')
            browse.clicked.connect(lambda checked=False, e=edit, c=is_cli: self._browse(e, c))
            row_layout.addWidget(browse)
            form.addRow(label, row)
        layout.addLayout(form)
        note = QLabel('The destination must be new or empty. The CLI field accepts its executable or folder.')
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Create playable copy')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self, edit, cli):
        if cli:
            filename, _ = QFileDialog.getOpenFileName(self, 'Choose UndertaleModCli', edit.text(), 'All files (*)')
        else:
            filename = QFileDialog.getExistingDirectory(self, 'Choose folder', edit.text())
        if filename:
            edit.setText(filename)

    def accept(self):
        if not all(e.text().strip() for e in (self.original, self.destination, self.cli)):
            QMessageBox.information(self, 'Setup', 'Choose all three paths first.')
            return
        super().accept()


class ReviewDialog(QDialog):
    def __init__(self, selected, installed, titles, destination, review, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Review the next build')
        self.resize(720, 520)
        layout = QVBoxLayout(self)
        additions = sorted(set(selected) - set(installed))
        removals = sorted(set(installed) - set(selected))
        lines = [f'Destination: {destination}', f'Songs in the next build: {len(selected)}']
        if additions:
            lines += ['Add: ' + ', '.join(titles.get(i, i) for i in additions)]
        if removals:
            lines += ['Remove from game: ' + ', '.join(titles.get(i, i) for i in removals)]
        if isinstance(review, dict) and review.get('changed'):
            lines += ['Update: ' + ', '.join(titles.get(i, i) for i in review['changed'])]
        if selected:
            lines += ['Rebuild selected songs from their current library contents.']
        else:
            lines += ['Restore stock game data and remove manager-owned custom charts.']
        summary = QLabel('\n'.join(lines))
        summary.setWordWrap(True)
        summary.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(summary)
        details = QPlainTextEdit()
        details.setReadOnly(True)
        details.setPlainText(json.dumps(review, indent=2, ensure_ascii=False, default=str) if not isinstance(review, str) else review)
        layout.addWidget(details)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Build and install')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class OszImportDialog(QDialog):
    """Choose archive assets and chart assignments before creating a library package."""
    def __init__(self, archive, reserved_ids, parent=None):
        super().__init__(parent)
        self.archive = archive
        self.reserved_ids = set(reserved_ids)
        self._title_edited = False
        self._artist_edited = False
        self._id_edited = False
        self._audio_edited = False
        self.setWindowTitle('Import an osu! archive')
        self.resize(1100, 700)
        layout = QVBoxLayout(self)
        explanation = QLabel('Choose the audio track and up to five charts, one per difficulty, and set their levels. '
                             'Unassigned charts will be skipped. Each difficulty can be assigned once.')
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        form = QFormLayout()
        self.audio_choice = QComboBox()
        self.audio_choice.addItem('Choose audio…', None)
        for name in archive.audio:
            self.audio_choice.addItem(name, name)
        self.jacket_choice = QComboBox()
        self.jacket_choice.addItem('Generic game jacket', None)
        for name in archive.images:
            self.jacket_choice.addItem(name, name)
        self.import_title = QLineEdit()
        self.import_artist = QLineEdit()
        self.import_id = QLineEdit()
        self.import_title.setPlaceholderText('Title from the first assigned chart')
        self.import_artist.setPlaceholderText('Artist from the first assigned chart')
        self.import_id.setPlaceholderText('A unique library ID is suggested automatically')
        form.addRow('Audio track', self.audio_choice)
        form.addRow('Cover image (optional)', self.jacket_choice)
        form.addRow('Title', self.import_title)
        form.addRow('Artist', self.import_artist)
        form.addRow('Package ID', self.import_id)
        layout.addLayout(form)
        self.table = QTableWidget(len(archive.charts), 6)
        self.table.setHorizontalHeaderLabels(['Chart / version', 'Type', 'Referenced audio', 'Import as', 'Level', 'Bumper holds'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(200)
        for row, chart in enumerate(archive.charts):
            for column, text in ((0, f"{chart['version']}\n{chart['file']}"), (1, f"{chart['keys']}K"), (2, chart.get('audio', ''))):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, column, item)
            slot = QComboBox()
            slot.addItem('Skip', None)
            for name in PACKAGE_DIFFICULTIES:
                slot.addItem(name.upper(), name)
            slot.currentIndexChanged.connect(self._suggest_metadata)
            self.table.setCellWidget(row, 3, slot)
            level = QDoubleSpinBox()
            level.setRange(0.1, 100)
            level.setDecimals(2)
            level.setSingleStep(0.5)
            level.setValue(4)
            self.table.setCellWidget(row, 4, level)
            bumper = QComboBox()
            bumper.addItem('Reject bumper holds', 'reject')
            bumper.addItem('Start tap', 'start')
            bumper.addItem('Start and end taps', 'both')
            bumper.setEnabled(chart['keys'] == 6)
            if chart['keys'] == 4:
                bumper.setToolTip('4K uses normal lanes only; bumper settings are ignored.')
            self.table.setCellWidget(row, 5, bumper)
        layout.addWidget(self.table, 1)
        if archive.rejected:
            layout.addWidget(QLabel('Unsupported charts — these cannot be imported:'))
            rejected = QPlainTextEdit()
            rejected.setReadOnly(True)
            rejected.setPlainText('\n'.join(f'{name}: {error}' for name, error in archive.rejected))
            rejected.setMaximumHeight(110)
            layout.addWidget(rejected)
        self.import_title.textEdited.connect(self._edit_title)
        self.import_artist.textEdited.connect(lambda text: setattr(self, '_artist_edited', bool(text)))
        self.import_id.textEdited.connect(lambda text: setattr(self, '_id_edited', bool(text)))
        self.audio_choice.activated.connect(lambda index: setattr(self, '_audio_edited', True))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Import to library')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _edit_title(self, text):
        self._title_edited = bool(text)
        if not self._id_edited:
            self.import_id.setText(unique_identifier(text, self.reserved_ids) if text else '')

    def _suggest_metadata(self, *args):
        selected = [chart for row, chart in enumerate(self.archive.charts)
                    if self.table.cellWidget(row, 3).currentData() is not None]
        if not selected:
            return
        first = selected[0]
        if not self._title_edited:
            self.import_title.setText(first.get('title') or Path(first['file']).stem)
        if not self._artist_edited:
            self.import_artist.setText(first.get('artist') or 'Unknown')
        if not self._id_edited:
            self.import_id.setText(unique_identifier(self.import_title.text(), self.reserved_ids))
        if not self._audio_edited:
            suggested = self.audio_choice.findData(first.get('audio'))
            self.audio_choice.setCurrentIndex(max(0, suggested))

    def values(self):
        audio = self.audio_choice.currentData()
        if audio is None:
            raise ValueError('Choose an audio track from the archive.')
        assignments = {}
        for row, chart in enumerate(self.archive.charts):
            slot = self.table.cellWidget(row, 3).currentData()
            if slot is None:
                continue
            if slot in assignments:
                raise ValueError(f'{slot.upper()} is assigned more than once. Assign each chart to a different slot or choose Skip.')
            assignments[slot] = dict(file=chart['file'], level=self.table.cellWidget(row, 4).value(),
                                     bumper_holds=self.table.cellWidget(row, 5).currentData())
        if not assignments:
            raise ValueError('Assign at least one supported chart to a difficulty slot.')
        ident = self.import_id.text().strip()
        if not re.fullmatch('[a-z][a-z0-9_]{0,63}', ident):
            raise ValueError('Use a lowercase package ID beginning with a letter, with letters, digits or underscores (64 characters maximum).')
        title, artist = self.import_title.text().strip(), self.import_artist.text().strip()
        if not title or not artist:
            raise ValueError('Provide a title and artist for the imported song.')
        return dict(audio=audio, assignments=assignments, ident=ident, title=title,
                    artist=artist, jacket=self.jacket_choice.currentData())

    def accept(self):
        try:
            self.values()
        except ValueError as exc:
            QMessageBox.information(self, 'Import settings', str(exc))
            return
        super().accept()


class SongManagerWindow(QMainWindow):
    def __init__(self, workspace: Path):
        super().__init__()
        self.workspace = workspace.resolve()
        self.library = self.workspace / 'library'
        self.library.mkdir(parents=True, exist_ok=True)
        self.manager = Manager(self.workspace)
        self._worker = None
        self._result = None
        self._failure = None
        self._cancelled = None
        self._success = None
        self._loading = False
        self._dirty = False
        self._current_id = None
        self._id_was_edited = False
        self._metadata = {}
        self._packages = {}
        self._fingerprints = {}
        self._selected_ids = set(self.manager.state.get('selected_ids', []))
        self.setWindowTitle('Vividstasis Custom Song Manager')
        self.resize(1180, 840)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        toolbar = QHBoxLayout()
        self.setup_button = QPushButton('Set up game copy…')
        self.review_button = QPushButton('Review & build…')
        self.rollback_button = QPushButton('Restore previous build')
        self.clean_button = QPushButton('RESTORE (clean game)')
        self.launch_button = QPushButton('Launch game')
        self.open_button = QPushButton('Open game folder')
        for button in (self.setup_button, self.review_button, self.rollback_button, self.clean_button, self.launch_button, self.open_button):
            toolbar.addWidget(button)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        splitter = QSplitter()
        layout.addWidget(splitter, 1)
        library_panel = QWidget()
        library_layout = QVBoxLayout(library_panel)
        library_layout.addWidget(QLabel('Library — checked songs are included in the next build'))
        self.list = QListWidget()
        self.list.setIconSize(QSize(64, 64))
        self.list.setWordWrap(True)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        library_layout.addWidget(self.list, 1)
        library_buttons = QHBoxLayout()
        self.new_button = QPushButton('New song')
        self.import_button = QPushButton('Import .vsc…')
        self.osz_button = QPushButton('Auto Import osz…')
        self.export_button = QPushButton('Export .vsc…')
        self.delete_button = QPushButton('Delete song…')
        for button in (self.new_button, self.import_button, self.export_button, self.delete_button):
            library_buttons.addWidget(button)
        library_layout.addLayout(library_buttons)
        library_layout.addWidget(self.osz_button)
        splitter.addWidget(library_panel)
        self.editor = QWidget()
        editor_layout = QVBoxLayout(self.editor)
        form = QFormLayout()
        self.song_id = QLineEdit()
        self.song_id.setPlaceholderText('lowercase_letters_digits_and_underscores')
        self.title = QLineEdit()
        self.artist = QLineEdit()
        self.jacket_artist = QLineEdit()
        form.addRow('Package ID', self.song_id)
        form.addRow('Title', self.title)
        form.addRow('Artist', self.artist)
        self.audio = QLineEdit()
        self.jacket = QLineEdit()
        form.addRow('Audio', self._asset_picker(self.audio, AUDIO_FILTER, 'Choose song audio'))
        form.addRow('Cover (optional)', self._asset_picker(self.jacket, IMAGE_FILTER, 'Choose cover image'))
        form.addRow('Cover artist', self.jacket_artist)
        editor_layout.addLayout(form)
        self.cover_preview = QLabel('No cover selected — generic game jacket will be used')
        self.cover_preview.setMinimumHeight(80)
        editor_layout.addWidget(self.cover_preview)
        editor_layout.addWidget(QLabel('4K / 6K osu!mania charts — detected automatically'))
        difficulty_help = QLabel('APOTHEOSIS is directly selectable for custom songs and can be supplied on its own.')
        difficulty_help.setWordWrap(True)
        editor_layout.addWidget(difficulty_help)
        self.charts = QTableWidget(0, 7)
        self.charts.setHorizontalHeaderLabels(['Difficulty', 'Chart file', 'Browse', 'Level', 'Designer', 'Bumper holds', 'Type'])
        self.charts.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.charts.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.charts.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.charts.setMinimumHeight(210)
        editor_layout.addWidget(self.charts, 1)
        chart_buttons = QHBoxLayout()
        self.add_chart_button = QPushButton('Add chart files…')
        self.remove_chart_button = QPushButton('Remove selected chart')
        chart_buttons.addWidget(self.add_chart_button)
        chart_buttons.addWidget(self.remove_chart_button)
        chart_buttons.addStretch()
        editor_layout.addLayout(chart_buttons)
        self.save_button = QPushButton('Save song to library')
        editor_layout.addWidget(self.save_button)
        splitter.addWidget(self.editor)
        splitter.setSizes([360, 800])
        progress_layout = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.cancel_button = QPushButton('Cancel operation')
        self.cancel_button.setEnabled(False)
        progress_layout.addWidget(self.progress, 1)
        progress_layout.addWidget(self.cancel_button)
        layout.addLayout(progress_layout)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(3000)
        self.log.setMaximumHeight(150)
        self.log.setPlaceholderText('Build progress and diagnostics appear here.')
        layout.addWidget(self.log)
        self.setup_button.clicked.connect(self._setup)
        self.review_button.clicked.connect(self._review)
        self.rollback_button.clicked.connect(self._rollback)
        self.clean_button.clicked.connect(self._restore_clean)
        self.launch_button.clicked.connect(self._launch)
        self.open_button.clicked.connect(self._open_game)
        self.new_button.clicked.connect(self._new)
        self.import_button.clicked.connect(self._import)
        self.osz_button.clicked.connect(self._import_osz)
        self.export_button.clicked.connect(self._export)
        self.delete_button.clicked.connect(self._delete_song)
        self.save_button.clicked.connect(self._save)
        self.add_chart_button.clicked.connect(self._add_charts)
        self.remove_chart_button.clicked.connect(self._remove_chart)
        self.cancel_button.clicked.connect(self._cancel)
        self.list.itemChanged.connect(self._checked)
        self.list.currentItemChanged.connect(self._selected)
        for edit in (self.song_id, self.title, self.artist, self.audio, self.jacket, self.jacket_artist):
            edit.textChanged.connect(self._mark_dirty)
        self.title.textEdited.connect(self._suggest_id)
        self.song_id.textEdited.connect(self._manual_id)
        self.jacket.textChanged.connect(self._preview_cover)
        self._reload_library()
        self._new(prompt=False)
        self._update_status()

    def _asset_picker(self, edit, file_filter, title):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edit)
        button = QPushButton('Browse…')
        button.clicked.connect(lambda: self._choose_asset(edit, file_filter, title))
        layout.addWidget(button)
        return row

    def _choose_asset(self, edit, file_filter, title):
        filename, _ = QFileDialog.getOpenFileName(self, title, edit.text(), file_filter)
        if filename:
            edit.setText(filename)

    def _preview_cover(self):
        filename = self.jacket.text().strip()
        pixmap = QPixmap(filename) if filename else QPixmap()
        if not pixmap.isNull():
            self.cover_preview.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.cover_preview.setText('Cover selected' if filename else 'No cover selected — generic game jacket will be used')

    def _mark_dirty(self, *args):
        if not self._loading:
            self._dirty = True
            self.save_button.setText('Save song to library *')

    def _manual_id(self, text):
        self._id_was_edited = bool(text)

    def _suggest_id(self, text):
        if self._current_id is None and not self._id_was_edited:
            self.song_id.setText(identifier(text) if text else '')

    def _update_status(self, message=None):
        configured = bool(self.manager.state.get('configured') or self.manager.state.get('destination'))
        installed = self.manager.state.get('installed_ids', [])
        destination = self.manager.state.get('destination', '')
        self.status.setText(message or (f'{len(self._selected_ids)} selected · {len(installed)} installed · {destination}' if configured else 'Set up a game copy to build and play selected library songs.'))
        busy = self._worker is not None
        self.setup_button.setText('Game copy details…' if configured else 'Set up game copy…')
        for button in (self.setup_button, self.new_button, self.import_button, self.osz_button, self.export_button,
                       self.save_button, self.add_chart_button, self.remove_chart_button):
            button.setEnabled(not busy)
        self.delete_button.setEnabled(not busy and self._current_id in self._packages)
        self.editor.setEnabled(not busy)
        self.list.setEnabled(not busy)
        self.review_button.setEnabled(configured and not busy)
        self.rollback_button.setEnabled(configured and not busy and bool(self.manager.state.get('previous_installation')))
        self.clean_button.setEnabled(configured and not busy)
        self.launch_button.setEnabled(configured and not busy)
        self.open_button.setEnabled(configured)
        self.cancel_button.setEnabled(busy)

    def _error(self, title, error):
        self.log.appendPlainText(str(error))
        QMessageBox.critical(self, title, str(error))

    def _decorate_item(self, item, root, data):
        package_id = data['id']
        selected = package_id in self._selected_ids
        installed = package_id in self.manager.state.get('installed_ids', [])
        old = self.manager.state.get('package_fingerprints', {}).get(package_id)
        changed = installed and old != self._fingerprints.get(package_id)
        if installed and not selected:
            state = 'Installed · pending removal'
        elif installed and changed:
            state = 'Installed · edited' + (' · pending update' if selected else '')
        elif installed:
            state = 'Installed'
        else:
            state = 'Pending installation' if selected else 'Library only'
        difficulties = ' / '.join(d.upper() for d in PACKAGE_DIFFICULTIES if d in data.get('charts', {}))
        item.setText(f"{data['title']}\n{data['artist']} · {package_id}\n{difficulties}\n{state}")
        item.setToolTip(f"{state}\n{root}")
        pixmap = QPixmap(str(root / data['jacket'])) if data.get('jacket') else QPixmap()
        item.setIcon(QIcon(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)) if not pixmap.isNull() else QIcon.fromTheme('audio-x-generic'))

    def _reload_library(self, focus=None):
        self._loading = True
        self.list.clear()
        self._packages = {}
        self._fingerprints = {}
        for folder in sorted(self.library.iterdir()):
            if not folder.is_dir() or folder.name.startswith('.'):
                continue
            try:
                with Package(folder) as package:
                    data = copy.deepcopy(package.metadata)
                    fingerprint = self.manager.fingerprint(package)
                package_id = data['id']
                if folder.name != package_id:
                    raise ValueError('Library folder name must match the package ID; import this folder as a package to normalize it.')
                self._packages[package_id] = (folder, data)
                self._fingerprints[package_id] = fingerprint
                item = QListWidgetItem()
                self._decorate_item(item, folder, data)
                item.setData(Qt.ItemDataRole.UserRole, package_id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if package_id in self._selected_ids else Qt.CheckState.Unchecked)
            except Exception as exc:
                item = QListWidgetItem(f'Invalid package: {folder.name}')
                item.setToolTip(str(exc))
                item.setData(Qt.ItemDataRole.UserRole, folder.name)
                item.setFlags((item.flags() & ~Qt.ItemFlag.ItemIsSelectable) | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked if folder.name in self._selected_ids else Qt.CheckState.Unchecked)
                self.log.appendPlainText(f'Cannot load {folder.name}: {exc}')
            self.list.addItem(item)
            if focus and item.data(Qt.ItemDataRole.UserRole) == focus:
                self.list.setCurrentItem(item)
        shown = {self.list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.list.count())}
        for package_id in sorted(set(self.manager.state.get('installed_ids', [])) - shown):
            pending = 'Reimport or uncheck before rebuilding' if package_id in self._selected_ids else 'Pending removal on the next build'
            item = QListWidgetItem(f'{package_id}\nInstalled · library package missing\n{pending}')
            item.setData(Qt.ItemDataRole.UserRole, package_id)
            item.setFlags((item.flags() & ~Qt.ItemFlag.ItemIsSelectable) | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if package_id in self._selected_ids else Qt.CheckState.Unchecked)
            item.setToolTip('Reimport this package to rebuild it, or leave it unchecked to remove its installed game files on the next build.')
            self.list.addItem(item)
        self._loading = False
        self._update_status()

    def _persist_selection(self):
        self.manager.select(sorted(self._selected_ids))

    def _checked(self, item):
        if self._loading:
            return
        package_id = item.data(Qt.ItemDataRole.UserRole)
        if not package_id:
            return
        old = set(self._selected_ids)
        if item.checkState() == Qt.CheckState.Checked:
            self._selected_ids.add(package_id)
        else:
            self._selected_ids.discard(package_id)
        try:
            self._persist_selection()
        except Exception as exc:
            self._selected_ids = old
            self._loading = True
            item.setCheckState(Qt.CheckState.Checked if package_id in old else Qt.CheckState.Unchecked)
            self._loading = False
            self._error('Cannot save selection', exc)
        if package_id in self._packages:
            root, data = self._packages[package_id]
            self._loading = True
            self._decorate_item(item, root, data)
            self._loading = False
        self._update_status()

    def _prompt_unsaved(self):
        if not self._dirty:
            return True
        reply = QMessageBox.question(self, 'Unsaved song', 'Save the current song before continuing?',
                                     QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                                     QMessageBox.StandardButton.Save)
        if reply == QMessageBox.StandardButton.Cancel:
            return False
        if reply == QMessageBox.StandardButton.Save:
            return self._save_package(refresh=False)
        if self._current_id:
            self._load_editor(self._current_id)
        else:
            self._new(prompt=False)
        return True

    def _selected(self, current, previous):
        if self._loading or current is None:
            return
        package_id = current.data(Qt.ItemDataRole.UserRole)
        if not package_id or package_id not in self._packages:
            return
        if not self._prompt_unsaved():
            self._loading = True
            self.list.setCurrentItem(previous)
            self._loading = False
            return
        self._load_editor(package_id)

    def _load_editor(self, package_id):
        root, metadata = self._packages[package_id]
        self._loading = True
        self._current_id = package_id
        self._metadata = copy.deepcopy(metadata)
        self.song_id.setReadOnly(True)
        self.song_id.setText(package_id)
        self.title.setText(metadata['title'])
        self.artist.setText(metadata['artist'])
        self.jacket_artist.setText(str(metadata.get('jacket_artist') or ''))
        self.audio.setText(str(root / metadata['audio']))
        self.jacket.setText(str(root / metadata['jacket']) if metadata.get('jacket') else '')
        self.charts.setRowCount(0)
        for difficulty in PACKAGE_DIFFICULTIES:
            if difficulty in metadata['charts']:
                chart = metadata['charts'][difficulty]
                self._chart_row(difficulty, str(root / chart['file']), chart.get('level', 4), chart.get('designer', ''), chart.get('bumper_holds', 'reject'))
        self._loading = False
        self._dirty = False
        self.save_button.setText('Save song to library')
        self._preview_cover()
        self._update_status()

    def _new(self, checked=False, prompt=True):
        if prompt and not self._prompt_unsaved():
            return
        if prompt:
            self._reload_library()
        self._loading = True
        self.list.clearSelection()
        self.list.setCurrentItem(None)
        self._current_id = None
        self._id_was_edited = False
        self._metadata = {}
        self.song_id.setReadOnly(False)
        for edit in (self.song_id, self.title, self.artist, self.audio, self.jacket, self.jacket_artist):
            edit.clear()
        self.charts.setRowCount(0)
        self._loading = False
        self._dirty = False
        self.save_button.setText('Save song to library')
        self._preview_cover()
        self._update_status()

    def _chart_row(self, difficulty, path='', level=4, designer='', bumper='reject'):
        row = self.charts.rowCount()
        self.charts.insertRow(row)
        difficulty_box = QComboBox()
        difficulty_box.addItems([d.upper() for d in PACKAGE_DIFFICULTIES])
        difficulty_box.setCurrentIndex(PACKAGE_DIFFICULTIES.index(difficulty))
        source = QLineEdit(path)
        browse = QPushButton('…')
        browse.clicked.connect(lambda checked=False, e=source: self._choose_asset(e, CHART_FILTER, 'Choose 4K or 6K osu!mania chart'))
        level_box = QDoubleSpinBox()
        level_box.setRange(0.1, 100)
        level_box.setDecimals(2)
        level_box.setSingleStep(0.5)
        level_box.setValue(float(level))
        designer_edit = QLineEdit(designer)
        bumper_box = QComboBox()
        bumper_box.addItem('Reject bumper holds', 'reject')
        bumper_box.addItem('Start tap', 'start')
        bumper_box.addItem('Start and end taps', 'both')
        bumper_box.setCurrentIndex(max(0, bumper_box.findData(bumper)))
        for column, widget in enumerate((difficulty_box, source, browse, level_box, designer_edit, bumper_box)):
            self.charts.setCellWidget(row, column, widget)
        type_label = QLabel()
        self.charts.setCellWidget(row, 6, type_label)
        def update_type():
            try:
                keys = detect_key_count(Path(source.text().strip()).read_text(encoding='utf-8-sig'))
            except (OSError, UnicodeError, ValueError) as exc:
                type_label.setText('Unknown' if not source.text().strip() else 'Invalid')
                type_label.setToolTip(str(exc))
                bumper_box.setEnabled(False)
                bumper_box.setToolTip('Choose a valid 4K or 6K osu!mania chart first.')
            else:
                type_label.setText(f'{keys}K')
                type_label.setToolTip('Detected from the chart’s CircleSize.')
                bumper_box.setEnabled(keys == 6)
                bumper_box.setToolTip('4K uses normal lanes only; bumper settings are ignored.' if keys == 4 else 'How to convert holds on the outer bumper lanes.')
        source.textChanged.connect(update_type)
        update_type()
        difficulty_box.currentIndexChanged.connect(self._mark_dirty)
        source.textChanged.connect(self._mark_dirty)
        level_box.valueChanged.connect(self._mark_dirty)
        designer_edit.textChanged.connect(self._mark_dirty)
        bumper_box.currentIndexChanged.connect(self._mark_dirty)

    def _add_charts(self):
        remaining = [d for d in PACKAGE_DIFFICULTIES if all(self.charts.cellWidget(r, 0).currentText().lower() != d for r in range(self.charts.rowCount()))]
        if not remaining:
            QMessageBox.information(self, 'Charts', 'All five chart slots are already assigned.')
            return
        filenames, _ = QFileDialog.getOpenFileNames(self, 'Choose 4K or 6K osu!mania charts', '', CHART_FILTER)
        if len(filenames) > len(remaining):
            QMessageBox.information(self, 'Charts', f'Choose at most {len(remaining)} more chart files.')
            return
        for filename, difficulty in zip(filenames, remaining):
            try:
                meta = osu_metadata(Path(filename))
            except (OSError, UnicodeError) as exc:
                self._error('Cannot read chart metadata', exc)
                return
            if not self.title.text():
                self.title.setText(meta.get('TitleUnicode') or meta.get('Title', ''))
            if not self.song_id.text():
                self.song_id.setText(identifier(self.title.text()))
            if not self.artist.text():
                self.artist.setText(meta.get('ArtistUnicode') or meta.get('Artist', ''))
            if not self.audio.text() and meta.get('AudioFilename'):
                chart_parent = Path(filename).resolve().parent
                audio_path = (chart_parent / meta['AudioFilename']).resolve()
                if audio_path.is_file() and audio_path.is_relative_to(chart_parent):
                    self.audio.setText(str(audio_path))
            self._chart_row(difficulty, filename, designer=meta.get('Creator', ''))
            self._mark_dirty()

    def _remove_chart(self):
        for row in sorted({index.row() for index in self.charts.selectedIndexes()}, reverse=True):
            self.charts.removeRow(row)
            self._mark_dirty()

    def _save(self):
        self._save_package()

    def _save_package(self, refresh=True):
        package_id = self.song_id.text().strip()
        if not re.fullmatch('[a-z][a-z0-9_]{0,63}', package_id):
            self._error('Cannot save song', 'Use a package ID beginning with a lowercase letter, followed by lowercase letters, digits or underscores (64 characters maximum).')
            return False
        if self._current_id is None and (self.library / package_id).exists():
            self._error('Cannot save song', 'That package ID already exists. Select its library entry to edit it, or choose a different ID.')
            return False
        try:
            is_new = self._current_id is None
            metadata = copy.deepcopy(self._metadata)
            metadata.update(format_version=1, id=package_id, title=self.title.text().strip(), artist=self.artist.text().strip(), jacket_artist=self.jacket_artist.text().strip())
            old_charts = metadata.get('charts', {})
            metadata['charts'] = {}
            # Validate a separate staged copy before replacing a library entry.
            with tempfile.TemporaryDirectory(prefix='.song-edit-', dir=self.workspace) as temporary:
                root = Path(temporary) / 'package'
                root.mkdir()
                def asset(filename, relative):
                    source = Path(filename).expanduser().resolve()
                    if not source.is_file():
                        raise ValueError(f'Choose an existing file: {filename or "(empty path)"}')
                    target = root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    return str(relative.as_posix())
                audio_source = self.audio.text().strip()
                metadata['audio'] = asset(audio_source, Path('assets') / ('audio' + Path(audio_source).suffix.lower()))
                jacket_source = self.jacket.text().strip()
                if jacket_source:
                    metadata['jacket'] = asset(jacket_source, Path('assets') / ('jacket' + Path(jacket_source).suffix.lower()))
                else:
                    metadata.pop('jacket', None)
                for row in range(self.charts.rowCount()):
                    difficulty = self.charts.cellWidget(row, 0).currentText().lower()
                    if difficulty in metadata['charts']:
                        raise ValueError(f'{difficulty.upper()} is assigned more than once.')
                    chart = copy.deepcopy(old_charts.get(difficulty, {}))
                    chart.update(file=asset(self.charts.cellWidget(row, 1).text().strip(), Path('charts') / (difficulty + '.osu')),
                                 level=self.charts.cellWidget(row, 3).value(),
                                 designer=self.charts.cellWidget(row, 4).text().strip(),
                                 bumper_holds=self.charts.cellWidget(row, 5).currentData())
                    metadata['charts'][difficulty] = chart
                write_metadata(root / 'data.toml', metadata)
                with Package(root) as package:
                    package.install_library(self.library, replace=self._current_id is not None)
                    self._fingerprints[package_id] = self.manager.fingerprint(package)
            self._current_id = package_id
            self._metadata = metadata
            if is_new:
                self._selected_ids.add(package_id)
            try:
                self._persist_selection()
            except Exception as exc:
                self._error('Song saved; selection could not be saved', exc)
            self._dirty = False
            self.save_button.setText('Save song to library')
            self._packages[package_id] = (self.library / package_id, copy.deepcopy(metadata))
            if refresh:
                self._reload_library(focus=package_id)
            self._load_editor(package_id)
            self._update_status(f'Saved {metadata["title"]} to the library.')
            return True
        except Exception as exc:
            self._error('Cannot save song', exc)
            return False

    def _import(self):
        if not self._prompt_unsaved():
            return
        if self._current_id:
            self._reload_library(focus=self._current_id)
        filenames, _ = QFileDialog.getOpenFileNames(self, 'Import custom-song packages', '', 'Custom-song packages (*.vsc);;All files (*)')
        imported = []
        for filename in filenames:
            try:
                with Package(filename) as package:
                    package_id = package.metadata['id']
                    replace = (self.library / package_id).exists()
                    if replace and QMessageBox.question(self, 'Update library song', f'Replace the library contents of {package_id}? Its stable game ID will be retained.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                        continue
                    package.install_library(self.library, replace=replace)
                    self._selected_ids.add(package_id)
                    imported.append(package_id)
            except Exception as exc:
                self._error(f'Cannot import {Path(filename).name}', exc)
        if imported:
            try:
                self._persist_selection()
            except Exception as exc:
                self._error('Cannot save selection', exc)
            self._dirty = False
            self._reload_library(focus=imported[-1])
            self._load_editor(imported[-1])

    def _import_osz(self):
        if self._worker is not None or not self._prompt_unsaved():
            return
        if self._current_id:
            self._reload_library(focus=self._current_id)
        filename, _ = QFileDialog.getOpenFileName(self, 'Auto import an osu! archive', '', 'osu! archives (*.osz);;All files (*)')
        if not filename:
            return
        # Archive inspection/extraction can be large, so keep it off the UI thread.
        self._start_operation('Inspecting osu! archive…', lambda progress, cancel: OszArchive(filename),
                              success=self._choose_osz_charts, cancelable=False)

    def _choose_osz_charts(self, archive):
        try:
            with archive:
                reserved = {folder.name for folder in self.library.iterdir()}
                reserved.update(self.manager.state.get('assignments', {}))
                dialog = OszImportDialog(archive, reserved, self)
                while True:
                    if dialog.exec() != QDialog.DialogCode.Accepted:
                        return
                    choices = dialog.values()
                    package_id = choices['ident']
                    replace = (self.library / package_id).exists()
                    if replace:
                        question = f'Replace the existing library package {package_id}? Its stable game ID will be retained. Choose Cancel to use a new package ID.'
                        if QMessageBox.question(self, 'Update library song', question,
                                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                                                QMessageBox.StandardButton.Cancel) != QMessageBox.StandardButton.Yes:
                            continue
                    elif package_id in self.manager.state.get('assignments', {}):
                        question = f'{package_id} was used by a previous library song. Reuse its reserved game identity? Choose Cancel to import with a new ID.'
                        if QMessageBox.question(self, 'Reuse package identity', question,
                                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                                                QMessageBox.StandardButton.Cancel) != QMessageBox.StandardButton.Yes:
                            continue
                    try:
                        # Copy every selected asset before the archive temporary root closes.
                        with tempfile.TemporaryDirectory(prefix='.osz-import-', dir=self.workspace) as temporary:
                            with archive.create_package(Path(temporary) / 'package', **choices) as package:
                                package.install_library(self.library, replace=replace)
                    except Exception as exc:
                        self._error('Cannot import the selected charts', exc)
                        continue  # Keep the user's assignments and metadata for correction.
                    break
            self._selected_ids.add(package_id)
            try:
                self._persist_selection()
            except Exception as exc:
                self._error('Song imported; selection could not be saved', exc)
            self._dirty = False
            self._reload_library(focus=package_id)
            self._load_editor(package_id)
            self._update_status('Archive imported to the library. Review its charts, then build when ready.')
        except Exception as exc:
            self._error('Cannot import osu! archive', exc)

    def _export(self):
        if not self._prompt_unsaved():
            return
        if not self._current_id:
            QMessageBox.information(self, 'Export song', 'Save or select a library song first.')
            return
        self._reload_library(focus=self._current_id)
        filename, _ = QFileDialog.getSaveFileName(self, 'Export custom-song package', self._current_id + '.vsc', 'Custom-song package (*.vsc)')
        if not filename:
            return
        path = Path(filename)
        if path.suffix.lower() != '.vsc':
            path = path.with_suffix('.vsc')
        # Package.export deliberately refuses overwrites; choose a new filename.
        if path.exists():
            self._error('Cannot export package', 'Choose a new filename; the destination already exists.')
            return
        try:
            with Package(self.library / self._current_id) as package:
                package.export(path)
            self._update_status(f'Exported {path.name}.')
        except Exception as exc:
            self._error('Cannot export package', exc)

    def _start_operation(self, label, task, success=None, cancelable=True):
        if self._worker is not None:
            return
        self._result = None
        self._failure = None
        self._cancelled = None
        self._success = success
        self._worker = Operation(task, self)
        self._worker.progress.connect(self._progress_message)
        self._worker.succeeded.connect(self._worker_succeeded)
        self._worker.failed.connect(self._worker_failed)
        self._worker.cancelled.connect(self._worker_cancelled)
        self._worker.finished.connect(self._operation_finished)
        self.log.appendPlainText(label)
        self.progress.setRange(0, 0)
        self._update_status(label)
        self.cancel_button.setEnabled(cancelable)
        self._worker.start()

    def _progress_message(self, message):
        self.log.appendPlainText(message)
        self.status.setText(message)

    def _worker_succeeded(self, result):
        self._result = result

    def _worker_failed(self, error):
        self._failure = error

    def _worker_cancelled(self, message):
        self._cancelled = message

    def _operation_finished(self):
        worker = self._worker
        result, failure, success = self._result, self._failure, self._success
        cancelled = self._cancelled
        self._worker = None
        self._success = None
        worker.deleteLater()
        self.progress.setRange(0, 1)
        self.progress.setValue(0 if failure or cancelled else 1)
        self._selected_ids = set(self.manager.state.get('selected_ids', self._selected_ids))
        self._reload_library(focus=self._current_id)
        self._update_status('Operation failed. See details below.' if failure else None)
        if cancelled:
            self.log.appendPlainText(cancelled)
            self._update_status(cancelled)
        elif failure:
            self._error('Operation did not complete', failure)
        elif success:
            try:
                success(result)
            except Exception as exc:
                self._error('Cannot finish operation', exc)

    def _cancel(self):
        if self._worker:
            self._worker.cancel_requested.set()
            self.cancel_button.setEnabled(False)
            self.status.setText('Cancellation requested. An installation already in progress will finish consistently.')

    def _setup(self):
        if self.manager.state.get('configured'):
            state = self.manager.state
            QMessageBox.information(self, 'Configured game copy',
                f"Original: {state.get('original', '')}\nPlayable copy: {state.get('destination', '')}\nCLI: {state.get('cli', '')}\nManager workspace: {self.workspace}\n\nUse --workspace with another directory to manage a different game copy.")
            return
        dialog = SetupDialog(self.manager.state, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            original, destination, cli = (e.text().strip() for e in (dialog.original, dialog.destination, dialog.cli))
            self._start_operation('Creating the playable game copy…', lambda progress, cancel: self.manager.setup(original, destination, cli), cancelable=False)

    def _review(self):
        if not self._prompt_unsaved():
            return
        if self._current_id:
            self._reload_library(focus=self._current_id)
        selected = sorted(self._selected_ids)
        def ready(review):
            titles = {i: data['title'] for i, (_, data) in self._packages.items()}
            dialog = ReviewDialog(selected, self.manager.state.get('installed_ids', []), titles, self.manager.state.get('destination', ''), review, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._start_operation('Building selected songs…', lambda progress, cancel: self.manager.build(selected, progress=progress, cancel=cancel), success=lambda result: self._update_status('Build installed. Launch the game to check playback and charts.'))
        self._start_operation('Reviewing selected songs…', lambda progress, cancel: self.manager.review(selected), success=ready, cancelable=False)

    def _rollback(self):
        if self._worker is not None:
            return
        if QMessageBox.question(self, 'Restore previous build', 'Restore the previous complete manager build? Library songs and reserved IDs will be retained.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self._start_operation('Restoring the previous build…', lambda progress, cancel: self.manager.rollback(progress=progress), cancelable=False)

    def _restore_clean(self):
        if self._worker is not None:
            return
        message = ('Restore the clean original game archive and remove every manager-installed custom chart? '
                   'Library packages and reserved song IDs will be retained. '
                   'This is separate from restoring the previous custom build.')
        if QMessageBox.question(self, 'Restore clean game', message,
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self._start_operation('Restoring the clean game…',
                                  lambda progress, cancel: self.manager.restore_clean(progress=progress),
                                  success=lambda result: self._update_status('Clean game restored. Library packages were retained.'),
                                  cancelable=False)

    def _delete_song(self):
        if self._worker is not None:
            return
        package_id = self._current_id
        if not package_id or package_id not in self._packages:
            QMessageBox.information(self, 'Delete library song', 'Select a saved library song first.')
            return
        title = self._packages[package_id][1]['title']
        message = (f'Delete "{title}" ({package_id}) from the library? This removes its editable package files. '
                   'An installed copy remains in the game until the next build or clean restore. '
                   'Reserved song IDs will be retained.')
        if self._dirty:
            message += ' Unsaved edits to this song will also be discarded.'
        if QMessageBox.question(self, 'Delete library song', message,
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_library_song(self.library, package_id)
        except Exception as exc:
            self._error('Cannot delete library song', exc)
            return
        self._selected_ids.discard(package_id)
        try:
            self._persist_selection()
        except Exception as exc:
            self._error('Song deleted; selection could not be saved', exc)
        self._dirty = False
        self._current_id = None
        self._new(prompt=False)
        self._reload_library()
        self._update_status('Song deleted from the library. Its installed copy remains until the next build or clean restore.')

    def _launch(self):
        self._start_operation('Checking the game copy and launching…',
                              lambda progress, cancel: self.manager.launch(),
                              success=lambda result: self._update_status('Game launched.'),
                              cancelable=False)

    def _open_game(self):
        destination = self.manager.state.get('destination')
        if destination:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(destination)))

    def closeEvent(self, event: QCloseEvent):
        if self._worker is not None:
            QMessageBox.information(self, 'Operation in progress', 'Wait for the current operation to finish, or request cancellation before closing.')
            event.ignore()
        elif self._prompt_unsaved():
            event.accept()
        else:
            event.ignore()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=PROJECT / '.song-manager', help='Manager state, library, build logs and stable ID assignments')
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    app.setApplicationName('Vividstasis Custom Song Manager')
    try:
        window = SongManagerWindow(args.workspace)
    except Exception as exc:
        QMessageBox.critical(None, 'Cannot open manager workspace', str(exc))
        return 1
    window.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
