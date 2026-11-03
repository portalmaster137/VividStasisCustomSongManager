#!/usr/bin/env python3
"""Generate version-specific mod ID evidence from shipped decompiled GML.
This recognizes literal addGlobalMod/addExtraMod declarations and literal numeric
for-loop bounds in this extraction. It does not evaluate GML or execute the game.
"""
from pathlib import Path
import json,re,collections
ROOT=Path(__file__).resolve().parents[2]
CODE=ROOT/'extraction/main/CodeEntries'
META=ROOT/'extraction/main/metadata'
strings=[json.loads(line)['data']['Content'] for line in (META/'Strings.jsonl').open()]
objects=[json.loads(line)['data'] for line in (META/'GameObjects.jsonl').open()]
def string(ref):return strings[int(ref['$ref'].split('/')[1])]
def source_record(path,line):return {'file':str(path.relative_to(ROOT)),'line':line}
def line_at(s,pos):return s.count('\n',0,pos)+1
setup=CODE/'gml_GlobalScript_mod_setup.gml';text=setup.read_text()
global_regs=[]
for i,m in enumerate(re.finditer(r'^addGlobalMod\("([^"]+)"',text,re.M)):
 global_regs.append(dict(id=i,name=m[1],source=source_record(setup,line_at(text,m.start()))))
easebody=re.search(r'global\.easeBytes\s*=\s*\{(.*?)\};',text,re.S)[1]
eases=[dict(id=int(i),name=name) for name,i in re.findall(r'(\w+):\s*(\d+)',easebody)]
loop_re=re.compile(r'^for \(var (\w+) = (\d+); \1 (<=|<) (\d+); \1\+\+\)\n\{\n(.*?)^\}',re.M|re.S)
call_re=re.compile(r'^[ \t]*addExtraMod\((\$?)"([^"\n]+)"',re.M)
results={}
for obj in objects:
 if not obj:continue
 name=string(obj['Name']); parentref=obj.get('ParentId')
 parent=string(objects[int(parentref['$ref'].split('/')[1])]['Name']) if parentref else None
 path=CODE/f'gml_Object_{name}_Create_0.gml'
 text=path.read_text() if path.exists() else ''
 if parent!='obj_base_gimmick' and name!='obj_base_gimmick' and 'addExtraMod(' not in text and 'extraMods =' not in text:continue
 result={'parent':parent,'evidence_kind':'static-source-registration-order; no game execution','source':str(path.relative_to(ROOT)) if path.exists() else None,'registrations':[],'ambiguities':[]}
 if name=='obj_base_gimmick':
  result['initial_registration_index']=1;results[name]=result;continue
 if parent!='obj_base_gimmick':result['ambiguities'].append('Parent is not the audited base gimmick; inherited registration index may differ.')
 if text and 'event_inherited();' not in text:result['ambiguities'].append('Create event does not explicitly call event_inherited; initialization not assumed.')
 loops=[]
 for m in loop_re.finditer(text):
  if 'addExtraMod(' in m[5]:loops.append(m)
 items=[]
 for m in call_re.finditer(text):
  loop=next((x for x in loops if x.start()<=m.start()<x.end()),None)
  if loop:continue
  if m[1] or '{' in m[2]:
   items.append((m.start(),[dict(name=m[2],id=None,source=source_record(path,line_at(text,m.start())),unresolved='Interpolated registration outside recognized literal loop')]))
  else:items.append((m.start(),[dict(name=m[2],source=source_record(path,line_at(text,m.start())))]))
 for m in loops:
  regs=[]; start=int(m[2]);end=int(m[4])+(m[3]=='<=')
  for i in range(start,end):
   for call in call_re.finditer(m[5]):
    regname=call[2].replace('{'+m[1]+'}',str(i))
    regs.append(dict(name=regname,source=source_record(path,line_at(text,m.start(5)+call.start())),loop_iteration=i))
  items.append((m.start(),regs))
 ordinal=1
 for _,regs in sorted(items):
  for reg in regs:
   if 'unresolved' in reg:result['ambiguities'].append(reg['unresolved'])
   reg['id']=ordinal|128 if not result['ambiguities'] else None
   reg['registration_index']=ordinal;ordinal+=1;result['registrations'].append(reg)
 # An old object uses a literal extraMods struct instead of addExtraMod.
 explicit=re.search(r'^extraMods\s*=\s*\{(.*?)^\};',text,re.M|re.S)
 if explicit:
  result['ambiguities']=[a for a in result['ambiguities'] if not a.startswith('Create event does not explicitly')]
  if result['registrations']:result['ambiguities'].append('Explicit extraMods assignment coexists with registration calls; inspect assignment order.')
  else:
   for m in re.finditer(r'^[ \t]*(\w+):[ \t]*(\d+)',explicit[1],re.M):result['registrations'].append(dict(name=m[1],id=int(m[2]),source=source_record(path,line_at(text,explicit.start(1)+m.start())),explicit_literal=True))
 result['effective_name_to_id']={r['name']:r['id'] for r in result['registrations']}
 last={r['name']:i for i,r in enumerate(result['registrations'])}
 result['shadowed_registrations']=[r for i,r in enumerate(result['registrations']) if last[r['name']]!=i]
 result['effective_id_to_name']={str(i):n for n,i in result['effective_name_to_id'].items() if i is not None}
 results[name]=result
payload={'scope':'GameMaker code extracted from supplied main data.win','method':'Static declarations in source order; constant numeric for-loops expanded; object parents taken from GameObjects metadata. No game code executed. Registration records retained even when later duplicate names shadow earlier IDs. Effective ID maps omit shadowed registrations.','global':global_regs,'easing':eases,'objects':results}
out=ROOT/'analysis/chart_format/mod_ids.json';out.write_text(json.dumps(payload,indent=2)+'\n')
lines=['# Chart mod and easing IDs','','These IDs are specific to the supplied game build. They were derived from the extracted GML without executing the game. [The JSON catalog](../analysis/chart_format/mod_ids.json) includes every registration, source filename and line, expanded literal-loop iteration, effective name/ID map, and any ambiguities. [The generator](../analysis/chart_format/generate_mod_ids.py) reproduces it.','','Global IDs are assigned from zero by `addGlobalMod`. The high bit selects chart-specific IDs, whose names depend on the selected gimmick object. The base gimmick initializes its extra-mod registration index to 1; `addExtraMod` assigns `index | 0x80`. Thus ordinary object-specific registration starts at `0x81`, not `0x80`. All cataloged derived gimmicks directly inherit from `obj_base_gimmick` according to the extracted object metadata.','','Duplicate names are not treated as two simultaneously valid names: the game stores name→ID in a struct, so a later registration overwrites the earlier value. Full registration history remains in JSON, while the effective reverse map omits shadowed registrations. This is a static interpretation of source assignment order, not runtime observation.','','## Global IDs','','| ID | Hex | Name |','| --- | --- | --- |']
for r in global_regs:lines.append(f"| {r['id']} | `0x{r['id']:02X}` | `{r['name']}` |")
lines+=['','## Easing IDs','','| ID | Name |','| --- | --- |']
for r in eases:lines.append(f"| {r['id']} | `{r['name']}` |")
lines+=['','## Object-specific IDs','','Object names are values of the chart mods configuration object field. Objects with no registrations are included to distinguish an empty mapping from an unexamined one. Nonliteral/runtime control flow is not evaluated; any unresolved situations are listed explicitly.']
for name,result in sorted(results.items()):
 lines+=['',f'### `{name}`','',f"Parent: `{result['parent']}`. "]
 if result['source']:lines[-1]+=f"[Create event](../{result['source']})."
 for ambiguity in result['ambiguities']:lines+=['',f'Unresolved: {ambiguity}']
 if not result['registrations']:lines+=['','No extra-mod registrations.'];continue
 lines+=['','| ID | Hex | Name | Source line |','| --- | --- | --- | --- |']
 effective=result['effective_name_to_id']
 for name2,ident in effective.items():
  reg=next(r for r in reversed(result['registrations']) if r['name']==name2)
  lines.append(f"| {ident if ident is not None else 'unresolved'} | {f'`0x{ident:02X}`' if ident is not None else '—'} | `{name2}` | {reg['source']['line']} |")
 if result['shadowed_registrations']:lines+=['','Shadowed registrations are retained in the JSON catalog and omitted from this effective mapping.']
(ROOT/'docs/chart_mod_ids.md').write_text('\n'.join(lines)+'\n')
print('Global mods',len(global_regs),'eases',len(eases),'objects',len(results),'registrations',sum(len(r['registrations']) for r in results.values()))
print('Ambiguities',[(n,r['ambiguities']) for n,r in results.items() if r['ambiguities']])
print('Shadowed',[(n,len(r['shadowed_registrations'])) for n,r in results.items() if r.get('shadowed_registrations')])
