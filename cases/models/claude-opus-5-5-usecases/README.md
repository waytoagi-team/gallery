# Claude Opus 5.5 使用案例

本专题使用仓库根目录的共享 `atlas/` 工具。迁移基线为 5,527 条案例，全部历史 ID、原帖身份、指标归属、资源与配图证据保留。

最近更新：[2026-10-21 多来源更新](reports/UPDATE-2026-10-21.md)，新增 195 条，当前 **7,347 条**；本轮为部分覆盖，历史互动数据已刷新，未完成核对的候选另行留档。

- `topic.json`：模型、别名、页面、基础来源与指南配置。
- `sources.json`：原有 46 个发现入口。
- `data/`：已审核输入及补充证据；文件按原顺序保留，历史自动编号依赖其顺序。
- `reports/`：历史更新说明、审核记录和迁移前 README；历史命令与相对路径仅供追溯。
- `content/`：中英文指南、原有海报与本专题的分享卡片模板。
- `public/`：自动生成的独立发布目录。可直接打开 `public/index.html`，支持中英文、筛选、排序和离线浏览。

从仓库根目录运行：

```bash
python3 -m atlas collect --topic opus-5-5 --since 2026-10-01
python3 -m atlas metrics --topic opus-5-5 --only github --output-dir .cache/metrics/opus-5-5/2026-10-03
python3 -m atlas build --topic opus-5-5
python3 -m atlas build --topic opus-5-5 --check
```

原 GoSail 专用导入器保留在 `tools/`，使用已审核的固定源快照；它们不是 Fable 的通用来源。原始抓取缓存不随专题提交。JSON 与 CSV 下载位于 `public/data/`。

线上地址仍为 `https://www.waytoagi.com/usecase-atlas/opus5-5/`。目录迁移的发布步骤见 [操作手册](../../../docs/atlas-operations.md)，实际切换状态见 [执行记录](../../../docs/multi-topic-execution.md)。

2026-10-06 增量整合后共 **6324 条**，保留较新远端数据与历史 ID。[增量更新记录](reports/UPDATE-2026-10-06-incremental.md)。
