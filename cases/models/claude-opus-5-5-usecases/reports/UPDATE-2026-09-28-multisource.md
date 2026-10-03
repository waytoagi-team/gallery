# 2026-09-28：多源全量刷新

在 GoSail 全量源更新之后，对 9 月 27 日以来的全部常规信源做了一次集中刷新，案例从 **3,953 增至 4,546**（+593）。本次刷新的完整记录见 [refresh_report.json](data/refresh_report.json)，GoSail 那次的记录已归档到 [refresh_history/2026-09-28-gosail.json](data/refresh_history/2026-09-28-gosail.json)。

## 新增案例

| 平台 | 新增 | 读取方式 |
| --- | ---: | --- |
| X | 275 | 从 44 个信源快照（整理列表与 newsletter）中提取推文链接，经 FxTwitter 读取原文后逐条审阅 |
| Bilibili | 78 | 搜索接口，翻到 23 页以覆盖 9 月 26 日以来的上传 |
| GitHub | 96 | `gh search` 仓库、Issue、PR，以及整理列表中的仓库链接 |
| Reddit | 47 | Arctic Shift 存档：r/ClaudeAI、r/ClaudeCode、r/claude、r/singularity |
| YouTube | 34 | 搜索页内嵌数据 |
| 网页 | 44 | note / Zenn / Qiita、掘金、V2EX、dev.to、Zvi / Simon Willison 等 feed，以及 18 次网页搜索 |
| Hacker News | 19 | Algolia 接口 |
| 合计 | 593 | |

推文候选：44 个快照中共发现约 2,400 条未收录的推文链接；排除 GoSail 已审阅的条目后读取 2,305 条原文，其中 381 条在正文或引用中明确提到 Opus 5.5，逐条审阅后保留 275 条。

## 指标与修正

- 刷新了 2,349 条已有 X 主帖的点赞、收藏和播放量，2,337 条成功，12 条原帖已删除（保留旧值）。指标单独存放在 [metric_refreshes.json](data/metric_refreshes.json)，构建时在补充层之后应用，较新的 `metricsCheckedAt` 生效；这样重新导入 GoSail 时不会覆盖它们。
- Anthropic 发布页把「OSWorld 2.0」改标为「OSWorld 2.1（部分任务）」，对应的官方案例已同步；引用旧名称的第三方推文按原文保留。
- GitHub star 数本次未刷新。

## 取舍与局限

- Reddit 从 9 月 27 日 00:00（UTC）起读取，有 4 条保留帖子早于上次刷新的截止时间（08:03）。上次刷新没有保存被排除的名单，这 4 条此前不在库中，本次按同样标准审阅后收录。
- 约 55 条新增 X 案例是同一个「15 秒动效简历」提示词的复现，逐条作为独立演示保留，品牌或产品推广在摘要中注明。
- 视频案例只依据标题和简介撰写摘要，没有观看视频。YouTube 搜索页有时返回空结果，覆盖偏少。
- 知乎返回 403；note 搜索接口返回 403，改用话题标签 feed；V2EX 搜索镜像不可用。
- 所有摘要均重新撰写；只收录链接与事实元数据，不镜像第三方视频、提示词或源码。演示与数据未经独立复现。

## 重建与验证

```bash
python3 scripts/collect_sources.py --since 2026-09-27
python3 scripts/build_html.py
python3 scripts/test_build_html.py
```

验证通过：ID 与来源身份唯一、必填字段齐全、CSV 与 JSON 逐行一致、页面内嵌数据与导出一致、脚本可编译、11 项回归测试通过、`git diff --check` 无问题；另在桌面与手机宽度下截图检查了页面。
