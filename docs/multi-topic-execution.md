# 多专题案例监控执行记录

## 2026 年 10 月 3 日

### 迁移前基线

- 本地起点：`f2f6920`，目录为单专题 Opus 项目，未配置 Git remote。
- 工作区原有未跟踪目录 `draft_f87d65c6_folder/`，实施不修改该目录。
- Opus 已审核案例 5,527 条。
- 原有 Python 测试 32 项通过，JavaScript 排序测试 3 项通过。
- 已保存所有受 Git 跟踪文件的 SHA-256 与合并数据副本到 `.cache/migration/`，用于无损核对。
- 已核对远端 gallery 与发布仓库：当前按源目录检测更新，分别锁定 SHA，发布由清单变更驱动。

### 目录迁移与实现

- 已将 Opus 的数据、历史报告、文章与素材移入专题目录。
- 共享模块、模板与测试迁往 `atlas/` 和 `tests/`。
- 原始抓取缓存保留在 `.cache/migration/legacy-data-cache/`，未发布。
- 新增独立专题配置和显式 `python -m atlas … --topic …` 入口，共享模块不使用可变的当前专题状态。
- 原 GoSail 专用导入器留在 Opus 的 tools 中，避免错误套用于 Fable；常用旧构建与采集入口保留轻量转发脚本。
- 基础来源和指南改为可选；Fable 从空案例开始，发布时间未知，不展示 Opus 指南或示例。
- public 只包含页面、素材、下载文件和构建清单；采集候选、审核报告与源码不进入发布目录。
- 分享卡片按模板 HTML 与图片校验值复用。新卡片或模板变化时才需要浏览器重新生成，离线构建检查可使用标准库运行。
- 新增 GitHub Actions 校验、浏览器回归与每日候选发现工作流；通知发布仓库的触发范围收窄至 public 产物变化。

### Fable 首次有限发现

- 执行时间：2026-10-03 10:54:08 至 10:54:10 UTC。
- 查询窗口：2026-09-01 起；用于回溯发现，不表示模型发布日期。
- 三种别名分别查询 GitHub 仓库与 HN，共 6 个入口，全部成功读取。
- 去重后保存 42 条待审核候选，新增已审核案例 0。
- `fable5.5` 的 GitHub 查询报告 68 条结果，本轮只取首 30 条；报告明确为部分覆盖。其他命中也可能只是提到关键词，未自动认定模型归属。
- [完整回执与候选](../cases/models/fable-5-5-usecases/reports/2026-10-03-discovery.json) 包含状态、来源 URL、时间及响应 SHA-256；原始正文保留在本地缓存。

### 验证结果

- Opus 的 `all_cases.json` 与迁移前字节一致，SHA-256 为 `f539c35404bca66140bb0c552ffb4617e95871b0eb1c014874fcc1f692068436`。
- 94 个数据、来源配置、指南与原海报文件逐文件校验全部一致；[校验清单](migration-validation.json) 可追溯每个文件。
- Python 回归测试 41 项通过，其中包含原有 32 项；JavaScript 排序测试 3 项通过。
- 两个专题均通过离线重建一致性检查、案例 ID 与来源去重检查、JSON/CSV 对齐、相对资源引用与发布文件检查。
- 浏览器检查覆盖 1440×1000、390×844、中英文及两个专题的 file:// 离线模式，共 10 个视图；无运行时错误或横向溢出。
- 检查了 Opus 搜索、排序、语言切换保留搜索条件与指南语言；Fable 零案例状态无 Opus 文案、无错误指南、无虚构发布日期。
- 冒烟脚本首次使用 `zh` 检查 HTML lang，发现现有页面规范值为 `zh-CN`；修正验证器后通过，未改变原语言行为。
- 已人工查看桌面、手机截图与 Fable 分享卡片；空页面文案改为说明候选审核过程，避免零条时仍宣称已有多来源案例。

### 发布接入状态

- [源码草稿 PR 24](https://github.com/waytoagi-team/gallery/pull/24)：共享工具、专题目录、Fable 有限发现、CI 与文档。
- [发布清单草稿 PR 41](https://github.com/waytoagi-team/waytoagi-static-pages/pull/41)：将 Opus 改为 public 挂载，新增 Fable public 挂载。
- 源码首轮 [GitHub CI](https://github.com/waytoagi-team/gallery/actions/runs/37119026915) 已通过。
- 发布清单的 [GitHub 完整预检](https://github.com/waytoagi-team/waytoagi-static-pages/actions/runs/37119203854) 已通过，包含发布仓库既有回归、组装、冒烟、线上差异计划和凭证扫描。
- 发布器已实际从远端拉取 `b9ae67008b8ce4a825fbd98b542bace12bee773e`：Opus 53 个发布文件、Fable 5 个发布文件，静态检查与两个挂载的浏览器冒烟通过。见 [发布器验证记录](deployment-validation.json)。
- 其他三个挂载（community-growth-deck、kemengopc、d20）逐字段不变。[清单变更副本](deployment/static-pages.patch) 可在本仓库审阅。
- 已使用 gitleaks 8.21.2 扫描完整待提交来源目录，未发现泄露；原始缓存、环境文件和凭证未提交。
- 远端仓库额外保留的旧 `preview.png` 已归档到 Opus 的 reports/migration，避免本地目录同步时丢失历史素材。
- PR 使用隔离的远端 checkout 创建；当前工作目录保留原单专题 Git 历史及迁移后的文件，未把本地历史强行覆盖到远端。

当前未合并两个 PR、未修改线上挂载或执行部署，定时任务要在源码合并至默认分支后才生效。发布草稿中的来源 SHA 用于预检；源码合并后应换成 main 上的实际合并 SHA 并重跑发布 CI，避免 squash/rebase 造成更新器祖先关系不连续。Opus 原公开 URL 保持不变。

### 当前边界

- Fable 已完成一次有限候选发现，42 条候选尚未逐条审核；网页已审核案例数仍为 0。
- 自动发现目前只配置 GitHub 与 HN。X、Reddit、视频等来源可按相同入口继续配置，未声称已有全平台覆盖。
- 候选报告保留 30 天，长期审核记录需要归档到专题 reports。
- 浏览器测试屏蔽外部海报请求，只验证页面行为与本地资源，未复测全部第三方图床可用性。
