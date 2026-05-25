"""Replace mermaid theme from 'base' to 'default' in all Postdoc profiles."""
import os
import glob

vault = r'z:\321\DHL\Self_Learning\Obsidian-Vault'
pattern = os.path.join(vault, '*', '*Postdoc*', '*.md')
files = glob.glob(pattern)
print(f'Found {len(files)} files')

total_blocks = 0
for fpath in files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    count = content.count('"theme": "base"')
    if count > 0:
        content = content.replace('"theme": "base"', '"theme": "default"')
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        total_blocks += count
        print(f'  [{count} blocks] {os.path.basename(fpath)}')

print(f'Total blocks replaced: {total_blocks}')
