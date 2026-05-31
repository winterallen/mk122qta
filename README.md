# MK122 全自动量化交易自治系统

MK122 是面向 A 股股票与 ETF 的全自动量化交易自治系统。当前工程从 P0 基建开始落地，目标是先建立可测试、可扩展的 Monorepo 骨架，再逐步实现数据湖、信号、策略、执行、风控、元自治与观测能力。

## 快速开始

```bash
uv sync
make test
make check
```

## 密钥配置

Tushare token 不写入仓库。开发环境请设置环境变量：

```bash
TUSHARE_TOKEN=your-token
```

也可以参考 `configs/secrets.local.yaml.example` 创建本地密钥文件；该文件已被 `.gitignore` 忽略。

## 数据接入样例

拉取 Tushare 日线数据并写入本地原始数据目录：

```bash
uv run mk-data-fetch-daily --ts-code 000001.SZ --start-date 20240102 --end-date 20240105
```

默认输出到 `data/raw/tushare/daily/`。`data/` 是本地数据目录，已被 `.gitignore` 排除。

## 当前阶段

- P0-1: Monorepo + uv workspace + 基础配置
- P0-2: `mk_common` 公共基础包，包含配置、事件、ID、结构化日志、统一异常和基础契约
- P0-3: `mk_data` 数据接入，支持 Tushare 日线拉取、原始落盘、Delta 快照、DuckDB 查询、血缘记录和质量门禁
- P0-4: `mk_simulation` 最小回测骨架，支持 close-to-close 可复现回测
- P1-1: `mk_signals` 10 个种子因子与综合评分
- P1-2: `mk_strategies` 主多因子 Alpha 策略 Actor
- P1-3: `mk_risk` 风险预算与 PASS/BLOCK/REDUCE/FREEZE/HALT 5 态闸门
- P1-4: `mk_execution` 仿真订单生成与 close fill
- P1-5: `mk_simulation` 组合/策略账本、10 日仿真、Sharpe 与对账
- P1-6: `mk_dashboard` 5 个只读页面 API 与 SSE 骨架
- P2-1: `mk_signals` 因子表达式 DSL、候选生成与统计变换
- P2-2: `mk_signals` 6 阶段因子验证流水线，覆盖 IC/IR、稳定性、相关性、过拟合和成本
- P2-3: `mk_signals` Pool/Shadow/Live/Veteran 4 状态晋级与 Thompson 权重分配
- P2-4: `mk_dashboard` 因子工厂 API，提供 IC 曲线、相关性热力和晋级队列
- P3-1: `mk_strategies` 6 条独立策略 Actor 目录
- P3-2: `mk_meta` 元调度器、策略级熔断、HRP 近似资金分配与贝叶斯裁剪审计
- P3-3: `mk_orchestrator` 多策略调度 App 入口
- P3-4: `mk_dashboard` 元调度审计 API 与决策日志 API
- P4-1: `mk_learning` 在线线性模型、FTRL 基线、梯度安全、弹性学习率与双轨投票
- P4-2: `mk_learning` PSI/KS/Wasserstein/残差/重要性 5 类漂移检测
- P4-3: `mk_learning` 7 模型动物园、Shadow 晋级和跨市场状态稳定性评估
- P4-4: `mk_dashboard` 漂移监控 API 与模型动物园 API

## 应用入口

```bash
uv run mk-strategy-runner
uv run mk-risk-gate
uv run mk-executor
uv run mk-dashboard
uv run mk-orchestrator
uv run mk-learning-worker
```

## P0 验证

```bash
uv run pytest
uv run ruff check packages apps tests
uv run ruff format --check packages apps tests
uv run mypy packages apps
uv run mkdocs build --strict
docker compose config
```

## P1 验证

```bash
uv run pytest
uv run ruff check packages apps tests
uv run ruff format --check packages apps tests
uv run mypy packages apps
uv run mkdocs build --strict
```

## P2 验证

```bash
uv run pytest
uv run ruff check packages apps tests
uv run ruff format --check packages apps tests
uv run mypy packages apps
uv run mkdocs build --strict
```

## P3 验证

```bash
uv run pytest
uv run ruff check packages apps tests
uv run ruff format --check packages apps tests
uv run mypy packages apps
uv run mk-orchestrator
uv run mkdocs build --strict
```

## P4 验证

```bash
uv run pytest
uv run ruff check packages apps tests
uv run ruff format --check packages apps tests
uv run mypy packages apps
uv run mk-learning-worker
uv run mkdocs build --strict
```
