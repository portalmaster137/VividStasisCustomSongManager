import unittest
from osu_to_vsb import convert, detect_key_count
from vsb import parse_chart


def chart(keys, objects):
    return f'osu file format v14\n[General]\nMode:3\n[Difficulty]\nCircleSize:{keys}\n[TimingPoints]\n0,500,4,2,0,100,1,0\n[HitObjects]\n' + '\n'.join(objects)


class KeyDetection(unittest.TestCase):
    def test_four_lanes_preserve_taps_and_holds_without_bumpers(self):
        source = chart(4, [f'{x},192,{1000+i*1000},128,0,{1500+i*1000}:0:0:0:0:' for i,x in enumerate([0,128,256,512])])
        for policy in ('reject','start','both'):
            raw, _, _ = convert(source, policy)
            notes = [n for n in parse_chart(raw)['blocks'][0]['notes'] if n['type'] != 3]
            self.assertEqual([n['lane'] for n in notes], [0,1,2,3])
            self.assertEqual([n['type'] for n in notes], [2]*4)
            self.assertEqual([n['extra']['1'] for n in notes], [1500,2500,3500,4500])
        self.assertEqual(detect_key_count(source), 4)

    def test_six_key_mapping_and_bumper_policy(self):
        raw, _, _ = convert(chart(6,[f'{x},192,{1000+i},1,0,0:0:0:0:' for i,x in enumerate([0,128,213,299,384,512])]))
        notes = [n for n in parse_chart(raw)['blocks'][0]['notes'] if n['type'] != 3]
        self.assertEqual([(n['type'],n['lane']) for n in notes], [(1,0),(0,0),(0,1),(0,2),(0,3),(1,2)])

    def test_unsupported_and_nonfinite_key_counts_rejected(self):
        for keys in ('nan','inf','4.5','5','invalid'):
            with self.subTest(keys=keys), self.assertRaises(ValueError):
                detect_key_count(chart(keys,[]))
