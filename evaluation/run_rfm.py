"""Dataset statistics and RFM segmentation of all Olist customers.

Run:  python evaluation/run_rfm.py
"""
from __future__ import annotations

from common import RESULTS, save_json
from backend.services.olist_metrics import (RFM_SEGMENTS, customer_rfm, daily_metrics,
                                            dataset_statistics, rfm_summary)


def main():
    stats = dataset_statistics()
    frame = daily_metrics()
    stats["evaluation_window"] = [str(frame.index[0].date()), str(frame.index[-1].date())]
    stats["evaluation_days"] = len(frame)
    stats["daily_mean"] = frame.mean().to_dict()
    stats["daily_std"] = frame.std().to_dict()

    rfm = customer_rfm()
    summary = rfm_summary(rfm)
    summary.to_csv(RESULTS / "rfm_segments.csv")
    freq = rfm["frequency"].value_counts().sort_index()
    save_json("dataset_and_rfm.json", {
        "dataset": stats,
        "rfm": {
            "customers_with_valid_orders": int(len(rfm)),
            "one_time_buyer_share": float((rfm["frequency"] == 1).mean()),
            "frequency_distribution": {int(k): int(v) for k, v in freq.items()},
            "segment_rules_in_priority_order": [name for name, _ in RFM_SEGMENTS],
            "segments": summary.reset_index().to_dict(orient="records"),
        },
    })
    print(stats)
    print(summary.round(1).to_string())


if __name__ == "__main__":
    main()
