# 多专题案例监控改造方案

本次改造把 Opus 5.5 单专题项目扩展为共享采集和页面代码、按专题保存配置与数据的案例库。Fable 5.5 是第二个专题。实施日期为 2026 年 10 月 3 日。

## 仓库与目录

`waytoagi-team/gallery` 是配置、审核数据、共享工具和静态产物的来源；`waytoagi-team/waytoagi-static-pages` 继续负责挂载、锁定版本、部署、线上校验和回滚。

- `atlas/`：专题配置、平台采集、合并去重、指标归属、页面与分享卡片构建。
- `cases/models/<topic>/topic.json`：稳定 ID、模型名称、关键词、发布时间、页面路径、可选基础来源与指南。
- `cases/models/<topic>/sources.json`：专题采集入口。
- `cases/models/<topic>/data/`：已审核的基础案例、增量案例和证据补充。
- `cases/models/<topic>/reports/`：执行记录、审核判断与覆盖缺口。
- `cases/models/<topic>/content/`：文章、专题素材和分享卡片输入。
- `cases/models/<topic>/public/`：页面、素材及可下载的 JSON/CSV，作为唯一发布目录。
- `.cache/`：原始响应、临时文件与迁移基线，不进入 Git 或网站。

## 数据与运行约束

保留 Opus 全部历史案例 ID、来源身份和审核证据。跨专题标识采用专题 ID 与案例 ID 的组合；一个来源可以进入多个专题，但每个专题独立核实模型归属。关键词命中只代表候选，不直接成为已审核案例。

基础案例来源和指南均为可选配置。Fable 从零条已审核案例开始，不套用 Opus 的发布时间、指南、例图或基础来源。未知日期保持未知。

采集按专题运行，回执与缓存按专题及运行批次隔离。失败保留状态与覆盖限制。指标刷新不冒充新的案例发现；重新构建不更新采集时间。

## 发布流程

采集与审核 → 生成专题数据和 public → gallery PR → 离线重建与校验 → 合并 → 发布仓库按专题创建 SHA 更新 PR → 发布 CI → 合并部署 → 线上校验。

现有发布器从 Git 指定目录取文件，因此 public 初期随源数据提交。专题变更只需重建该专题；共享代码变更重建全部专题。发布清单分别锁定 Opus 与 Fable 的完整来源 SHA，底层继续统一组装全站并串行部署。

旧地址 `/usecase-atlas/opus5-5/` 保持不变；新增地址为 `/usecase-atlas/fable5-5/`。发布迁移需要将 Opus 源目录改为 public，并添加 Fable 挂载。正式环境以发布仓库中实际合并的清单为准。

## 验收

1. Opus 的 5,527 条案例内容、ID、来源与证据无损迁移。
2. 原有 32 项 Python 和 3 项排序测试继续通过。
3. 同一进程内分别构建两个专题，数据、路径与名称不会串用。
4. Fable 零案例时，中英文、筛选、下载与分享卡片可用，不声明已经完成监控或验证。
5. 离线重建可检查产物与输入一致；发布目录只包含网站所需文件。
6. 首次 Fable 有限采集保存可核对回执，未审核结果不进入案例库。
7. 发布接入变更可审阅、可回滚，并记录本地验证与实际上线状态。

## 已核对的现有发布机制

- [gallery 通知工作流](https://github.com/waytoagi-team/gallery/blob/main/.github/workflows/notify-static-pages.yml)
- [发布仓库操作说明](https://github.com/waytoagi-team/waytoagi-static-pages/blob/main/README.md)
- [挂载清单](https://github.com/waytoagi-team/waytoagi-static-pages/blob/main/mounts.yaml)
- [按目录检测更新的实现](https://github.com/waytoagi-team/waytoagi-static-pages/blob/main/staticpages/updates.py)

实施结果见 [执行记录](multi-topic-execution.md)。
