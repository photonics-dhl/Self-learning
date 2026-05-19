import hashlib, os, glob, sys

vault = r'z:\321\DHL\Self_Learning\Obsidian-Vault'
matches = glob.glob(os.path.join(vault, '*', 'visualizations', 'fb7a6fbb'))
if not matches:
    matches = glob.glob(os.path.join(vault, '**', 'visualizations', 'fb7a6fbb'), recursive=True)

out = [f"Found: {len(matches)} dirs"]
if matches:
    d = matches[0]
    out.append(f"Dir: {d}")
    for fn in sorted(os.listdir(d)):
        p = os.path.join(d, fn)
        s = os.path.getsize(p)
        with open(p, 'rb') as f:
            h = hashlib.md5(f.read()).hexdigest()
        out.append(f'{fn}: {s}B MD5={h}')
    # Show which ones are used
    out.append('\n--- Used in Huber profile ---')
    used = ['fb7a6fbb9e308ee2_p02_f00.png', 'fb7a6fbb9e308ee2_p03_f02.png', 'fb7a6fbb9e308ee2_p03_f03.png']
    for fn in used:
        out.append(f'  USED: {fn}')
    unused = [x for x in os.listdir(d) if x not in used]
    out.append(f'\n--- Unused ---')
    for fn in sorted(unused):
        out.append(f'  UNUSED: {fn}')

result = '\n'.join(out)
with open(r'z:\321\DHL\Self_Learning\.claude\scripts\huber_check.txt', 'w', encoding='utf-8') as f:
    f.write(result)
print('Done - see huber_check.txt')
