"""List all mermaid diagram types used in Postdoc profiles."""
import os, re, glob

vault = r'z:\321\DHL\Self_Learning\Obsidian-Vault'
files = glob.glob(os.path.join(vault, '*', '*Postdoc*', '*.md'))

types = {}
for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    blocks = re.findall(r'```mermaid\n(.*?)```', content, re.DOTALL)
    for block in blocks:
        lines = block.strip().split('\n')
        for line in lines:
            clean = line.strip().lstrip('> ').strip()
            if clean and not clean.startswith('%%'):
                t = clean.split()[0]
                fname = os.path.basename(fpath).replace('.md', '')
                types.setdefault(t, []).append(fname)
                break

for t, files in sorted(types.items()):
    print(f'{t}: {len(files)} blocks in {len(set(files))} profiles')
