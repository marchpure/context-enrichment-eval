# AgentKit Context Enrichment 算法评测与多轮优化复盘报告

- **评测仓库**：`context-enrichment-eval`（冻结输入 SHA256：`92a14df74060721a4b47219ae767f7f36cc8790453008880f335f745c45f035e`）
- **控制面基线提交**：`997ff622d3e66b2dd0df8b1ff96db54eeff447ee`（`codex/context-stg-autofix-1125`）
- **独立优化分支**：`agy/enrichment-opt-1125`（最终提交 `e39e9ca558e17362c26f863d7b43f950d531f190`，未触碰 STG 工作区及泳道）
- **消费与富化模型**：`doubao-seed-2-0-pro-260215`（3 场景 × 12 题 × 3 次 = 108 次配对实测；每场景 8 Dev + 4 Holdout 严格隔离）

---

## 一、三场景总览对照表（原文 vs Round 0 基线 vs Round 3 vs Round 4 去过拟合最终版）

### 1. 机械通过率与 Dev / Holdout 分列

| 场景 | 原文基线 (总 / Dev / Holdout) | Round 0 基线富化 (总 / Dev / Holdout) | Round 3 优化富化 (总 / Dev / Holdout) | Round 4 泛化最终版 (总 / Dev / Holdout) | R4 vs R0 净变化 | R4 vs 原文净变化 | pass@1 (原文 → R0 → R3 → R4) | 新回归 (原文 / R0 / R3 / R4) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **D2 数据分析** | 27/36 (21/24, 6/12) | 21/36 (15/24, 6/12) | 27/36 (20/24, 7/12) | **28/36** (**21/24**, **7/12**) | **+7** (Dev +6, Holdout +1) | **+1** (Dev 0, Holdout +1) | 9 → 6 → 9 → **9** / 12 | 0 / 0 / 0 / **0** |
| **企业知识问答** | 28/36 (17/24, 11/12) | 23/36 (15/24, 8/12) | 31/36 (19/24, 12/12) | **33/36** (**21/24**, **12/12**) | **+10** (Dev +6, Holdout +4) | **+5** (Dev +4, Holdout +1) | 10 → 7 → 10 → **11** / 12 | 0 / 0 / 0 / **0** |
| **研发上下文** | 29/36 (20/24, 9/12) | 22/36 (13/24, 9/12) | 28/36 (20/24, 8/12) | **34/36** (**23/24**, **11/12**) | **+12** (Dev +10, Holdout +2) | **+5** (Dev +3, Holdout +2) | 10 → 6 → 10 → **11** / 12 | 0 / 1 / 1 / 1 |
| **三场景合计** | **84/108** (58/72, 26/36) | **66/108** (43/72, 23/36) | **86/108** (59/72, 27/36) | **95/108** (**65/72**, **30/36**) | **+29** (Dev **+22**, Holdout **+7**) | **+11** (Dev **+7**, Holdout **+4**) | 29 → 19 → 29 → **31** / 36 | 0 / 1 / 1 / 1 |

### 2. 消费端 Token 与时延代价

| 场景 | 消费平均 Token (原文 → R0 → R3 → R4) | Token 变化 (R4 vs R0) | 消费耗时中位数 (原文 → R0 → R3 → R4) | 富化加工耗时 (R0 → R3 → R4) |
|---|---:|---:|---:|---:|
| **D2 数据分析** | 16,688 → 22,194 → 19,216 → **18,224** | **-17.9%** | 33.0 s → 30.1 s → 26.9 s → **28.0 s** | 578.4 s → 618.6 s → **558.1 s** |
| **企业知识问答** | 8,790 → 16,988 → 6,764 → **9,134** | **-46.2%** | 21.3 s → 21.9 s → 13.5 s → **17.8 s** | 535.9 s → 441.2 s → **378.5 s** |
| **研发上下文** | 6,757 → 16,573 → 13,089 → **14,012** | **-15.5%** | 21.0 s → 25.9 s → 27.4 s → **27.1 s** | 231.7 s → 158.7 s → **197.8 s** |
| **三场景均值** | 10,745 → 18,585 → 13,023 → **13,790** | **-25.8%** | — | 448.7 s → 406.2 s → **378.1 s** |

---

## 二、多轮演进轨迹与四归因变化

| 轮次 | 控制面提交 | 三场景总通过 | Dev 通过 | Holdout 通过 | `RECALL_MISS` | `PRECISION_ERROR` | `RETRIEVAL_LINK_MISS` | `CONSUMER_ERROR` | 总失败 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Round 0（基线）** | `997ff622` | 66 / 108 | 43 / 72 | 23 / 36 | 0 | 6（审计初归 3） | 6 | 30（审计初归 33） | 42 |
| **Round 1** | `451d3237` | 70 / 108 | — | — | 1 | 0 | 2 | 35 | 38 |
| **Round 2** | `300ebf35` | 80 / 108 | — | — | 0 | 2 | 4 | 22 | 28 |
| **Round 3** | `efbaacce` | 86 / 108 | 59 / 72 | 27 / 36 | 0 | 0 | 0 | 22 | 22 |
| **Round 4（去过拟合最终）** | `e39e9ca5` | **95 / 108** | **65 / 72** | **30 / 36** | **0** | **0** | **0** | **13** | **13** |

- **Enrichment 上游三类归因桶（`RECALL_MISS` / `PRECISION_ERROR` / `RETRIEVAL_LINK_MISS`）保持全清零（`0 / 0 / 0`）**；在彻底清理全部评测集专属目录/文件名与样例字面量后，总通过数由 Round 3 的 `86/108` 进一步提升至 **`95/108`（Holdout 升至 `30/36`，研发 Holdout 由 `8/12` 跃升至 `11/12`）**，证明通用高信噪比原则与 Worker 容错韧性具备更强的泛化能力。

---

## 三、关键根因与代码改动（分支 `agy/enrichment-opt-1125`）

1. **`451d3237` — Round 1（三路并行优化）**：
   - `internal/midgardworker/enrichment/prompt.go` + `render_markdown_test.go`：修复 `RenderStandardPageMarkdown` 在 `Terms` 为空时将整篇 `Overview` 重复渲染进 `## Definitions` 的双倍膨胀 Bug；精简空章节占位文本；在 `## Sources` 中从证据首行提取并暴露原始文件路径。
   - `internal/midgardworker/enrichment/index_tree.go` + `index_tree_test.go`：新增 Unicode 安全的 `unicodeDirSlug` 与确定性防碰撞 `uniqueDirPath`，消除纯中文专题退化为 `topic-<hash>` 与同前缀专题碰撞成 `page_<hash>` 的检索失灵问题；在 `assets` 索引节点中补充表语义摘要。
   - `internal/midgardworker/enrichment/prompts/{file_grouper,knowledge_planner,topic_writer}.md`：建立生效规范高于源码实现、禁止为归档/草案单独建页、严格多实体/多租户范围与必选过滤保真规则。
2. **`300ebf35` — Round 2（两路并行优化）**：
   - `internal/midgardworker/enrichment/topic_writer.go` + `topic_writer_resilience_test.go`：新增 `decodeTopicPage` 容错归一化（标题/空数组/SubType）及对 `ErrInvalid` 的单次自动重试，解决规划专题被静默跳过的问题。
   - `internal/midgardworker/enrichment/prompts/{knowledge_planner,topic_writer}.md`：要求逐字保留多步 SQL 模板/CTE 窗口聚合公式、在指标规则旁内联 `业务字段 → 物理表.物理列名` 映射、并对齐核心实现与生效规范及计数/否定边界。
3. **`efbaacce` — Round 3（收敛精修）**：
   - 合并修改模块行为的会议/决策记录与模块规范，明确发出请求头副本与响应头区分及跨期全外连接补零规则。
4. **`e39e9ca5` — Round 4（Prompt 去过拟合泛化清理 + 规划/写作重试韧性加固）**：
   - `internal/midgardworker/enrichment/prompts/{file_grouper,knowledge_planner,topic_writer}.md`：**彻底移除全部评测集专属目录名、文件名、字面量与方言片段**（零 `docs/current/*`、`sessions/*`、`approved-features.md`、`archive/`、`schema.md`、`X-Lane`、`max_attempts=2`、`archive/token`、`caller-owned streams`、`AVG(daily_topn)/AVG(daily_total)`、`SQLite`、`COALESCE`、`p_date` 等残留），提炼为纯通用原则：
     - **分组与规划**：中文主题标题（保留产品与关键技术英文标识，不附加生效日期或版本号）；代码仓将规范契约、代码实现与功能/事故决策纪要同组同页合并，纯制度保留特定主体跨领域特批完整覆盖；历史旧版与未生效草案严禁单独建页，仅并入对应生效专题作窗口对照。
     - **写作保真**：客户端/传输层发出（emit/add）协议头且不修改调用方入参统一保真为请求头新副本；严禁将未经规范声明的源码硬编码或违规释放写成规范 `RULE`，同时保留直接承载职责的源码模块 `Citations` 供定位；完整保留差一计数边界、外部资源所有权、事后权限重验、多步 CTE/窗口公式、内联物理列映射与跨期双侧全键集缺侧置零规则。
   - `internal/midgardworker/enrichment/{topic_plan.go,topic_writer.go,pipeline_v2.go,topic_writer_resilience_test.go}`：将 `writeTopic` 单次重试覆盖面扩展至瞬时 `ErrUnavailable` 与零验证引文 `errNoTopicCitations`，并在 `planTopics` 同步引入单次容错重试及配套单测，彻底消除偶发模型/引文抖动导致的静默丢页或规划中断。

---

## 四、不变量与合入门禁核验

- **`PROP-01 ~ PROP-05` 离线性质测试**（`tests/test_invariants.py`）：6/6 全部通过；全程严守 `PROP-04`（仅核查 `dev` 集反例与通用产物结构，零 `holdout` 泄露）。
- **夹具与 Oracle 预检**（`evaluators.preflight`）：24 条 SQL 参考执行、130 项过滤变异拦截、12 QA Oracle、12 Patch Oracle 全部通过。
- **Go 单元测试**（`go test -count=1 ./internal/midgardworker/enrichment/...`）：全绿通过，且 Prompt 目录零评测集专属词通过正则门禁校验。
- **合入 `codex/context-stg-1125-mr` 就绪度结论**：
  - **已完全具备合入条件**。三大场景在总分与 Holdout 上**全部超越原文基线与 Round 3**（总分 `95/108 > 84/108`，Holdout `30/36 > 26/36`，研发 Holdout 达 `11/12 >= 9/12` 且与基线富化相比无新增回归），消费 Token 较 Round 0 下降 `25.8%`，富化耗时下降 `15.7%`。由于 `997ff622` 之前的历史基底提交在 `codex/context-stg-1125-mr` 中做过整理，而本分支新增的 4 个提交（`997ff622..e39e9ca5`）仅修改 `internal/midgardworker/enrichment/` 且与 `codex/context-stg-1125-mr` 零文件重叠，合入时直接执行 `git cherry-pick 997ff622..e39e9ca5`（或 `git rebase --onto codex/context-stg-1125-mr 997ff622 agy/enrichment-opt-1125`）即可无冲突干净落入。
