#!/usr/bin/env python3
"""Explicit staged commands; preflight never starts the posterior campaign."""
from pathlib import Path
import argparse,json,sys,atexit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from inference.campaign_runtime import CampaignRuntime
from inference.campaign_training import train_block
from inference.campaign_iid import produce_target,release_raw
from inference.campaign_io import positive_int,write_json_new

def main():
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['preflight','train','produce','release']);p.add_argument('--experiment',type=Path,required=True);p.add_argument('--data',type=Path,required=True);p.add_argument('--table',type=Path,required=True);p.add_argument('--table-manifest',type=Path,required=True);p.add_argument('--validation-config',type=Path,required=True);p.add_argument('--run-config',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--proposals',type=Path);p.add_argument('--raw',type=Path);p.add_argument('--diagnostic',type=Path);p.add_argument('--block',type=int);p.add_argument('--target',type=int);p.add_argument('--backend-factory');p.add_argument('--native-library',type=Path);p.add_argument('--native-build-manifest',type=Path);p.add_argument('--threads',type=int,default=1);p.add_argument('--training-threads',type=int,default=1);p.add_argument('--plan-file',type=Path);p.add_argument('--resume',action='store_true');p.add_argument('--execute',action='store_true');a=p.parse_args()
 runtime=CampaignRuntime(a.experiment,a.data,a.table,a.table_manifest,a.validation_config,a.run_config,backend_factory=a.backend_factory,threads=a.threads,training_threads=a.training_threads,native_library_path=a.native_library,native_build_manifest_path=a.native_build_manifest);atexit.register(runtime.close);report=runtime.preflight()
 if a.stage=='preflight':
  if a.plan_file:write_json_new(a.plan_file,report)
  display={k:v for k,v in report.items() if k not in ('training_blocks','production_blocks')};display['training_block_count']=len(report['training_blocks']);display['production_block_count']=len(report['production_blocks']);print(json.dumps(display,indent=2));return
 if not a.execute:raise RuntimeError('Use --execute for an explicit stage; otherwise choose preflight.')
 if a.target is not None:
  targets=[positive_int(a.target,'target',True)]
 elif a.block is not None:
  block=positive_int(a.block,'block',True)
  blocks=report['training_blocks' if a.stage=='train' else 'production_blocks']
  if block>=len(blocks):raise ValueError('Block outside plan.')
  targets=blocks[block]
 else:raise ValueError('Select --block or --target; the CLI never starts all500 silently.')
 if a.stage=='train':
  rows=train_block(runtime,targets,a.output,resume=a.resume);print(json.dumps({'stage':'train','completed_targets':[r['target'] for r in rows]}));return
 if a.stage=='produce':
  if a.proposals is None or a.raw is None:raise ValueError('Explicit --proposals and --raw paths required.')
  for target in targets:
   row=produce_target(runtime,target,a.proposals,a.output,a.raw,resume=a.resume);print(json.dumps({'stage':'produce','target':target,'status':row['status']}),flush=True)
  return
 if len(targets)!=1 or a.raw is None or a.diagnostic is None:raise ValueError('Release one target with explicit --raw and --diagnostic.')
 row=release_raw(runtime,targets[0],a.output,a.raw,a.diagnostic,resume=a.resume);print(json.dumps(row,indent=2))
if __name__=='__main__':main()
