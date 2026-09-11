#!/usr/bin/env python3
"""Lossless bounded gzip parts for large immutable numerical artifacts.

Only standard-library byte transport; no NumPy deserialization or validation
of scientific content. The original whole-file SHA256 is preserved.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,os,re,shutil,tempfile

SCHEMA='BOUNDED_GZIP_PARTS_v1'
BLOCK=1024**2

def require(value,message):
    if not value:raise ValueError(message)
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(BLOCK),b''):h.update(block)
    return h.hexdigest()
def integer(x,name,maximum):
    require(type(x) is int and 0<x<=maximum,'Invalid '+name)
    return x
def fresh_path(path):
    p=Path(path).absolute();require(not p.exists() and not p.is_symlink() and p.parent.is_dir(),'A new destination under an existing parent is required.')
    return p.parent.resolve()/p.name

def pack(source,output,*,expected_sha256,maximum_part_bytes=90*1024**2):
    source=Path(source).absolute();output=fresh_path(output)
    require(source.is_file() and not source.is_symlink(),'A regular nonsymlink source is required.')
    require(re.fullmatch('[0-9a-f]{64}',expected_sha256 or '') is not None,'Explicit expected source SHA256 required.')
    integer(maximum_part_bytes,'part limit',99_999_999)
    before=source.stat();require(before.st_size>0,'Nonempty source required.')
    with tempfile.TemporaryDirectory(prefix='.gzip_parts_',dir=output.parent) as temp:
        stage=Path(temp);compressed=stage/'payload.gz';h=hashlib.sha256();count=0
        with source.open('rb') as src,compressed.open('xb') as raw:
            with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0,compresslevel=6) as dst:
                for block in iter(lambda:src.read(BLOCK),b''):
                    count+=len(block);h.update(block);dst.write(block)
        after=source.stat()
        require((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns) and count==before.st_size and h.hexdigest()==expected_sha256,'Source changed or differs from the approved SHA256.')
        parts=[]
        with compressed.open('rb') as src:
            index=0
            while True:
                block=src.read(min(BLOCK,maximum_part_bytes))
                if not block:break
                path=stage/f'payload.gz.part{index:04d}';h=hashlib.sha256();used=0
                with path.open('xb') as dst:
                    while block:
                        dst.write(block);h.update(block);used+=len(block)
                        if used==maximum_part_bytes:break
                        block=src.read(min(BLOCK,maximum_part_bytes-used))
                parts.append(dict(file=path.name,bytes=used,sha256=h.hexdigest()));index+=1
        compressed_bytes=compressed.stat().st_size;compressed_sha=digest(compressed)
        compressed.unlink() # Only this tool's private staging stream.
        manifest=dict(schema=SCHEMA,status='LOSSLESS_BYTES_NO_SCIENTIFIC_VALIDATION',source_name=source.name,
            original_bytes=count,original_sha256=expected_sha256,compression='gzip_mtime0_level6',
            compressed_bytes=compressed_bytes,compressed_sha256=compressed_sha,
            maximum_part_bytes=maximum_part_bytes,parts=parts,scientific_content_deserialized=False)
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
        shutil.copyfile(__file__,stage/'compactar_arquivo.py')
        (stage/'README.md').write_text('# Arquivo numérico em partes\n\n'
            'As partes conservam todos os bytes do arquivo original, incluindo metadados internos. '
            'Nenhum float foi arredondado ou reconstruído.\n\n'
            'Restaurar com `python3 compactar_arquivo.py unpack --bundle . --output /caminho/novo.npz`. '
            'O destino deve ser novo. O comando verifica cada parte, o fluxo gzip e o SHA256 original. '
            'Os hashes garantem integridade em relação ao manifesto versionado, não validação científica.\n')
        require(not output.exists(),'Output appeared during packing.')
        os.rename(stage,output)
    return manifest

def unpack(bundle,output,*,maximum_output_bytes=2*1024**3):
    bundle=Path(bundle).absolute();output=fresh_path(output)
    require(bundle.is_dir() and not bundle.is_symlink(),'Real bundle directory required.')
    integer(maximum_output_bytes,'output byte limit',64*1024**3)
    m=json.loads((bundle/'manifest.json').read_text())
    require(m.get('schema')==SCHEMA and m.get('status')=='LOSSLESS_BYTES_NO_SCIENTIFIC_VALIDATION' and m.get('compression')=='gzip_mtime0_level6','Unknown byte archive schema.')
    integer(m['original_bytes'],'original length',maximum_output_bytes)
    cap=integer(m['maximum_part_bytes'],'part limit',99_999_999)
    parts=m['parts'];require(isinstance(parts,list) and parts,'Nonempty part inventory required.')
    require([p['file'] for p in parts]==[f'payload.gz.part{i:04d}' for i in range(len(parts))],'Part sequence/path is invalid.')
    require(sum(integer(p['bytes'],'part bytes',cap) for p in parts)==m['compressed_bytes'],'Compressed size differs.')
    require(all(p['bytes']==cap for p in parts[:-1]),'Only the final part may be short.')
    with tempfile.TemporaryDirectory(prefix='.gzip_restore_',dir=output.parent) as temp:
        stage=Path(temp);compressed=stage/'payload.gz';whole=hashlib.sha256()
        with compressed.open('xb') as dst:
            for part in parts:
                path=bundle/part['file'];require(path.is_file() and not path.is_symlink() and path.stat().st_size==part['bytes'],'Missing, unsafe, or differently sized part.')
                h=hashlib.sha256();n=0
                with path.open('rb') as src:
                    for block in iter(lambda:src.read(BLOCK),b''):
                        n+=len(block);require(n<=part['bytes'],'Part changed during read.');h.update(block);whole.update(block);dst.write(block)
                require(n==part['bytes'] and h.hexdigest()==part['sha256'],'Part SHA256 differs.')
        require(whole.hexdigest()==m['compressed_sha256'],'Compressed whole-file SHA256 differs.')
        restored=stage/'restored';h=hashlib.sha256();n=0
        with gzip.open(compressed,'rb') as src,restored.open('xb') as dst:
            for block in iter(lambda:src.read(BLOCK),b''):
                n+=len(block);require(n<=m['original_bytes'],'Decompressed output exceeds declared length.');h.update(block);dst.write(block)
        require(n==m['original_bytes'] and h.hexdigest()==m['original_sha256'],'Restored whole-file SHA256/length differs.')
        # Same-filesystem exclusive creation publishes verified bytes without
        # overwriting a destination that appeared after the initial check.
        os.link(restored,output)
    return dict(status='RESTORED_EXACT_ORIGINAL_BYTES',bytes=n,sha256=h.hexdigest(),scientific_validation_claimed=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    a=s.add_parser('pack');a.add_argument('--source',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    a.add_argument('--expected-sha256',required=True);a.add_argument('--maximum-part-bytes',type=int,default=90*1024**2)
    a=s.add_parser('unpack');a.add_argument('--bundle',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--maximum-output-bytes',type=int,default=2*1024**3)
    a=p.parse_args()
    if a.command=='pack':r=pack(a.source,a.output,expected_sha256=a.expected_sha256,maximum_part_bytes=a.maximum_part_bytes)
    else:r=unpack(a.bundle,a.output,maximum_output_bytes=a.maximum_output_bytes)
    print(json.dumps(r,sort_keys=True))
