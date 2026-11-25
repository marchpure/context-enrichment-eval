# metrics/business-operations/revenue/actual/subproduct_revenue_tos.yaml

原始路径：metrics/business-operations/revenue/actual/subproduct_revenue_tos.yaml

### id

```text
subproduct_revenue_tos
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
指定月份内 TOS 子产品实际收入，定义为存储二级产品线下，子产品名称为对象存储或 Torch Object Storage。
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
### dataset_refs

```json
[]
```
### dataset_candidates[0].id

```text
aeolus_app_556321_dataset_revenue
```
### dataset_candidates[0].file

```text
../../../../dataset/aeolus/aeolus_app_556321_dataset_revenue.yaml
```
### dataset_candidates[0].evidence

```text
ontology_scope
```
### depends_on[0].id

```text
revenue_month_base
```
### depends_on[0].file

```text
revenue_month_base.yaml
```
### derived_from

```text
revenue_month_base
```
### implementation.hints

```text
对应仪表盘 report_id=14187279。
```
### implementation.sql_templates[0].engine

```text
hsql
```
### implementation.sql_templates[0].template

```text
SELECT
  'TOS' AS subproduct,
  SUM(`计收金额`) AS value
FROM (${metric:revenue_month_base:hsql}) base
WHERE `二级产品线(含BP)` = '存储(含BP)'
  AND `子产品名称` IN ('对象存储', 'Torch Object Storage')

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
`core_product_operations`
```
### kind

```text
metric
```
### name

```text
TOS子产品实际收入
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
TOS子产品实际收入
```
### phrases[1]

```text
对象存储收入
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
semantics.metrics[id=subproduct_revenue_tos]
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
