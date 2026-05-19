import os, re, json
from collections import defaultdict

vault = r'z:\321\DHL\Self_Learning\Obsidian-Vault'
profiles_dir = os.path.join(vault, '2️⃣ 研究方向', 'Postdoc方向')
viz_dir = os.path.join(vault, '6️⃣ 工具', 'visualizations')

output_path = r'z:\321\DHL\Self_Learning\.claude\scripts\audit_result.txt'
lines = []

def p(s=''):
    lines.append(str(s))

profiles = {}
for fn in os.listdir(profiles_dir):
    if fn.endswith('.md') and fn != 'README.md':
        fpath = os.path.join(profiles_dir, fn)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        imgs = re.findall(r'!\[\[(6[^]]+visualizations[^]]+)\]\]', content)
        profiles[fn] = {'path': fpath, 'images': imgs, 'img_count': len(imgs)}

all_viz_files = set()
hash_dir_files = defaultdict(list)
if os.path.exists(viz_dir):
    for root, dirs, files in os.walk(viz_dir):
        for fname in files:
            if fname.endswith(('.png', '.jpg', '.jpeg')):
                all_viz_files.add(os.path.join(root, fname))
                hash_dir_files[os.path.basename(root)].append(fname)

p("=== IMAGE AUDIT ===")
p(f"Profiles: {len(profiles)}")
total = sum(pdata['img_count'] for pdata in profiles.values())
p(f"Total image refs: {total}")

# Duplicates
img_ref_counts = defaultdict(list)
for pname, pdata in profiles.items():
    for img in pdata['images']:
        img_ref_counts[img].append(pname.replace('.md', ''))

p("\n--- DUPLICATE IMAGES (same file used in multiple places) ---")
found = False
for img, users in img_ref_counts.items():
    if len(users) > 1:
        found = True
        p(f"  {img}: {users}")
if not found:
    p("  None")

# Broken refs
p("\n--- BROKEN REFERENCES ---")
broken = 0
for pname, pdata in profiles.items():
    for img in pdata['images']:
        norm = img.replace('/', os.sep)
        if not os.path.exists(os.path.join(vault, norm)):
            p(f"  [{pname}] {img}")
            broken += 1
if broken == 0:
    p("  None")

# Unused images (files in viz_dir not referenced by any profile)
p("\n--- UNUSED IMAGES ---")
all_refs_full = set()
for pdata in profiles.values():
    for img in pdata['images']:
        all_refs_full.add(os.path.join(vault, img.replace('/', os.sep)))
unused = all_viz_files - all_refs_full
if unused:
    for u in sorted(unused):
        p(f"  {os.path.relpath(u, vault)}")
else:
    p("  None")

# Per profile
p("\n--- PER-PROFILE IMAGE COUNT ---")
for pname in sorted(profiles.keys()):
    p(f"  {pname.replace('.md','')}: {profiles[pname]['img_count']} images")

# Hash dir sharing
p("\n--- HASH DIR SHARING ---")
hash_to_profiles = defaultdict(set)
for pname, pdata in profiles.items():
    for img in pdata['images']:
        parts = img.split('/')
        if len(parts) >= 3:
            hash_to_profiles[parts[2]].add(pname.replace('.md', ''))

shared = False
for h, ps in sorted(hash_to_profiles.items()):
    if len(ps) > 1:
        shared = True
        p(f"  SHARED: {h} -> {ps}")
if not shared:
    p("  No cross-profile hash sharing")

# Hash dirs with unused files
p("\n--- HASH DIRS WITH UNUSED/EXTRA FILES ---")
for h, ps in sorted(hash_to_profiles.items()):
    if len(ps) == 1:
        files_in_dir = hash_dir_files.get(h, [])
        profile_name = list(ps)[0] + '.md'
        if profile_name in profiles:
            used_count = sum(1 for img in profiles[profile_name]['images'] if h in img)
            if len(files_in_dir) != used_count:
                p(f"  {h}: {len(files_in_dir)} files in dir, {used_count} used by {list(ps)[0]}")

with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f'Results written to {output_path}')
for line in lines:
    try:
        print(line)
    except:
        print('[encoding error, see output file]')
