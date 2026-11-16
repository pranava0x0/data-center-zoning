"""Optional, local-only token meter. Reads just identified chat and its direct children;
publishes aggregates only (no chat, prompts, credentials or account information).
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # scripts/ on the import path
import argparse, json, os
from pathlib import Path
import lib.discovery as c
def main():
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True,nargs='+');p.add_argument('--thread',default=os.environ.get('CODEX_THREAD_ID'));a=p.parse_args()
    if not a.thread:raise SystemExit('Supply --thread for the specific session family.')
    result={}
    for file in sorted({f for day in a.directory for f in day.glob('*.jsonl')}):
        with file.open() as f:
            try:h=json.loads(f.readline())['payload']
            except (ValueError,KeyError):continue
            parent=h.get('source');child=parent.get('subagent',{}).get('thread_spawn',{}) if isinstance(parent,dict) else {}
            if h.get('id')!=a.thread and child.get('parent_thread_id')!=a.thread:continue
            role=child.get('agent_path','coordinator');total=None
            for line in f:
                if '"token_count"' not in line:continue
                try:
                    d=json.loads(line)['payload']
                    if d.get('type')=='token_count' and d.get('info',{}):total=d['info']['total_token_usage']
                except (ValueError,KeyError):continue
            if total:result[role]={k:total[k] for k in ('input_tokens','cached_input_tokens','output_tokens','total_tokens')}
    if not result:raise SystemExit('No matched local usage events; no estimate invented.')
    totals={k:sum(x[k] for x in result.values()) for k in next(iter(result.values()))}
    c.dump(c.OUT/'token_usage.json',dict(measured_utc=c.now(),measurement='Latest cumulative usage event in each cooperating chat; cached tokens included in input. Snapshot taken before final reply; not an invoice.',roles=result,total=totals,uncached_input=totals['input_tokens']-totals['cached_input_tokens']))
if __name__=='__main__':main()
