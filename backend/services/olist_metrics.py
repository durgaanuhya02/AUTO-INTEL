"""Business metrics derived from the Olist Brazilian e-commerce dataset.

Everything the agents observe and everything the evaluation scripts measure comes from here, so the
paper's numbers and the running system share one definition of each metric.

Daily metrics are causal: each is indexed by the date the underlying event happened, so replaying the
series day by day never reveals information from the future.
  revenue                sum of item prices (R$) of orders purchased that day
  orders                 number of orders purchased that day
  customer_satisfaction  mean review score (1-5) of reviews created that day
  delivery_delay         mean purchase-to-delivery time (days) of orders delivered that day
Orders that were canceled or unavailable are excluded from revenue and orders.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

DATA_DIR = Path(os.environ.get("OLIST_DATA_DIR", Path(__file__).resolve().parents[2] / "data"))

# The dataset is sparse before Feb 2017 and truncated after 22 Aug 2018 (daily orders fall from ~250
# to single digits), so both ends are excluded.
WINDOW_START = pd.Timestamp("2017-02-01")
WINDOW_END = pd.Timestamp("2018-08-22")

METRICS = ["revenue", "orders", "customer_satisfaction", "delivery_delay"]

# Delivery and review activity nearly stops on Sundays; a mean over a handful of events is noise, so
# such days carry the previous day's value forward.
MIN_EVENTS_PER_DAY = 20

_EXCLUDED_STATUSES = {"canceled", "unavailable"}


@lru_cache(maxsize=None)
def load_olist(data_dir: str = str(DATA_DIR)) -> Dict[str, pd.DataFrame]:
    d = Path(data_dir)
    orders = pd.read_csv(
        d / "olist_orders_dataset.csv",
        parse_dates=["order_purchase_timestamp", "order_delivered_customer_date",
                     "order_estimated_delivery_date"],
    )
    return {
        "orders": orders,
        "items": pd.read_csv(d / "olist_order_items_dataset.csv"),
        "reviews": pd.read_csv(d / "olist_order_reviews_dataset.csv",
                               parse_dates=["review_creation_date"]),
        "customers": pd.read_csv(d / "olist_customers_dataset.csv"),
        "payments": pd.read_csv(d / "olist_order_payments_dataset.csv"),
        "products": pd.read_csv(d / "olist_products_dataset.csv"),
    }


def _event_mean(values: pd.Series, index: pd.DatetimeIndex) -> pd.Series:
    """Daily mean of `values` (indexed by event time), forward-filled on days with too few events."""
    daily = values.resample("D").agg(["mean", "count"]).reindex(index)
    mean = daily["mean"].where(daily["count"] >= MIN_EVENTS_PER_DAY)
    return mean.ffill().bfill()


@lru_cache(maxsize=None)
def daily_metrics(data_dir: str = str(DATA_DIR)) -> pd.DataFrame:
    """One row per day in [WINDOW_START, WINDOW_END], columns = METRICS."""
    data = load_olist(data_dir)
    orders = data["orders"]
    index = pd.date_range(WINDOW_START, WINDOW_END, freq="D")

    live = orders[~orders["order_status"].isin(_EXCLUDED_STATUSES)]
    order_value = data["items"].groupby("order_id")["price"].sum()
    live = live.assign(value=live["order_id"].map(order_value).fillna(0.0))
    by_day = live.set_index("order_purchase_timestamp").resample("D")
    revenue = by_day["value"].sum().reindex(index, fill_value=0.0)
    n_orders = by_day["order_id"].count().reindex(index, fill_value=0)

    reviews = data["reviews"].set_index("review_creation_date")["review_score"]

    delivered = orders.dropna(subset=["order_delivered_customer_date"])
    days = (delivered["order_delivered_customer_date"] - delivered["order_purchase_timestamp"]
            ).dt.total_seconds() / 86400
    delivery = pd.Series(days.values, index=delivered["order_delivered_customer_date"]).sort_index()

    frame = pd.DataFrame({
        "revenue": revenue.astype(float),
        "orders": n_orders.astype(float),
        "customer_satisfaction": _event_mean(reviews.sort_index(), index),
        "delivery_delay": _event_mean(delivery, index),
    }, index=index)
    frame.index.name = "date"
    return frame


@lru_cache(maxsize=None)
def dataset_statistics(data_dir: str = str(DATA_DIR)) -> Dict[str, float]:
    data = load_olist(data_dir)
    orders, items = data["orders"], data["items"]
    delivered = orders[orders["order_status"] == "delivered"].dropna(
        subset=["order_delivered_customer_date"])
    delivery_days = (delivered["order_delivered_customer_date"]
                     - delivered["order_purchase_timestamp"]).dt.total_seconds() / 86400
    on_time = delivered["order_delivered_customer_date"] <= delivered["order_estimated_delivery_date"]
    return {
        "orders": int(len(orders)),
        "order_items": int(len(items)),
        "revenue_brl": float(items["price"].sum()),
        "aov_brl": float(items["price"].sum() / items["order_id"].nunique()),
        "unique_customers": int(data["customers"]["customer_unique_id"].nunique()),
        "products": int(data["products"]["product_id"].nunique()),
        "categories": int(data["products"]["product_category_name"].nunique()),
        "states": int(data["customers"]["customer_state"].nunique()),
        "payment_types": int(data["payments"]["payment_type"].nunique()),
        "mean_review_score": float(data["reviews"]["review_score"].mean()),
        "on_time_rate": float(on_time.mean()),
        "mean_delivery_days": float(delivery_days.mean()),
        "first_purchase": str(orders["order_purchase_timestamp"].min().date()),
        "last_purchase": str(orders["order_purchase_timestamp"].max().date()),
    }


# --------------------------------------------------------------------------------------------------
# RFM
# --------------------------------------------------------------------------------------------------
# 96.9% of Olist customers ordered exactly once, so frequency quintiles are degenerate. Recency and
# monetary value are scored in quintiles (5 = best); frequency is binary (repeat vs. one-time buyer).
# Segments are checked in order; the first match wins.
RFM_SEGMENTS = [
    ("Champions", lambda r, f, m: f & (r >= 4) & (m >= 4)),
    ("Loyal", lambda r, f, m: f & (r >= 3)),
    ("Lapsed Repeat", lambda r, f, m: f),
    ("High-Value New", lambda r, f, m: (r >= 4) & (m >= 4)),
    ("Low-Value New", lambda r, f, m: r >= 4),
    ("High-Value Lapsing", lambda r, f, m: (r <= 2) & (m >= 4)),
    ("Hibernating", lambda r, f, m: (r <= 2) & (m <= 2)),
    ("Needs Attention", lambda r, f, m: np.ones_like(r, dtype=bool)),
]


@lru_cache(maxsize=None)
def customer_rfm(data_dir: str = str(DATA_DIR)) -> pd.DataFrame:
    """Per-customer recency (days), frequency (orders), monetary (R$), scores and segment."""
    data = load_olist(data_dir)
    orders = data["orders"][~data["orders"]["order_status"].isin(_EXCLUDED_STATUSES)]
    orders = orders.merge(data["customers"][["customer_id", "customer_unique_id"]], on="customer_id")
    order_value = data["items"].groupby("order_id")["price"].sum()
    orders = orders.assign(value=orders["order_id"].map(order_value).fillna(0.0))

    snapshot = orders["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    rfm = orders.groupby("customer_unique_id").agg(
        last_purchase=("order_purchase_timestamp", "max"),
        frequency=("order_id", "nunique"),
        monetary=("value", "sum"),
    )
    rfm["recency"] = (snapshot - rfm.pop("last_purchase")).dt.days
    # rank() breaks ties so qcut always gets 5 equal-sized bins.
    rfm["R"] = pd.qcut(rfm["recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["M"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["repeat"] = rfm["frequency"] > 1

    r, f, m = rfm["R"].to_numpy(), rfm["repeat"].to_numpy(), rfm["M"].to_numpy()
    segment = np.full(len(rfm), "", dtype=object)
    for name, rule in RFM_SEGMENTS:
        hit = (segment == "") & rule(r, f, m)
        segment[hit] = name
    rfm["segment"] = segment
    return rfm


def rfm_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    total_customers, total_revenue = len(rfm), rfm["monetary"].sum()
    order = [name for name, _ in RFM_SEGMENTS]
    summary = rfm.groupby("segment").agg(
        customers=("monetary", "size"),
        revenue=("monetary", "sum"),
        mean_monetary=("monetary", "mean"),
        mean_recency=("recency", "mean"),
        mean_frequency=("frequency", "mean"),
    ).reindex(order).dropna(how="all")
    summary["pct_customers"] = 100 * summary["customers"] / total_customers
    summary["pct_revenue"] = 100 * summary["revenue"] / total_revenue
    return summary
