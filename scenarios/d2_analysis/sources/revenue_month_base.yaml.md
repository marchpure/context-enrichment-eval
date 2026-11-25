# metrics/business-operations/revenue/actual/revenue_month_base.yaml

原始路径：metrics/business-operations/revenue/actual/revenue_month_base.yaml

### id

```text
revenue_month_base
```
### version

```text
1.0
```
### status

```text
collected
```
### definition

```text
指定月份、最新可用分区下的收入基础明细，供各二级产品线和子产品收入指标复用。
```
### contract.status

```text
unresolved
```
### contract.unit

```json
null
```
### contract.grain

```json
null
```
### contract.time_window

```json
null
```
### contract.numerator

```json
null
```
### contract.denominator

```json
null
```
### contract.aggregation

```json
null
```
### contract.filters

```json
null
```
### contract.null_and_zero_policy

```json
null
```
### contract.note

```text
原定义与 SQL 已保留；上述结构化契约需逐项核验，不从名称自动推断。
```
### dataset_refs[0].id

```text
aeolus_app_556321_dataset_revenue
```
### dataset_refs[0].file

```text
../../../../dataset/aeolus/aeolus_app_556321_dataset_revenue.yaml
```
### dataset_candidates

```json
[]
```
### depends_on

```json
[]
```
### implementation.hints

```text
全量表查询时统一加上 `p_date` = '${p_date}'。
p_date 取最新可用分区（最近有数分区；通常 T-1，若数据延迟则回退至 T-2 等更早分区）。建议在执行 SQL 前先查询 `max(p_date)` 得到 latest_p_date，再将其透传为参数 `${p_date}`。
month 参数为 YYYY-MM，并转换为当月起止日期过滤 `计收月份`。
```
### implementation.sql_templates[0].engine

```text
hsql
```
### implementation.sql_templates[0].template

```text
SELECT
  `p_date`,
  `计收月份`,
  `收入类型`,
  `二级产品线(含BP)`,
  `二级产品线`,
  `子产品名称`,
  `计费单元`,
  `ArkClaw类型`,
  `计收金额`
FROM `revenue`
WHERE `p_date` = '${p_date}'
  AND `收入类型` IN ('内部收入-外', '外部收入')
  AND `计收月份` >= toDate('${month}-01')
  AND `计收月份` < addMonths(toDate('${month}-01'), 1)

```
### implementation.context_refs[0].id

```text
subproduct_revenue_ontology
```
### implementation.context_refs[0].file

```text
../../../_context/business-operations/revenue/subproduct_revenue_ontology.yaml
```
### usage_notes

```text
`core_product_churn`、`effective_billing_customer_lifecycle`、`effective_billing_customer_comparison`
```
### kind

```text
metric
```
### name

```text
指定月份收入基础明细
```
### category

```text
revenue-and-billing
```
### owner

```text
unassigned
```
### phrases[0]

```text
指定月份收入基础明细
```
### phrases[1]

```text
月度收入基础表
```
### provenance.decision

```text
inherited
```
### provenance.source

```text
metric_context:subproduct_revenue_ontology
```
### provenance.locator

```text
semantics.metrics[id=revenue_month_base]
```
### provenance.migration_source_sha256

```text
72dc150fa008fbac39affa101b13e573f25a59640d56cba67bcfcdfe0e236248
```
### provenance.migration_input

```text
metrics/revenue-and-billing.md
```
### provenance.migration_input_sha256

```text
cb2e7f45436f6ae341d99f3593f8d04cc0ff58260b1d92fded3cb2af783602b8
```
