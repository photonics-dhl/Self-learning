# Protected Directories (Never Delete)

受 `.claude/settings.json` deny 规则保护，禁止递归删除：

| 目录 | 保护原因 |
|------|---------|
| `Obsidian-Vault/` | 知识库核心资产 |
| `academic_rag/chroma_db/` | 向量数据库，重建成本极高 |
| `DHL/` | 研究论文和论文数据库 |
| `.claude/` | 系统配置 |
