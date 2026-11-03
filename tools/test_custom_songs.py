"""Package boundary and transaction tests; all assets are temporary fixtures."""
import stat
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest import mock

import custom_songs
from custom_songs import Package, write_metadata

OSU = ('osu file format v14\n[General]\nMode:3\n[Difficulty]\nCircleSize:6\n'
       '[TimingPoints]\n0,500,4,2,0,100,1,0\n[HitObjects]\n'
       '128,192,1000,1,0,0:0:0:0:\n')


def metadata(**changes):
    result = dict(format_version=1, id='test', title='A "title"', artist='Artist',
                  audio='audio.mp3', charts={'opening':dict(file='chart.osu', level=4.5, designer='Mapper')})
    result.update(changes)
    return result


def fixture(root, data=None):
    root.mkdir(parents=True, exist_ok=True)
    (root/'audio.mp3').write_bytes(b'fixture audio')
    (root/'chart.osu').write_text(OSU, encoding='utf-8')
    write_metadata(root/'data.toml', metadata() if data is None else data)
    return root


class Packages(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = fixture(self.root/'source')

    def make_archive(self, entries):
        path = self.root/'bad.vsc'
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(path, 'w') as archive:
                for name, data in entries:
                    archive.writestr(name, data)
        return path

    def test_roundtrip_unicode_nested_assets_and_multiple_difficulties(self):
        data = metadata(title='Title "雪"\nsecond line', artist='アーティスト', jacket='art/jacket.png',
                        charts={'opening':dict(file='charts/easy.osu', level=4.5, designer='Mapper'),
                                'encore':dict(file='chart.osu', level=13, bumper_holds='both')})
        (self.source/'art').mkdir(); (self.source/'art/jacket.png').write_bytes(b'jacket')
        (self.source/'charts').mkdir(); (self.source/'charts/easy.osu').write_text(OSU)
        write_metadata(self.source/'data.toml', data)
        with Package(self.source) as package:
            package.export(self.root/'song.vsc')
        with Package(self.root/'song.vsc') as loaded:
            self.assertEqual(loaded.metadata, data)
            self.assertEqual(loaded.asset('audio.mp3').read_bytes(), b'fixture audio')
            self.assertEqual(loaded.asset('art/jacket.png').read_bytes(), b'jacket')
            self.assertEqual(set(loaded.charts), {'opening', 'encore'})

    def test_archive_escape_absolute_and_windows_paths(self):
        for name in ('../escape', '/escape', 'sub/../../escape', 'C:/escape', 'sub\\escape', './escape'):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    Package(self.make_archive([(name, b'bad')]))
        self.assertFalse((self.root/'escape').exists())

    def test_duplicate_entry(self):
        with self.assertRaises(ValueError):
            Package(self.make_archive([('data.toml', ''), ('data.toml', '')]))

    def test_archive_rejects_normalized_path_aliases(self):
        with self.assertRaises(ValueError):
            Package(self.make_archive([('sub//audio.mp3', b'first'), ('sub/audio.mp3', b'second')]))

    def test_archive_rejects_unix_symlink(self):
        info = zipfile.ZipInfo('link')
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaisesRegex(ValueError, 'symlink'):
            Package(self.make_archive([(info, '../outside')]))

    def test_archive_limit_is_cumulative_uncompressed_bytes(self):
        path = self.make_archive([('one', b'abc'), ('two', b'def')])
        with mock.patch.object(custom_songs, 'LIMIT', 5):
            with self.assertRaisesRegex(ValueError, 'exceeds'):
                Package(path)

    def test_invalid_schema_is_a_validation_error(self):
        base = 'format_version=1\nid="test"\ntitle="Song"\nartist="Artist"\naudio="audio.mp3"\n'
        cases = {
            'boolean version': base.replace('format_version=1', 'format_version=true')+'[charts.opening]\nfile="chart.osu"\nlevel=4\n',
            'numeric id': base.replace('id="test"', 'id=12')+'[charts.opening]\nfile="chart.osu"\nlevel=4\n',
            'charts string': base+'charts="bad"\n',
            'charts array': base+'charts=[]\n',
            'chart scalar': base+'[charts]\nopening="bad"\n',
            'missing chart file': base+'[charts.opening]\nlevel=4\n',
            'chart filename boolean': base+'[charts.opening]\nfile=false\nlevel=4\n',
            'designer nontext': base+'[charts.opening]\nfile="chart.osu"\nlevel=4\ndesigner=99\n',
        }
        for description, contents in cases.items():
            with self.subTest(description=description):
                (self.source/'data.toml').write_text(contents)
                with self.assertRaises(ValueError):
                    Package(self.source)

    def test_invalid_levels(self):
        for level in (True, False, 0, -1, 100.01, float('nan'), float('inf'), '4'):
            with self.subTest(level=level):
                data = metadata();data['charts']['opening']['level'] = level
                write_metadata(self.source/'data.toml', data)
                with self.assertRaises(ValueError): Package(self.source)

    def test_unknown_or_empty_difficulty_is_rejected(self):
        for charts in ({}, {'shatter':dict(file='chart.osu',level=10)}):
            write_metadata(self.source/'data.toml', metadata(charts=charts))
            with self.assertRaises(ValueError): Package(self.source)

    def test_invalid_or_traversing_id(self):
        for identifier in ('../escape', 'MixedCase', '_prefix', 'a'*65, '', 'has space'):
            with self.subTest(identifier=identifier):
                write_metadata(self.source/'data.toml', metadata(id=identifier))
                with self.assertRaises(ValueError): Package(self.source)

    def test_asset_paths_must_be_canonical_and_contained(self):
        with Package(self.source) as package:
            for path in ('../audio.mp3', '/etc/passwd', 'a/../audio.mp3', './audio.mp3',
                         'a//audio.mp3', 'C:/audio.mp3', 'a\\audio.mp3', '', None):
                with self.subTest(path=path):
                    with self.assertRaises(ValueError): package.asset(path)

    def test_referenced_symlink_escape_is_rejected(self):
        external = self.root/'outside.mp3';external.write_bytes(b'outside')
        (self.source/'escape.mp3').symlink_to(external)
        write_metadata(self.source/'data.toml', metadata(audio='escape.mp3'))
        with self.assertRaises(ValueError): Package(self.source)

    def test_chart_must_be_valid_six_key_mania(self):
        for chart in ('not a beatmap', OSU.replace('CircleSize:6', 'CircleSize:4'), OSU.replace('Mode:3', 'Mode:0')):
            with self.subTest(chart=chart[:20]):
                (self.source/'chart.osu').write_text(chart)
                with self.assertRaises(ValueError): Package(self.source)

    def test_bumper_hold_policy_is_applied(self):
        (self.source/'chart.osu').write_text(OSU.replace('128,192,1000,1,0,0:0:0:0:', '0,192,1000,128,0,1500:0:0:0:0:'))
        with self.assertRaisesRegex(ValueError, 'Bumper hold'): Package(self.source)
        for mode in ('start', 'both'):
            data = metadata();data['charts']['opening']['bumper_holds'] = mode
            write_metadata(self.source/'data.toml', data)
            with Package(self.source) as package: self.assertEqual(package.charts['opening']['bumper_holds'], mode)

    def test_export_only_referenced_assets_and_preserves_existing_destination(self):
        (self.source/'private.txt').write_bytes(b'not exported')
        target = self.root/'song.vsc'
        with Package(self.source) as package:
            package.export(target)
            original = target.read_bytes()
            with self.assertRaises(FileExistsError): package.export(target)
        self.assertEqual(target.read_bytes(), original)
        with zipfile.ZipFile(target) as archive:
            self.assertEqual(set(archive.namelist()), {'data.toml', 'audio.mp3', 'chart.osu'})

    def test_export_write_failure_leaves_no_partial_destination(self):
        target = self.root/'song.vsc'
        real_write = zipfile.ZipFile.write
        calls = 0
        def fail_second(archive, *args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2: raise OSError('injected write failure')
            return real_write(archive, *args, **kwargs)
        with Package(self.source) as package:
            with mock.patch.object(zipfile.ZipFile, 'write', fail_second):
                with self.assertRaisesRegex(OSError, 'injected'):
                    package.export(target)
        self.assertFalse(target.exists(), 'failed export must not leave a partial archive')

    def test_install_conflict_requires_explicit_replace(self):
        library = self.root/'library'
        with Package(self.source) as package:
            target = package.install_library(library)
            self.assertEqual(target, library/'test')
            (target/'audio.mp3').write_bytes(b'old audio')
            with self.assertRaises(FileExistsError): package.install_library(library)
            self.assertEqual((target/'audio.mp3').read_bytes(), b'old audio')

    def test_install_copies_only_referenced_assets_not_unreferenced_symlinks(self):
        outside = self.root/'outside-secret';outside.write_bytes(b'secret')
        (self.source/'secret-link').symlink_to(outside)
        (self.source/'private.txt').write_bytes(b'private')
        with Package(self.source) as package: target = package.install_library(self.root/'library')
        self.assertEqual({p.name for p in target.iterdir()}, {'data.toml','audio.mp3','chart.osu'})
        self.assertEqual(outside.read_bytes(), b'secret')

    def test_replace_commits_new_assets_and_removes_backup(self):
        library = self.root/'library'
        with Package(self.source) as package: package.install_library(library)
        incoming = fixture(self.root/'incoming', metadata(title='Updated'))
        (incoming/'audio.mp3').write_bytes(b'new audio')
        with Package(incoming) as package: target = package.install_library(library, replace=True)
        with Package(target) as package:
            self.assertEqual(package.metadata['title'], 'Updated')
            self.assertEqual(package.asset('audio.mp3').read_bytes(), b'new audio')
        self.assertEqual({p.name for p in library.iterdir()}, {'test'})

    def test_failed_replace_restores_original_and_cleans_staging(self):
        library = self.root/'library'
        with Package(self.source) as package: package.install_library(library)
        incoming = fixture(self.root/'incoming', metadata(title='Updated'))
        original_rename = Path.rename
        def fail_commit(path, target):
            if path.name == 'song': raise OSError('injected commit failure')
            return original_rename(path, target)
        with Package(incoming) as package:
            with mock.patch.object(Path, 'rename', fail_commit):
                with self.assertRaisesRegex(OSError, 'injected commit'):
                    package.install_library(library, replace=True)
        with Package(library/'test') as package: self.assertEqual(package.metadata['title'], metadata()['title'])
        self.assertEqual({p.name for p in library.iterdir()}, {'test'})

    def test_preexisting_backup_requires_recovery_without_touching_original(self):
        library = self.root/'library'
        with Package(self.source) as package: package.install_library(library)
        backup = library/'.old-test';backup.mkdir();(backup/'recovery.txt').write_bytes(b'keep')
        with Package(self.source) as package:
            with self.assertRaisesRegex(ValueError, 'recovery'):
                package.install_library(library, replace=True)
        self.assertEqual((backup/'recovery.txt').read_bytes(), b'keep')
        self.assertEqual((library/'test/audio.mp3').read_bytes(), b'fixture audio')
        self.assertEqual({p.name for p in library.iterdir()}, {'test','.old-test'})

    def test_in_memory_edits_are_serialized_for_export_and_library(self):
        with Package(self.source) as package:
            package.metadata['title'] = 'Edited title'
            package.metadata['charts'] = {'encore':dict(file='chart.osu', level=12.5, designer='New mapper')}
            package.export(self.root/'edited.vsc')
            installed = package.install_library(self.root/'library')
        for source in (self.root/'edited.vsc', installed):
            with self.subTest(source=source):
                with Package(source) as loaded:
                    self.assertEqual(loaded.metadata['title'], 'Edited title')
                    self.assertEqual(set(loaded.charts), {'encore'})
                    self.assertEqual(loaded.charts['encore']['designer'], 'New mapper')
        with Package(self.source) as original:
            self.assertEqual(original.metadata['title'], metadata()['title'])

    def test_export_commit_failure_cleans_staging(self):
        target = self.root/'song.vsc'
        before = set(self.root.iterdir())
        with Package(self.source) as package:
            with mock.patch.object(custom_songs.os, 'link', side_effect=OSError('unsupported hard links')):
                with self.assertRaisesRegex(OSError, 'unsupported hard links'):
                    package.export(target)
        self.assertFalse(target.exists())
        self.assertEqual(set(self.root.iterdir()), before)

    def test_library_song_symlinks_are_not_replaced_or_followed(self):
        library = self.root/'library';library.mkdir()
        external = fixture(self.root/'external')
        for exists in (True, False):
            for replace in (True, False):
                with self.subTest(exists=exists, replace=replace):
                    target = library/'test'
                    target.symlink_to(external if exists else self.root/'nonexistent')
                    try:
                        with Package(self.source) as package:
                            with self.assertRaises((ValueError, FileExistsError)):
                                package.install_library(library, replace=replace)
                        self.assertTrue(target.is_symlink())
                        self.assertEqual({p.name for p in library.iterdir()}, {'test'})
                        self.assertEqual((external/'audio.mp3').read_bytes(), b'fixture audio')
                    finally:
                        if target.is_symlink(): target.unlink()

    def test_archive_context_cleans_extracted_temporary_directory(self):
        target = self.root/'song.vsc'
        with Package(self.source) as package: package.export(target)
        with Package(target) as package: extracted = package.root;self.assertTrue(extracted.is_dir())
        self.assertFalse(extracted.exists())


if __name__ == '__main__': unittest.main()
