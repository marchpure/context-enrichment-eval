# metrics/cloud-operations/gpu/customer/gpu_active_users_base.yaml

原始路径：metrics/cloud-operations/gpu/customer/gpu_active_users_base.yaml

### id

```text
gpu_active_users_base
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
GPU 保有资源用户基础明细，按天去重保留 account_id，用于衍生指标复用。
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
aeolus_app_556078_dataset_gpu
```
### dataset_refs[0].file

```text
../../../../dataset/aeolus/aeolus_app_556078_dataset_gpu.yaml
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
统一封装 GPU 保有用户筛选口径，供周期/新增/流失/环比等指标复用。
```
### implementation.sql_templates[0].engine

```text
hsql
```
### implementation.sql_templates[0].template

```text
SELECT
  p_date,
  account_id
FROM `gpu`
WHERE p_date BETWEEN '${start_date}' AND '${end_date}'
  AND pay_type IN ('PostPaid', 'PrePaid', 'Spot')
  AND (account_tag = '外部账号' OR income_type IN ('外部收入', '内部收入-外') OR account_id = '9993')
  AND p_hour = '23'
  AND instance_gpu_model IN (
    'AMD MI308x-192G', 'AMD MI308x-192G-80CU', 'Bytedance jiuhuashan',
    'CAMBRICON MLU580X6', 'CAMBRICON MLU590 M9DK', 'FF40', 'FF45D',
    'HUAWEI Ascend 910b', 'HUAWEI Ascend 910c', 'Iluvatar BI-V150',
    'NVIDIA A10', 'NVIDIA A30', 'NVIDIA A40',
    'NVIDIA A800-SXM4-40GB', 'NVIDIA A800-SXM4-80GB',
    'NVIDIA GeForce RTX 4090', 'NVIDIA GeForce RTX 4090 D',
    'NVIDIA H100-SXM5-80GB', 'NVIDIA H20-3e',
    'NVIDIA H20-SXM5-96GB', 'NVIDIA H800-SXM5-80GB',
    'NVIDIA L20', 'NVIDIA L4', 'NVIDIA L40', 'NVIDIA L40S',
    'NVIDIA V100-PCIE-32GB', 'Tesla A100 80G', 'Tesla T4', 'Tesla V100',
    '4090', '4090D', '910b', 'A10', 'A100', 'A30', 'A800',
    'H100', 'H20', 'L20', 'L4', 'NVIDIA T4', 'T4', 'V100'
  )
  AND product IN ('GPU Compute Service', 'GPU云服务器', '机器学习平台-公有云', '高性能计算GPU云服务器', '云服务器')
GROUP BY p_date, account_id

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
GPU保有资源用户
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
GPU保有资源用户
```
### phrases[1]

```text
GPU保有用户基础
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
semantics.metrics[id=gpu_active_users_base]
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
