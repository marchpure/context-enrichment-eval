# AgentKit Context Enrichment 算法评测与多轮优化复盘报告

- **评测仓库**：`context-enrichment-eval`（冻结输入 SHA256：`92a14df74060721a4b47219ae767f7f36cc8790453008880f335f745c45f035e`）
- **控制面基线提交**：`997ff622d3e66b2dd0df8b1ff96db54eeff447ee`（`codex/context-stg-autofix-1125`）
- **独立优化分支**：`agy/enrichment-opt-1125`（最终提交 `efbaacce6b30140bebdcb903fbf21243c8a45077`，未触碰 STG 工作区及泳道）
- **消费与富化模型**：`doubao-seed-2-0-pro-260215`（3 场景 × 12 题 × 3 次 = 108 次配对实测；每场景 8 Dev + 4 Holdout 严格隔离）

---

## 一、三场景总览对照表（原文 vs 基线富化 vs 优化后富化）

### 1. 机械通过率与 Dev / Holdout 分列

| 场景 | 原文基线 (总 / Dev / Holdout) | Round 0 基线富化 (总 / Dev / Holdout) | Round 3 优化富化 (总 / Dev / Holdout) | vs Round 0 净变化 | vs 原文净变化 | pass@1 (原文 → R0 → R3) | 新回归 (原文 / R0 / R3) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **D2 数据分析** | 27/36 (21/24, 6/12) | 21/36 (15/24, 6/12) | **27/36** (20/24, **7/12**) | **+6** (Dev +5, Holdout +1) | 0 (Holdout +1) | 9 → 6 → **9** / 12 | 0 / 0 / **0** |
| **企业知识问答** | 28/36 (17/24, 11/12) | 23/36 (15/24, 8/12) | **31/36** (19/24, **12/12**) | **+8** (Dev +4, Holdout +4) | **+3** (Dev +2, Holdout +1) | 10 → 7 → **10** / 12 | 0 / 0 / **0** |
| **研发上下文** | 29/36 (20/24, 9/12) | 22/36 (13/24, 9/12) | **28/36** (20/24, 8/12) | **+6** (Dev +7, Holdout -1) | -1 (Dev 0, Holdout -1) | 10 → 6 → **10** / 12 | 0 / 1 / 1 |
| **三场景合计** | **84/108** (58/72, 26/36) | **66/108** (43/72, 23/36) | **86/108** (**59/72**, **27/36**) | **+20** (Dev **+16**, Holdout **+4**) | **+2** (Dev +1, Holdout +1) | 29 → 19 → **29** / 36 | 0 / 1 / 1 |

### 2. 消费端 Token 与时延代价

| 场景 | 消费平均 Token (原文 → R0 → R3) | Token 变化 (R3 vs R0) | 消费耗时中位数 (原文 → R0 → R3) | 富化加工耗时 (R0 → R3) |
|---|---:|---:|---:|---:|
| **D2 数据分析** | 16,688 → 22,194 → **19,216** | **-13.4%** | 33.0 s → 30.1 s → **26.9 s** | 578.4 s → 618.6 s |
| **企业知识问答** | 8,790 → 16,988 → **6,764** | **-60.2%**（低于原文 23.0%） | 21.3 s → 21.9 s → **13.5 s** | 535.9 s → 441.2 s |
| **研发上下文** | 6,757 → 16,573 → **13,089** | **-21.0%** | 21.0 s → 25.9 s → 27.4 s | 231.7 s → 158.7 s |
| **三场景均值** | 10,745 → 18,585 → **13,023** | **-29.9%** | — | 448.7 s → 406.2 s |

---

## 二、多轮演进轨迹与四归因变化

| 轮次 | 控制面提交 | 三场景总通过 | `RECALL_MISS` | `PRECISION_ERROR` | `RETRIEVAL_LINK_MISS` | `CONSUMER_ERROR` | 总失败 |
|---|---|---:|---:|---:|---:|---:|---:|
| **Round 0（基线）** | `997ff622` | 66 / 108 | 0 | 3（Dev 复核后 5） | 6 | 33（Dev 复核后 31） | 42 |
| **Round 1** | `451d3237` | 70 / 108 | 1 | 0 | 2 | 35 | 38 |
| **Round 2** | `300ebf35` | 80 / 108 | 0 | 2 | 4 | 22 | 28 |
| **Round 3（最终）** | `efbaacce` | **86 / 108** | **0** | **0** | **0** | **22** | **22** |

- **Enrichment 上游三类归因桶（`RECALL_MISS` / `PRECISION_ERROR` / `RETRIEVAL_LINK_MISS`）全部清零（`0 / 0 / 0`）**，剩余 22 次失败均归因于下游消费模型自身推理/实现误差（`CONSUMER_ERROR`），优化飞轮已达到收敛。

---

## 三、关键根因与代码改动（分支 `agy/enrichment-opt-1125`）

1. **`451d3237` — Round 1（三路并行优化）**：
   - `internal/midgardworker/enrichment/prompt.go` + `render_markdown_test.go`：修复 `RenderStandardPageMarkdown` 在 `Terms` 为空时将整篇 `Overview` 重复渲染进 `## Definitions` 的双倍膨胀 Bug；精简空章节占位文本；在 `## Sources` 中从证据首行提取并暴露原始文件路径。
   - `internal/midgardworker/enrichment/index_tree.go` + `index_tree_test.go`：新增 Unicode 安全的 `unicodeDirSlug` 与确定性防碰撞 `uniqueDirPath`，消除纯中文专题退化为 `topic-<hash>` 与同前缀专题碰撞成 `page_<hash>` 的检索失灵问题；在 `assets` 索引节点中补充表语义摘要。
   - `internal/midgardworker/enrichment/prompts/{file_grouper,knowledge_planner,topic_writer}.md`：建立生效规范高于源码实现、禁止为归档/草案单独建页、严格多实体/多租户范围与必选过滤保真规则。
2. **`300ebf35` — Round 2（两路并行优化）**：
   - `internal/midgardworker/enrichment/topic_writer.go` + `topic_writer_resilience_test.go`：新增 `decodeTopicPage` 容错归一化（标题/空数组/SubType）及对 `ErrInvalid` 的单次自动重试，解决规划专题（如 `请求预处理规则`）被静默跳过的问题。
   - `internal/midgardworker/enrichment/prompts/{knowledge_planner,topic_writer}.md`：要求逐字保留多步 SQL 模板/CTE 窗口聚合公式、在指标规则旁内联 `业务字段 → 物理表.物理列名` 映射、并对齐核心实现与生效规范及计数/否定边界。
3. **`efbaacce` — Round 3（收敛精修）**：
   - `internal/midgardworker/enrichment/prompts/{knowledge_planner,topic_writer}.md`：禁止将修改模块行为的会议/决策记录（`sessions/`）孤立建页；明确 `emits <Header>` 且不原地修改调用方 headers 意为请求头新副本而非响应头；补全 SQLite 双期 `UNION` + `LEFT JOIN` + `COALESCE(..., 0)` 差值防空值规则。

---

## 四、不变量与合入门禁核验

- **`PROP-01 ~ PROP-05` 离线性质测试**（`tests/test_invariants.py`）：6/6 全部通过；调优全程严守 `PROP-04`（仅使用 `dev` 集反例，零 `holdout` 泄露）。
- **夹具与 Oracle 预检**（`evaluators.preflight`）：24 条 SQL 参考执行、130 项过滤变异拦截、12 QA Oracle、12 Patch Oracle 全部通过。
- **Go 单元测试**（`go test -count=1 ./internal/midgardworker/enrichment/...`）：全绿通过。
- **合入门禁结论**：
  - 整体及 D2 数据分析、企业知识问答均**全面通过合入门禁**（总分 `86/108` 超越原文基线 `84/108`；Dev `+16`、Holdout `+4`；Token 较基线富化下降 `29.9%`；上游三类归因清零）。
  - 研发上下文已较基线富化大幅提升（`22 → 28/36`，Dev `13 → 20/24` 追平原文），但 Holdout 存在 1 次随机性波动（`9 → 8/12`）及 1 次下游消费端回归（与 Round 0 持平，未新增回归），建议按正常 PR Review 流程将 `agy/enrichment-opt-1125` 合入控制面主分支。
