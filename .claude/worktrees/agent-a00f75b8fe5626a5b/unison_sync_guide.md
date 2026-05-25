# Unison 同步指南

## 同步架构

```
C:\Users\Mac\.claude\   ←—— Unison SSH ——→   /data/home/zju321/.claude\
                                              ↓ (symlink)
                              /data/home/zju321/.openclaw/.../.claude/memory
```

## 快速开始

### 同步（本地运行）

```powershell
# 方法1: bat 脚本
C:\Users\Mac\.claude\sync_claude.bat

# 方法2: 直接运行
D:\Softwares_new\unison-2.53.8-windows-x86_64\bin\unison.exe claude -batch
```

### 查看状态（不实际同步）

```powershell
D:\Softwares_new\unison-2.53.8-windows-x86_64\bin\unison.exe claude -terse
```

### 服务器端同步（从服务器 SSH 回本地）

```bash
ssh dirac-key "UNISONLOCALHOSTNAME=mu02 /data/home/zju321/softwares/unison-2.53.8-ubuntu-22.04-x86_64-static/bin/unison claude -batch"
```

## 文件位置

| 文件 | 路径 |
|------|------|
| Unison 本地 | `D:\Softwares_new\unison-2.53.8-windows-x86_64\bin\unison.exe` |
| Unison 服务器 | `/data/home/zju321/softwares/unison-2.53.8-ubuntu-22.04-x86_64-static/bin/unison` |
| Profile 配置 | `C:\Users\Mac\.unison\claude.prf` |
| 同步脚本(Win) | `C:\Users\Mac\.claude\sync_claude.bat` |
| 同步脚本(Shell) | `C:\Users\Mac\.claude\sync_claude.sh` |

## 当前同步范围

Profile `claude.prf` 中配置了以下路径：

| 路径 | 说明 |
|------|------|
| `projects` | 项目目录（含所有项目会话） |
| `sessions` | Claude Code 对话历史 |
| `skills` | 技能配置 |
| `memory` | 项目记忆文件 |
| `settings.json` | Claude Code 全局配置 |

已忽略：`backups`、`plugins`、`telemetry`、`shell-snapshots`、`session-env` 等非必要目录。

## 如何新增同步路径

### 场景：想把 `scripts/` 目录也同步

1. 编辑 `C:\Users\Mac\.unison\claude.prf`，在 `path` 部分加一行：
   ```
   path = projects/z---openclaw-workspace-projects-Dirac/scripts
   ```

2. 运行同步：
   ```powershell
   D:\Softwares_new\unison-2.53.8-windows-x86_64\bin\unison.exe claude -batch
   ```

## 如何忽略某些文件

在 `claude.prf` 中添加：

```bash
# 按文件名忽略
ignore = Name .DS_Store
ignore = Name Thumbs.db

# 按路径忽略
ignore = Path session-env
ignore = Path telemetry
ignore = Path backups
```

改完运行同步即可生效。

## Profile 完整示例

```bash
# Roots — 两端根目录
root = C:/Users/Mac/.claude
root = ssh://zju321@10.72.212.33//data/home/zju321/.claude

# SSH 连接（使用 dirac-key）
sshargs = -i C:/Users/Mac/.ssh/id_ed25519_dirac

# 服务器 unison 路径（版本必须与本地一致）
servercmd = /data/home/zju321/softwares/unison-2.53.8-ubuntu-22.04-x86_64-static/bin/unison

# 双向自动同步
batch = true

# 同步路径（按需增减）
path = projects
path = sessions
path = skills
path = memory
path = settings.json

# 忽略项
ignore = Name .DS_Store
ignore = Name Thumbs.db
ignore = Path session-env
ignore = Path shell-snapshots
ignore = Path telemetry
ignore = Path backups
ignore = Path plugins
ignore = Path plans

# 重试次数
retry = 3

# 日志
log = true
logfile = C:/Users/Mac/.unison/unison.log
```

## 注意事项

- **版本必须一致**：本地和服务器都用 Unison 2.53.8，否则报 archive 错误
- **首次同步**：会建立 `.unison` archive 文件，后续增量同步会快很多
- **SSH key**：必须能无密码登录，否则同步会卡在认证
- **Symlink**：OpenClaw 的 `.claude/memory` 通过 symlink 指向 Unison 同步目标，两端自动共享同一份记忆
