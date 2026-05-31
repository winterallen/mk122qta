from __future__ import annotations

from decimal import Decimal

from mk_data.schemas import DailyBar
from mk_signals import (
    FactorOperator,
    evaluate_expression,
    generate_candidate_expressions,
    parse_factor_expression,
)


def make_bar(trade_date: str, close: str) -> DailyBar:
    return DailyBar.model_validate(
        {
            "ts_code": "000001.SZ",
            "trade_date": trade_date,
            "open": close,
            "high": str(Decimal(close) * Decimal("1.01")),
            "low": str(Decimal(close) * Decimal("0.99")),
            "close": close,
            "pre_close": close,
            "change": "0.00",
            "pct_chg": "0.00",
            "vol": "1000",
            "amount": str(Decimal(close) * Decimal("1000")),
        }
    )


def test_parse_factor_expression_and_evaluate_momentum() -> None:
    expression = parse_factor_expression("momentum(close,2)")
    value = evaluate_expression(
        expression,
        (
            make_bar("20240102", "10.00"),
            make_bar("20240103", "10.50"),
            make_bar("20240104", "11.00"),
        ),
    )

    assert expression.operator == FactorOperator.MOMENTUM
    assert value == Decimal("0.04761904761904761904761904762")


def test_generate_candidate_expressions_supports_p2_scale() -> None:
    expressions = generate_candidate_expressions(limit=1000)

    assert len(expressions) >= 50
    assert all(expression.depth <= 4 for expression in expressions)
    assert len({expression.dsl for expression in expressions}) == len(expressions)
