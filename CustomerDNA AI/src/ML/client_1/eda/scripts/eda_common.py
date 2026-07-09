from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


CURRENT_DIR = Path(__file__).resolve().parent
EDA_ROOT = CURRENT_DIR.parent
CLIENT_ML_ROOT = EDA_ROOT.parent
PROJECT_ROOT = CLIENT_ML_ROOT.parents[2]
ML_ARTIFACTS_ROOT = PROJECT_ROOT / "artifacts" / "client_1" / "ml"
EDA_ARTIFACTS_ROOT = ML_ARTIFACTS_ROOT / "eda"
PLOTS_ROOT = EDA_ARTIFACTS_ROOT / "plots"
REPORTS_ROOT = EDA_ARTIFACTS_ROOT / "reports"
MODEL_METADATA_DIR = ML_ARTIFACTS_ROOT / "models" / "model_metadata"


def utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def find_latest_file(directory: Path, pattern: str) -> Path:
    candidates = sorted(
        directory.glob(pattern),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No files found for pattern '{pattern}' in {directory}")
    return candidates[0]


def ensure_use_case_directories(use_case: str) -> dict[str, Path]:
    plot_dir = PLOTS_ROOT / use_case
    report_dir = REPORTS_ROOT
    plot_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    return {
        "plot_dir": plot_dir,
        "report_dir": report_dir,
    }


def apply_plot_style() -> None:
    plt.style.use("ggplot")
    plt.rcParams.update(
        {
            "figure.figsize": (10, 6),
            "axes.titlesize": 14,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "figure.dpi": 130,
        }
    )


def save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
