# AgentKit Context Enrichment 算法效果评测与优化套件

面向 AgentKit Context 知识加工（Enrichment）的独立评测仓库，与前端/全栈工程回归仓 `context-fe-e2e` 解耦并行运转：

- **`context-fe-e2e`**：守住工程质量（页面通不通、接口快不快、权限与状态对不对）。
- **`context-enrichment-eval`**：守住算法效果（富化后的 Context Set 是否有真实净收益、规则与实体是否保真、消费 Token 是否划算）。

评测方法论与三大真实可执行场景继承自 **第六轮三场景概念驱动实测**（D2 数据分析 / 企业知识问答 / 研发上下文补丁）。

## 目录结构

```text
context-enrichment-eval/
├── AGENTS.md                        # 团队共享评测与「先归因后优化」规范
├── EVAL_MATRIX.md                   # 三场景 36 题效果矩阵 + 性质检查 + 基线对照
├── evaluators/
│   └── invariants.py                # 四类 Enrichment 性质校验器、Dev/Holdout 隔离与四归因汇总
├── tests/
│   └── test_invariants.py           # 随机化多粒度的离线性质与防过拟合自测
├── scenarios/
│   ├── d2_analysis/                 # D2 数据分析场景题单、SQL 验收与夹具说明
│   ├── policy_qa/                   # 企业政策问答场景题单与实体/版本断言
│   └── dev_context/                 # 研发上下文场景题单与补丁/回归单测
└── reports/
    └── attribution_template.md      # 每轮四归因账单与前后对比报告模板
```

## 快速运行（离线性质与防过拟合自测）

```bash
python3 -m unittest discover -s tests -v
```

## 并行优化飞轮用法

1. 新开 Codex Session 时将项目目录选为 `context-enrichment-eval`（自动加载本仓 `AGENTS.md`）。
2. 先跑一轮基线评测并输出 **四归因错题账单**（`RECALL_MISS` / `PRECISION_ERROR` / `RETRIEVAL_LINK_MISS` / `CONSUMER_ERROR`）。
3. 按归因桶并行派发多个 `agy cli`（`gemini-4-carbon-high`）优化对应模块（提取、校验、目录/Link 组织）。
4. 统一重跑 `dev` + `holdout` 全量对照，确认净收益提升、零新回归且 Token 成本受控后再合入。

## 三场景实测

题单保留第六轮归档 ID。每场景冻结 8 道 Dev 和 4 道 Holdout，两臂各跑 3 次。[FROZEN.json](scenarios/FROZEN.json) 记录逐文件 SHA256。两臂使用相同消费模型、步数、预算和原文库。原文臂从原文进入，富化臂从 Worker 生成的条目进入，之后均可查询原文。

配置 `OPENAI_BASE_URL` 和 `OPENAI_API_KEY` 指向获准推理端点。提前拉取 Python 单测镜像 `python:3.12-slim`，也可用 `ENRICH_EVAL_PYTHON_IMAGE` 固定镜像 digest。`ENRICH_EVAL_DOCKER_CONTEXT` 可指定本机 Docker daemon。`CONTEXT_CHECKOUT` 指向包含 `MULTI_AGENT_V2` 管线的 AgentKit Context Go checkout，`ROUND_DIR` 为本轮本地结果目录。

```bash
python3 -m evaluators.preflight
python3 -m evaluators.build_enriched "$CONTEXT_CHECKOUT" "$ROUND_DIR/enrichment"
python3 -m evaluators.consume "$ROUND_DIR/consumption" --arm raw
python3 -m evaluators.consume "$ROUND_DIR/consumption" --arm enriched --enrichment "$ROUND_DIR/enrichment"
python3 -m evaluators.attribution "$ROUND_DIR"
python3 -m evaluators.report "$ROUND_DIR" reports/round-01.md
```

归因需要逐次核对原文、富化叶条目和实际读取路径。确认后标记回执的 `confirmed`，再用 `python3 -m evaluators.tuning "$ROUND_DIR" PRECISION_ERROR` 等命令导出对应桶的 Dev 证据。agy 工作目录只放产品源码及对应桶的 Dev 证据。用相同配置重跑候选，`evaluators.report` 的 `--raw-round` 和 `--previous-round` 可指定两份历史对照。

Go 适配器通过 overlay 调用真实 Worker、Codex provider、方舟推理与产物编译。来源和权限由本地合成环境提供。消费适配器读取提案、表上下文、概念页和目录索引，按路径与修订回查原文。实测覆盖本地 Worker 和消费链路。部署端 Catalog、MCP 与发布链路需要单独在测试环境验证。运行轨迹保存在 Git 忽略的 `runs/` 中。
