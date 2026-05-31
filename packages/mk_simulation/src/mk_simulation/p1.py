from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, replace
from decimal import Decimal

from mk_data.schemas import DailyBar
from mk_execution import ExecutionFill, SimulatedExecutor, build_rebalance_orders
from mk_risk import RiskBudget, RiskDecision, RiskGateState, RiskSnapshot, evaluate_risk_gate
from mk_signals import DEFAULT_SEED_FACTORS, SeedFactor, score_bars
from mk_strategies import MultiFactorAlphaStrategyActor, StrategyConfig, TargetWeight

from mk_simulation.ledger import (
    LedgerSnapshot,
    PortfolioLedger,
    ReconciliationReport,
    StrategyLedger,
)

ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class AlphaSimulationReport:
    strategy_id: str
    start_date: str
    end_date: str
    trading_days: int
    sharpe: float
    snapshots: tuple[LedgerSnapshot, ...]
    fills: tuple[ExecutionFill, ...]
    risk_decisions: tuple[RiskDecision, ...]
    reconciliation: ReconciliationReport
    strategy_ledger: StrategyLedger


def calculate_annualized_sharpe(
    returns: Sequence[Decimal],
    *,
    periods_per_year: int = 252,
) -> float:
    if len(returns) < 2:
        return 0.0
    float_returns = [float(value) for value in returns]
    mean_return = sum(float_returns) / len(float_returns)
    variance = sum((value - mean_return) ** 2 for value in float_returns) / len(float_returns)
    volatility = math.sqrt(variance)
    if volatility == 0.0:
        return 99.0 if mean_return > 0 else 0.0
    return mean_return / volatility * math.sqrt(periods_per_year)


def _bars_by_date(bars: Sequence[DailyBar]) -> dict[str, tuple[DailyBar, ...]]:
    grouped: defaultdict[str, list[DailyBar]] = defaultdict(list)
    for bar in bars:
        grouped[bar.trade_date_yyyymmdd].append(bar)
    return {trade_date: tuple(day_bars) for trade_date, day_bars in grouped.items()}


def _prices(day_bars: tuple[DailyBar, ...]) -> dict[str, Decimal]:
    return {bar.ts_code: bar.close for bar in day_bars}


def _scale_targets(targets: tuple[TargetWeight, ...], scale: Decimal) -> tuple[TargetWeight, ...]:
    return tuple(replace(target, target_weight=target.target_weight * scale) for target in targets)


def _risk_snapshot(
    targets: tuple[TargetWeight, ...],
    order_notional: Decimal,
    portfolio_value: Decimal,
    cash: Decimal,
) -> RiskSnapshot:
    gross_exposure = sum((target.target_weight for target in targets), ZERO)
    max_symbol_weight = max((target.target_weight for target in targets), default=ZERO)
    return RiskSnapshot(
        gross_exposure=gross_exposure,
        max_symbol_weight=max_symbol_weight,
        order_notional=order_notional,
        daily_turnover=ZERO if portfolio_value == ZERO else order_notional / portfolio_value,
        cash_buffer=ZERO if portfolio_value == ZERO else cash / portfolio_value,
    )


def run_single_strategy_simulation(
    bars: Sequence[DailyBar],
    *,
    initial_cash: Decimal = Decimal("1000000"),
    strategy_config: StrategyConfig | None = None,
    risk_budget: RiskBudget | None = None,
    factors: tuple[SeedFactor, ...] = DEFAULT_SEED_FACTORS,
) -> AlphaSimulationReport:
    if not bars:
        raise ValueError("simulation requires daily bars")

    grouped_by_date = _bars_by_date(bars)
    trade_dates = tuple(sorted(grouped_by_date))
    strategy = MultiFactorAlphaStrategyActor(strategy_config)
    strategy_ledger = StrategyLedger(strategy.config.strategy_id)
    portfolio = PortfolioLedger(initial_cash)
    executor = SimulatedExecutor()
    decisions: list[RiskDecision] = []
    all_fills: list[ExecutionFill] = []
    history: list[DailyBar] = []
    last_reconciliation: ReconciliationReport | None = None

    for trade_date in trade_dates:
        day_bars = grouped_by_date[trade_date]
        history.extend(day_bars)
        prices = _prices(day_bars)
        portfolio_value = portfolio.total_equity(prices)
        scores = score_bars(history, factors=factors)
        targets = strategy.generate_targets(scores)
        strategy_ledger.record_targets(len(targets))
        orders = build_rebalance_orders(
            targets,
            current_positions=portfolio.position_quantities(),
            prices=prices,
            portfolio_value=portfolio_value,
            strategy_id=strategy.config.strategy_id,
            trade_date=trade_date,
        )
        order_notional = sum((order.notional for order in orders), ZERO)
        decision = evaluate_risk_gate(
            _risk_snapshot(targets, order_notional, portfolio_value, portfolio.cash),
            risk_budget,
        )
        decisions.append(decision)

        if decision.state == RiskGateState.REDUCE:
            targets = _scale_targets(targets, decision.approved_weight_scale)
            orders = build_rebalance_orders(
                targets,
                current_positions=portfolio.position_quantities(),
                prices=prices,
                portfolio_value=portfolio_value,
                strategy_id=strategy.config.strategy_id,
                trade_date=trade_date,
            )
        elif not decision.is_tradable:
            orders = ()

        strategy_ledger.record_orders(len(orders))
        fills = executor.fill_at_close(orders, day_bars)
        strategy_ledger.record_fills(len(fills))
        for fill in fills:
            portfolio.apply_fill(fill)
        all_fills.extend(fills)
        snapshot = portfolio.mark_to_market(trade_date, prices)
        last_reconciliation = portfolio.reconcile(snapshot, prices)

    returns = [snapshot.daily_return for snapshot in portfolio.snapshots[1:]]
    reconciliation = last_reconciliation or ReconciliationReport(ZERO, ZERO, ZERO)
    return AlphaSimulationReport(
        strategy_id=strategy.config.strategy_id,
        start_date=trade_dates[0],
        end_date=trade_dates[-1],
        trading_days=len(trade_dates),
        sharpe=calculate_annualized_sharpe(returns),
        snapshots=tuple(portfolio.snapshots),
        fills=tuple(all_fills),
        risk_decisions=tuple(decisions),
        reconciliation=reconciliation,
        strategy_ledger=strategy_ledger,
    )
