"""Measured model quality and real predictions for the dashboard.

Quality figures come from evaluation/results/*.json (written by the evaluation scripts), so the
dashboard shows the same numbers as the paper instead of invented accuracies. Forecasts are genuine
SARIMA fits on the Olist daily series, using the orders selected in evaluation/run_forecasting.py.
"""
from __future__ import annotations

import json
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from .olist_metrics import customer_rfm, daily_metrics, rfm_summary

RESULTS_DIR = Path(__file__).resolve().parents[2] / "evaluation" / "results"
DEPLOYED_DETECTOR = "weekday/hybrid"


def _load(name: str) -> Dict[str, Any]:
    path = RESULTS_DIR / name
    return json.loads(path.read_text()) if path.exists() else {}


@lru_cache(maxsize=None)
def model_cards() -> Dict[str, Dict[str, Any]]:
    """One card per model: what it is and its measured test-set quality (None if not evaluated)."""
    anomaly = _load("anomaly.json")
    forecasting = _load("forecasting.json")
    detector = anomaly.get("test", {}).get(DEPLOYED_DETECTOR, {})
    revenue = forecasting.get("revenue", {})
    revenue_h1 = revenue.get("metrics", {}).get("h1", {}).get("sarima", {})
    order = revenue.get("selection", {})
    return {
        "anomaly_detection": {
            "model": "Weekday-adjusted Isolation Forest + z-score (hybrid)",
            "status": "active",
            "metric_name": "F1 (test, injected anomalies)",
            "metric_value": detector.get("f1"),
            "details": {k: detector.get(k) for k in ("precision", "recall", "f1_std")},
        },
        "revenue_forecasting": {
            "model": f"SARIMA{tuple(order.get('order', ()))}{tuple(order.get('seasonal_order', ()))}",
            "status": "active",
            "metric_name": "MAPE, 1 day ahead (test)",
            "metric_value": revenue_h1.get("mape") / 100 if revenue_h1.get("mape") else None,
            "details": {"mae_brl": revenue_h1.get("mae")},
        },
        "customer_segmentation": {
            "model": "RFM (R, M quintiles; repeat vs one-time)",
            "status": "active",
            "metric_name": "Customers segmented",
            "metric_value": None,
            "details": {"customers": len(customer_rfm())},
        },
    }


def _sarima_next_day(series, order, seasonal_order) -> Dict[str, float]:
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = SARIMAX(series.to_numpy(), order=order, seasonal_order=seasonal_order,
                      trend="c" if order[1] == 0 else "n").fit(disp=False)
    forecast = fit.get_forecast(1)
    low, high = forecast.conf_int(alpha=0.05)[0]
    return {"value": float(forecast.predicted_mean[0]), "low_95": float(low), "high_95": float(high)}


@lru_cache(maxsize=None)
def next_day_forecast() -> Dict[str, Any]:
    """Revenue and orders for the day after the last day of the Olist series."""
    frame = daily_metrics()
    forecasting = _load("forecasting.json")
    out: Dict[str, Any] = {"forecast_date": str((frame.index[-1] + frame.index.freq).date())}
    for metric in ("revenue", "orders"):
        selection = forecasting.get(metric, {}).get("selection")
        if not selection:
            continue
        out[metric] = _sarima_next_day(frame[metric], tuple(selection["order"]),
                                       tuple(selection["seasonal_order"]))
        out[metric]["test_mape"] = forecasting[metric]["metrics"]["h1"]["sarima"]["mape"]
    return out


def replayed_decisions(limit: int = 10) -> List[Dict[str, Any]]:
    """The last decisions the five-agent pipeline made while replaying the Olist days.

    Written by evaluation/run_pipeline.py: real outputs of the Simulation, Decision and Governance
    agents, each tagged with the Olist date it was made for.
    """
    import pandas as pd

    path = RESULTS_DIR / "pipeline_decisions.csv"
    if not path.exists():
        return []
    rows = pd.read_csv(path).query("completed").tail(limit).iloc[::-1]
    decisions = []
    for i, row in enumerate(rows.itertuples()):
        auto = bool(row.action == "auto_approve")
        decisions.append({
            "id": i + 1,
            "title": f"{row.metric.replace('_', ' ').title()} anomaly on {row.date[:10]}",
            "description": f"Recommended: {row.scenario}",
            "status": "approved" if auto else "pending",
            "confidence_score": float(row.score),
            "financial_impact": float(row.financial_impact),
            "requires_approval": not auto,
            "reasoning": f"{row.severity} {row.source} alert; governance action: {row.action}",
            "recommended_scenario": row.scenario,
            "created_at": row.date,
            "category": row.metric,
        })
    return decisions


@lru_cache(maxsize=None)
def segment_counts() -> Dict[str, int]:
    return rfm_summary(customer_rfm())["customers"].astype(int).to_dict()


@lru_cache(maxsize=None)
def rfm_recommendations() -> List[str]:
    """Recommendations stated as facts about the segments, not as promised returns."""
    rfm = customer_rfm()
    summary = rfm_summary(rfm)
    one_time = float((rfm["frequency"] == 1).mean())

    def seg(name):
        row = summary.loc[name]
        return int(row["customers"]), float(row["pct_revenue"])

    lapsing, lapsing_rev = seg("High-Value Lapsing")
    lapsed_days = int(rfm.loc[rfm["segment"] == "High-Value Lapsing", "recency"].min())
    new, new_rev = seg("High-Value New")
    champions, champions_rev = seg("Champions")
    return [
        f"Win back {lapsing:,} high-value customers with no purchase for {lapsed_days}+ days "
        f"({lapsing_rev:.1f}% of revenue).",
        f"Convert {new:,} recent high-value first-time buyers into repeat customers "
        f"({new_rev:.1f}% of revenue).",
        f"Repeat purchasing is rare: {one_time:.1%} of customers bought once; retention is the "
        f"largest lever.",
        f"Protect {champions:,} Champions (repeat, recent, high-value; {champions_rev:.1f}% of revenue).",
    ]
