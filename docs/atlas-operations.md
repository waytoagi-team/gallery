# 多专题案例监控操作与发布手册

所有命令从 gallery 仓库根目录运行。配置与已审核输入是内容来源，public 是自动生成的发布目录，缓存与候选不自动成为案例。

## 开发环境

使用 Python 3.10+ 和 Node.js 22；CI 使用 Python 3.12。采集与合并只用标准库。GitHub 请求通过 `gh api` 使用现有登录，先运行 `gh auth status`；CI 注入 `GH_TOKEN`。

首次构建分享卡片或运行浏览器测试时，创建虚拟环境、安装 `requirements-dev.txt`，再运行 `python -m playwright install chromium`。分享卡片保存在专题的 `content/assets/og-image.png`，旁边的 `.card.json` 记录模板输入与图片的 SHA-256。构建将图片复制到 public；离线检查只复用已匹配的卡片，避免不同系统字体导致重新截图的差异。

## 发现候选

```bash
python -m atlas list --enabled --json
python -m atlas collect --topic fable-5-5 --dry-run
python -m atlas collect --topic fable-5-5 --since 2026-09-01 \
  --report cases/models/fable-5-5-usecases/reports/discovery-2026-10-03.json
```

每次运行自动生成独立批次目录 `.cache/atlas/<topic>/<run>/`。`--output-dir` 可指定一个空目录，重复使用已有目录会被拒绝，避免旧响应被当成新结果。返回码 1 表示至少一个入口失败，其他成功回执仍然保存。

GitHub 搜索与 HN 搜索暂只获取每个查询的首个有界页面；日期窗口分别转换为 GitHub 仓库 pushed、Issue updated 与 HN created_at_i 条件。其他来源可能不支持日期过滤，抓取成功不意味着分页完成。GitHub 与 HN JSON 可输出最小候选元数据；其余 Opus 既有入口仍保留响应供本地审核。

首次 Fable 回溯窗口从 2026 年 9 月 1 日开始，仅用于发现，不是模型发布日期。后续默认窗口为过去两天，允许重叠。定时工作流按专题串行运行，单个专题失败不取消另一个。候选报告作为 GitHub Actions artifact 保留 30 天，需在过期前完成审核或将最小报告归档到 reports；原始正文不会上传 artifact。

## 审核与入库

先打开原帖、原仓库或对应文档，确认具体作品、任务、模型版本与模型承担的角色。关键词命中、合集名称、父帖的模型名称都不足以证明某个作品的模型归属。

审核结果记录在专题 reports 中；接受的案例追加到相应 `data/extra_<source>.json`。新专题使用稳定的显式 `id`，避免调整列表顺序导致 ID 变化。Opus 的已有顺序编号继续保留，历史列表按追加方式维护。

Fable 案例必须包含普通案例字段，以及以下审核字段：

```json
{
  "id": "github-example-project",
  "checkedAt": "实际核对的 ISO 时间",
  "evidenceUrl": "原始证据的 HTTPS URL",
  "evidenceBasis": "用自己的话说明原文如何支持模型版本和具体任务",
  "modelAttribution": {
    "topicId": "fable-5-5",
    "basis": "explicit-source",
    "role": "例如实现、评测或工具集成"
  }
}
```

构建会检查这些字段和专题归属。字段校验不能代替内容审核。一个项目涉及多个模型时，在各专题分别说明角色，不跨专题自动复制评价结论。

更新 `data/refresh_report.json` 时只记录实际完成的工作：发现更新、指标更新、完整覆盖时间分别维护。不要因为构建成功或搜索入口返回 200 就声称完整刷新。Fable 当前的发现报告与零案例数据快照分开，页面显示“尚无已审核案例”。

对于可选基础列表，`fetch-base` 只写缓存；`normalize-base --raw … --output .cache/…/base-candidate.json` 只生成待审核文件，禁止直接写入 data/public。比较来源身份并保留历史条目后再更新已审核基础列表，避免上游列表缩减造成案例丢失。

## 构建与验证

```bash
python -m atlas build --topic fable-5-5
python -m atlas build --all
python -m atlas build --all --check
python -m atlas validate --all
python -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_ranking.cjs
python -m atlas.smoke --all
```

共享代码变更后重建全部专题。当前只有两个专题，CI 每次检查两者，降低漏测共享依赖的风险。`--check` 在临时目录重建并核对所有 public 文件；发现陈旧分享卡片、页面、下载文件或多余文件会失败，不修改已提交产物。

浏览器回归在实际嵌套路径下检查桌面与手机、中英文、搜索、语言切换、排序状态、可选指南、零案例状态及 file:// 离线浏览。第三方海报请求在测试中屏蔽，原始海报 URL 由数据保留；这不验证第三方图床当前可用性。

## 接入发布仓库

发布配置位于 `waytoagi-team/waytoagi-static-pages/mounts.yaml`。两个挂载使用同一个 gallery 来源仓库，各自锁定完整 40 位 SHA：

| path | source.dir |
| --- | --- |
| `/usecase-atlas/opus5-5/` | `cases/models/claude-opus-5-5-usecases/public` |
| `/usecase-atlas/fable5-5/` | `cases/models/fable-5-5-usecases/public` |

首次迁移要一起审阅源码 PR 与发布清单 PR。先确认源码构建与浏览器检查通过，再合并源码和对应的发布清单变更。过渡期间旧挂载仍指向已发布 SHA；不要合并使用旧 source.dir 的自动 bump PR，它不能代表 public 目录迁移已经接入。

草稿发布 PR 先锁定源码分支的 SHA 供预检。源码合并后，发布前将两处 ref 更新为 gallery 默认分支上的实际合并 SHA 并重新运行发布 CI，尤其是采用 squash 或 rebase 合并时。当前更新器按 Git 提交祖先关系判断是否存在新版本，不能长期把被 squash 的分支提交当作 main 上的发布基线。

发布仓库根据各 public 目录的新提交创建独立 bump PR。部署仍然组装全站，未变专题保留原清单 SHA。部署环境、缓存刷新、源站校验和正式地址检查沿用现有工作流。

回滚某专题时，恢复该挂载上一版完整 SHA；目录切换本身需要回滚时，同时恢复原 source.dir。用同一条发布流水线完成校验与部署。不要将整个来源仓库版本统一回退而误伤其他专题。

本地构建、远端 PR、CI 和正式部署是不同状态，具体执行证据统一记录在 [执行记录](multi-topic-execution.md)。

首次迁移的 [清单补丁](deployment/static-pages.patch) 以零上下文格式保存，便于审阅改动字段；如需在对应基线的发布仓库应用，使用 `git apply --unidiff-zero`。完整上下文以发布 PR 为准。
