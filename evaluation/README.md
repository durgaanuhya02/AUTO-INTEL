# Evaluation

Every number and figure reported for AutoIntel is produced by these scripts from the Olist data in
`data/`. Run them from this directory:

| Script | Produces | Runtime (i7-1165G7) |
|---|---|---|
| `python run_rfm.py` | `results/dataset_and_rfm.json`, `results/rfm_segments.csv` | ~10 s |
| `python run_anomaly.py` | `results/anomaly.json`, validation grid, per-day scores, `figures/anomaly_detection.*` | ~35 min |
| `python run_forecasting.py` | `results/forecasting.json`, `results/forecasts.csv`, `figures/forecast_revenue.*` | ~9 min |
| `python run_pipeline.py` | `results/pipeline.json`, `results/pipeline_decisions.csv` (latency: run on an idle machine) | ~2 min |

Protocols are documented at the top of each script. In short:

- **Anomaly detection**: real daily revenue, orders, satisfaction and delivery time; 10% of days get
  injected anomalies (the magnitudes of AutoIntel's own injector, plus a mild joint shift); every
  detector judges day *t* only against the 60 days before it; hyperparameters are chosen on
  Jun–Dec 2017 and reported once on Jan–Aug 2018; 5 seeds. `check_equivalence()` asserts the
  evaluated detector matches `backend/services/anomaly_detection.py` exactly.
- **Forecasting**: rolling origin over the last 90 days, 1- and 7-day horizons; SARIMA order chosen by
  AIC on data before the first origin.
- **Pipeline**: the five production agents over Redis pub/sub (fakeredis, so no network time), one
  Olist day per cycle, OpenAI disabled (rule-based analysis).
