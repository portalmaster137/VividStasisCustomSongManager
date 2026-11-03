#!/usr/bin/env python3
"""Evaluate the real ImHex pattern runtime on a chart corpus (requires plcli)."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,subprocess,time

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--runtime',type=Path,required=True);p.add_argument('--includes',type=Path,required=True)
 p.add_argument('--charts',type=Path,default=Path('vividstasis/Charts'));p.add_argument('--pattern',type=Path,default=Path('patterns/vividstasis_vsb.hexpat'))
 p.add_argument('--output',type=Path,default=Path('analysis/chart_format/imhex_validation.json'));p.add_argument('--jobs',type=int,default=4)
 a=p.parse_args();files=sorted(a.charts.rglob('*.vsb'));start=time.monotonic()
 def run(path):
  command=[str(a.runtime),'run','-p',str(a.pattern),'-i',str(path),'-I',str(a.includes)]
  try:
   r=subprocess.run(command,capture_output=True,text=True,timeout=120)
   result=dict(path=str(path),returncode=r.returncode)
   if r.returncode:result.update(stdout=r.stdout[-8000:],stderr=r.stderr[-8000:])
   return result
  except subprocess.TimeoutExpired:return dict(path=str(path),returncode=None,error='120 second timeout')
 records=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:
  for row in pool.map(run,files):
   records.append(row)
   if len(records)%100==0:print('Evaluated',len(records),'/',len(files),flush=True)
 errors=[r for r in records if r['returncode']!=0]
 report=dict(runtime=str(a.runtime),runtime_sha256=hashlib.sha256(a.runtime.read_bytes()).hexdigest(),runtime_source='Cached ImHex 1.38.1 PatternLanguage, standalone plcli build',pattern=str(a.pattern),pattern_sha256=hashlib.sha256(a.pattern.read_bytes()).hexdigest(),includes=str(a.includes),files=len(records),passed=len(records)-len(errors),failures=errors,elapsed_seconds=round(time.monotonic()-start,2),results=records)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
 print('Pattern runtime:',report['passed'],'passed;',len(errors),'failed')
 if errors:raise SystemExit(1)
if __name__=='__main__':main()
