#!/usr/bin/env python3
"""Generate or verify M1–M5 chapters from the authoritative AI-era method baseline."""
from pathlib import Path
import sys, re

ROOT = Path(__file__).resolve().parents[1]
REFS = next((ROOT/'skills').glob('*/references'))
FULL = REFS/'ai-era-teaching-methods.md'

def derive(text):
    heads = list(re.finditer(r'^## M([1-5])｜[^\n]*$', text, re.M))
    tail = re.search(r'^## 02｜', text, re.M)
    if [int(h.group(1)) for h in heads] != [1,2,3,4,5] or not tail or tail.start() <= heads[-1].start():
        raise ValueError('Unexpected method chapter structure: M1–M5 / 02')
    return {i+1: text[h.start():heads[i+1].start() if i < 4 else tail.start()] for i,h in enumerate(heads)}

def main():
    shards = derive(FULL.read_text(encoding='utf-8'))
    check='--check' in sys.argv
    mismatches=[]
    for num,body in shards.items():
        target=REFS/f'ai-era-m{num}.md'
        if check:
            if not target.is_file() or target.read_text(encoding='utf-8')!=body: mismatches.append(str(target))
        else:
            target.write_text(body,encoding='utf-8')
    if mismatches:
        print('FAIL: shard mismatch:', ', '.join(mismatches));return 1
    print('PASS: M1–M5 shards match authoritative baseline' if check else 'Generated M1–M5 from authoritative baseline')
    return 0

if __name__=='__main__':sys.exit(main())
