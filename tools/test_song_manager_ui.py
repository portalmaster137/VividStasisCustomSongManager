"""Offscreen desktop action tests; skipped when the optional Qt dependency is absent."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HAS_QT = importlib.util.find_spec('PySide6') is not None
if HAS_QT:
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication, QMessageBox
    from song_manager import SongManagerWindow

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

    def test_alternate_slot_requires_encore_without_saving_invalid_draft(self):
        self.fill()
        self.window._chart_row('apotheosis', str(self.chart))
        slot = self.window.charts.cellWidget(0, 0)
        self.assertEqual(slot.count(), 5)
        self.assertEqual(slot.currentText(), 'APOTHEOSIS')
        self.assertEqual(self.window.charts.cellWidget(0, 6).text(), '4K')
        with patch.object(QMessageBox, 'critical') as error:
            self.assertFalse(self.window._save_package())
        self.assertIn('ENCORE', str(error.call_args))
        self.assertFalse((self.window.library / 'test_song').exists())
        self.window._chart_row('encore', str(self.chart))
        self.assertTrue(self.window._save_package())
        self.assertEqual(set(self.window._metadata['charts']), {'encore', 'apotheosis'})

    def test_delete_removes_only_library_and_leaves_install_pending_removal(self):
        self.fill()
        self.window._chart_row('opening', str(self.chart))
        self.assertTrue(self.window._save_package())
        self.window.manager.state['installed_ids'] = ['test_song']
        game = self.root / 'game'
        game.mkdir()
        (game / 'data.win').write_bytes(b'unchanged-game')
        self.window.manager.state['destination'] = str(game)
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            self.window._delete_song()
        self.assertFalse((self.window.library / 'test_song').exists())
        self.assertNotIn('test_song', self.window._selected_ids)
        self.assertNotIn('test_song', self.window.manager.state['selected_ids'])
        self.assertEqual(self.window.manager.state['installed_ids'], ['test_song'])
        self.assertEqual((game / 'data.win').read_bytes(), b'unchanged-game')
        self.assertTrue(any('Pending removal' in self.window.list.item(i).text()
                            for i in range(self.window.list.count())))

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


if __name__ == '__main__':
    unittest.main()
