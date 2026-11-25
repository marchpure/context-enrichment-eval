# AgentKit Enrichment Round 0 基线实测

- Worker 代码 `997ff622d3e66b2dd0df8b1ff96db54eeff447ee`
- 消费模型 `doubao-seed-2-0-pro-260215`，每题 3 次
- 冻结输入 SHA256 `92a14df74060721a4b47219ae767f7f36cc8790453008880f335f745c45f035e`

| 场景 | 原文通过 | 当前富化通过 | pass@1 原文 → 富化 | Dev 原文 → 富化 | Holdout 原文 → 富化 | 配对进步 / 退化 | 新回归 原文 / 富化 |
|---|---:|---:|---:|---:|---:|---:|---:|
| D2 数据分析 | 27/36 | 21/36 | 9 → 6 / 12 | 21 → 15 / 24 | 6 → 6 / 12 | 4 / 10 | 0 / 0 |
| 企业知识问答 | 28/36 | 23/36 | 10 → 7 / 12 | 17 → 15 / 24 | 11 → 8 / 12 | 3 / 8 | 0 / 0 |
| 研发上下文 | 29/36 | 22/36 | 10 → 6 / 12 | 20 → 13 / 24 | 9 → 9 / 12 | 2 / 9 | 0 / 1 |

| 场景 | 消费平均 Token 原文 → 富化 | 消费耗时中位数 原文 → 富化 | 富化加工耗时 | 机械通过且可回源 原文 → 富化 |
|---|---:|---:|---:|---:|
| D2 数据分析 | 16688 → 22194 | 33.0 s → 30.1 s | 578.4 s | 1/27 → 0/21 |
| 企业知识问答 | 8790 → 16988 | 21.3 s → 21.9 s | 535.9 s | 15/28 → 0/23 |
| 研发上下文 | 6757 → 16573 | 21.0 s → 25.9 s | 231.7 s | 0/29 → 0/22 |

## 富化臂四归因账单

| 归因 | 审计归类 | 已核对 |
|---|---:|---:|
| `RECALL_MISS` | 0 | 0 |
| `PRECISION_ERROR` | 6 | 5 |
| `RETRIEVAL_LINK_MISS` | 6 | 4 |
| `CONSUMER_ERROR` | 30 | 20 |

未归类 0 次，已有候选归因待核对 13 次。

### Dev 逐次证据

| 题号 | 重复 | 归因 | 核对 | 观察 |
|---|---:|---|---|---|
| ANA-01 | 1 | `RETRIEVAL_LINK_MISS` | 完成 | 该次任务仅读取到enriched/documents/sqlite和schema.md，未读取到包含GPU保有资源用户筛选口径、字段定义的gpu_active_users_base.yaml.md及对应富化叶条目enriched/documents/gpu、enriched/assets/source-0fb148ed77f022cc，导致误认为缺少计费状态、GPU型号字段，未能生成合法SQL。 |
| ANA-02 | 1 | `CONSUMER_ERROR` | 完成 | 消费端错误判断收入表无2026年11月可用分区，未按规则使用最新p_date=2026-12-31分区过滤计收月份，且错误返回null SQL，实际规则允许使用最新分区筛选对应计收月份数据。 |
| ANA-02 | 2 | `RETRIEVAL_LINK_MISS` | 完成 | 执行时未读取收入口径相关的富化叶条目（如subproduct_revenue_tos.yaml.md、revenue_month_base.yaml.md等），错误声称无权限查看表结构、字段定义不明确，实际相关字段映射与规则已在富化条目中明确。 |
| ANA-02 | 3 | `PRECISION_ERROR` | 完成 | 现有SQL未按规则添加p_date过滤条件（使用最新可用分区）、未过滤收入类型为'内部收入-外'或'外部收入'，导致adversarial模式下计算结果错误。 |
| ANA-03 | 1 | `RETRIEVAL_LINK_MISS` | 完成 | 富化叶条目enriched/documents/topic-4f341461237466f6b1c96bb0deedfe6d中已明确GPU收入计算所需的收入类型、二级产品线、子产品集合、分区规则及字段对应关系，但本次任务未读取该条目，导致SQL过滤条件错误、收入金额返回null。 |
| ANA-03 | 2 | `CONSUMER_ERROR` | 完成 | 已送达的收入规则明确要求过滤收入类型为'内部收入-外'或'外部收入'、使用max(p_date)最新分区、billing_month过滤2026年12月，且子产品集合需包含6个枚举值，但消费端遗漏收入类型过滤、分区规则、billing_month过滤，且子产品枚举不全，导致计算结果错误。 |
| ANA-04 | 2 | `RETRIEVAL_LINK_MISS` | 完成 | 已送达的富化叶条目包含GPU TOP20客户占比的计算规则（top_n>10时走原始明细路径，需复用gpu_usage_base的过滤条件、按日排名取前20再算日均），但本次执行未读取gpu_usage_base.yaml.md的过滤规则，SQL中缺失pay_type、账号范围、p_hour、GPU型号、产品范围等必要过滤条件，且计算逻辑错误（先算客户全月日均再取前20，未按日排名），导致结果不符合预期。 |
| ANA-04 | 3 | `CONSUMER_ERROR` | 完成 | 已送达所有必要规则（gpu_usage_base过滤条件、top_n>10时的明细计算逻辑、SQLite资产表结构），但执行步数耗尽未生成有效结果，属于消费端超时/步数超限错误。 |
| ANA-05 | 1 | `CONSUMER_ERROR` | 完成 | 消费端生成的SQL通过SELECT DISTINCT account_id, pay_type FROM period_usage获取全量键，导致仅在单期出现的单边账号（如lost、new）未被纳入结果集，未正确使用两期聚合结果全外连接的方式保留所有单边账号，符合规则要求的保留单边账号逻辑错误 |
| DEV-01 | 1 | `CONSUMER_ERROR` | 完成 | 消费端编写headers函数时未遵循契约中“请求头覆盖值为None时移除该头”的规则，对值为None的自定义头未做过滤直接合并进结果，导致X-Remove键（值为None）被保留在输出中，不符合验收测试断言要求 |
| DEV-03 | 2 | `PRECISION_ERROR` | 完成 | 富化叶条目enriched/documents/topic-516a86b28d4580498ce790564797dc8d中记录的跨域重定向请求头处理规则错误，未包含需要不区分大小写剥离Cookie头的要求，导致修复时仅移除了Authorization的大小写变体，遗漏Cookie头，与docs/current/redirects.md中的规则不符 |
| DEV-03 | 3 | `CONSUMER_ERROR` | 完成 | 关键规则已通过富化叶条目enriched/documents/topic-7f2086f92b373290242a37ed17e3848b准确送达，但生成的补丁格式错误，在answer中额外嵌套了decision层，不符合要求的顶层files结构，导致invalid source file mapping错误 |
| DEV-06 | 1 | `CONSUMER_ERROR` | 完成 | 修复时仅修改cedar/transport.py移除了finally块的release调用，未同步修正cedar/body.py中rewind函数固定seek(0)的错误，导致重试时回退到流起始位置而非首次尝试前的初始位置，不符合重放位置规则要求。 |
| DEV-06 | 2 | `CONSUMER_ERROR` | 完成 | 修复时仅修改cedar/body.py将rewind函数改为seek(initial)，但未同步修正release函数关闭流的错误，导致流被越权关闭，违反请求体所有权规则要求。 |
| DEV-07 | 1 | `PRECISION_ERROR` | 完成 | 富化叶条目将原文 opt-in trace=True emits X-Lane 错误转写为“生成X-Lane响应头”，导致消费端将 X-Lane 写入响应头而非请求头。 |
| DEV-07 | 2 | `PRECISION_ERROR` | 完成 | 富化叶条目将原文 opt-in trace=True emits X-Lane 错误转写为“生成X-Lane响应头”，导致消费端将 X-Lane 写入响应头而非请求头。 |
| DEV-07 | 3 | `PRECISION_ERROR` | 完成 | 富化叶条目将原文 opt-in trace=True emits X-Lane 错误转写为“生成X-Lane响应头”，导致消费端将 X-Lane 写入响应头而非请求头。 |
| DEV-08 | 1 | `CONSUMER_ERROR` | 完成 | 超出步数限制未完成代码修改，关键规则已送达但未产出有效实现 |
| DEV-08 | 2 | `CONSUMER_ERROR` | 完成 | 已送达的规则明确仅GET和HEAD方法可重试429，但实现中未校验请求方法，导致POST方法返回429时错误执行休眠，违反契约要求 |
| DEV-08 | 3 | `CONSUMER_ERROR` | 完成 | 已送达的规则明确仅GET和HEAD方法可重试429，但实现中未校验请求方法，导致POST方法返回429时错误执行休眠，违反契约要求 |
| QA-01 | 2 | `CONSUMER_ERROR` | 完成 | 所有必要规则相关的原文与富化叶条目均已送达，但消费端未完成答案生成，触发步数限制导致失败 |
| QA-02 | 1 | `CONSUMER_ERROR` | 完成 | 已送达BorealDocs当前服务支持政策、Cobalt-2特批规则及跨产品特批限制规则，仍错误认定有效支持计划为Enterprise，错误采用Enterprise档位的响应与升级分钟数，未校验请求客户身份与特批适用租户的一致性，错误适用特批规则。 |
| QA-02 | 2 | `CONSUMER_ERROR` | 完成 | 已送达BorealDocs Cobalt-2特批适用范围与当前服务支持政策，仍错误认定本次客户（Cobalt-1）可适用Cobalt-2的特批规则，采用特批对应的Enterprise档位响应与升级分钟数，未校验请求客户身份与特批租户的匹配性。 |
| QA-02 | 3 | `CONSUMER_ERROR` | 完成 | 已送达特批适用租户身份规则与BorealDocs Business档位标准时限，仍错误将Cobalt-1的请求匹配为Cobalt-2的特批权益，采用特批的响应与升级分钟数，未正确识别请求客户与特批租户不一致。 |
| QA-07 | 1 | `CONSUMER_ERROR` | 完成 | 消费端已获取到审计服务恢复后需重新验证权限和审批的规则，仍错误判断该字段为null，属于自身推理错误 |
| QA-07 | 2 | `CONSUMER_ERROR` | 完成 | 消费端已获取到审计服务恢复后需重新验证权限和审批的规则，仍错误认为无需重验证，属于自身推理错误 |
| QA-08 | 1 | `CONSUMER_ERROR` | 完成 | 现有已送达的富化叶条目已明确导出操作仅在创建/重新签发时校验ACL，已签发的导出归档不存在绕过后续ACL变更的规则，应判定archive_bypasses_acl为false，但消费端错误认为规则不足返回null。 |
| QA-08 | 2 | `CONSUMER_ERROR` | 完成 | 现有已送达的规则明确导出仅在创建/重签发时校验ACL，已签发的归档访问无需校验后续ACL变更，应判定archive_bypasses_acl为false，但消费端错误认为缺少规则返回null。 |
| QA-08 | 3 | `CONSUMER_ERROR` | 完成 | 现有已送达的规则明确导出时已校验ACL，已签发的归档不存在后续ACL校验要求，无需额外核查审批与日志即可判定archive_bypasses_acl为false，但消费端错误认为信息不足返回null。 |
