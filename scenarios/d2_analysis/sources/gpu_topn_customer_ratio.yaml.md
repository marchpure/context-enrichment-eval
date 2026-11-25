# metrics/cloud-operations/gpu/concentration/gpu_topn_customer_ratio.yaml

原始路径：metrics/cloud-operations/gpu/concentration/gpu_topn_customer_ratio.yaml

### id

```text
gpu_topn_customer_ratio
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
GPU TOPN 客户最近30天日均资源用量占 GPU 整体最近30天日均资源用量的比例；当 top_n <= 10 时使用 dws 预聚合快照，当 top_n > 10 时回退原始明细按窗口现算。
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
aeolus_app_1009314_dataset_snapshot
```
### dataset_refs[0].file

```text
../../../../dataset/aeolus/aeolus_app_1009314_dataset_snapshot.yaml
```
### dataset_refs[1].id

```text
aeolus_app_556078_dataset_gpu
```
### dataset_refs[1].file

```text
../../../../dataset/aeolus/aeolus_app_556078_dataset_gpu.yaml
```
### dataset_candidates

```json
[]
```
### depends_on[0].id

```text
gpu_usage_base
```
### depends_on[0].file

```text
../resource/gpu_usage_base.yaml
```
### derived_from

```text
gpu_usage_base
```
### implementation.hints

```text
1. 双轨逻辑：当 top_n <= 10 时，使用 dws 层预聚合结果，并在数据集内按 `account_total_mom` 重排后对前 top_n 的 `account_total_mom` 求和作为分子，分母统一取同快照同产品任一行的 `product_total_mom`（用 MAX）。严禁对 `客户规模占比` 求和。
2. 当 top_n > 10 时，回退到 GPU 明细表，按 start_date/end_date 窗口逐日聚合、排序并现算 TOPN 客户日均占比。
3. dws 路径依赖 snapshot_date；raw 路径依赖 start_date/end_date。
4. top_n <= 10 可复用 dws；top_n > 10 必须走 raw。
```
### implementation.sql_templates[0].engine

```text
hsql
```
### implementation.sql_templates[0].template

```text
WITH
dws_ranked AS (
  SELECT
    p_date,
    account_total_mom,
    ROW_NUMBER() OVER (PARTITION BY p_date, product ORDER BY account_total_mom DESC) AS rnk
  FROM `snapshot`
  WHERE p_date = '${snapshot_date}'
    AND product = 'GPU'
),
dws_result AS (
  SELECT
    SUM(CASE WHEN rnk <= ${top_n} THEN account_total_mom ELSE 0 END)
    / MAX(product_total_mom) AS topn_ratio
  FROM dws_ranked
),
raw_daily AS (
  SELECT
    p_date,
    SUM(gpu_usage) AS daily_total_gpu,
    SUM(CASE WHEN rnk <= ${top_n} THEN gpu_usage ELSE 0 END) AS daily_topn_gpu
  FROM (
    SELECT
      p_date,
      customer_short_name,
      SUM(instance_gpu_num) AS gpu_usage,
      ROW_NUMBER() OVER (PARTITION BY p_date ORDER BY SUM(instance_gpu_num) DESC) AS rnk
    FROM (${metric:gpu_usage_base:hsql}) base
    GROUP BY p_date, customer_short_name
  ) ranked
  GROUP BY p_date
),
raw_result AS (
  SELECT ROUND(AVG(daily_topn_gpu) * 100.0 / AVG(daily_total_gpu), 2) AS topn_ratio
  FROM raw_daily
)
SELECT topn_ratio
FROM dws_result
WHERE ${top_n} <= 10
UNION ALL
SELECT topn_ratio
FROM raw_result
WHERE ${top_n} > 10

```
### implementation.context_refs[0].id

```text
gpu_ops_ontology
```
### implementation.context_refs[0].file

```text
../../../_context/cloud-operations/gpu/gpu_ops_ontology.yaml
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
GPU TOPN客户占比
```
### category

```text
usage-and-resource
```
### owner

```text
unassigned
```
### phrases[0]

```text
GPU TOPN客户占比
```
### phrases[1]

```text
GPU TopN 客户占比
```
### phrases[2]

```text
GPU TOP10客户规模占比
```
### phrases[3]

```text
GPU TOP20客户占比
```
### provenance.decision

```text
inherited
```
### provenance.source

```text
metric_context:gpu_ops_ontology
```
### provenance.locator

```text
semantics.metrics[id=gpu_topn_customer_ratio]
```
### provenance.migration_source_sha256

```text
11d1940e6d9fa0db92f7631a743eed1205735f9cb631272862fb80af916659fa
```
### provenance.migration_input

```text
metrics/usage-and-resource.md
```
### provenance.migration_input_sha256

```text
cb77a0bb32a74b24a9885b7a04965e867975c80331ce7e628999bd9516555dcd
```
