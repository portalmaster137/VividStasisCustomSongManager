import tempfile
import unittest
from pathlib import Path
from custom_songs import Package, delete_library_song, write_metadata
from test_custom_songs import fixture, metadata


class LibraryActions(unittest.TestCase):
    def test_alternate_requires_encore_and_roundtrips(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = fixture(Path(temporary)/'test')
            chart = dict(file='chart.osu', level=12)
            data = metadata(charts={'apotheosis':chart})
            write_metadata(root/'data.toml', data)
            with self.assertRaisesRegex(ValueError, 'requires an ENCORE'): Package(root)
            data['charts']['encore'] = dict(chart, level=10)
            write_metadata(root/'data.toml', data)
            with Package(root) as package: package.export(Path(temporary)/'song.vsc')
            with Package(Path(temporary)/'song.vsc') as package:
                self.assertEqual(set(package.charts), {'encore','apotheosis'})

    def test_delete_removes_only_selected_library_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            library = Path(temporary)/'library'
            fixture(library/'test')
            other = library/'other'; other.mkdir(); (other/'keep').write_text('keep')
            game = Path(temporary)/'data.win'; game.write_bytes(b'game')
            delete_library_song(library, 'test')
            self.assertFalse((library/'test').exists())
            self.assertTrue((other/'keep').exists())
            self.assertEqual(game.read_bytes(),b'game')
            with self.assertRaises(ValueError): delete_library_song(library,'../data.win')
            (library/'link').symlink_to(other, target_is_directory=True)
            with self.assertRaises(ValueError): delete_library_song(library,'link')
            self.assertTrue((other/'keep').exists())
