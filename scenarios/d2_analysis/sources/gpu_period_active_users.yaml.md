# metrics/cloud-operations/gpu/customer/gpu_period_active_users.yaml

原始路径：metrics/cloud-operations/gpu/customer/gpu_period_active_users.yaml

### id

```text
gpu_period_active_users
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
统计任意查询周期内 GPU 保有资源用户数（按账号去重）。
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
aeolus_app_556078_dataset_gpu
```
### dataset_candidates[0].file

```text
../../../../dataset/aeolus/aeolus_app_556078_dataset_gpu.yaml
```
### dataset_candidates[0].evidence

```text
ontology_scope
```
### dataset_candidates[1].id

```text
aeolus_app_1009314_dataset_snapshot
```
### dataset_candidates[1].file

```text
../../../../dataset/aeolus/aeolus_app_1009314_dataset_snapshot.yaml
```
### dataset_candidates[1].evidence

```text
ontology_scope
```
### depends_on[0].id

```text
gpu_active_users_base
```
### depends_on[0].file

```text
gpu_active_users_base.yaml
```
### derived_from

```text
gpu_active_users_base
```
### implementation.hints

```text
复用 GPU 保有用户基础明细，对 account_id 去重计数。
```
### implementation.sql_templates[0].engine

```text
hsql
```
### implementation.sql_templates[0].template

```text
SELECT
  COUNT(DISTINCT account_id) AS value
FROM (
  ${metric:gpu_active_users_base:hsql}
) t

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
当前仅登记于 `云基础核心运营 - GPU` 领域
```
### kind

```text
metric
```
### name

```text
周期内GPU保有资源用户数
```
### category

```text
user-and-customer
```
### owner

```text
unassigned
```
### phrases[0]

```text
周期内GPU保有资源用户数
```
### phrases[1]

```text
GPU周期保有用户数
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
semantics.metrics[id=gpu_period_active_users]
```
### provenance.migration_source_sha256

```text
11d1940e6d9fa0db92f7631a743eed1205735f9cb631272862fb80af916659fa
```
### provenance.migration_input

```text
metrics/user-and-customer.md
```
### provenance.migration_input_sha256

```text
98ee892f25c5c5ddfaa41868666424e165d92f2661dc4353b1b3c9df51026e22
```
