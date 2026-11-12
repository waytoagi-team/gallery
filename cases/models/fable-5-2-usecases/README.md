# Fable 5.2 案例监控

2026-11-12 更新后共 **72 条**：X 50、GitHub 6、Reddit 2、B 站 4、YouTube 2、官方/合作方案例 8。每条保留原始出处、核对时间和模型角色；效果、费用与性能为作者或官方自述，未独立复现。

现有 **56 张来源封面**，原样保存为本地静态资源，并记录原图地址、尺寸与 SHA-256。其余 16 条尚未核实到合适图片，保留文字展示。构建会检查本地封面文件和校验值，浏览器回归会实际解码图片。

本轮 GitHub/Hacker News 分页发现 385 个去重候选，同时读取作品合集、X 原帖、视频作者简介和项目 README。覆盖为部分；关键词和合集标签不足以证明版本归属。首次批次的 377 个来源与后续批次分别留档，未审核候选不自动发布。

[公开页面](https://www.waytoagi.com/usecase-atlas/fable5-2/) · [本轮更新与封面修复](reports/UPDATE-2026-11-12.md) · [审核和图片回执](reports/2026-11-12-review.json) · [首次抓取记录](reports/UPDATE-2026-11-10.md)

从仓库根目录运行：

```bash
python3 -m atlas collect --topic fable-5-2 --dry-run
python3 -m atlas collect --topic fable-5-2
python3 -m atlas build --topic fable-5-2
python3 -m atlas build --topic fable-5-2 --check
```

采集仅产生候选。审核后写入 `data/extra_<source>.json`，使用稳定显式 ID，`modelAttribution.topicId` 必须为 `fable-5-2`。原始抓取正文留在被忽略的缓存，不随页面发布。封面维护和发布规则见 [操作手册](../../../docs/atlas-operations.md)。

模型发布日期依据官方公告记为 2026-11-09。Fable 5.5 保持归档，不将其旧案例自动改标为 5.2。
