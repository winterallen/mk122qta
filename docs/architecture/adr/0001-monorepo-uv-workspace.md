# ADR-0001: Monorepo 与 uv Workspace

## 状态

Accepted

## 背景

MK122 的 P0-P7 会同时演进公共契约、数据、信号、策略、执行、风控、仿真、观测与应用进程。多仓库会增加跨包契约同步成本。

## 决策

采用 Monorepo，并用 uv workspace 管理 `packages/*` 与 `apps/*`。

## 后果

所有包共享锁文件与 CI 基线。跨包依赖必须显式声明，后续需要用 import-linter 或等价规则防止依赖倒置。
