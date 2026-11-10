# Fable 5.2 案例监控

本专题监控 `Fable 5.2`、`fable5.2`、`fable-5-2` 相关的项目与使用记录，配置包含 3 个 GitHub 仓库查询和 3 个 Hacker News 查询。关键词匹配只产生待审核候选，不证明使用了该版本，也不代表全网完整覆盖。

2026-11-10 首次多来源抓取后收录 **26 条**案例：X 13 条、GitHub 3 条、Reddit 1 条、B 站 1 条、官方/合作方案例 8 条。跨来源去重共 377 个来源，358 个仍待审核；本轮为部分覆盖。

官方发布公告日期为 2026-11-09，已写入配置。费用、性能与效果均为作者或官方自述，未经独立复现。Fable 5.2 独立维护数据和模型归属，不自动复用 Fable 5.5 案例。

从仓库根目录运行：

```bash
python3 -m atlas collect --topic fable-5-2 --dry-run
python3 -m atlas collect --topic fable-5-2
python3 -m atlas build --topic fable-5-2
python3 -m atlas build --topic fable-5-2 --check
```

[首次多来源抓取与审核记录](reports/UPDATE-2026-11-10.md) · [候选和回执](reports/2026-11-10-multisource.json)

审核后将案例写入 `data/extra_<source>.json`，使用稳定显式 ID，并将 `modelAttribution.topicId` 设为 `fable-5-2`。审核字段与收录规则见 [操作手册](../../../docs/atlas-operations.md)。

`public/index.html` 支持零案例、中英文、JSON / CSV 下载及独立分享卡片。发布路径为 [Fable 5.2 案例图谱](https://www.waytoagi.com/usecase-atlas/fable5-2/)，通过发布仓库的独立挂载部署。
