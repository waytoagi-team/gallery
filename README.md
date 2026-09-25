# WaytoAGI Gallery

收集、展示和复现各种 AI **模型（Models）**与**工具（Tools）**的优秀案例。

这里不是简单的链接列表。每个 Case 都应尽量说明：它解决了什么问题、如何实现、效果如何，以及其他人怎样复现。

## 浏览 Cases

| 分类 | 目录 | 内容 |
| --- | --- | --- |
| 模型案例 | [`cases/models`](cases/models) | LLM、多模态、图像、视频、语音等模型的应用案例 |
| 工具案例 | [`cases/tools`](cases/tools) | Agent、工作流、编程、研究、创作与自动化工具案例 |

### 最新收录

- [Claude Opus 5.5 使用案例合集](cases/models/claude-opus-5-5-usecases)：1795 条公开案例，含结构化数据与可离线浏览的 HTML

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
