---
title: "Claude Opus 5.5 使用案例合集（3750 条）"
category: model # model | tool
products: ["Claude Opus 5.5"]
tags: ["claude", "opus-5.5", "use-cases", "dataset", "coding", "agent", "games", "3d", "video"]
author: "WaytoAGI"
source: "https://www.anthropic.com/claude-opus-5-5"
demo: "index.html"
license: "各案例内容归原作者；本目录数据与脚本 MIT"
verified_at: "2026-09-27"
---

# Claude Opus 5.5 使用案例合集

> Claude Opus 5.5 发布（2026-09-22）后前五天的 **3750 条**公开使用案例，来自 X、Reddit、YouTube / B 站、GitHub、Hacker News 和网页（官方、评测、博客、媒体），已做结构化整理。每条案例都标注了类别、证据类型和原始出处，并附一个可离线打开的单文件浏览页面。

## 效果展示

![上一版界面预览](assets/preview.png)

上图为上一版界面；最新数量与内容以 `index.html` 和下方数据表为准。

下载 [`index.html`](index.html) 后直接用浏览器打开（数据已内嵌，无需服务器），页面支持：

- 按标题、摘要、作者全文搜索
- 按 14 个任务类别、5 种证据类型、6 个来源筛选
- 按点赞、收藏或时间排序
- 中英文切换

页面按 WaytoAGI 品牌视觉规范设计：官方 Logo、品牌色 token、编辑部式章节编号、按来源浏览的 Route Bar、深色证据区与紫色行动区。Logo 放在 `assets/`，构建时内联进 `index.html`，页面仍是离线可用的单文件。

## 数据概览

数据截至 2026-09-27，共 **3750** 条，较上一版净增 **1173** 条（新增 1179 个来源身份，合并 6 条历史重复）。主库沿用策展摘要，另外逐条审阅补充了 87 条库外案例；数量不等于独立成功项目数。

| 来源 | 条数 | 说明 |
| --- | ---: | --- |
| X | 2965 | 作品演示、模型对比、产品集成、评测数据，含点赞与收藏数和封面图 |
| Reddit | 214 | r/ClaudeAI、r/ClaudeCode 等社区的第一手作品、实测与踩坑（帖子和评论） |
| 视频 | 186 | YouTube 与 B 站上的实测、教程与作品视频（摘要只依据标题和简介） |
| 网页 | 172 | Anthropic 发布页客户案例、Every / Vals AI / Sonar 等实测与评测、公司博客、newsletter、Zenn / Qiita / note、掘金 / V2EX |
| GitHub | 148 | 仓库、Issue、PR：用 Opus 5.5 构建的项目、评测仓库、兼容性问题 |
| Hacker News | 65 | 评论与帖子，只保留有具体任务和结果的第一手经验 |

| 任务类别 | 条数 | 任务类别 | 条数 |
| --- | ---: | --- | ---: |
| 视频编辑与制作 | 1088 | 网站与界面 | 186 |
| 游戏开发 | 503 | 业务分析与文档 | 153 |
| 代码维护与测试 | 367 | 写作与知识解释 | 96 |
| 3D 建模与场景 | 351 | 科学研究与电路 | 83 |
| 创意图形与动画 | 345 | 音乐与声音 | 77 |
| Agent 与开发工作流 | 220 | 电脑操作 | 42 |
| 交互教育与可视化 | 213 | 视觉理解与数据标注 | 26 |

证据类型：演示 2112 · 评测 713 · 集成 549 · 教程 212 · 限制 164

## 本轮补充的信源

- [Lemo-Opuscar](https://github.com/lemomo-ai/lemo-opuscar)：39 种影片风格，附可复用提示词、样片源码、导演与技术指南，整库计一条工作流案例。
- [Blender AI Arena](https://blenderai.org/gallery)：12 个相同提示的 Opus 5.5 作品对照，保留失败结果；不同工具的生成路径不同。
- [Qiita 实测记录](https://qiita.com/mamagotolab/items/37d3bdd0bafdd81ba392)：4 次会话、579 条响应的个人样本，附去重统计脚本；费用为试算，非实际账单。

这三条案例的卡片新增六个中英文资料入口。详细信源取舍、Google 检索记录和采集边界见 [2026-09-27 更新说明](UPDATE-2026-09-27.md)。

## 值得一看的案例

**工程与企业**
- 把 HAProxy 从 C 迁移到 Rust：[Anthropic 发布页](https://www.anthropic.com/claude-opus-5-5)称用时 9.5 小时，回归测试全部通过（相关讨论见 [@bcherny](https://x.com/bcherny/status/2102439069053747549)）。
- Stripe：据 [Anthropic 发布页](https://www.anthropic.com/claude-opus-5-5)的客户引述，一次会话 rebase 了 40 个堆叠 PR，全部通过 CI。
- [Box](https://blog.box.com/claude-opus-55-faster-and-leaner-high-quality-work)：token 用量约为 Opus 5 的三分之一，技术类任务准确率从 63% 升到 74%。

**长时间自主运行**
- [24 小时从零写出国际象棋引擎](https://github.com/stevemaughan/opus-5.5-chess-24hrs)：作者称约 3463 Elo。
- [一条提示生成 5 分钟讲解视频](https://news.ycombinator.com/item?id=49837060)，并自动上传到 YouTube。

**创作**
- [一条提示生成 Wasmer 发布视频](https://news.ycombinator.com/item?id=49837469)：HTML 动画加 ffmpeg 录制，替代原本 6–12 小时的手工制作。
- [读懂 1819 年博斯普鲁斯古地图](https://cahidarda.com/articles/bosphore-1819)：子代理识别、定位并翻译了 387 个标注。

**局限**
- max 档可能用满 128k 输出 token 仍未作答，见 [Simon Willison](https://simonwillison.net/2026/Sep/22/opus-and-sol-and-luna/)。
- 网络安全与生物类问题会被安全分类器误拒（数据里有多条「限制」类案例）。
- [Vals AI](https://www.vals.ai/models/anthropic_claude-opus-5-5)：综合指数第一，但法律 agent 任务表现较弱。

> 完整清单请看 `index.html`，或筛选「限制」证据类型。

## 数据格式

`data/all_cases.json`：`{ "meta": {...}, "cases": [...] }`，每条案例的字段如下：

| 字段 | 说明 |
| --- | --- |
| `id` / `source` | 唯一 ID；来源为 `x` / `github` / `hn` / `web` / `reddit` / `video` |
| `platform` | 出处平台，如 X、GitHub、Hacker News、Anthropic、Zenn |
| `category` | 14 个任务类别之一，中英文名称见 `meta.categories` |
| `evidenceType` / `evidenceType_en` | 演示 / 评测 / 集成 / 教程 / 限制 |
| `title` / `title_en`, `summary` / `summary_en` | 中英文标题与摘要 |
| `author`, `sourceUrl`, `date` | 原作者、原始链接、发布日期 |
| `likes`, `bookmarks`, `stars`, `views` | 点赞、收藏、GitHub star 和视频播放量；缺失值保留为空 |
| `mediaKind`, `poster`, `video` | 媒体类型与原始媒体链接（直接引用原站，不在本仓库存储） |
| `checkedAt`, `discoveredVia`, `evidenceUrl`, `evidenceBasis` | 新审阅案例的核验时间、发现渠道、证据入口及摘要依据 |
| `metricsCheckedAt` | 仅更新互动或播放指标的核验时间 |
| `resources` | 可选的 `{label, label_en, url}` 资料入口；CSV 中编码为 JSON 文本 |

`meta.asOf` 为最新案例日期，`meta.refreshedAt` 为全库采集时间，后续定向补充记在 `refresh_report.json` 的 `supplements`。

其他文件：

- `all_cases.csv`：同一份数据的表格版，可直接用 Excel 打开。
- `base_cases.json`、`extra_*.json`：合并前的分批整理结果。其中 `extra_lists.json` 来自其他公开整理列表，只保留原始链接，摘要按原帖内容重写：coolbat/awesome-opus-5.5-usecase（CC0）、opusvideo/awesome-claude-video、TripoGrowthLab/awesome-opus-5-5-prompts、[athemeroy/awesome-opus-5-5-videos](https://github.com/athemeroy/awesome-opus-5-5-videos)（CC-BY-4.0，部分条目的选取来自该列表）、theolundqvist/frontier-games（只用链接和元数据）、Latent Space AINews 2026-09-23 期。`extra_reddit.json` 来自 Arctic Shift 的 Reddit 存档接口，`extra_video.json` 来自 YouTube 搜索页和 B 站搜索接口。
- `source_eval.json`：对 70 个候选信源的评估（覆盖量、第一手比例、是否可程序化读取、授权条款、结论）。

- `refresh_report.json`：更新数量、采集窗口、失败状态和校验记录。
- `source_endpoints.json`：可重复的只读信源抓取入口。
- `google_discovery.json`：六组实际 Google 浏览器检索及观察结果。

## 复现步骤

```bash
cd cases/models/claude-opus-5-5-usecases
python3 scripts/fetch_base.py       # 抓取基础案例列表（中英文）-> data/_raw_base.json
python3 scripts/normalize_base.py   # 规范化 -> data/base_cases.json
python3 scripts/collect_sources.py  # 抓取候选信源快照，审阅后再加入 extra_*.json
python3 scripts/build_html.py       # 合并 extra_*.json 并去重 -> data/all_cases.json / .csv + index.html
python3 scripts/test_build_html.py  # 来源身份去重的 8 项回归测试
```

只依赖 Python 3 标准库。几点实现说明：

- 基础案例列表页面服务端只渲染前约 20 条，但全部案例都内嵌在 Next.js 的 RSC payload（`self.__next_f.push`）里，脚本直接从中解析。
- `extra_*.json` 保存审阅后的公开补充案例。本轮结合 Google、网页搜索、GitHub 搜索、公开 API 和 RSS 发现候选，再核对原始出处。`collect_sources.py --only <key,...>` 可按信源定向抓取，快照写入忽略的 `data/_refresh/`，不会自动收录未经审阅的搜索结果。
- X 案例通过 fxtwitter 公开接口读取推文原文、点赞、收藏和封面图后再核实，不只依赖搜索摘要。
- 去重规则：X / Reddit 按原帖 ID，视频按视频 ID，GitHub 按仓库或条目链接去重，保留有语义的 URL 参数和大小写；编辑文章按 URL 与标题区分同页的多个独立案例。

## 成本与性能

- 抓取耗时取决于网络、限流和来源数量；人工审阅不计入构建耗时。
- `index.html` 约 2.8 MiB，数据内嵌，案例按每批 48 条逐步渲染。

## 局限与风险

- **案例数不等于成功项目数**：大量案例是平台推广或作者自述，摘要中已尽量标注"作者称""平台推广"。
- **部分早期 X 案例（`extra_x.json`）依据搜索摘要**：这批案例没有读过原文全文；后续新增的 X 案例都按推文原文核实。部分 YouTube 条目只依据视频标题，部分中文媒体报道属二手转述。
- **覆盖不全**：本轮 GitHub 取最新 100/378 条、HN 取最新 100/295 条；Reddit 三个社区各取最新 100 条，跳过 166 条正文已删除或移除的记录；B 站取得 50 条，第二页返回 412。其余访问失败和窗口限制见更新说明。
- **Reddit 分数不全**：存档接口只记录归档时的分数，约三分之一的 Reddit 条目有点赞数。
- **视频摘要只依据标题和简介**：没有逐个观看视频。
- **时效**：数据截至 2026-09-27（发布后约 5 天）。可重新抓取候选，但仍需审阅后才能更新案例。
- **媒体链接可能失效**：封面图与视频直接引用 twimg 等原站地址，原帖删除后会失效。

## 参考资料与致谢

- 官方发布：[Anthropic · Claude Opus 5.5](https://www.anthropic.com/claude-opus-5-5)
- 各案例版权归原作者所有，请以 `sourceUrl` 指向的原帖为准。
