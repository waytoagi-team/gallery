# Fable 5.2 案例监控

2026-11-13 更新后共 **189 条**：X 136、GitHub 14、Web/官方博客 12、B 站 9、YouTube 9、Reddit 7、Hacker News 2。每条保留原始出处、核对时间和模型角色；效果、费用与性能为作者或官方自述，未独立复现。

现有 **160 张来源封面**，原样保存为本地静态资源，并记录原图地址、尺寸与 SHA-256（含 8 条从原视频取帧的清晰中段画面及取帧秒数）。其余 29 条为纯文本或无图仓库，保留文字展示。构建会检查本地封面文件和校验值，浏览器回归会实际解码图片。

本轮按扩展发现路径执行 X 多语言检索与回复链追踪、GitHub/HN 跨页发现、Reddit/B 站/YouTube 及工程评测博客补充（部分覆盖，不声称穷尽全网），同时刷新存量 X（87/88 成功）与 GitHub（5/6 成功）指标。关键词和合集标签不足以证明版本归属，未审核候选不自动发布。

[公开页面](https://www.waytoagi.com/usecase-atlas/fable5-2/) · [本轮更新报告](reports/UPDATE-2026-11-13.md) · [本轮审核与去重回执](reports/2026-11-13-review.json) · [2026-11-12 更新](reports/UPDATE-2026-11-12.md) · [首次抓取记录](reports/UPDATE-2026-11-10.md)

从仓库根目录运行：

```bash
python3 -m atlas collect --topic fable-5-2 --dry-run
python3 -m atlas collect --topic fable-5-2
python3 -m atlas build --topic fable-5-2
python3 -m atlas build --topic fable-5-2 --check
```

采集仅产生候选。审核后写入 `data/extra_<source>.json`，使用稳定显式 ID，`modelAttribution.topicId` 必须为 `fable-5-2`。原始抓取正文留在被忽略的缓存，不随页面发布。封面维护和发布规则见 [操作手册](../../../docs/atlas-operations.md)。

寻找更多案例时，按操作手册的 [扩展发现路径](../../../docs/atlas-operations.md#扩展发现路径) 执行：优先沿 X 回复与引用链、作者项目、GitHub 工程证据和社区复盘追踪，并结合演示反查、多语言检索、团队与工具生态。查询覆盖、版本证据、去重和媒体核对结果一并留档。

模型发布日期依据官方公告记为 2026-11-09。Fable 5.5 保持归档，不将其旧案例自动改标为 5.2。

2026-11-12 第二轮沿 X 站内搜索、合集引用和原作者回复追踪，新增 38 条及 37 张原帖封面；详见 [X 扩展审核记录](reports/2026-11-12-x-expansion.json)。仅记录可核实的模型归属，作者性能自述未独立复现。
