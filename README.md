# WaytoAGI Gallery

收集、展示和复现各种 AI **模型（Models）**与**工具（Tools）**的优秀案例。

这里不是简单的链接列表。每个 Case 都应尽量说明：它解决了什么问题、如何实现、效果如何，以及其他人怎样复现。

## 模型案例监控

Opus 5.5 与 Fable 5.5 使用同一套 `atlas/` 采集、校验和页面代码，各自维护配置、已审核数据、发现候选及发布产物。

| 专题 | 配置与数据 | 页面路径 |
| --- | --- | --- |
| Claude Opus 5.5 | [专题目录](cases/models/claude-opus-5-5-usecases/) | `/usecase-atlas/opus5-5/` |
| Fable 5.5 | [专题目录](cases/models/fable-5-5-usecases/) | `/usecase-atlas/fable5-5/`（发布接入待合并） |

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium

python3 -m atlas list
python3 -m atlas collect --topic fable-5-5 --dry-run
python3 -m atlas collect --topic fable-5-5 --since 2026-09-01
.venv/bin/python -m atlas build --all
python3 -m atlas build --all --check
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_ranking.cjs
.venv/bin/python -m atlas.smoke --all
```

常规采集、JSON 合并和离线核对只需要 Python 3.10+ 标准库；GitHub 采集使用 `gh` 登录或 CI 的 `GH_TOKEN`。首次构建或分享卡片输入变化时需要 Playwright；已有卡片按 HTML 输入与图片校验值复用，离线核对不重新栅格化图片。浏览器回归测试也使用 Playwright。

采集只产生候选与回执，不自动修改已审核案例或线上页面。`monitor.yml` 计划每天北京时间 08:17 运行，合并到 GitHub 默认分支后才生效，执行可能延迟；仅上传最小候选元数据与回执，原始响应留在被忽略的缓存中。

[改造方案](docs/multi-topic-plan.md) · [操作与发布手册](docs/atlas-operations.md) · [执行记录](docs/multi-topic-execution.md)

## 浏览 Cases

| 分类 | 目录 | 内容 |
| --- | --- | --- |
| 模型案例 | [`cases/models`](cases/models) | LLM、多模态、图像、视频、语音等模型的应用案例 |
| 工具案例 | [`cases/tools`](cases/tools) | Agent、工作流、编程、研究、创作与自动化工具案例 |

### 最新收录

2026-10-06 增量整合：Opus 共 **6,324 条**，Fable 共 **27 条**。保留较新的远端数据与历史案例身份；发现仍为部分覆盖。

- [Claude Opus 5.5 使用案例合集](cases/models/claude-opus-5-5-usecases)：含已审核数据与可离线浏览的 HTML
- [Fable 5.5 使用案例合集](cases/models/fable-5-5-usecases)：27 条作者归属案例，后台模型身份未独立核验

## 提交一个 Case

1. 复制 [`templates/case-template.md`](templates/case-template.md)。
2. 将文件放入 `cases/models/<slug>/README.md` 或 `cases/tools/<slug>/README.md`。
3. 补充可复现步骤、输入输出示例、成本与限制。
4. 提交 Pull Request；也可以使用 **Case submission** Issue 先推荐案例。

建议的目录结构：

```text
cases/
├── models/
│   └── your-case/
│       ├── README.md
│       └── assets/
└── tools/
    └── your-case/
        ├── README.md
        └── assets/
```

## 收录标准

- **真实**：来自实际使用或可验证的公开演示。
- **可复现**：包含足够的环境、步骤、Prompt 或代码信息。
- **有结果**：展示输出、截图、视频或可访问的 Demo。
- **讲边界**：注明成本、速度、已知限制及安全风险。
- **尊重版权**：只提交有权分享的材料，并标注原作者与来源。

## Case 元数据

每个 Case 顶部使用 YAML Front Matter：

```yaml
---
title: "案例名称"
category: model # model | tool
products: ["模型或工具名称"]
tags: ["agent", "coding"]
author: "作者或团队"
source: "https://..."
demo: "https://..."
license: "原始内容许可证"
verified_at: "YYYY-MM-DD"
---
```

## 参与贡献

请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。提交内容即表示你确认拥有分享权，并同意仓库按 [MIT License](LICENSE) 分发你原创的仓库内容；引用内容仍遵循其原始许可证。

## License

MIT
