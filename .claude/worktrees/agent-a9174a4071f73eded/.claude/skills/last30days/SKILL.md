---
name: last30days
description: |
  热门讨论聚合技能。研究任意话题在 Reddit、X、YouTube、HN、Polymarket、GitHub 等平台上的讨论，
  并按真实互动数据（点赞、评论、Polymarket 赔率）合成摘要。
  当用户询问"最近的趋势"、"热门讨论"、"某话题的舆论"时触发。
tags:
  - research
  - social-media
  - trending
  - reddit
  - github
---

# Last30Days Skill

多源社交研究技能，聚合 Reddit、Hacker News、Polymarket、GitHub 等平台的热门讨论。

## 快速使用

```bash
# 基本研究
last30days "AI Agents 最新进展"

# 深度研究
last30days "量子计算" --deep

# 指定来源
last30days "Llama 3" --search reddit,github
```

## 数据源

### 免费源 (零配置)

- Reddit (含评论)
- Hacker News
- Polymarket
- GitHub

### 可选付费源

- X/Twitter (需登录)
- YouTube (需 yt-dlp)
- TikTok/Instagram/Threads (需 ScrapeCreators)
- Perplexity Sonar (需 OpenRouter key)

## 输出格式

```bash
# 紧凑输出 (默认)
last30days "话题"

# JSON 格式
last30days "话题" --emit json

# 上下文格式 (用于 LLM)
last30days "话题" --emit context
```

## 高级用法

```bash
# GitHub 用户模式
last30days --github-user steipete

# GitHub 仓库模式
last30days --github-repo openclaw/openclaw

# 深度研究 (使用 Perplexity)
last30days "话题" --deep-research
```

## 依赖

- Python 3.12+
- API keys (可选，用于付费源)

## 安装

```bash
git clone https://github.com/mvanhorn/last30days-skill.git ~/.claude/skills/last30days
```
