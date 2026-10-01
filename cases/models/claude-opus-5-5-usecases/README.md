---
title: "Claude Opus 5.5 使用案例合集（5181 条）"
category: model # model | tool
products: ["Claude Opus 5.5"]
tags: ["claude", "opus-5.5", "use-cases", "dataset", "coding", "agent", "games", "3d", "video"]
author: "WaytoAGI"
source: "https://www.anthropic.com/claude-opus-5-5"
demo: "index.html"
license: "各案例内容归原作者；本目录数据与脚本 MIT"
verified_at: "2026-10-01"
---

# Claude Opus 5.5 使用案例合集

> Claude Opus 5.5 发布（2026-09-22）后的 **5181 条**公开使用案例，来自 X、Reddit、YouTube / B 站、GitHub、Hacker News 和网页（官方、评测、博客、媒体），已做结构化整理。每条案例都标注了类别、证据类型和原始出处，并附一个可离线打开的单文件浏览页面。

## 效果展示

![上一版界面预览](assets/preview.png)

上图为上一版界面；最新数量与内容以 `index.html` 和下方数据表为准。

下载 [`index.html`](index.html) 后直接用浏览器打开（数据已内嵌，无需服务器），页面支持：

- 按标题、摘要、作者、分类全文搜索，命中词高亮；输入分类名时提示直接筛选
- 按 14 个任务类别、5 种证据类型、6 个来源筛选，每组筛选下方显示当前条件与结果数
- 排序：精选混排（默认，按来源比例轮排）、热度（来源内排名）、点赞、收藏（仅 X）、时间
- 整张卡片可点开原帖；缩略图加载失败时显示品牌来源色块，不跳动
- 筛选、搜索、排序和语言写进网址（`?src=&cat=&ev=&q=&sort=&lang=`），可直接分享某个视图
- 中英文切换；手机端搜索栏、菜单与筛选反馈单独适配

分享到 X、飞书、Telegram、Discord 等平台时显示 1200×630 的分享卡片（`assets/og-image.png`）：标题、案例总数、"每条附原帖链接 · 含失败与限制"，两侧是五张真实案例卡片。卡片由 `scripts/render_og.py` 按最新数字渲染（需 Playwright），页面用内容哈希（`?v=`）引用以刷新平台缓存。微信不读取 og 标签，只显示页面标题。

页面按 WaytoAGI 品牌视觉规范设计：官方 Logo、品牌色 token、编辑部式章节编号、按来源浏览的 Route Bar、深色证据区与紫色行动区。Logo 放在 `assets/`，构建时内联进 `index.html`，页面仍是离线可用的单文件。

## 数据概览

最近更新于 2026-10-01，共 **5181** 条。10 月 1 日多源更新新增 128 条（5053 → 5181），并刷新 3,533 条 X 帖子的互动指标；部分接口受限，覆盖范围见 [2026-10-01 更新说明](UPDATE-2026-10-01.md)。此前 9 月 30 日完整校验并刷新全部常规信源（+507 条），9 月 28 日多源刷新（+593 条）。数量不等于独立成功项目数。

| 来源 | 条数 | 说明 |
| --- | ---: | --- |
| X | 3575 | 作品演示、模型对比、产品集成、评测数据，含点赞与收藏数和封面图 |
| Reddit | 339 | r/ClaudeAI、r/ClaudeCode 等社区的第一手作品、实测与踩坑（帖子和评论） |
| 视频 | 566 | YouTube 与 B 站上的实测、教程与作品视频（摘要只依据标题和简介） |
| 网页 | 263 | Anthropic 发布页客户案例、Every / Vals AI / Sonar 等实测与评测、公司博客、newsletter、Zenn / Qiita / note、掘金 / V2EX |
| GitHub | 315 | 仓库、Issue、PR：用 Opus 5.5 构建的项目、评测仓库、兼容性问题 |
| Hacker News | 123 | 评论与帖子，只保留有具体任务和结果的第一手经验 |

| 任务类别 | 条数 | 任务类别 | 条数 |
| --- | ---: | --- | ---: |
| 视频编辑与制作 | 1704 | 网站与界面 | 238 |
| 游戏开发 | 726 | 业务分析与文档 | 174 |
| 代码维护与测试 | 472 | 写作与知识解释 | 122 |
| 3D 建模与场景 | 465 | 科学研究与电路 | 111 |
| 创意图形与动画 | 410 | 音乐与声音 | 95 |
| 交互教育与可视化 | 315 | 电脑操作 | 48 |
| Agent 与开发工作流 | 271 | 视觉理解与数据标注 | 30 |

证据类型：演示 3062 · 评测 913 · 集成 638 · 教程 326 · 限制 242

10 月 1 日检查全部 **1,420 条缺图案例**，从原帖附件、明确引用或链接的作品、仓库及文章上下文中补入 **533 张配图**：X 178、Reddit 143、GitHub 123、网页 74、Hacker News 15。有图案例增至 **4,294 / 5,181（82.9%）**；887 条仍未确认可用且匹配的图片，保留无图。通用平台卡片、空白视频首帧、头像、徽章及无关图片未采用。新增图片均通过来源匹配、实际图像读取及画面检查；原有配图、案例内容和互动指标不变。

[配图覆盖文件](data/poster_enrichments.json) 保存来源页、关联方式、图片尺寸、核验时间和校验值，[检查决策](data/refresh_history/2026-10-01-poster-review.json) 覆盖全部缺图案例。只引用外部图片，不镜像图片或原文；图片权利归原作者，未独立核验再利用许可。

## 信源补充记录

最近两轮多源刷新的来源、取舍与局限见 [2026-09-28 多源刷新](UPDATE-2026-09-28-multisource.md) 和 [2026-09-30 校验与刷新](UPDATE-2026-09-30.md)。9 月 28 日完整接入 [GoSail 视频案例源](https://github.com/zhuyansen/awesome-opus-5.5-video)，保留逐条审核结果、原帖指标快照和提示词出处。详见 [2026-09-28 更新说明](UPDATE-2026-09-28.md)。以下三项为上一轮补充，资料入口继续保留。

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
| `mediaKind`, `poster`, `video` | 媒体类型与媒体链接（直接引用原站，不在本仓库存储）；`poster` 同步写入 CSV |
| `posterEvidence` | 新增配图的来源页、关联方式、尺寸、核验时间及实际检查图片的 SHA-256；CSV 中编码为 JSON |
| `checkedAt`, `discoveredVia`, `evidenceUrl`, `evidenceBasis` | 新审阅案例的核验时间、发现渠道、证据入口及摘要依据 |
| `metricsCheckedAt` | 仅更新互动或播放指标的核验时间 |
| `promptEvidence` | 提示来源、原始关联帖、核验时间和上游类型；`completenessVerified` 为 false，不代表完整复现 |
| `relatedSources` / `sourceSnapshots` | 后续记录、来源固定提交与原帖内容校验值 |
| `resources` | 可选的 `{label, label_en, url}` 资料入口；CSV 中编码为 JSON 文本 |

`meta.asOf` 为最新案例日期，`meta.refreshedAt` 为最近更新时间，`meta.refreshScope` 说明覆盖范围，`meta.lastFullRefreshAt` 保留上次多源采集时间。

其他文件：

- `all_cases.csv`：同一份数据的表格版，可直接用 Excel 打开。
- `base_cases.json`、`extra_*.json`：合并前的分批整理结果。其中 `extra_lists.json` 来自其他公开整理列表，只保留原始链接，摘要按原帖内容重写：coolbat/awesome-opus-5.5-usecase（CC0）、opusvideo/awesome-claude-video、TripoGrowthLab/awesome-opus-5-5-prompts、[athemeroy/awesome-opus-5-5-videos](https://github.com/athemeroy/awesome-opus-5-5-videos)（CC-BY-4.0，部分条目的选取来自该列表）、theolundqvist/frontier-games（只用链接和元数据）、Latent Space AINews 2026-09-23 期。`extra_reddit.json` 来自 Arctic Shift 的 Reddit 存档接口，`extra_video.json` 来自 YouTube 搜索页和 B 站搜索接口。
- `source_eval.json`：对 71 个候选信源的评估（覆盖量、第一手比例、是否可程序化读取、授权条款、结论）。

- `extra_gosail.json`：203 条新审阅案例；`case_enrichments.json` 在去重后应用补充，重建基础库时仍保留提示链接。
- `gosail_review.json` / `gosail_fetch_manifest.json`：全部 962 条决策、1066 条原帖/回复的读取凭据和 3 个站外提示页。
- `refresh_report.json`：最近一次更新的数量、范围、刷新前校验和抓取记录；`refresh_history/` 保留此前各轮报告（9 月 27 日多源、9 月 28 日 GoSail、9 月 28 日多源）。
- `poster_enrichments.json`：去重后填补缺图；同时匹配案例 ID 和来源身份，同篇文章中的不同案例还需匹配标题。已有上游配图优先，后续离线重建保留已审核的补图。
- `metric_refreshes.json`：X 帖子的纯指标更新，构建时在 `case_enrichments.json` 之后应用，`metricsCheckedAt` 较新者生效。
- `source_endpoints.json`：可重复的只读信源抓取入口。
- `google_discovery.json`：六组实际 Google 浏览器检索及观察结果。

## 复现步骤

```bash
cd cases/models/claude-opus-5-5-usecases
python3 scripts/fetch_base.py       # 抓取基础案例列表（中英文）-> data/_raw_base.json
python3 scripts/normalize_base.py   # 规范化 -> data/base_cases.json
python3 scripts/collect_sources.py  # 抓取候选信源快照，审阅后再加入 extra_*.json
python3 scripts/build_html.py       # 合并 extra_*.json 并去重 -> data/all_cases.json / .csv + index.html
python3 -m unittest discover -s scripts -p 'test_*.py'  # 26 项回归测试
```

GitHub API 采集通过 `gh api` 复用当前登录身份；先用 `gh auth status` 检查，未登录时运行 `gh auth login --hostname github.com`。凭据由 GitHub CLI 管理，不复制到项目文件或抓取回执。单独补刷仓库指标可运行 `python3 scripts/refresh_metrics.py --only github --output-dir data/_refresh/github-authenticated`，默认两路并发，保留 X 指标和失败仓库的旧值。

完整重建不需要联网。重新采集本轮固定版本并应用既有审核决定：

```bash
python3 scripts/collect_gosail.py --ref ffb3c5a22d27c0d9a5328ffbfb2df33e0887103c --output-dir data/_refresh/gosail
python3 scripts/import_gosail.py --cache data/_refresh/gosail
python3 scripts/build_html.py
```

重新读取会更新指标与核验时间。上游若变更版本，需要先更新逐条审核决定，不能直接自动导入。离线数据构建只依赖 Python 3 标准库；GitHub API 采集另需已登录的 GitHub CLI。几点实现说明：

- 基础案例列表页面服务端只渲染前约 20 条，但全部案例都内嵌在 Next.js 的 RSC payload（`self.__next_f.push`）里，脚本直接从中解析。
- `extra_*.json` 保存审阅后的公开补充案例。9 月 27 日结合 Google、网页搜索、GitHub 搜索、公开 API 和 RSS 发现候选，再核对原始出处。`collect_sources.py --only <key,...>` 可按信源定向抓取，快照写入忽略的 `data/_refresh/`，不会自动收录未经审阅的搜索结果。
- X 案例通过 fxtwitter 公开接口读取推文原文、点赞、收藏和封面图后再核实，不只依赖搜索摘要。
- 去重规则：X / Reddit 按原帖 ID，视频按视频 ID，GitHub 按仓库或条目链接去重，保留有语义的 URL 参数和大小写；编辑文章按 URL 与标题区分同页的多个独立案例。

## 成本与性能

- 抓取耗时取决于网络、限流和来源数量；人工审阅不计入构建耗时。
- `index.html` 约 4.0 MiB，数据内嵌。首屏文案在构建时预填，并在 4 MB 数据之前内嵌一份小的计数摘要，慢网下首屏与分享链接加载的布局位移（CLS）≤ 0.03。案例按每批 48 条渲染，自动加载两批后改为"加载更多"。海报请求卡片尺寸的 WebP 缩图。
- 视觉与交互审查及实施情况见 [reviews/ux-review-2026-10-01.md](reviews/ux-review-2026-10-01.md)。

## 局限与风险

- **案例数不等于成功项目数**：大量案例是平台推广或作者自述，摘要中已尽量标注"作者称""平台推广"。
- **部分早期 X 案例（`extra_x.json`）依据搜索摘要**：这批案例没有读过原文全文；后续新增的 X 案例都按推文原文核实。部分 YouTube 条目只依据视频标题，部分中文媒体报道属二手转述。
- **覆盖不全**：9 月 27 日 GitHub 取最新 100/378 条、HN 取最新 100/295 条；Reddit 三个社区各取最新 100 条，跳过 166 条正文已删除或移除的记录；B 站取得 50 条，第二页返回 412。其余访问失败和窗口限制见更新说明。
- **Reddit 分数不全**：存档接口只记录归档时的分数，约三分之一的 Reddit 条目有点赞数。
- **视频未逐一观看或复现**：YouTube / B 站摘要依据标题和简介；本轮 X 案例读取原帖正文及附件元数据。上游 full/brief 提示分类保留为来源自述，截图提示未转录。
- **时效**：最新案例日期为 2026-10-01，最近一次更新于 2026-10-01（部分接口受限），最近一次完整多源刷新于 2026-09-30。可重新抓取候选，但仍需审阅后才能更新案例。
- **10 月 1 日更新的限制**：GitHub 认证补刷成功读取 306 个仓库中的 303 个，62 个 star 数变化；另 3 个返回 404，保留旧值。部分 Reddit 子版与 B 站关键词未完整翻页；FxTwitter 对发现请求返回 403，改用 VxTwitter 读取原文。详见更新说明。
- **9 月 30 日刷新的限制**：YouTube 播放页限流（HTTP 429），其日期按相对时间推算、摘要依据搜索片段；许多 B 站案例只依据标题和简介；约 55 个低 star 新仓库、掘金和 note 第 3 页以后未审阅；44 条早期案例仍缺日期。
- **媒体链接可能失效**：封面图与视频直接引用 twimg 等原站地址，原帖删除后会失效。

## 参考资料与致谢

- 官方发布：[Anthropic · Claude Opus 5.5](https://www.anthropic.com/claude-opus-5-5)
- 各案例版权归原作者所有，请以 `sourceUrl` 指向的原帖为准。
