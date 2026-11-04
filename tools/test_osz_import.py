import tempfile
import unittest
import zipfile
from pathlib import Path
from osz_import import OszArchive
from custom_songs import Package

OSU = 'osu file format v14\n[General]\nMode:3\nAudioFilename: music.mp3\n[Metadata]\nTitle:Song\nArtist:Artist\nCreator:Mapper\nVersion:Hard\n[Difficulty]\nCircleSize:4\n[TimingPoints]\n0,500,4,2,0,100,1,0\n[HitObjects]\n64,192,1000,1,0,0:0:0:0:\n'


class OszImport(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)

    def archive(self, extra=None):
        path=self.root/'map.osz'
        entries={'set/map.osu':OSU, 'set/music.mp3':b'first', 'other.ogg':b'second', 'art.png':b'cover',
                 'unsupported.osu':OSU.replace('CircleSize:4','CircleSize:7')}
        entries.update(extra or {})
        with zipfile.ZipFile(path,'w') as archive:
            for name,data in entries.items():archive.writestr(name,data)
        return path

    def test_select_audio_and_chart_then_persist_without_temp_paths(self):
        with OszArchive(self.archive()) as source:
            self.assertEqual(len(source.charts),1)
            self.assertEqual(source.charts[0]['keys'],4)
            self.assertEqual(source.charts[0]['audio'],'set/music.mp3')
            self.assertEqual(len(source.rejected),1)
            with source.create_package(self.root/'package','other.ogg',
                    {'apotheosis':dict(file='set/map.osu',level=12)},ident='song',jacket='art.png') as package:
                self.assertEqual(package.asset(package.metadata['audio']).read_bytes(), b'second')
                self.assertEqual(package.charts['apotheosis']['designer'],'Mapper')
                package.install_library(self.root/'library')
        with Package(self.root/'library/song') as package:
            self.assertTrue(package.asset(package.charts['apotheosis']['file']).is_file())
            self.assertEqual(package.metadata['title'],'Song')

    def test_invalid_selection_leaves_no_package(self):
        with OszArchive(self.archive()) as source:
            for audio, charts in [('outside.mp3',{'opening':{'file':'set/map.osu'}}),
                                  ('other.ogg',{}),('other.ogg',{'opening':{'file':'unsupported.osu'}}),
                                  ('other.ogg',{'opening':{'file':'set/map.osu','level':-1}})]:
                with self.subTest(audio=audio,charts=charts),self.assertRaises(ValueError):
                    source.create_package(self.root/'package', audio, charts,ident='song')
                self.assertFalse((self.root/'package').exists())

    def test_unsafe_archive_rejected(self):
        for name in ['../escape','/escape','sub/..','a\\b','C:/bad']:
            with self.subTest(name=name),self.assertRaises(ValueError):
                with OszArchive(self.archive({name:b'bad'})):pass

    def test_bumper_hold_policy_chosen_before_validation(self):
        six=OSU.replace('CircleSize:4','CircleSize:6').replace('64,192,1000,1,0,0:0:0:0:', '0,192,1000,128,0,1500:0:0:0:0:')
        with OszArchive(self.archive({'six.osu':six})) as source:
            with self.assertRaisesRegex(ValueError,'Bumper hold'):
                source.create_package(self.root/'package','other.ogg',{'opening':dict(file='six.osu',level=4)},ident='song')
            with source.create_package(self.root/'package','other.ogg',{'opening':dict(file='six.osu',level=4,bumper_holds='both')},ident='song') as package:
                self.assertEqual(package.charts['opening']['bumper_holds'],'both')
