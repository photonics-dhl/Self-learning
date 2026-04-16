#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量分析图片内容"""

import sys, json
sys.path.insert(0, '.')

from academic_rag.processors.multimodal_analyzer import MultimodalAnalyzer
from academic_rag.db.models import Figure

analyzer = MultimodalAnalyzer()

# 分析太赫兹成像笔记中引用的关键图片
images = [
    ('Bitzer_p4_i0', 'Obsidian-Vault/6️⃣ 工具/visualizations/Bitzer2010_NearField/Bitzer2010_NearField_p4_i0.jpeg', 'Bitzer 2010 near-field imaging'),
    ('Bitzer_p5_i0', 'Obsidian-Vault/6️⃣ 工具/visualizations/Bitzer2010_NearField/Bitzer2010_NearField_p5_i0.jpeg', 'Bitzer 2010 imaging result'),
    ('Chen_p2_i0', 'Obsidian-Vault/6️⃣ 工具/visualizations/Chen2019_Compressive/Chen2019_Compressive_p2_i0.jpeg', 'Chen 2019 compressive sensing'),
    ('Heindl_p2_i1', 'Obsidian-Vault/6️⃣ 工具/visualizations/Heindl2022_QuantumDot/Heindl2022_QuantumDot_p2_i1.jpeg', 'Heindl 2022 quantum dot THz'),
]

results = {}
for name, path, ctx in images:
    fig = Figure(figure_id=name, figure_label=name, image_path=path, page_num=1)
    try:
        result = analyzer.analyze_figure(fig, context=ctx)
        results[name] = result.to_dict()
        print(f'[OK] {name}: {result.description[:80]}...')
    except Exception as e:
        print(f'[FAIL] {name}: {e}')
        results[name] = {'error': str(e)}

with open('image_analysis_batch.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('\\nAnalysis saved to image_analysis_batch.json')
