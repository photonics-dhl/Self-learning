#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix mermaid dark theme: add %%{init: {'theme': 'base'}}%% to all mermaid blocks."""
import re
import os
import glob
import sys
sys.stdout.reconfigure(encoding='utf-8')

VAULT_DIR = r'Obsidian-Vault'
postdoc_dirs = glob.glob(os.path.join(VAULT_DIR, '*', '*Postdoc*'))
if not postdoc_dirs:
    print('ERROR: Postdoc dir not found')
    sys.exit(1)

PD = postdoc_dirs[0]
files = sorted(glob.glob(os.path.join(PD, '*.md')))

fixed = 0
for fpath in files:
    name = os.path.basename(fpath)
    with open(fpath, encoding='utf-8') as f:
        text = f.read()

    original = text

    # Fix callout-wrapped mermaid blocks:
    # "> ```mermaid\n> timeline" or "> ```mermaid\n> graph"
    text = re.sub(
        r'(> ```mermaid\n)',
        r'\1> %%{init: {"theme": "base"}}%%\n',
        text
    )

    # Fix non-callout mermaid blocks (README.md):
    # "```mermaid\ngraph"
    text = re.sub(
        r'(```mermaid\n)(graph\w*\s)',
        r'\1%%{init: {"theme": "base"}}%%\n\2',
        text
    )

    if text != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(text)
        blocks_before = original.count('```mermaid')
        blocks_after = text.count('```mermaid')
        print(f'  {name}: {blocks_before} blocks fixed')
        fixed += blocks_before

print(f'\nTotal: {fixed} mermaid blocks fixed across {len(files)} files')
