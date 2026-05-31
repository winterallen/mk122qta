# ADR-0007: Delta Lake 与 DuckDB 数据湖查询

## 状态

Accepted

## 背景

P0 需要从原始行情文件形成可复现历史快照，并支持本地快速查询与回测。

## 决策

使用 Delta Lake 保存快照与版本元数据，使用 DuckDB 做本地分析查询。P0 通过 delta-rs 写表，并将 Delta 表读入 DuckDB 查询。

## 后果

本地开发无需外部数据库即可跑通 raw -> snapshot -> query -> backtest。后续可扩展到 MinIO/S3 与更完整的数据血缘治理。
