# Enrichment 评测与四归因复盘模板

- **实验轮次**：`round-XX`
- **日期**：`YYYY-MM-DD`
- **被测代码基线**：`context@<commit>` / `context-core@<commit>`
- **输入源冻结哈希**：`<sha256>`

## 一、三场景前后对照总表

| 场景 | 原文基线（`/36`） | 上轮富化（`/36`） | 本轮富化（`/36`） | Dev 通过 | Holdout 通过 | 新回归数 | 消费 Token 倍率 |
|---|---:|---:|---:|---:|---:|---:|---:|
| D2 数据分析 | - | - | - | - | - | 0 | 1.00x |
| 企业知识问答 | - | - | - | - | - | 0 | 1.00x |
| 研发上下文 | - | - | - | - | - | 0 | 1.00x |

## 二、错题四归因账单（仅针对 `dev` 集展开反例）

| 归因桶 | 失败次数 | 占比 | 代表错题与根因摘要 | 对应优化 Worker |
|---|---:|---:|---|---|
| `RECALL_MISS`（漏提取） | 0 | 0% | - | Worker-1（提取 Prompt / 切分） |
| `PRECISION_ERROR`（写错/串绑） | 0 | 0% | - | Worker-2（实体/条件校验器） |
| `RETRIEVAL_LINK_MISS`（组织/召回失败） | 0 | 0% | - | Worker-3（目录/EntryLink 组织） |
| `CONSUMER_ERROR`（消费端失误） | 0 | 0% | - | 单独记录，不盲改 Enrichment |

## 三、Property / 不变量门禁

- `PROP-01` 实体不串绑：PASS / FAIL
- `PROP-02` 条件不丢失：PASS / FAIL
- `PROP-03` 版本与状态保真：PASS / FAIL
- `PROP-04` Holdout 零泄漏：PASS / FAIL
- `PROP-05` 归因守恒：PASS / FAIL
