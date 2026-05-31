from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from mk_data.schemas import DailyBar


@dataclass(frozen=True, slots=True)
class QualityIssue:
    code: str
    message: str
    row: int | None = None


@dataclass(frozen=True, slots=True)
class DailyQualityReport:
    rows_checked: int
    issues: tuple[QualityIssue, ...]

    @property
    def passed(self) -> bool:
        return not self.issues

    def raise_if_failed(self) -> None:
        if self.passed:
            return

        details = "; ".join(issue.message for issue in self.issues)
        raise ValueError(f"Daily quality gate failed: {details}")


@dataclass(frozen=True, slots=True)
class DailyQualityRules:
    expected_ts_code: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    max_abs_pct_chg: Decimal = Decimal("30")


def validate_daily_bars(
    bars: list[DailyBar],
    *,
    rules: DailyQualityRules | None = None,
) -> DailyQualityReport:
    active_rules = rules or DailyQualityRules()
    issues: list[QualityIssue] = []

    if not bars:
        issues.append(QualityIssue(code="empty", message="daily dataset is empty"))
        return DailyQualityReport(rows_checked=0, issues=tuple(issues))

    seen_keys: set[tuple[str, str]] = set()
    for index, bar in enumerate(bars):
        key = (bar.ts_code, bar.trade_date_yyyymmdd)
        row_name = f"{bar.ts_code} {bar.trade_date_yyyymmdd}"
        if active_rules.expected_ts_code and bar.ts_code != active_rules.expected_ts_code:
            issues.append(
                QualityIssue(
                    code="unexpected_symbol",
                    message=f"unexpected ts_code for {row_name}",
                    row=index,
                )
            )

        if active_rules.start_date and bar.trade_date < active_rules.start_date:
            issues.append(
                QualityIssue(
                    code="date_before_range",
                    message=f"trade_date before expected range for {row_name}",
                    row=index,
                )
            )

        if active_rules.end_date and bar.trade_date > active_rules.end_date:
            issues.append(
                QualityIssue(
                    code="date_after_range",
                    message=f"trade_date after expected range for {row_name}",
                    row=index,
                )
            )

        if key in seen_keys:
            issues.append(
                QualityIssue(
                    code="duplicate_key",
                    message=f"duplicate ts_code/trade_date: {row_name}",
                    row=index,
                )
            )
        seen_keys.add(key)

        if bar.high < max(bar.open, bar.low, bar.close):
            issues.append(
                QualityIssue(
                    code="invalid_high",
                    message=f"high is below open/low/close for {row_name}",
                    row=index,
                )
            )

        if bar.low > min(bar.open, bar.high, bar.close):
            issues.append(
                QualityIssue(
                    code="invalid_low",
                    message=f"low is above open/high/close for {row_name}",
                    row=index,
                )
            )

        if abs(bar.pct_chg) > active_rules.max_abs_pct_chg:
            issues.append(
                QualityIssue(
                    code="extreme_pct_chg",
                    message=f"pct_chg exceeds threshold for {row_name}",
                    row=index,
                )
            )

    return DailyQualityReport(rows_checked=len(bars), issues=tuple(issues))
