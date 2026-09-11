#!/usr/bin/env python3
"""Separate, explicitly truth-reading diagnostic of identified completed targets."""
from pathlib import Path
import argparse, atexit, json, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from inference.campaign_runtime import CampaignRuntime
from inference.campaign_diagnostics import diagnose_target
from inference.campaign_io import positive_int


def main():
    parser=argparse.ArgumentParser()
    for name in ('experiment','data','table','table_manifest','validation_config','run_config',
                 'production','raw','truth_data','truth_logl','protocol','output'):
        parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    parser.add_argument('--native-library',type=Path);parser.add_argument('--native-build-manifest',type=Path)
    parser.add_argument('--backend-factory');parser.add_argument('--training-threads',type=int,default=1)
    parser.add_argument('--threads',type=int,default=1);parser.add_argument('--target',type=int)
    parser.add_argument('--block',type=int);parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    runtime=CampaignRuntime(args.experiment,args.data,args.table,args.table_manifest,args.validation_config,args.run_config,
        backend_factory=args.backend_factory,threads=args.threads,training_threads=args.training_threads,
        native_library_path=args.native_library,native_build_manifest_path=args.native_build_manifest)
    atexit.register(runtime.close)
    if (args.target is None)==(args.block is None):raise ValueError('Select exactly one --target or --block.')
    if args.target is not None:targets=[positive_int(args.target,'target',True)]
    else:
        blocks=runtime.preflight()['production_blocks'];index=positive_int(args.block,'block',True)
        if index>=len(blocks):raise ValueError('Block outside campaign.')
        targets=blocks[index]
    for target in targets:
        result=diagnose_target(runtime,args.production/f'target_{target:06d}.json',args.raw,args.truth_data,
            args.protocol,args.output,truth_loglikelihood_path=args.truth_logl,resume=args.resume)
        print(json.dumps(dict(target=target,status=result['status'],cdf_precision_pass=result['summary']['cdf_precision_pass'],
            max_mcse=result['summary']['maximum_finite_high_mcse'],seconds=result['seconds'])),flush=True)

if __name__=='__main__':main()
