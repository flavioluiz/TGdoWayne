"""Download the C10 release archives, checking sizes and SHA-256 before use."""
from pathlib import Path
import argparse, hashlib, json, os, urllib.request
R = Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--destination',type=Path,default=R,help='Project root receiving the archive paths')
    a=p.parse_args();root=a.destination.resolve()
    catalog=json.loads((R/'results/C10/production_reproducibility/distribution.json').read_text())
    for entry in catalog['assets']:
        path=root/entry['path'];assert path.resolve().is_relative_to(root)
        if path.exists():
            assert path.stat().st_size==entry['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],str(path)
            print('Verified existing '+path.name,flush=True);continue
        path.parent.mkdir(parents=True,exist_ok=True);partial=path.with_suffix(path.suffix+'.part')
        digest=hashlib.sha256();size=0
        with urllib.request.urlopen(entry['url'],timeout=120) as response,partial.open('wb') as output:
            while data:=response.read(1024*1024):
                size+=len(data);assert size<=entry['bytes'],'Unexpected download size'
                output.write(data);digest.update(data)
        assert size==entry['bytes'] and digest.hexdigest()==entry['sha256'],'Download integrity failure: '+path.name
        os.replace(partial,path);print('Downloaded and verified '+path.name,flush=True)


if __name__=='__main__':main()
