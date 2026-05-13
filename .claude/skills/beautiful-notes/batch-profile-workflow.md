# 批量研究者档案生成工作流 (Batch Profile Workflow)

> **定位**: 15位教授分4波批量处理的标准操作流程。确保质量一致性和跨档案交叉验证。

---

## 波次安排

### Wave 1: 领域奠基人 (Pilot)

| # | 教授 | 优先级 | 原因 |
|---|------|--------|------|
| 1 | **Ferenc Krausz** | P0 | Nobel context, 论文最多，故事最完整 |
| 2 | **Anne L'Huillier** | P0 | 第二位Nobel, 高次谐波理论奠基 |

**目的**: 建立质量基线，验证模板和评分矩阵是否可操作。

### Wave 2: 方法开发者

| # | 教授 | 优先级 |
|---|------|--------|
| 3 | **Ursula Keller** | P1 |
| 4 | **Mauro Nisoli** | P1 |
| 5 | **Margaret Murnane** | P1 |

### Wave 3: 应用与拓展

| # | 教授 | 优先级 |
|---|------|--------|
| 6 | **Claus Ropers** | P1 |
| 7 | **Franz X Kärtner** | P1 |
| 8 | **Matthias Kling** | P1 |
| 9 | **Peter Hommelhoff** | P1 |
| 10 | **Peter Baum** | P1 |

### Wave 4: 专精方向

| # | 教授 | 优先级 |
|---|------|--------|
| 11 | **Rupert Huber** | P2 |
| 12 | **Zenghu Chang** | P2 |
| 13 | **Stephen Leone** | P2 |
| 14 | **Nuh Gedik** | P2 |
| 15 | **Jianwei Miao** | P2 |

---

## 单篇档案生成流程

```
┌─────────────────────────────────────────────────────────┐
│  1. researcher-profiler                                 │
│     ├── Zotero collection items → paper list            │
│     ├── Semantic Scholar → author profile, citations    │
│     ├── Cluster analysis → topic groups, method fingerprint│
│     └── Output: Researcher Corpus Card                  │
│                         ↓                               │
│  2. note-planner                                        │
│     ├── Scan Postdoc方向/ for existing profiles         │
│     ├── Relationship analysis (META_SYNTHESIS)          │
│     ├── Trajectory analysis card                        │
│     └── Output: Planning Card                           │
│                         ↓                               │
│  3. note-generator                                      │
│     ├── Apply researcher-profile 8-section template     │
│     ├── Apply knowledge-structure principles            │
│     ├── Generate Mermaid diagrams & tables              │
│     └── Output: Obsidian note (*.md)                    │
│                         ↓                               │
│  4. note-reviewer                                       │
│     ├── Phase 1: Planning compliance                    │
│     ├── Phase 2: Formatting check                       │
│     ├── Phase 3: Top-journal rubric scoring (9 dims)    │
│     └── Output: Review report + score                   │
│                         ↓                               │
│  Score < 18?  →  Revise (max 3 cycles)                  │
│  Score ≥ 18?  →  Save to vault                          │
│  Score ≥ 24?  →  "Publishable" quality                  │
└─────────────────────────────────────────────────────────┘
```

---

## 波间质量控制

### 每波完成后执行

1. **跨档案一致性检查**
   - 同一研究方向在不同教授档案中描述一致吗？
   - 教授间的对比关系是双向一致的吗？
   - 术语统一吗？

2. **README 更新**
   - 更新横向对比矩阵
   - 更新"按研究方向聚类"表
   - 标记已完成档案的状态

3. **评审回溯**
   - 如果某位教授在后来教授的档案中被频繁提及，回去补充到前者的"七、与其他研究者关系"

### Wave 1 Pilot 特殊流程

1. 生成 Krausz 档案
2. 评分 → 修改（最多3轮）
3. 审核通过后，**不立即进入下一个教授**
4. 根据 Krausz 经验，review 以下是否需调整：
   - researcher-profile.md 模板
   - note-planner 轨迹分析卡
   - note-generator 质量门槛
   - top-journal-rubric 评分维度
5. 调整完成后，生成 L'Huillier 档案
6. 两位档案通过后，交叉对比 Krausz ↔ L'Huillier
7. 确认模板和评分矩阵稳定，再启动 Wave 2

---

## 质量门槛

### 每篇档案最低标准

| 等级 | 条件 | 允许进入下一波？ |
|------|------|:---:|
| **A** (≥24) | 全部 P0=3, P1≥2 | ✅ |
| **B** (≥18) | 全部 P0≥2, P1≥1 | ✅ (标注待优化项) |
| **C** (<18) | 有 P0=1 | ❌ 必须修复 |
| **D** | 有 P0=0 | ❌ 结构性重写 |

### 迭代限制

- 每篇档案最多 **3轮** review→revise
- 3轮后仍不通过 → 标记 `[需人工介入]`，继续处理下一档案
- Wave 完成后，统一处理 `[需人工介入]` 档案

---

## 效率优化

### 可并行步骤

```
同一教授档案内（串行）：
  profiler → planner → generator → reviewer

不同教授档案间（可并行）：
  教授A (profiler) || 教授B (profiler)
  教授A (generator) || 教授B (generator)
```

### Token 管理

- 每个档案估计消耗: profiler (5-10k) + planner (2-3k) + generator (10-20k) + reviewer (3-5k) ≈ 20-40k tokens
- 每波间执行 `/compact` 清理上下文
- 大型论文列表使用引用格式而非完整摘要

---

## 进度追踪表

| Wave | 教授 | 状态 | 评分 | 审核轮次 | 备注 |
|------|------|------|------|---------|------|
| 1 | Krausz | ⏳ | — | — | |
| 1 | L'Huillier | ⏳ | — | — | |
| 2 | Keller | ⏳ | — | — | |
| 2 | Nisoli | ⏳ | — | — | |
| 2 | Murnane | ⏳ | — | — | |
| 3 | Ropers | ⏳ | — | — | |
| 3 | Kärtner | ⏳ | — | — | |
| 3 | Kling | ⏳ | — | — | |
| 3 | Hommelhoff | ⏳ | — | — | |
| 3 | Baum | ⏳ | — | — | |
| 4 | Huber | ⏳ | — | — | |
| 4 | Chang | ⏳ | — | — | |
| 4 | Leone | ⏳ | — | — | |
| 4 | Gedik | ⏳ | — | — | |
| 4 | Miao | ⏳ | — | — | |
