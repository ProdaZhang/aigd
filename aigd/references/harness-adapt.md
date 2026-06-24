# 跨 harness 适配（Claude Code / Codex / Gemini CLI / Copilot CLI）

> AIGD 的**包结构跨 harness 通用**:Claude Code / ZCode / Gemini CLI / Codex 都用"一个子目录 + `SKILL.md`(`name`/`description` frontmatter)"这套 skill 格式,子 skill 用 `../aigd/references/` 取方法论的相对路径在哪家都成立(只要 7 个文件夹平级)。**Copilot CLI(1.0.63)经实测无此 skills 机制**,需另行适配——详见下「实测状态」。
> 不同的只有三件:**装哪个目录、怎么唤起、读写/跑命令用哪个工具名**。本页一次说清。方法论正文一律"说动作"(读/写/跑/搜),工具名按本表对应到你的 harness。

---

## 0. 实测状态（2026-06-23）

下表是**实际装跑过的结果**,不是纸面推断:

| harness | 版本 | 装入 | 发现 | 路由 | 执行 |
|---------|------|------|------|------|------|
| Claude Code（原生·真项目） | — | ✅ | ✅ | ✅ | ✅ |
| ZCode（Claude 系桌面端） | 3.1.3 | ✅ | ✅ | ✅ | ✅ |
| Gemini CLI（Google·跨厂） | 0.47 | ✅ | ✅ | ✅ | ✅ |
| Codex（OpenAI·跨厂） | 0.140 | ✅ | ✅ | ✅ | ✅ |
| Copilot CLI（GitHub） | 1.0.63 | ❌ 无 skills 机制 | — | — | — |

- **Gemini**:`gemini skills install https://github.com/<owner>/<repo>`(不带 `--path` 会发现仓库内全部 skill 一次装齐),装到 `~/.gemini/skills/`。免费 OAuth 个人档已被 Google 下线(提示迁移 Antigravity)→ 用 AI Studio 的 `GEMINI_API_KEY`。
- **Codex**:用户 skill 放 `$CODEX_HOME/skills/<名>`(默认 `~/.codex/skills/`),与内置 `.system` 平级;**装完需重启 Codex**。也可让其自带 skill-installer 从 GitHub 装:`install-skill-from-github.py --repo <owner>/<repo> --path aigd aigd-concept …`(一条多 `--path` 装多个)。
- **Copilot CLI 1.0.63**:命令只有 `login/mcp/plugin/init/config…`,无 skills 概念;aigd 这套 SKILL.md 装不进,要用得改走 `AGENTS.md`/MCP/plugin 适配。
- 结论:SKILL.md skill 机制在 **Claude Code / ZCode / Gemini / Codex** 通用且实测跑通(含 Gemini、Codex 两个跨厂);**Copilot 当前不兼容**。

---

## 1. 装哪 + 怎么唤起

| harness | skills 目录 | 唤起方式 | 指令文件(本包不依赖) |
|---------|------------|----------|----------------------|
| **Claude Code** | `.claude/skills/`(项目) 或 `~/.claude/skills/`(用户) | `Skill` 工具 | `CLAUDE.md` |
| **Codex** | `~/.codex/skills/` **或** `~/.agents/skills/` | 原生加载,直接照 SKILL.md 走(无显式唤起工具) | `AGENTS.md` |
| **Gemini CLI** | `~/.gemini/skills/` **或** `~/.agents/skills/` | `activate_skill` 工具 | `GEMINI.md` |
| **Copilot CLI** | —(1.0.63 无 skills 机制) | 不支持 SKILL.md;改走 `AGENTS.md`/MCP/plugin 适配 | `AGENTS.md` |

> **共享路径**:`~/.agents/skills/` 据文档是 Codex/Gemini 等的跨运行时共享路径;但本次实测用的是各 harness 自己的 `~/.<harness>/skills/`(`~/.codex/skills/`、`~/.gemini/skills/`、`~/.zcode/skills/`,均有效)。Claude Code 用 `.claude/skills/`。**Copilot 1.0.63 无 skills 机制,不适用**(见上「实测状态」)。
> 无论装哪,**7 个文件夹(`aigd` + 6 个 `aigd-*`)必须平级**——子 skill 靠同级 `aigd/` 取 references,缺了或层级错就断链。

---

## 2. 工具名对应（方法论"说动作" → 各 harness 工具）

| 动作 | Claude Code | Codex | Gemini CLI |
|------|-------------|-------|-----------|
| 读文件 | `Read` | `shell`(`cat`/`head`) | `read_file` / `read_many_files` |
| 写新文件 | `Write` | `apply_patch` | `write_file` |
| 改文件 | `Edit` | `apply_patch` | `replace` |
| 跑命令 | `Bash` | `shell` | `run_shell_command` |
| 搜内容 | `Grep` | `shell`(`grep`/`rg`) | `grep_search` |
| 找文件 | `Glob` | `shell`(`find`/`ls`) | `glob` / `list_directory` |
| 派子 agent | `Agent` | `spawn_agent`(需 `multi_agent=true`) | `invoke_agent`(`@generalist`) |
| 任务跟踪 | `TodoWrite` | `update_plan` | `write_todos` |

校验器脚本是 `argv` 驱动的纯命令行(`python …/config_check.py …`),**跟 harness 无关**——任何能跑 shell 的环境都一样用,只要有 Python。

---

## 3. 两个 harness 相关的坑（方法论/速查里已泛化,这里给具体写法）

### 工具调用格式
不同 harness 的 function-call 块语法不同,**用错会静默不执行**(文件没写、命令没跑,却以为做了)。发前核一遍你 harness 要求的格式:
- **Claude Code**:必须带 `antml:` 命名空间前缀(写成裸 `invoke`/`parameter` → "tool call was malformed" 静默丢弃)。
- **Codex / Gemini**:按各自的工具调用协议;调用后确认产物真落盘(`shell ls` / `read_file` 复核),别假设已生效。

### 写文件用 UTF-8 无 BOM
中文文件被加 BOM / 变 UTF-16 会让下游读出乱码。各环境写法:
- **Claude Code**:`Write`/`Edit` 默认无 BOM,直接用;**别**用裸 PowerShell `Out-File`/`Set-Content`(会加 BOM)。Windows 下非要用 PowerShell 写中文 → `New-Object System.Text.UTF8Encoding $false`。
- **Codex(apply_patch)/ Gemini(write_file)**:默认 UTF-8 无 BOM,直接用。
- 通用底线:**落盘前确认是 UTF-8 无 BOM**,跨平台用 `/` 路径。

---

## 4. 指令文件(CLAUDE.md / AGENTS.md / GEMINI.md)

**AIGD 不建也不依赖任何 harness 的指令文件**——把"建 CLAUDE.md/AGENTS.md"塞进方法论会把它绑死在某 harness。本包只要求一个**改动账本**(默认项目根 `CHANGELOG.md`,见方法论「项目环境前置」),与指令文件无关。所以换 harness 时**指令文件那一栏可以无视**,装好 7 个文件夹 + 有 Python 即可。
