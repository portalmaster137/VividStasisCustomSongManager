"""Offscreen desktop action tests; skipped when the optional Qt dependency is absent."""
import importlib.util
import os
from pathlib import Path
import tempfile
import threading
import time
import zipfile
import unittest
from unittest.mock import patch

HAS_QT = importlib.util.find_spec('PySide6') is not None
if HAS_QT:
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication, QMessageBox, QDialogButtonBox
    from song_manager import SongManagerWindow, OszImportDialog, SetupDialog
    from manager_backend import Cancelled
    from osz_import import OszArchive

CHART = '''osu file format v14
[General]
Mode:3
[Metadata]
Title:Test
Artist:Artist
Creator:Mapper
[Difficulty]
CircleSize:4
[TimingPoints]
0,500,4,2,0,100,1,0
[HitObjects]
64,192,1000,1,0,0:0:0:0:
'''


@unittest.skipUnless(HAS_QT, 'PySide6 is not installed')
class ManagerActions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.window = SongManagerWindow(self.root / 'manager')
        self.audio = self.root / 'audio.ogg'
        self.audio.write_bytes(b'OggS-test-asset')
        self.chart = self.root / 'chart.osu'
        self.chart.write_text(CHART, encoding='utf8')

    def tearDown(self):
        self.window._worker = None
        self.window._dirty = False
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.temporary.cleanup()

    def fill(self):
        self.window.song_id.setText('test_song')
        self.window.title.setText('Test Song')
        self.window.artist.setText('Artist')
        self.window.audio.setText(str(self.audio))

    def test_apotheosis_slot_saves_without_encore(self):
        self.fill()
        self.window._chart_row('apotheosis', str(self.chart))
        slot = self.window.charts.cellWidget(0, 0)
        self.assertEqual(slot.count(), 5)
        self.assertEqual(slot.currentText(), 'APOTHEOSIS')
        self.assertEqual(self.window.charts.cellWidget(0, 6).text(), '4K')
        self.assertTrue(self.window._save_package())
        self.assertEqual(set(self.window._metadata['charts']), {'apotheosis'})
        self.assertTrue((self.window.library / 'test_song' / 'charts' / 'apotheosis.osu').is_file())
        self.assertFalse((self.window.library / 'test_song' / 'charts' / 'encore.osu').exists())
        self.assertIn('APOTHEOSIS', self.window.list.item(0).text())

    def test_delete_removes_only_library_and_leaves_install_pending_removal(self):
        self.fill()
        self.window._chart_row('opening', str(self.chart))
        self.assertTrue(self.window._save_package())
        self.window.manager.state['installed_ids'] = ['test_song']
        game = self.root / 'game'
        game.mkdir()
        (game / 'data.win').write_bytes(b'unchanged-game')
        self.window.manager.state['destination'] = str(game)
        # Model a completed installation on disk. Selection updates reload state
        # under the manager lock, as they would after an actual committed build.
        self.window.manager._save()
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            self.window._delete_song()
        self.assertFalse((self.window.library / 'test_song').exists())
        self.assertNotIn('test_song', self.window._selected_ids)
        self.assertNotIn('test_song', self.window.manager.state['selected_ids'])
        self.assertEqual(self.window.manager.state['installed_ids'], ['test_song'])
        reloaded = type(self.window.manager)(self.window.workspace)
        self.assertEqual(reloaded.state['installed_ids'], ['test_song'])
        self.assertNotIn('test_song', reloaded.state['selected_ids'])
        self.assertEqual((game / 'data.win').read_bytes(), b'unchanged-game')
        self.assertTrue(any('Pending removal' in self.window.list.item(i).text()
                            for i in range(self.window.list.count())))

    def archive_fixture(self):
        archive = self.root / 'song.osz'
        source = CHART.replace('Mode:3', 'AudioFilename: audio.ogg\nMode:3')
        with zipfile.ZipFile(archive, 'w') as output:
            output.writestr('audio.ogg', b'OggS-test-asset')
            output.writestr('other.ogg', b'OggS-other-test-asset')
            output.writestr('chart.osu', source)
            output.writestr('other.osu', source.replace('CircleSize:4', 'CircleSize:6'))
            output.writestr('incompatible.osu', source.replace('Mode:3', 'Mode:0'))
        return archive

    def test_osz_dialog_requires_assignments_and_audio_rejects_duplicate_slots(self):
        with OszArchive(self.archive_fixture()) as archive:
            dialog = OszImportDialog(archive, {'test'}, self.window)
            self.assertEqual(len(archive.charts), 2)
            self.assertEqual(len(archive.rejected), 1)
            self.assertIsNone(dialog.audio_choice.currentData())
            with self.assertRaises(ValueError):
                dialog.values()
            dialog.table.cellWidget(0, 3).setCurrentIndex(1)  # OPENING
            values = dialog.values()
            self.assertEqual(values['audio'], 'audio.ogg')
            self.assertEqual(values['ident'], 'test_2')
            self.assertEqual(values['assignments']['opening']['level'], 4)
            dialog.audio_choice.setCurrentIndex(0)
            with self.assertRaisesRegex(ValueError, 'audio'):
                dialog.values()
            dialog.audio_choice.setCurrentIndex(dialog.audio_choice.findData('other.ogg'))
            dialog.table.cellWidget(1, 3).setCurrentIndex(1)
            with self.assertRaisesRegex(ValueError, 'more than once'):
                dialog.values()
            dialog.deleteLater()

    def test_osz_import_copies_assets_before_archive_closes(self):
        archive = OszArchive(self.archive_fixture())
        archive_root = archive.root
        def choose(dialog):
            dialog.table.cellWidget(0, 3).setCurrentIndex(1)
            return dialog.DialogCode.Accepted
        with patch.object(OszImportDialog, 'exec', choose):
            self.window._choose_osz_charts(archive)
        self.assertFalse(archive_root.exists())
        package = self.window.library / 'test'
        self.assertTrue((package / 'audio.ogg').is_file())
        self.assertTrue((package / 'charts' / 'opening.osu').is_file())
        self.assertIn('test', self.window.manager.state['selected_ids'])
        self.assertEqual(self.window._current_id, 'test')

    def test_osz_validation_retry_preserves_chart_choices(self):
        archive_file = self.root / 'hold.osz'
        source = CHART.replace('Mode:3', 'AudioFilename: audio.ogg\nMode:3')
        source = source.replace('CircleSize:4', 'CircleSize:6').replace('64,192,1000,1,0,0:0:0:0:', '0,192,1000,128,0,1500:0:0:0:0:')
        with zipfile.ZipFile(archive_file, 'w') as output:
            output.writestr('audio.ogg', b'OggS-test-asset')
            output.writestr('chart.osu', source)
        visits = []
        def choose(dialog):
            visits.append(1)
            if len(visits) == 1:
                dialog.table.cellWidget(0, 3).setCurrentIndex(1)
            else:
                self.assertEqual(len(visits), 2)
                self.assertEqual(dialog.table.cellWidget(0, 3).currentData(), 'opening')
                self.assertFalse((self.window.library / 'test').exists())
                dialog.table.cellWidget(0, 5).setCurrentIndex(2)  # both bumper taps
            return dialog.DialogCode.Accepted
        with patch.object(OszImportDialog, 'exec', choose), patch.object(QMessageBox, 'critical') as error:
            self.window._choose_osz_charts(OszArchive(archive_file))
        self.assertEqual(len(visits), 2)
        error.assert_called_once()
        self.assertEqual(self.window._metadata['charts']['opening']['bumper_holds'], 'both')

    def test_restore_clean_is_separate_worker_action_and_idle_guarded(self):
        calls = []
        self.window._start_operation = lambda label, task, **options: calls.append((label, task, options))
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            self.window._restore_clean()
        self.assertEqual(len(calls), 1)
        self.assertIn('clean', calls[0][0])
        self.assertFalse(calls[0][2]['cancelable'])
        with patch.object(self.window.manager, 'restore_clean', return_value='restored') as restore:
            self.assertEqual(calls[0][1](lambda _: None, lambda: False), 'restored')
            restore.assert_called_once()
        self.window._worker = object()
        with patch.object(QMessageBox, 'question') as question:
            self.window._restore_clean()
            self.window._delete_song()
            question.assert_not_called()


@unittest.skipUnless(HAS_QT, 'PySide6 is not installed')
class SetupCliActions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name) / 'manager'
        self.workspace.mkdir()
        self.dialog = SetupDialog(dict(original='original-game', destination='playable-game', cli='manual-cli'), workspace=self.workspace)

    def tearDown(self):
        if self.dialog._cli_worker is not None:
            self.dialog._cli_worker.cancel_requested.set()
            self.dialog._cli_worker.wait(5000)
            self.app.processEvents()
        self.dialog.close()
        self.dialog.deleteLater()
        self.app.processEvents()
        self.temporary.cleanup()

    def wait_finished(self):
        deadline = time.monotonic() + 5
        while self.dialog._cli_worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.005)
        self.app.processEvents()
        self.assertIsNone(self.dialog._cli_worker, 'CLI worker did not finish')

    def test_cli_install_success_updates_path_after_worker_finished(self):
        executable = self.workspace / 'cli' / 'UndertaleModCli'
        def install(workspace, progress=None, cancel=None):
            self.assertEqual(workspace, self.workspace)
            progress('Checking the supported CLI…')
            executable.parent.mkdir()
            executable.write_text('verified test executable')
            return executable
        with patch('cli_setup.install_cli', side_effect=install):
            self.dialog._install_cli()
            self.assertEqual(self.dialog.cli.text(), 'manual-cli')
            self.assertFalse(self.dialog.original.isEnabled())
            self.assertFalse(self.dialog.cli_setup_button.isEnabled())
            self.assertFalse(self.dialog.buttons.button(QDialogButtonBox.StandardButton.Ok).isEnabled())
            self.wait_finished()
        self.assertEqual(self.dialog.cli.text(), str(executable))
        self.assertEqual(self.dialog.original.text(), 'original-game')
        self.assertEqual(self.dialog.destination.text(), 'playable-game')
        self.assertTrue(self.dialog.original.isEnabled())
        self.assertTrue(self.dialog.cli_setup_button.isEnabled())
        self.assertIn('ready', self.dialog.cli_status.text())

    def test_cli_install_failure_keeps_paths_and_allows_retry(self):
        with patch('cli_setup.install_cli', side_effect=ValueError('Test download failure')), patch.object(QMessageBox, 'critical') as error:
            self.dialog._install_cli()
            self.wait_finished()
            error.assert_called_once()
            self.assertIn('Test download failure', str(error.call_args))
        self.assertEqual(self.dialog.cli.text(), 'manual-cli')
        self.assertEqual(self.dialog.original.text(), 'original-game')
        self.assertEqual(self.dialog.destination.text(), 'playable-game')
        self.assertTrue(self.dialog.buttons.button(QDialogButtonBox.StandardButton.Ok).isEnabled())
        with patch('cli_setup.install_cli', return_value=self.workspace / 'retry-cli'):
            self.dialog._install_cli()
            self.wait_finished()
        self.assertEqual(self.dialog.cli.text(), str(self.workspace / 'retry-cli'))

    def test_cli_cancel_waits_for_worker_and_close_is_guarded(self):
        entered = threading.Event()
        finish = threading.Event()
        def install(workspace, progress=None, cancel=None):
            entered.set()
            while not finish.is_set():
                time.sleep(.005)
            if cancel():
                raise Cancelled('Test CLI setup cancelled')
            return workspace / 'should-not-be-selected'
        self.dialog.show()
        with patch('cli_setup.install_cli', side_effect=install):
            self.dialog._install_cli()
            self.assertTrue(entered.wait(2))
            self.assertFalse(self.dialog.close())
            self.assertTrue(self.dialog.isVisible())
            self.dialog.reject()
            self.assertIsNotNone(self.dialog._cli_worker)
            self.assertTrue(self.dialog._cli_worker.cancel_requested.is_set())
            self.assertTrue(self.dialog.isVisible())
            finish.set()
            self.wait_finished()
        self.assertFalse(self.dialog.isVisible())
        self.assertEqual(self.dialog.cli.text(), 'manual-cli')


if __name__ == '__main__':
    unittest.main()
