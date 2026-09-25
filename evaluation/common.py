"""Shared paths and helpers for the evaluation scripts."""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RESULTS = ROOT / "evaluation" / "results"
FIGURES = ROOT / "evaluation" / "figures"
RESULTS.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

SEEDS = [0, 1, 2, 3, 4]


def save_json(name: str, data) -> Path:
    path = RESULTS / name
    path.write_text(json.dumps(data, indent=2, default=float))
    return path


def hardware() -> dict:
    info = {"python": platform.python_version(), "platform": platform.platform(),
            "processor": platform.processor()}
    try:
        import psutil
        info["cpu_count_logical"] = psutil.cpu_count()
        info["cpu_count_physical"] = psutil.cpu_count(logical=False)
        info["ram_gb"] = round(psutil.virtual_memory().total / 2**30, 1)
    except ImportError:
        pass
    return info


def setup_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "serif", "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
        "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "figure.dpi": 150, "savefig.bbox": "tight", "axes.spines.top": False,
        "axes.spines.right": False,
    })
    return plt
