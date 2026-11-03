import struct
import unittest
from vsb import EXTRA_FORMATS, FormatError, encode_chart, parse_chart

HEADER=b'VSC\x01\0'
def f32(value):return struct.pack('<f',value)

class VSBTests(unittest.TestCase):
    def roundtrip(self,raw):
        chart=parse_chart(raw)
        self.assertEqual(encode_chart(chart),raw)
        return chart
    def test_default_fields_and_variable_order(self):
        raw=HEADER+b'\xc0\xa0\xa1\xa0\xa4'+f32(1234.5)+b'\xa3\x03\xa2\x06\xa1\xc1\xff'
        chart=self.roundtrip(raw);notes=chart['blocks'][0]['notes']
        self.assertEqual((notes[0]['type'],notes[0]['lane'],notes[0]['time']),(0,0,0))
        self.assertEqual((notes[1]['type'],notes[1]['lane'],notes[1]['time']),(6,3,1234.5))
    def test_all_extra_widths_signedness_and_strings(self):
        values=[255,-128,0xFF00A1FF,-123456,1.5,-12.25,True,'utf8: 音']
        raw=bytearray(HEADER+b'\xc0\xa0\xa6')
        for key,((tag,fmt),value) in enumerate(zip(EXTRA_FORMATS.items(),values)):
            raw.extend((tag,key));raw.extend(value.encode()+b'\0' if fmt=='string' else struct.pack('<'+fmt,value))
        raw.extend(b'\xa7\xa1\xc1\xff');chart=self.roundtrip(bytes(raw))
        self.assertEqual(list(chart['blocks'][0]['notes'][0]['extra'].values()),values)
    def test_repeated_fields_and_extra_group_replacement(self):
        raw=HEADER+b'\xc0\xa0\xa3\x02\xa3\x01\xa6\xb0\x01\x05\xa7\xa6\xb1\x02\xff\xa7\xa1\xc1\xff'
        note=self.roundtrip(raw)['blocks'][0]['notes'][0]
        self.assertEqual(note['lane'],1);self.assertEqual(note['extra'],{'2':-1})
    def test_mod_records_and_unsigned_file(self):
        tween=b'\xe9'+f32(2)+f32(4)+b'\x13'+f32(-1)+f32(5)+b'\x81\xff'
        callback=b'\xec'+f32(3)+f32(9)+b'spin\0'
        raw=HEADER+b'\xc0\xc1\xe0\xe4\x02\xe5obj_base_gimmick\0\xe2'+tween+callback+b'\xe3\xe1\xff'
        chart=self.roundtrip(raw);records=chart['blocks'][1]['fields'][2]['records']
        self.assertEqual(records[0]['proxy'],-1);self.assertEqual(records[1]['function'],'spin')
        self.assertEqual(chart['trailer_bytes'],0)
    def test_trailer_is_opaque_even_with_control_tag_bytes(self):
        trailer=bytes(range(256))+bytes(range(128))
        chart=self.roundtrip(HEADER+b'\xff'+trailer)
        self.assertEqual(chart['payload_end'],6);self.assertEqual(chart['trailer_bytes'],384)
    def test_truncated_payload_at_every_boundary(self):
        raw=HEADER+b'\xc0\xa0\xa4'+f32(1234)+b'\xa6\xb8\x01hello\0\xa7\xa1\xc1\xff'
        for length in range(len(raw)):
            with self.subTest(length=length), self.assertRaises(FormatError):parse_chart(raw[:length])
    def test_unsupported_versions_and_unknown_tags_fail(self):
        for raw in [b'VSC\x02\0\xff',HEADER+b'\xcc\xff',HEADER+b'\xc0\xa0\xa5\xa1\xc1\xff',HEADER+b'\xc0\xa0\xa6\xb4\x01\0\xa7\xa1\xc1\xff',HEADER+b'\xe0\xe2\xea\xe3\xe1\xff']:
            with self.subTest(raw=raw),self.assertRaises(FormatError):parse_chart(raw)

if __name__=='__main__':unittest.main()
