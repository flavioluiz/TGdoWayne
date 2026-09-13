"""Run a frozen Python worker with read-only relocation of historical file paths.

The worker and input bytes remain unchanged. Python open events that still name
 the original science tree are rejected. This is an I/O audit, not an OS sandbox.
"""
import argparse, builtins, hashlib, io, json, os, runpy, sys, time
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-root',type=Path,required=True)
    parser.add_argument('--clean-root',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('worker')
    parser.add_argument('arguments',nargs=argparse.REMAINDER)
    a=parser.parse_args();old=str(a.original_root.resolve());clean=str(a.clean_root.resolve())
    runtime=str(Path(sys.executable).absolute().parent.parent)
    if clean==old or clean.startswith(old+'/'):raise ValueError('Independent destination required')
    source=Path(clean)/a.worker
    if not source.is_file():raise ValueError('Worker must exist in clean export')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    receipt=a.receipt.resolve()
    if receipt.exists():raise ValueError('Fresh audit receipt required')
    original_open=builtins.open;original_io=io.open;original_os_open=os.open
    mapping={};blocked=[]
    def scientific(p):
        return p.startswith(old+'/') and not p.startswith(runtime+'/')
    def mapped(p):
        if isinstance(p,int):return p
        s=os.fsdecode(p)
        if scientific(s):
            new=clean+s[len(old):];mapping[s]=new
            return os.fsencode(new) if isinstance(p,bytes) else new
        return p
    def audit(event,args):
        if event=='open' and not isinstance(args[0],int):
            s=os.fsdecode(args[0])
            if scientific(s):
                blocked.append(s);raise PermissionError('Original scientific tree denied: '+s)
    sys.addaudithook(audit)
    try:
        original_open(old+'/project_status.json','rb')
    except PermissionError:negative_control=True
    else:raise AssertionError('I/O guard negative control failed')
    def op(p,*args,**kw):return original_open(mapped(p),*args,**kw)
    def iop(p,*args,**kw):return original_io(mapped(p),*args,**kw)
    def osp(p,*args,**kw):return original_os_open(mapped(p),*args,**kw)
    builtins.open=op;io.open=iop;os.open=osp
    for name in ('stat','lstat','access','listdir','scandir','readlink'):
        fn=getattr(os,name)
        def wrap(p='.',*args,_fn=fn,**kw):return _fn(mapped(p),*args,**kw)
        setattr(os,name,wrap)
    os.chdir(clean);sys.path.insert(0,str(source.parent));sys.argv=[str(source),*a.arguments]
    start=time.monotonic();failure=None
    try:
        runpy.run_path(str(source),run_name='__main__')
    except SystemExit as exc:
        if exc.code not in (None,0):failure=repr(exc);raise
    except BaseException as exc:
        failure=repr(exc);raise
    finally:
        result=dict(worker=a.worker,worker_sha256=digest,arguments=a.arguments,original_root=old,clean_root=clean,
                    negative_control_passed=negative_control,blocked_reads=blocked,
                    mapped_paths=mapping,wall_seconds=time.monotonic()-start,failure=failure,
                    scope='Python file-I/O relocation audit; no original scientific input opened. Runtime dependencies reused.')
        with original_open(receipt,'x') as f:json.dump(result,f,indent=2);f.write('\n')

if __name__=='__main__':main()
