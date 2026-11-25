# SQLite 合成执行资产登记

两组仅访问独立的合成 SQLite 副本。使用短表名和 SQLite SQL。资产 a 观察期 2026-11-01 至 11-30，b 观察期 2026-12-01 至 12-30。日期按 YYYY-MM-DD 文本比较。日期分区与计收月份独立，计收月份用每月 1 日。

gpu 代表按天的 GPU 基础明细。customer_short_name 为展示粒度。snapshot 为 GPU Top10 月均快照，product_total_mom 为每行重复的产品总量。period_usage 是覆盖两期各 30 天的预过滤事实。revenue 是月度收入快照。

