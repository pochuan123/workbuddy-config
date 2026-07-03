---
name: hap-skills
description: HAP 技能合集总入口 —— 一组面向明道云 HAP 的 AI Agent 技能，覆盖 CLI / MCP / API 三种操作 HAP 的方式。**立即触发条件**：用户提到"安装 HAP 技能"、"HAP skills"、"安装所有 HAP 技能"、"HAP 技能合集"、"用 HAP 建应用/查数据/搭网站/做接口/开发视图插件"，或只说"HAP"且尚不确定要用哪个具体技能。本技能负责介绍合集、引导一键安装全部技能，并把需求路由到对应的子技能。
---

# HAP Skills 合集总入口

一组面向 **HAP（明道云）** 的 AI Agent 技能集合，覆盖三种操作 HAP 的方式：

- **CLI** — 基于 `hap` 命令行，让 Agent 在终端里直接建应用、改应用、查数据；
- **MCP** — 基于 HAP MCP 服务，对话式全自动搭建应用（方案设计 → 确认 → 物理搭建）；
- **API** — 基于 HAP V3 HTTP 接口，做数据接口调用、用 HAP 当后端搭网站、开发自定义视图插件。

技能按场景分目录存放（`skills/cli/`、`skills/mcp/`、`skills/api/`），可以整组安装，也可以单装。本 skill 是**总入口**：负责介绍合集、引导安装、把用户需求路由到正确的子技能。

> 本仓库只包含 Skill，不含 `hap-cli` 的源码；`hap-cli` 通过 `pip` 单独安装（见下方「前置依赖」）。

---

## 工作方式

1. **判断用户意图**：是想「安装这套技能」，还是想「直接用 HAP 做某件事」。
2. **要安装** → 走下面的「安装」一节，默认一键装全部；用户只想要某一类场景就按目录整组安装。
3. **要用** → 按「技能路由」把需求匹配到对应的子技能，直接调用那个子技能。
4. 任何针对单个 HAP 命令/接口的参数，永远以该子技能内的说明或 `hap <命令> --help` 为准，不要凭记忆猜。

---

## 包含的技能

| 场景 | Skill | 作用 |
| --- | --- | --- |
| CLI | **hap-cli** | 总览与导航：介绍 `hap` 命令行能做什么、怎么登录，以及待办、日程、动态、聊天、应用数据增删改 |
| CLI | **hap-cli-app-creator** | 从一句业务需求一站式建出**真实可用、带示例数据**的 HAP 应用 |
| CLI | **hap-cli-app-editor** | 对**已有应用**做精确的局部修改（字段/视图/工作表/角色权限/工作流/自定义动作/页面） |
| CLI | **hap-cli-data-query** | 复杂查数：多条件 AND/OR 筛选、嵌套分组、透视聚合统计（求和/计数/平均/分组） |
| CLI | **hap-cli-environments** | 多环境/多账号操作守则：决定在哪个环境/账号上执行，破坏性操作前先确认 |
| MCP | **hap-mcp-app-builder** | 全自动一站式应用构建器：方案设计（Plan）→ 确认 → 自动物理搭建（Build），支持中断后续建 |
| API | **hap-apiv3-data** | HAP V3 接口实操：鉴权（Appkey/Sign/PAT/OAuth）、Filter 筛选、记录的查询与增删改 |
| API | **hap-api-website** | HAP + 前端项目完整搭建指南：用 HAP 当后端，后台配置 → 前端结构 → API 集成与数据渲染 |
| API | **hap-view-plugin** | 开发 HAP 自定义视图插件（mdye）：初始化项目、启动调试、开发工作流、V3 接口集成 |

---

## 前置依赖

不同场景依赖不同，按要用的场景准备：

**CLI 场景** —— 基于 `hap` 命令行，先装好并登录：

```bash
pip install hap-cli      # 安装命令行工具
hap auth login           # 浏览器授权登录
hap auth whoami          # 确认已登录、查看当前用户与组织
```

**MCP 场景** —— 在 Agent 客户端里配置 HAP MCP 服务（`api.mingdao.com/mcp` 或 `api2.mingdao.com/mcp`）后即可调用。

**API 场景** —— 准备好目标 HAP 应用的 V3 接口鉴权密钥（Appkey / Sign，或 PAT / OAuth）。若已配置 HAP MCP，部分技能可自动从 MCP 配置中提取密钥。

---

## 安装

### 方式一：用 `npx skills`（推荐）

一次性安装全部技能：

```bash
npx skills add mingdaocom/hap-skills
```

按场景整组安装（只装需要的那一类）：

```bash
npx skills add https://github.com/mingdaocom/hap-skills/tree/main/skills/cli   # CLI 场景
npx skills add https://github.com/mingdaocom/hap-skills/tree/main/skills/mcp   # MCP 场景
npx skills add https://github.com/mingdaocom/hap-skills/tree/main/skills/api   # API 场景
```

按需安装其中某个技能：

```bash
# CLI
npx skills add mingdaocom/hap-skills --skill hap-cli
npx skills add mingdaocom/hap-skills --skill hap-cli-app-creator
npx skills add mingdaocom/hap-skills --skill hap-cli-app-editor
npx skills add mingdaocom/hap-skills --skill hap-cli-data-query
npx skills add mingdaocom/hap-skills --skill hap-cli-environments
# MCP
npx skills add mingdaocom/hap-skills --skill hap-mcp-app-builder
# API
npx skills add mingdaocom/hap-skills --skill hap-apiv3-data
npx skills add mingdaocom/hap-skills --skill hap-api-website
npx skills add mingdaocom/hap-skills --skill hap-view-plugin
```

### 方式二：在 AI Agent 对话里一句话安装

在 **Claude Code、Codex、Antigravity、Hermes、Open Claw** 等 Agent 的对话中直接输入：

```text
帮我安装这个 skills: https://github.com/mingdaocom/hap-skills
```

只想装某一类场景，把场景目录说清楚即可，例如：

```text
帮我安装 https://github.com/mingdaocom/hap-skills/tree/main/skills/cli 下的所有 skills
```

Agent 会自动克隆仓库并把技能装到对应位置。

> **企业整组上传**：把整个仓库（含本根目录 `SKILL.md` 与 `skills/` 目录）打包上传到企业技能库即可。本根 `SKILL.md` 作为合集入口被识别，再由它引导安装并路由到 `skills/` 下的各子技能。

---

## 技能路由（用户想直接用 HAP 时）

把用户的需求匹配到对应子技能，然后直接调用那个 skill：

| 用户意图 | 切到哪个 skill |
| --- | --- |
| 查人 / 发消息 / 发动态 / 看日程 / 处理审批 / 单点读写记录 | **hap-cli** |
| 从零搭一个完整应用（CRM/库存/报修/借阅…，命令行方式） | **hap-cli-app-creator** |
| 改已有应用的某个元素（字段/视图/表/角色/工作流/动作/页面） | **hap-cli-app-editor** |
| 复杂筛选 / 透视聚合统计查数据 | **hap-cli-data-query** |
| 多个环境或账号，要决定/切换在哪里执行 | **hap-cli-environments** |
| 一句话全自动建应用（MCP 服务方式） | **hap-mcp-app-builder** |
| 直接调 HAP V3 接口（鉴权、Filter、记录增删改） | **hap-apiv3-data** |
| 用 HAP 当后端、前后端分离搭网站 | **hap-api-website** |
| 开发 HAP 自定义视图插件（mdye） | **hap-view-plugin** |

> **CLI vs MCP 建应用怎么选**：`hap-cli-app-creator` 走命令行，`hap-mcp-app-builder` 走 MCP 服务，解决同类问题，按用户当前可用的接入方式选。

---

## 验证

安装完成后，在对话中输入下面任意一句，看 Agent 是否进入对应技能：

```text
帮我用 HAP 建一个图书借阅管理应用          # → hap-cli-app-creator
在某张表里加一个字段                      # → hap-cli-app-editor
查一下某张表上个月各产品的销售额前 5        # → hap-cli-data-query
切到我测试用的那个环境再操作               # → hap-cli-environments
帮我查一下待办和未读消息并总结要点          # → hap-cli
帮我全自动搭建一个客户管理应用             # → hap-mcp-app-builder
用 HAP V3 接口查一下某张表的数据          # → hap-apiv3-data
用 HAP 做一个企业官网、前后端分离          # → hap-api-website
开发一个 HAP 自定义视图插件               # → hap-view-plugin
```

---

## 目录结构

```
hap-skills/
├── SKILL.md                    # ← 本文件：合集总入口
├── README.md
└── skills/
    ├── cli/                     # CLI 场景：基于 hap 命令行
    │   ├── SKILL.md             # hap-cli 导航入口
    │   ├── hap-cli-app-creator/
    │   ├── hap-cli-app-editor/
    │   ├── hap-cli-data-query/
    │   └── hap-cli-environments/
    ├── mcp/                     # MCP 场景：基于 MCP 服务
    │   └── hap-mcp-app-builder/
    └── api/                     # API 场景：基于 HAP V3 HTTP 接口
        ├── hap-apiv3-data/
        ├── hap-api-website/
        └── hap-view-plugin/
```

每个技能目录下的 `SKILL.md` 是该技能的入口，Agent 会自动读取。

## 许可

MIT
