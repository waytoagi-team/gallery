# Fable 5.5 案例监控

本专题监控 `Fable 5.5`、`fable5.5`、`fable-5-5` 相关的项目与使用记录。初始配置包含 3 个 GitHub 仓库查询和 3 个 Hacker News 查询。第一轮为有界发现，不代表全平台或全网完整覆盖。

现收录 27 条作者归属案例，路由与后台模型身份未独立核验。首次发现于 2026 年 10 月 3 日执行，读取 6 个入口，去重得到 42 条待审核候选；关键词匹配并不证明使用了该版本。模型发布时间未在本任务中核实，配置保留为空。

[首次发现回执与候选](reports/2026-10-03-discovery.json) 保存查询、时间、返回数量、响应校验值和候选来源。原始响应不进入 Git，也不随网页发布。

从仓库根目录运行：

```bash
python3 -m atlas collect --topic fable-5-5 --dry-run
python3 -m atlas collect --topic fable-5-5 --since 2026-09-01
python3 -m atlas build --topic fable-5-5
python3 -m atlas build --topic fable-5-5 --check
```

基础来源与指南均为可选项；当前不配置这两项。`public/index.html` 支持零案例、中英文、下载与独立分享卡片。收录规则与发布步骤见 [操作手册](../../../docs/atlas-operations.md)。

2026-10-06 增量整合后共 **27 条**，保留较新远端数据与历史 ID。[增量更新记录](reports/UPDATE-2026-10-06-incremental.md)。
