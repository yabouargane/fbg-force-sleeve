"""Calibration fit and performance metrics for real bench data.

Use these on measured data. They are tested here only on synthetic data.

Conventions
-----------
states      (n, 4): reference values [Fx, Fy, Fz, dT] in N, N, N, degrees C
d_lambda    (n, 4): wavelength shifts of the four gratings in pm, relative to a zero-load,
            reference-temperature recording
"""
from __future__ import annotations

import numpy as np


def fit_sensitivity(d_lambda: np.ndarray, states: np.ndarray) -> np.ndarray:
    """Least-squares estimate of K in d_lambda = K @ state."""
    d = np.asarray(d_lambda, dtype=float)
    x = np.asarray(states, dtype=float)
    if d.shape != x.shape or d.shape[1] != 4:
        raise ValueError("d_lambda and states must both have shape (n, 4)")
    if np.linalg.matrix_rank(x) < 4:
        raise ValueError("The states do not excite all four unknowns (rank < 4). Add loads or temperatures.")
    A, *_ = np.linalg.lstsq(x, d, rcond=None)  # x @ A = d  ->  K = A.T
    return A.T


def errors(est: np.ndarray, truth: np.ndarray) -> dict:
    """Mean absolute error, RMSE and maximum absolute error, per column."""
    e = np.asarray(est, dtype=float) - np.asarray(truth, dtype=float)
    return {
        "mae": np.mean(np.abs(e), axis=0),
        "rmse": np.sqrt(np.mean(e**2, axis=0)),
        "max_abs": np.max(np.abs(e), axis=0),
    }


def linearity_error_percent(truth: np.ndarray, est: np.ndarray, full_scale: float) -> float:
    """Maximum deviation from the best-fit line, as a percentage of full scale (one axis)."""
    t = np.asarray(truth, dtype=float)
    y = np.asarray(est, dtype=float)
    slope, intercept = np.polyfit(t, y, 1)
    return float(np.max(np.abs(y - (slope * t + intercept))) / full_scale * 100.0)


def hysteresis_percent(est_up: np.ndarray, est_down: np.ndarray, full_scale: float) -> float:
    """Largest difference between loading and unloading readings at the same load levels,
    as a percentage of full scale. est_up and est_down must be taken at the same levels."""
    up = np.asarray(est_up, dtype=float)
    down = np.asarray(est_down, dtype=float)
    if up.shape != down.shape:
        raise ValueError("est_up and est_down must have the same shape")
    return float(np.max(np.abs(up - down)) / full_scale * 100.0)


def noise_floor_from_rest(est_at_rest: np.ndarray) -> np.ndarray:
    """One-sigma noise per column from a recording at constant load and temperature."""
    return np.std(np.asarray(est_at_rest, dtype=float), axis=0, ddof=1)


def drift_per_hour(time_s: np.ndarray, est_at_rest: np.ndarray) -> np.ndarray:
    """Linear drift per hour for each column of a rest recording."""
    t = np.asarray(time_s, dtype=float)
    y = np.asarray(est_at_rest, dtype=float)
    if y.ndim == 1:
        y = y[:, None]
    return np.array([np.polyfit(t, y[:, i], 1)[0] * 3600.0 for i in range(y.shape[1])])
