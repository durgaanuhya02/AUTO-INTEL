"""Anomaly detection on real Olist daily metrics with injected ground-truth anomalies.

Protocol
  * Series: daily revenue, orders, customer_satisfaction, delivery_delay (backend/services/olist_metrics).
  * Every detector runs causally: day t is judged against the WINDOW days before it only.
  * Injected days (10% of each evaluation split) are the positives. Injected values stay in the
    series, so later windows contain past anomalies, as they would in operation.
  * Two feature settings are compared on identical days: raw daily values, and weekday-adjusted
    values (each day divided by the median of the same weekday over the previous 4 weeks).
  * Hyperparameters are selected on the validation split (2017) by F1; the test split (2018) is
    reported once with those settings. 5 seeds vary the injection and the forest's random_state.

Run:  python evaluation/run_anomaly.py
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score

from common import FIGURES, RESULTS, SEEDS, save_json, setup_matplotlib
from backend.services.anomaly_detection import MultivariateAnomalyDetector, seasonal_ratio
from backend.services.olist_metrics import METRICS, daily_metrics

WINDOW = 60
INJECTION_RATE = 0.10
VAL = ("2017-06-01", "2017-12-31")   # late enough for the weekday baseline + window
TEST = ("2018-01-01", "2018-08-22")
N_ESTIMATORS = 100
SEASONAL_PERIOD, SEASONAL_CYCLES = 7, 4
FEATURES = ["raw", "weekday"]

CONTAMINATIONS = [0.05, 0.10, 0.15]
Z_THRESHOLDS = [2.0, 2.5, 3.0, 3.5]

REV, ORD, SAT, DEL = range(4)
ANOMALY_TYPES = ["revenue_spike", "order_drop", "satisfaction_drop", "delivery_delay", "joint_shift"]


def inject(values: np.ndarray, days: np.ndarray, rng: np.random.Generator):
    """Multiply selected days in place; returns the anomaly type of each injected day.

    Single-metric magnitudes are those of AutoIntel's built-in anomaly injector.
    """
    types = rng.choice(ANOMALY_TYPES, size=len(days))
    for day, kind in zip(days, types):
        if kind == "revenue_spike":
            values[day, REV] *= rng.uniform(1.3, 1.8)
        elif kind == "order_drop":            # fewer orders means proportionally less revenue
            f = rng.uniform(0.6, 0.8)
            values[day, ORD] *= f
            values[day, REV] *= f
        elif kind == "satisfaction_drop":
            values[day, SAT] *= rng.uniform(0.85, 0.92)
        elif kind == "delivery_delay":
            values[day, DEL] *= rng.uniform(1.3, 1.8)
        elif kind == "joint_shift":           # mild on every metric, at once
            f = rng.uniform(0.80, 0.90)
            values[day, REV] *= f
            values[day, ORD] *= f
            values[day, SAT] *= rng.uniform(0.93, 0.97)
            values[day, DEL] *= rng.uniform(1.10, 1.20)
    return types


def forest_scores(train: np.ndarray, current: np.ndarray, seed: int):
    """score_samples of the window and of the current point.

    sklearn sets offset_ to the `contamination` percentile of the training scores, so one fit gives
    the decision for every contamination value (checked against the production class in main()).
    """
    model = IsolationForest(n_estimators=N_ESTIMATORS, random_state=seed).fit(train)
    return model.score_samples(train), float(model.score_samples(current.reshape(1, -1))[0])


def static_thresholds(frame: pd.DataFrame) -> dict:
    median = frame[METRICS].median()
    return {"rev_min": 0.25 * median["revenue"], "rev_max": 5 * median["revenue"],
            "ord_min": 0.25 * median["orders"], "ord_max": 5 * median["orders"],
            "del_max": 2 * median["delivery_delay"]}


def features(values: np.ndarray, feature: str) -> np.ndarray:
    if feature == "raw":
        return values
    return seasonal_ratio(values, SEASONAL_PERIOD, SEASONAL_CYCLES)


def score_day(values: np.ndarray, raw: np.ndarray, t: int, seed: int, thresholds: dict) -> dict:
    """`values` feed the statistical detectors; static thresholds always see the raw values."""
    window = values[t - WINDOW:t]
    x = values[t]
    r = raw[t]
    mean, std = window.mean(axis=0), window.std(axis=0)
    z = np.abs(np.divide(x - mean, std, out=np.zeros_like(mean), where=std > 0))

    multi_train, multi_x = forest_scores(window, x, seed)
    uni = [forest_scores(window[:, [j]], x[[j]], seed) for j in range(len(METRICS))]

    static = (r[REV] < thresholds["rev_min"] or r[REV] > thresholds["rev_max"]
              or r[ORD] < thresholds["ord_min"] or r[ORD] > thresholds["ord_max"]
              or r[SAT] < 3.0 or r[DEL] > thresholds["del_max"])

    out = {"static": bool(static), "max_z": float(z.max())}
    for c in CONTAMINATIONS:
        q = 100 * c
        out[f"multi_{c}"] = multi_x < np.percentile(multi_train, q)
        out[f"multi_margin_{c}"] = float(np.percentile(multi_train, q) - multi_x)  # >0 anomalous
        uni_margins = [np.percentile(tr, q) - cur for tr, cur in uni]
        out[f"uni_{c}"] = max(uni_margins) > 0
        out[f"uni_margin_{c}"] = float(max(uni_margins))
    return out


def run_seed(seed: int, frame: pd.DataFrame, feature: str) -> pd.DataFrame:
    # The injection depends on the seed only, so both feature settings see the same anomalies.
    rng = np.random.default_rng(seed)
    values = frame[METRICS].to_numpy(dtype=float).copy()
    thresholds = static_thresholds(frame)

    rows = []
    labels = np.zeros(len(frame), dtype=bool)
    kinds = np.full(len(frame), "", dtype=object)
    splits = np.full(len(frame), "", dtype=object)
    for name, (start, end) in {"val": VAL, "test": TEST}.items():
        idx = np.flatnonzero((frame.index >= start) & (frame.index <= end))
        splits[idx] = name
        chosen = np.sort(rng.choice(idx, size=int(round(INJECTION_RATE * len(idx))), replace=False))
        kinds[chosen] = inject(values, chosen, rng)
        labels[chosen] = True

    feats = features(values, feature)
    for t in np.flatnonzero(splits != ""):
        row = score_day(feats, values, t, seed, thresholds)
        row.update(seed=seed, feature=feature, date=frame.index[t], split=splits[t],
                   label=labels[t], kind=kinds[t])
        rows.append(row)
    return pd.DataFrame(rows)


def detector_flags(df: pd.DataFrame, detector: str, params: dict) -> np.ndarray:
    if detector == "static":
        return df["static"].to_numpy()
    if detector == "zscore":
        return (df["max_z"] > params["k"]).to_numpy()
    if detector == "uni_if":
        return df[f"uni_{params['c']}"].to_numpy()
    if detector == "multi_if":
        return df[f"multi_{params['c']}"].to_numpy()
    if detector == "hybrid":
        return (df[f"multi_{params['c']}"] | (df["max_z"] > params["k"])).to_numpy()
    raise ValueError(detector)


def continuous_score(df: pd.DataFrame, detector: str, params: dict):
    if detector == "zscore":
        return df["max_z"].to_numpy()
    if detector == "uni_if":
        return df[f"uni_margin_{params['c']}"].to_numpy()
    if detector == "multi_if":
        return df[f"multi_margin_{params['c']}"].to_numpy()
    return None


def prf(labels: np.ndarray, flags: np.ndarray) -> dict:
    tp = int((flags & labels).sum())
    fp = int((flags & ~labels).sum())
    fn = int((~flags & labels).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


GRIDS = {
    "static": [{}],
    "zscore": [{"k": k} for k in Z_THRESHOLDS],
    "uni_if": [{"c": c} for c in CONTAMINATIONS],
    "multi_if": [{"c": c} for c in CONTAMINATIONS],
    "hybrid": [{"c": c, "k": k} for c, k in itertools.product(CONTAMINATIONS, Z_THRESHOLDS)],
}


def mean_metrics(df: pd.DataFrame, detector: str, params: dict) -> dict:
    per_seed = [prf(g["label"].to_numpy(), detector_flags(g, detector, params))
                for _, g in df.groupby("seed")]
    return {k: float(np.mean([m[k] for m in per_seed])) for k in per_seed[0]} | {
        f"{k}_std": float(np.std([m[k] for m in per_seed])) for k in ("precision", "recall", "f1")}


def check_equivalence(frame: pd.DataFrame):
    """The fit-once shortcut must agree with the class the Observer runs."""
    values = frame[METRICS].to_numpy(dtype=float)
    for feature in FEATURES:
        feats = features(values, feature)
        seasonal = SEASONAL_PERIOD if feature == "weekday" else None
        det = MultivariateAnomalyDetector(METRICS, contamination=0.1, random_state=0,
                                          seasonal_period=seasonal, seasonal_cycles=SEASONAL_CYCLES)
        for t in (150, 250, 400, 500):
            d = det.detect(values[t - WINDOW - det.lookback:t], values[t])
            tr, cur = forest_scores(feats[t - WINDOW:t], feats[t], seed=0)
            assert d.is_anomaly == (cur < np.percentile(tr, 10)), f"mismatch {feature} day {t}"
            assert abs(d.score - (cur - np.percentile(tr, 10))) < 1e-9, f"score {feature} day {t}"


def real_event_check(frame: pd.DataFrame, chosen: dict) -> dict:
    """Which detectors flag known real events in the clean (uninjected) series."""
    values = frame[METRICS].to_numpy(dtype=float)
    thresholds = static_thresholds(frame)
    events = {"Black Friday 2017-11-24": "2017-11-24"}
    out = {}
    for name, day in events.items():
        t = frame.index.get_loc(pd.Timestamp(day))
        out[name] = {}
        for (feature, det), params in chosen.items():
            row = pd.DataFrame([score_day(features(values, feature), values, t, 0, thresholds)])
            out[name][f"{feature}/{det}"] = bool(detector_flags(row, det, params)[0])
    return out


def plot(test_results: dict):
    plt = setup_matplotlib()
    detectors = list(GRIDS)
    x = np.arange(len(detectors))
    width = 0.38
    fig, ax = plt.subplots(figsize=(3.4, 2.0))
    for i, (feature, color, label) in enumerate([("raw", "#9DB4D3", "Raw values"),
                                                 ("weekday", "#2F5D8C", "Weekday-adjusted")]):
        means = [test_results[f"{feature}/{d}"]["f1"] for d in detectors]
        stds = [test_results[f"{feature}/{d}"]["f1_std"] for d in detectors]
        ax.bar(x + (i - 0.5) * width, means, width, yerr=stds, capsize=1.5, color=color,
               label=label, error_kw={"lw": 0.6})
    ax.set_xticks(x)
    ax.set_xticklabels(["Static", "z-score", "Uni. IF", "Multi. IF", "Hybrid"])
    ax.set_ylim(0, 1)
    ax.set_ylabel(r"Test F$_1$ (mean $\pm$ sd, 5 seeds)")
    ax.legend(frameon=False, loc="upper left")
    for ext in ("pdf", "png"):
        fig.savefig(FIGURES / f"anomaly_detection.{ext}")


def main():
    frame = daily_metrics()
    check_equivalence(frame)

    jobs = [(s, f) for s in SEEDS for f in FEATURES]
    runs = Parallel(n_jobs=-1)(delayed(run_seed)(s, frame, f) for s, f in jobs)
    df = pd.concat(runs, ignore_index=True)
    df.to_csv(RESULTS / "anomaly_scores.csv", index=False)

    grid_rows, chosen = [], {}
    for feature in FEATURES:
        sub = df[df["feature"] == feature]
        val = sub[sub["split"] == "val"]
        for detector, grid in GRIDS.items():
            if detector == "static" and feature != "raw":
                continue   # thresholds are on raw values; identical under both settings
            best = None
            for params in grid:
                m = mean_metrics(val, detector, params)
                grid_rows.append({"feature": feature, "detector": detector, **params, **m})
                if best is None or m["f1"] > best[1]["f1"]:
                    best = (params, m)
            chosen[(feature, detector)] = best[0]
    pd.DataFrame(grid_rows).to_csv(RESULTS / "anomaly_validation_grid.csv", index=False)

    test_results, per_type, auc = {}, {}, {}
    for (feature, detector), params in chosen.items():
        key = f"{feature}/{detector}"
        test = df[(df["feature"] == feature) & (df["split"] == "test")]
        test_results[key] = mean_metrics(test, detector, params)
        flags = detector_flags(test, detector, params)
        per_type[key] = {kind: float(flags[(test["kind"] == kind).to_numpy()].mean())
                         for kind in ANOMALY_TYPES}
        if continuous_score(test, detector, params) is not None:
            aucs = [roc_auc_score(g["label"], continuous_score(g, detector, params))
                    for _, g in test.groupby("seed")]
            auc[key] = {"mean": float(np.mean(aucs)), "std": float(np.std(aucs))}
    test_results["weekday/static"] = test_results["raw/static"]

    raw = df[df["feature"] == "raw"]
    summary = {
        "protocol": {"window_days": WINDOW, "injection_rate": INJECTION_RATE, "val": VAL,
                     "test": TEST, "seeds": SEEDS, "n_estimators": N_ESTIMATORS,
                     "seasonal": {"period": SEASONAL_PERIOD, "cycles": SEASONAL_CYCLES},
                     "val_days": int(raw[raw["split"] == "val"].groupby("seed").size().iloc[0]),
                     "test_days": int(raw[raw["split"] == "test"].groupby("seed").size().iloc[0]),
                     "test_positives_per_seed":
                         int(raw[raw["split"] == "test"].groupby("seed")["label"].sum().iloc[0])},
        "selected_on_validation": {f"{f}/{d}": p for (f, d), p in chosen.items()},
        "test": test_results,
        "test_recall_by_type": per_type,
        "test_roc_auc": auc,
        "real_events_clean_series": real_event_check(frame, chosen),
    }
    save_json("anomaly.json", summary)
    plot(test_results)

    print("Selected on validation:", summary["selected_on_validation"])
    for key, m in test_results.items():
        print(f"{key:20s} P={m['precision']:.3f}+-{m['precision_std']:.3f} "
              f"R={m['recall']:.3f}+-{m['recall_std']:.3f} F1={m['f1']:.3f}+-{m['f1_std']:.3f}")
    print("Recall by type:\n", pd.DataFrame(per_type).round(2).to_string())
    print("ROC-AUC:", auc)
    print("Real events:", summary["real_events_clean_series"])


if __name__ == "__main__":
    main()
