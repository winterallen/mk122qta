# ADR-0003: 事件总线选择 NATS JetStream，Redis Streams 备用

## 状态

Accepted

## 背景

自治系统中数据、信号、计划、订单、风险与观测需要事件驱动，且要支持持久化与重放。

## 决策

主事件总线选择 NATS JetStream，Redis Streams 作为低门槛备用方案。

## 后果

P0 先提供事件契约与 docker-compose 基础服务。真正的事件发布订阅封装在多进程化前逐步补齐。
