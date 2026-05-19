import os

vault = r'z:\321\DHL\Self_Learning\Obsidian-Vault'
found = []
for root, dirs, files in os.walk(vault):
    if 'fb7a6fbb' in dirs:
        found.append(os.path.join(root, 'fb7a6fbb'))
        break  # stop after first match

out_lines = []
for d in found:
    out_lines.append(f'DIR: {d}')
    for fn in sorted(os.listdir(d)):
        fp = os.path.join(d, fn)
        out_lines.append(f'  {fn} ({os.path.getsize(fp)} bytes)')

with open(r'z:\321\DHL\Self_Learning\.claude\scripts\huber_paths.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines))
print('Done')
