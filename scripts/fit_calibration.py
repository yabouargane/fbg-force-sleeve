"""Fit the sensitivity matrix K from a CSV recorded on the bench and report metrics.

Input CSV columns (header required), one row per steady-state point:
    Fx_N, Fy_N, Fz_N, dT_C, wl1_pm, wl2_pm, wl3_pm, wl4_pm
Wavelengths are shifts in pm relative to a zero-load, reference-temperature recording.

Usage (from the repository root):
    python scripts/fit_calibration.py calibration.csv --split 0.7
The first fraction of rows (--split) fits K, the rest is held out for the report.
No measured file ships with this repository.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from fbg_sim.calibration import errors, fit_sensitivity  # noqa: E402
from fbg_sim.model import decouple_linear  # noqa: E402

STATE_COLS = ["Fx_N", "Fy_N", "Fz_N", "dT_C"]
WL_COLS = ["wl1_pm", "wl2_pm", "wl3_pm", "wl4_pm"]


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    missing = [c for c in STATE_COLS + WL_COLS if rows and c not in rows[0]]
    if missing:
        raise SystemExit(f"Missing columns: {missing}")
    states = np.array([[float(r[c]) for c in STATE_COLS] for r in rows])
    wl = np.array([[float(r[c]) for c in WL_COLS] for r in rows])
    return states, wl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--split", type=float, default=0.7, help="fraction of rows used for the fit")
    ap.add_argument("--out", default="calibration_result.json")
    args = ap.parse_args()

    states, wl = load(args.csv)
    n_fit = int(len(states) * args.split)
    rng = np.random.default_rng(0)
    order = rng.permutation(len(states))
    fit_idx, test_idx = order[:n_fit], order[n_fit:]

    K = fit_sensitivity(wl[fit_idx], states[fit_idx])
    est = decouple_linear(K, wl[test_idx])
    err = errors(est, states[test_idx])
    result = {
        "K": K.tolist(),
        "condition_number": float(np.linalg.cond(K)),
        "n_fit": int(len(fit_idx)),
        "n_test": int(len(test_idx)),
        "holdout_errors": {k: dict(zip(STATE_COLS, v.tolist())) for k, v in err.items()},
    }
    np.save(os.path.splitext(args.out)[0] + "_K.npy", K)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
