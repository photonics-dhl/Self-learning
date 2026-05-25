"""Swap Krausz 图9 (Nobel FIG.17) and 图10 (Nobel FIG.16) to match original lecture order."""
import re

fpath = r'z:\321\DHL\Self_Learning\Obsidian-Vault\2️⃣ 研究方向\Postdoc方向\Krausz.md'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the two figure blocks by looking for their callout starts
# Block A: 图 9 — FIG. 17 (currently first)
# Block B: 图 10 — FIG. 16 (currently second)

# Find the positions
fig9_start = content.find('> [!figure]+ 图 9：')
fig10_start = content.find('> [!figure]+ 图 10：')
fig11_start = content.find('> [!figure]+ 图 11：')

if fig9_start == -1 or fig10_start == -1:
    print('ERROR: Could not find figure blocks')
    exit(1)

# Block A is from fig9_start to fig10_start
# Block B is from fig10_start to fig11_start (or next figure callout)
block_a = content[fig9_start:fig10_start]
block_b = content[fig10_start:fig11_start]

# Swap the figure numbers back (keep 图9, 图10 numbering but swap content)
# Make 图9 = former 图10 content (FIG.16, which should come first)
# Make 图10 = former 图9 content (FIG.17, which should come second)
new_block_a = block_b.replace('图 10：', '图 9：')
new_block_b = block_a.replace('图 9：', '图 10：')

# Rebuild content
new_content = (content[:fig9_start] + new_block_a + new_block_b +
               content[fig11_start:])

with open(fpath, 'w', encoding='utf-8') as f:
    f.write(new_content)

# Verify
with open(fpath, 'r', encoding='utf-8') as f:
    verify = f.read()

# Check new order: FIG.16 should be 图9, FIG.17 should be 图10
import re
fig9_match = re.search(r'图 9：(.+?)(?:FIG\. \d+)', verify[fig9_start:fig9_start+500])
fig10_match = re.search(r'图 10：(.+?)(?:FIG\. \d+)', verify[fig10_start:fig10_start+500])

# More robust: just find the FIG references near the figure headers
for name, fig_num in [('图 9', 'FIG. 16'), ('图 10', 'FIG. 17')]:
    pos = verify.find(f'{name}：')
    snippet = verify[pos:pos+200]
    if fig_num in snippet:
        print(f'OK: {name} now references {fig_num}')
    else:
        print(f'WARNING: {name} may not reference {fig_num}: ...{snippet[:100]}...')
