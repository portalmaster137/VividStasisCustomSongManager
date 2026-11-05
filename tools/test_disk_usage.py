"""Storage accounting and cancellation checks without Qt."""
from pathlib import Path
import tempfile
import unittest

from disk_usage import scan_usage, measure, format_bytes
from manager_backend import Cancelled


class DiskUsageTests(unittest.TestCase):
    def test_workspace_total_and_separate_game_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / 'manager'
            library = workspace / 'library'
            library.mkdir(parents=True)
            (library / 'audio.ogg').write_bytes(b'a' * 20)
            (workspace / 'state.json').write_bytes(b'{}')
            game = root / 'game'
            game.mkdir()
            (game / 'data.win').write_bytes(b'b' * 50)
            rows, drives = scan_usage(workspace, {'destination': str(game)}, lambda _: None, lambda: False)
            sizes = {label: size for label, _, size, _ in rows}
            self.assertEqual(sizes['Song library'], 20)
            self.assertEqual(sizes['Other workspace files'], 2)
            self.assertEqual(sizes['Workspace total'], 22)
            self.assertEqual(sizes['Playable game copy'], 50)
            self.assertEqual(sizes['Conversion cache'], 0)
            self.assertEqual(len(drives), 2)

    def test_missing_path_is_reported_as_partial(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(measure(Path(temporary) / 'missing', lambda: False), (0, 1))

    def test_scan_can_be_cancelled(self):
        with self.assertRaises(Cancelled):
            measure(Path('.'), lambda: True)

    def test_binary_units(self):
        self.assertEqual(format_bytes(0), '0 B')
        self.assertEqual(format_bytes(1024), '1.00 KiB')


if __name__ == '__main__':
    unittest.main()
