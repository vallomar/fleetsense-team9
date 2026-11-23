import json, pathlib, requests, concurrent.futures, hashlib
ROOT=pathlib.Path(__file__).parent
RAW=ROOT/'data/raw'; RAW.mkdir(parents=True,exist_ok=True)
sources=json.loads((ROOT/'sources.json').read_text())
(ROOT/'sources.json').write_text(json.dumps(sources,indent=2))
def get(item):
 url=item['url']; name=url.rsplit('/',1)[-1]; p=RAW/name
 if not p.exists():
  r=requests.get(url,timeout=180); r.raise_for_status(); p.write_bytes(r.content)
 return {'file':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'url':url}
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
  rows=list(ex.map(get,sources))
 (ROOT/'download_manifest.json').write_text(json.dumps(rows,indent=2))
 for r in rows: print(r['file'],r['bytes'])
