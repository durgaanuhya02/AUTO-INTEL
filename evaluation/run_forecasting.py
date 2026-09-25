"""Daily revenue and order-volume forecasting on Olist, rolling-origin evaluation.

Protocol
  * Series: daily revenue (R$) and orders, 2017-02-01 .. 2018-08-22.
  * Test origins: every day of the last TEST_DAYS days. At each origin the models see only the past
    and forecast 1 and 7 days ahead.
  * (S)ARIMA order is selected once by AIC on the data before the first test origin, then refitted
    (fixed order) at every origin. Linear regression uses a trailing LR_WINDOW-day window.
  * The ensemble is the unweighted mean of SARIMA and LR (nothing tuned on the test period).

Run:  python evaluation/run_forecasting.py
"""
from __future__ import annotations

import itertools
import warnings

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.statespace.sarimax import SARIMAX

from common import FIGURES, RESULTS, save_json, setup_matplotlib
from backend.services.olist_metrics import daily_metrics

TEST_DAYS = 90
HORIZONS = [1, 7]
LR_WINDOW = 120
SEASON = 7

ORDER_GRID = list(itertools.product([0, 1, 2], [0, 1], [0, 1, 2]))
SEASONAL_GRID = [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 1, 1)]

MODELS = ["naive", "seasonal_naive", "linear_regression", "sarima", "ensemble"]
LABELS = {"naive": "Naive (last value)", "seasonal_naive": "Seasonal naive (t-7)",
          "linear_regression": "Linear regression", "sarima": "SARIMA (AIC-selected)",
          "ensemble": "SARIMA + LR ensemble"}


def select_order(train: pd.Series):
    best = None
    for order, seasonal in itertools.product(ORDER_GRID, SEASONAL_GRID):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fit = SARIMAX(train.to_numpy(), order=order, seasonal_order=(*seasonal, SEASON),
                              trend="c" if order[1] == 0 else "n").fit(disp=False)
        except Exception:
            continue
        if best is None or fit.aic < best[0]:
            best = (fit.aic, order, seasonal)
    return best


def lr_forecast(history: pd.Series, steps: int) -> np.ndarray:
    window = history.iloc[-LR_WINDOW:]
    t = np.arange(len(window))

    def design(t_values, dates):
        dow = np.eye(7)[dates.dayofweek][:, 1:]
        return np.column_stack([t_values, dow])

    model = LinearRegression().fit(design(t, window.index), window.to_numpy())
    future = pd.date_range(window.index[-1] + pd.Timedelta(days=1), periods=steps, freq="D")
    return model.predict(design(np.arange(len(window), len(window) + steps), future))


def forecast_origin(series: pd.Series, origin: int, order, seasonal) -> dict:
    """Forecasts made at the end of day origin-1 for days origin .. origin+max(H)-1."""
    history = series.iloc[:origin]
    steps = max(HORIZONS)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = SARIMAX(history.to_numpy(), order=order, seasonal_order=(*seasonal, SEASON),
                      trend="c" if order[1] == 0 else "n").fit(disp=False)
    sarima = fit.forecast(steps)
    lr = lr_forecast(history, steps)
    last = history.iloc[-1]
    seasonal_naive = np.array([history.iloc[-SEASON + (h % SEASON)] for h in range(steps)])
    return {
        "naive": np.full(steps, last),
        "seasonal_naive": seasonal_naive,
        "linear_regression": lr,
        "sarima": sarima,
        "ensemble": (sarima + lr) / 2,
    }


def evaluate(series: pd.Series, name: str):
    first_origin = len(series) - TEST_DAYS
    aic, order, seasonal = select_order(series.iloc[:first_origin])
    origins = range(first_origin, len(series))
    forecasts = Parallel(n_jobs=-1)(delayed(forecast_origin)(series, o, order, seasonal)
                                    for o in origins)

    rows = []
    for o, fc in zip(origins, forecasts):
        for h in HORIZONS:
            target = o + h - 1
            if target >= len(series):
                continue
            actual = series.iloc[target]
            for model in MODELS:
                rows.append({"series": name, "origin": series.index[o], "date": series.index[target],
                             "h": h, "model": model, "actual": actual, "forecast": fc[model][h - 1]})
    df = pd.DataFrame(rows)
    df["abs_err"] = (df["actual"] - df["forecast"]).abs()
    df["ape"] = 100 * df["abs_err"] / df["actual"].abs()
    df["sq_err"] = (df["actual"] - df["forecast"]) ** 2
    metrics = df.groupby(["h", "model"]).agg(mape=("ape", "mean"), mae=("abs_err", "mean"),
                                              rmse=("sq_err", lambda s: float(np.sqrt(s.mean()))),
                                              n=("ape", "size"))
    return df, metrics, {"aic": aic, "order": order, "seasonal_order": (*seasonal, SEASON)}


def plot(df: pd.DataFrame):
    plt = setup_matplotlib()
    d = df[(df["series"] == "revenue") & (df["h"] == 1)]
    pivot = d.pivot(index="date", columns="model", values="forecast")
    actual = d.drop_duplicates("date").set_index("date")["actual"]
    fig, ax = plt.subplots(figsize=(3.4, 1.8))
    ax.plot(actual.index, actual / 1000, color="black", lw=1.1, label="Actual")
    ax.plot(pivot.index, pivot["sarima"] / 1000, color="#2F5D8C", lw=0.9, label="SARIMA")
    ax.plot(pivot.index, pivot["naive"] / 1000, color="#C44E52", lw=0.7, ls="--",
            label="Naive")
    ax.set_ylabel(r"Revenue (R\$ k/day)")
    ax.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    ax.xaxis.set_major_formatter(__import__("matplotlib.dates", fromlist=["x"]).DateFormatter("%d %b"))
    for ext in ("pdf", "png"):
        fig.savefig(FIGURES / f"forecast_revenue.{ext}")


def main():
    frame = daily_metrics()
    all_rows, summary = [], {"protocol": {"test_days": TEST_DAYS, "horizons": HORIZONS,
                                          "lr_window": LR_WINDOW,
                                          "test_start": str(frame.index[-TEST_DAYS].date()),
                                          "test_end": str(frame.index[-1].date())}}
    for name in ["revenue", "orders"]:
        df, metrics, selection = evaluate(frame[name], name)
        all_rows.append(df)
        summary[name] = {"selection": selection,
                         "metrics": {f"h{h}": {m: metrics.loc[(h, m)].to_dict() for m in MODELS}
                                     for h in HORIZONS}}
        print(f"\n{name}: order={selection['order']} seasonal={selection['seasonal_order']}")
        print(metrics.round(2).to_string())
    df = pd.concat(all_rows)
    df.to_csv(RESULTS / "forecasts.csv", index=False)
    save_json("forecasting.json", summary)
    plot(df)


if __name__ == "__main__":
    import sys
    if "--plot-only" in sys.argv:
        plot(pd.read_csv(RESULTS / "forecasts.csv", parse_dates=["date", "origin"]))
    else:
        main()
