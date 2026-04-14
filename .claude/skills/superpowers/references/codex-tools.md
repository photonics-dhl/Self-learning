# Codex Tool Mapping

Skills use Claude Code tool names. When you encounter these in a skill, use your platform equivalent:

(This document provides guidance for adapting Claude Code skills to work with Codex, covering tool mappings, multi-agent setup, and platform-specific considerations.)

## Tool Mappings

| Claude Code | Codex |
|-------------|-------|
| `Task` tool | `spawn_agent` |
| `TodoWrite` | `update_plan` |
| `Read` | `Read` |
| `Write` | `Write` |
| `Edit` | `Edit` |
| `Bash` | `Bash` |
| `Grep` | `Grep` |
| `Glob` | `Glob` |

## Multi-Agent Setup

Requires enabling `multi_agent = true` in the config file.

## Named Agent Dispatch

Since Codex lacks a named agent registry, you must:
1. Locate the agent's prompt file
2. Read it
3. Fill template placeholders
4. Spawn a `worker` agent with that content

## Message Framing

Use task-delegation style ("Your task is...") wrapped in XML tags for instruction clarity.

## Environment Detection

Use git commands to detect worktree status and handle detached HEAD scenarios.

## Sandbox Finishing

When operations are blocked, commit work and provide:
- Suggested branch names
- Commit messages
- PR descriptions for manual completion
