#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test multimodal analyzer"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from academic_rag.db.models import Figure
from academic_rag.processors.multimodal_analyzer import MultimodalAnalyzer

# Use ASCII-safe path
fig_path = 'Obsidian-Vault/6️⃣ 工具/visualizations/Zhang2022_TiltedPulseFront/Zhang2022_TiltedPulseFront_p2_i1.png'

print('Path exists:', os.path.exists(fig_path))

analyzer = MultimodalAnalyzer()

fig = Figure(
    figure_id='test_001',
    figure_label='Fig. 1',
    figure_caption='Experimental setup for tilted pulse-front THz generation',
    image_path=fig_path,
    page_num=1,
)

print('Analyzing figure...')
analysis = analyzer.analyze_figure(fig, context='Zhang 2022, Optics Letters - THz pulse generation')

print()
print('=== Analysis Result ===')
print('Description:', analysis.description)
print('Key Findings:', analysis.key_findings)
print('Related Concepts:', analysis.related_concepts)
print('Suggested Knowledge Points:', analysis.suggested_knowledge_points)
print('Figure Type:', analysis.figure_type)
