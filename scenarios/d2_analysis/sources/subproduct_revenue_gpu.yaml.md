# metrics/business-operations/revenue/actual/subproduct_revenue_gpu.yaml

原始路径：metrics/business-operations/revenue/actual/subproduct_revenue_gpu.yaml

### id

```text
subproduct_revenue_gpu
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
指定月份内 GPU 子产品口径的实际收入，口径与 GPU 二级产品线一致：二级产品线属于基础深度学习或计算，且子产品名称命中 GPU/MLP 相关产品集合。
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
口径与 secondary_product_line_revenue_gpu 保持一致。
```
### implementation.sql_templates[0].engine

```text
hsql
```
### implementation.sql_templates[0].template

```text
SELECT
  'GPU' AS subproduct,
  SUM(`计收金额`) AS value
FROM (${metric:revenue_month_base:hsql}) base
WHERE `二级产品线(含BP)` IN ('基础深度学习(含BP)', '计算(含BP)')
  AND `子产品名称` IN ('GPU Compute Service', 'GPU云服务器', '高性能计算GPU云服务器', 'High Performance Compute Service', '机器学习平台-公有云', 'MLP')

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
GPU子产品实际收入
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
GPU子产品实际收入
```
### phrases[1]

```text
GPU子产品收入
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
semantics.metrics[id=subproduct_revenue_gpu]
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
