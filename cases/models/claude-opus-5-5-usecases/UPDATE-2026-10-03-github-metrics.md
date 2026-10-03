# 2026-10-03 GitHub 指标归属与排序纠正

检查全库 **369 条 GitHub 案例**，发现 **68 条**使用了所属仓库的 Stars：33 条 PR、28 条 Issue、7 个文件页。已移除错误指标。另有 300 条仓库入口和 1 条 Gist，Gist 原本就没有 Stars。案例总数仍为 **5,527**，没有新增或删除案例；原文链接、摘要、配图及已审核的补充资料保持不变。

用户指出的 [OpenClaw 支持 Claude Opus 5.5](https://github.com/openclaw/openclaw/pull/155966) 是 PR `#155966`。此前错误显示所属仓库的 **391,203 Stars**。本次读取该 PR 的独立指标为 **1 次表情回应、5 条讨论评论**；该回应是 eyes，并不代表赞同。其他受影响条目包括 Claude Code 的问题反馈，以及 Vercel AI SDK 示例文件。完整 68 条纠正清单及 61 次 API 回执见[审计数据](data/refresh_history/2026-10-03-github-metrics.json)。

## 采用的规则

| 原始链接类型 | 展示指标 | 热度计算 |
| --- | --- | --- |
| 仓库首页 | 本仓库 Stars | 与其他仓库的 Stars 比较 |
| PR | 此 PR 正文的表情回应总数、讨论评论数 | 仅按回应数，与其他 PR 比较 |
| Issue | 此 Issue 正文的表情回应总数、讨论评论数 | 仅按回应数，与其他 Issue 比较 |
| 文件、Gist、具体评论及其他页面 | 暂无独立热度 | 不借用仓库指标，不计分 |

表情回应包括各类回应，不等于赞同、作品质量或模型归属证据。评论数只展示，不参与排序，以免讨论或争议较多直接推高热度；此接口的评论数不包含代码行评审评论。仓库 Stars 也只说明仓库受关注程度。

各组按指标升序计算并列平均名次，组内有 N 条有效记录时，得分为 `并列项的平均零起始名次 / (N - 1)`。相同数值始终同分；数值为 0 时固定为 0；缺失为内部未计分值 -1；单条正数记录取 0.5。默认精选混排的来源队列也使用修正后的得分。得分在完整快照上计算，不因搜索或筛选改变。排序用于浏览，不应当作跨平台关注人数或作品质量的统一尺度。

同时修正了原有相同值受录入顺序影响的问题，以及视频缺播放量时把点赞数混进播放量组的问题。其他来源仍使用原有指标；视频播放与点赞现分组排名。

## 读取、持久化与防止复发

1. 先备份当前数据和报告，按每条 `sourceUrl` 识别对象类型；遍历所有 GitHub 条目和非 GitHub 条目的 Stars，确认错误范围。
2. 通过已登录的 `gh api` 读取全部 61 条 PR／Issue，**61 次全部成功**；本轮不重新读取仓库 Stars。指标读取完成于 **2026-10-03 09:02:43 UTC（北京时间 17:02:43）**。
3. 根据 GitHub 的 [Issue API](https://docs.github.com/en/rest/issues/issues#get-an-issue)，PR 也可从 Issue 接口获取正文回应和讨论评论；校验返回链接、仓库名、编号、PR／Issue 类型及非负整数计数后写入。仓库使用 [Repository API](https://docs.github.com/en/rest/repos/repos#get-a-repository) 的 `stargazers_count`。
4. 保存 `githubKind`、`metricsSourceUrl` 和 `metricsCheckedAt`，JSON 与 CSV 同步。0 是已取得的计数，缺失不填 0。文件页去除错误 Stars 及对应的错误核验时间。
5. 后续刷新按对象调用接口；失败时仅保留有匹配 API 出处的旧 PR／Issue 指标。即使接口失败，旧的仓库 Stars 也不会留在 PR／Issue 上。构建时再检查一次，防止旧导入或补充数据带回错误指标。
6. 页面用中英文标明仓库／PR／Issue／文件／Gist，展示对应指标及排名口径。没有独立指标的案例仍可搜索、筛选和访问。

本轮是既有指标纠正，未执行新的多平台发现。`lastMultiSourceRefreshAt` 保留本日 08:33:29 UTC，`lastFullRefreshAt` 保留 9 月 30 日。上一轮多源抓取的部分覆盖限制仍适用；历史报告中的仓库抓取数量不能解释为当时每个案例的指标归属都正确。

## 验证

- 32 项 Python 回归测试与 3 项 JavaScript 排名测试通过，覆盖对象身份、错误指标剔除、失败保留、零值与缺失、同值并列、跨指标隔离和离线页面数据。
- 对比全部 5,527 条记录：ID、正文、来源、配图和其他非指标字段一致；非 GitHub 记录完全一致；300 条仓库的 Stars 不变；既有指标补丁、回复资料、配图补充文件字节一致。
- 检查 CSV／JSON 一致性及离线构建可重复；在桌面、手机、中英文页面验证五类 GitHub 条目的展示、筛选、热度排序和语言切换。

[审计清单与回执](data/refresh_history/2026-10-03-github-metrics.json) · [纠正前报告](data/refresh_history/2026-10-03-before-github-metrics.json) · [当前报告](data/refresh_report.json)
