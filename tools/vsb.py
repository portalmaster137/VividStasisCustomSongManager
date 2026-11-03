#!/usr/bin/env python3
"""Evidence-based Vividstasis VSC v1 decoder and corpus validator (stdlib only)."""
from pathlib import Path
import argparse, collections, hashlib, json, struct

EXTRA_FORMATS={0xB0:'B',0xB1:'b',0xB2:'I',0xB3:'i',0xB5:'e',0xB6:'f',0xB7:'?',0xB8:'string'}

class FormatError(ValueError): pass

class Reader:
    def __init__(self,data): self.data=data; self.pos=0
    def fail(self,message): raise FormatError(f'0x{self.pos:X}: {message}')
    def take(self,size):
        if size<0 or self.pos+size>len(self.data): self.fail(f'truncated read of {size} bytes')
        result=self.data[self.pos:self.pos+size]; self.pos+=size; return result
    def value(self,fmt):
        if fmt=='string':
            end=self.data.find(b'\0',self.pos)
            if end<0: self.fail('unterminated string')
            raw=self.take(end-self.pos+1)[:-1]
            return raw.decode('utf-8',errors='surrogateescape')
        return struct.unpack('<'+fmt,self.take(struct.calcsize('<'+fmt)))[0]
    def byte(self): return self.value('B')
    def expect(self,value):
        actual=self.byte()
        if actual!=value:self.fail(f'expected 0x{value:02X}, found 0x{actual:02X}')


def parse_chart(data):
    r=Reader(data)
    if r.take(5)!=b'VSC\x01\0':r.fail('expected VSC version 1, reserved zero')
    blocks=[]
    while True:
        at=r.pos; tag=r.byte()
        if tag==0xFF:break
        if tag==0xC0:
            notes=[]
            while True:
                note_at=r.pos; flag=r.byte()
                if flag==0xC1:break
                if flag!=0xA0:r.fail(f'expected note start A0 or list end C1, got {flag:02X}')
                fields=[];note=dict(offset=note_at,type=0,lane=0,time=0.0,extra={},fields=fields)
                while True:
                    field_at=r.pos;flag=r.byte()
                    if flag==0xA1:break
                    if flag in (0xA2,0xA3,0xA4):
                        name={0xA2:'type',0xA3:'lane',0xA4:'time'}[flag]
                        value=r.value('f' if flag==0xA4 else 'B');note[name]=value
                        fields.append(dict(offset=field_at,tag=flag,value=value))
                    elif flag==0xA6:
                        extras=[];note['extra']={}
                        while True:
                            extra_at=r.pos;kind=r.byte()
                            if kind==0xA7:break
                            if kind not in EXTRA_FORMATS:r.fail(f'unsupported extra type {kind:02X}')
                            key=r.byte();value=r.value(EXTRA_FORMATS[kind])
                            extras.append(dict(offset=extra_at,tag=kind,id=key,value=value));note['extra'][str(key)]=value
                        fields.append(dict(offset=field_at,tag=flag,entries=extras))
                    else:r.fail(f'unknown note field {flag:02X}; refusing to desynchronize')
                notes.append(note)
            blocks.append(dict(offset=at,tag=tag,notes=notes))
        elif tag==0xE0:
            fields=[]
            while True:
                field_at=r.pos;flag=r.byte()
                if flag==0xE1:break
                if flag==0xE4:fields.append(dict(offset=field_at,tag=flag,proxies=r.byte()))
                elif flag==0xE5:fields.append(dict(offset=field_at,tag=flag,object=r.value('string')))
                elif flag==0xE2:
                    records=[]
                    while True:
                        rec_at=r.pos;kind=r.byte()
                        if kind==0xE3:break
                        if kind==0xE9:
                            rec=dict(offset=rec_at,tag=kind,beat=r.value('f'),duration=r.value('f'),ease=r.byte(),value1=r.value('f'),value2=r.value('f'),mod=r.byte(),proxy=r.value('b'))
                        elif kind==0xEC:
                            rec=dict(offset=rec_at,tag=kind,begin=r.value('f'),end=r.value('f'),function=r.value('string'))
                        else:r.fail(f'unknown modifier record {kind:02X}')
                        records.append(rec)
                    fields.append(dict(offset=field_at,tag=flag,records=records))
                else:r.fail(f'unknown modifier field {flag:02X}')
            blocks.append(dict(offset=at,tag=tag,fields=fields))
        else:r.fail(f'unknown top-level tag {tag:02X}')
    payload_end=r.pos;trailer=data[payload_end:]
    return dict(header='5653430100',blocks=blocks,payload_end=payload_end,trailer_bytes=len(trailer),trailer_hex=trailer.hex())


def encode_chart(chart):
    out=bytearray.fromhex(chart['header'])
    def put(fmt,value):
        out.extend(value.encode('utf-8',errors='surrogateescape')+b'\0' if fmt=='string' else struct.pack('<'+fmt,value))
    for block in chart['blocks']:
        out.append(block['tag'])
        if block['tag']==0xC0:
            for note in block['notes']:
                out.append(0xA0)
                for field in note['fields']:
                    tag=field['tag'];out.append(tag)
                    if tag==0xA6:
                        for extra in field['entries']:
                            out.extend((extra['tag'],extra['id']));put(EXTRA_FORMATS[extra['tag']],extra['value'])
                        out.append(0xA7)
                    else:put('f' if tag==0xA4 else 'B',field['value'])
                out.append(0xA1)
            out.append(0xC1)
        elif block['tag']==0xE0:
            for field in block['fields']:
                tag=field['tag'];out.append(tag)
                if tag==0xE4:put('B',field['proxies'])
                elif tag==0xE5:put('string',field['object'])
                elif tag==0xE2:
                    for record in field['records']:
                        out.append(record['tag'])
                        names=[('f','beat'),('f','duration'),('B','ease'),('f','value1'),('f','value2'),('B','mod'),('b','proxy')] if record['tag']==0xE9 else [('f','begin'),('f','end'),('string','function')]
                        for fmt,name in names:put(fmt,record[name])
                    out.append(0xE3)
            out.append(0xE1)
    out.append(0xFF);out.extend(bytes.fromhex(chart['trailer_hex']));return bytes(out)


def validate(root):
    report=dict(files=[],errors=[]);note_types=collections.Counter();lanes=collections.defaultdict(collections.Counter);extra_types=collections.Counter();extras=collections.Counter();trailer_sizes=collections.Counter();modids=collections.Counter();easeids=collections.Counter();proxies=collections.Counter();objects=collections.Counter();callbacks=collections.Counter();notes_total=mods_total=perframe_total=0
    for path in sorted(root.rglob('*.vsb')):
        try:
            raw=path.read_bytes();chart=parse_chart(raw)
            if encode_chart(chart)!=raw:raise FormatError('round-trip mismatch')
            notes=[n for b in chart['blocks'] if b['tag']==0xC0 for n in b['notes']]
            notes_total+=len(notes);trailer_sizes[chart['trailer_bytes']]+=1
            modifiers=[];perframes=[]
            for n in notes:
                note_types[n['type']]+=1;lanes[n['type']][n['lane']]+=1
                for field in n['fields']:
                    for extra in field.get('entries',[]):extra_types[hex(extra['tag'])]+=1;extras[f"{n['type']}:{extra['id']}"]+=1
            for b in chart['blocks']:
                if b['tag']!=0xE0:continue
                obj='obj_base_gimmick'
                for field in b['fields']:
                    if field['tag']==0xE5:obj=field['object'];objects[obj]+=1
                    for rec in field.get('records',[]):
                        if rec['tag']==0xE9:modifiers.append(rec);modids[f"{obj}:{rec['mod']}"]+=1;easeids[rec['ease']]+=1;proxies[rec['proxy']]+=1
                        else:perframes.append(rec);callbacks[f"{obj}:{rec['function']}"]+=1
            mods_total+=len(modifiers);perframe_total+=len(perframes)
            report['files'].append(dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),notes=len(notes),modifiers=len(modifiers),per_frame=len(perframes),payload_end=chart['payload_end'],trailer_bytes=chart['trailer_bytes'],roundtrip=True))
        except (ValueError,UnicodeError,struct.error) as e:report['errors'].append(dict(path=str(path),error=str(e)))
    report.update(file_count=len(report['files']),notes_total=notes_total,modifiers_total=mods_total,per_frame_total=perframe_total,note_types=dict(note_types),lanes_by_type={k:dict(v) for k,v in lanes.items()},extra_types=dict(extra_types),extras_by_note_type_and_id=dict(extras),trailer_sizes=dict(trailer_sizes),mod_ids=dict(modids),ease_ids=dict(easeids),proxy_targets=dict(proxies),objects=dict(objects),callbacks=dict(callbacks))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    dec=sub.add_parser('decode');dec.add_argument('file',type=Path);dec.add_argument('-o','--output',type=Path)
    val=sub.add_parser('validate');val.add_argument('directory',type=Path);val.add_argument('-o','--output',type=Path,required=True)
    args=p.parse_args()
    result=parse_chart(args.file.read_bytes()) if args.command=='decode' else validate(args.directory)
    text=json.dumps(result,indent=2,ensure_ascii=True)+'\n'
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)
    else:print(text,end='')
    if args.command=='validate':
        print(f"Parsed and byte-identically re-encoded {result['file_count']} charts; {len(result['errors'])} errors")
        if result['errors']:raise SystemExit(1)

if __name__=='__main__':main()
