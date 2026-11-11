"""Forward and inverse model of a four-grating FBG force sleeve.

SIMULATION ONLY. Every sensitivity value below is an illustrative assumption,
not a measurement. Replace the matrix with the one you obtain by calibration
(see docs/calibration_procedure.md).

State vector x = [Fx, Fy, Fz, dT]  (N, N, N, degrees C)
Measurement    d_lambda = wavelength shifts of the 4 gratings (pm)

Proposed layout (the one simulated):
  - gratings 1-3 bonded on a flexure at 120 degree spacing: they see lateral
    bending (Fx, Fy), axial load (Fz) and temperature;
  - grating 4 is strain-isolated and sees temperature only (reference).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

STATE_LABELS = ("Fx", "Fy", "Fz", "dT")


@dataclass(frozen=True)
class SleeveParams:
    """Illustrative sensitivities. ASSUMED values, to be replaced by calibration."""

    # Defaults: a bare 8 mm tube with fibers 3.5 mm from the axis
    # (about 13 microstrain per N lateral, under 0.5 pm per N axial).
    k_lateral: float = 15.7  # pm per N, lateral bending on a strained grating
    k_axial: float = 0.5  # pm per N, axial load on a strained grating (upper bound)
    # Thermal sensitivities. A bare silica FBG reads 10 to 13 pm per degree C near 1550 nm (online sources).
    # A grating bonded to steel also sees the substrate expansion: 1.2 pm/microstrain x (16 to 17 ppm/K
    # minus 0.55 ppm/K) adds about 19 pm/C, giving roughly 28 to 33 pm/C. That is a physical ESTIMATE,
    # no direct measurement was found. The reference grating is free, so it keeps the bare value.
    k_temp: float = 30.0  # pm per degree C, strained gratings bonded to the steel shaft (estimate)
    k_temp_ref: float = 11.5  # pm per degree C, strain-free reference grating (bare fiber)
    angles_deg: tuple = (0.0, 120.0, 240.0)
    force_full_scale_n: float = 5.0


# Scenarios used by scripts/run_simulation.py. All are ASSUMPTIONS to be replaced by calibration.
# Beam-theory sensitivities for a hollow steel tube: strain = F * L * c / (E * I) laterally and
# F / (E * A) axially, with E = 196 GPa and 1.2 pm per microstrain.
#   5 mm tube, wall 0.5 mm, lever arm L = 100 mm (wall and L are ASSUMED): 70.4 microstrain/N lateral
#   = 84.5 pm/N, 0.72 microstrain/N axial = 0.87 pm/N.
SCENARIOS = {
    # Baseline: 8 mm tube, fibers 3.5 mm from the axis (the SleeveParams defaults).
    "tube8_baseline": {"params": SleeveParams(), "sigma_pm": 1.0},
    # 5 mm shaft (most common manual size), assumed wall and lever arm, loaned interrogator.
    "tube5_beam_assumed": {"params": SleeveParams(k_lateral=84.5, k_axial=0.87), "sigma_pm": 1.0},
    # Same 5 mm shaft read with a low-cost edge-filter interrogator (2.4 to 3.6 pm reported online).
    "tube5_lowcost_readout": {"params": SleeveParams(k_lateral=84.5, k_axial=0.87), "sigma_pm": 3.0},
    # Hypothetical flexure that multiplies every strain sensitivity by 10 (arbitrary factor, not a
    # design result), with the low-cost readout.
    "flexure_x10_assumed": {"params": SleeveParams(k_lateral=845.0, k_axial=8.7), "sigma_pm": 3.0},
}


def sensitivity_matrix(p: SleeveParams = SleeveParams()) -> np.ndarray:
    """4x4 matrix K with d_lambda = K @ [Fx, Fy, Fz, dT]."""
    rows = []
    for a in np.deg2rad(p.angles_deg):
        rows.append([p.k_lateral * np.cos(a), p.k_lateral * np.sin(a), p.k_axial, p.k_temp])
    rows.append([0.0, 0.0, 0.0, p.k_temp_ref])  # reference grating, temperature only, free fiber
    return np.array(rows, dtype=float)


def symmetric_matrix(p: SleeveParams = SleeveParams()) -> np.ndarray:
    """Four strained gratings at 0/90/180/270 degrees and no reference grating.

    Fz and dT then move all four gratings by the same amount, so the two columns
    are parallel and the matrix is singular. Used to show why a reference
    grating (or another source of independent information) is required.
    """
    rows = []
    for a in np.deg2rad((0.0, 90.0, 180.0, 270.0)):
        rows.append([p.k_lateral * np.cos(a), p.k_lateral * np.sin(a), p.k_axial, p.k_temp])
    return np.array(rows, dtype=float)


def forward(K: np.ndarray, x: np.ndarray, beta: float = 0.0, p: SleeveParams = SleeveParams()) -> np.ndarray:
    """Wavelength shifts for states x of shape (n, 4) or (4,).

    beta adds an ASSUMED odd quadratic crosstalk on the force part, equal to
    beta times the full-scale lateral response at full scale.
    """
    x = np.asarray(x, dtype=float)
    single = x.ndim == 1
    x2 = np.atleast_2d(x)
    dl = x2 @ K.T
    if beta:
        lin_force = x2[:, :3] @ K[:, :3].T
        ref = p.k_lateral * p.force_full_scale_n
        dl = dl + beta * np.sign(lin_force) * lin_force**2 / ref
    return dl[0] if single else dl


def decouple_linear(K: np.ndarray, d_lambda: np.ndarray, max_cond: float = 1e3) -> np.ndarray:
    """Invert K. Refuses an ill-conditioned matrix."""
    cond = np.linalg.cond(K)
    if cond > max_cond:
        raise ValueError(f"Calibration matrix is ill-conditioned (cond = {cond:.3g})")
    d = np.asarray(d_lambda, dtype=float)
    single = d.ndim == 1
    d2 = np.atleast_2d(d)
    x = np.linalg.solve(K, d2.T).T
    return x[0] if single else x


def naive_force_estimate(K: np.ndarray, d_lambda: np.ndarray) -> np.ndarray:
    """Force from the three strained gratings while ignoring temperature.

    This is what a sensor does when it does not separate force from heat.
    Returns shape (n, 3).
    """
    d2 = np.atleast_2d(np.asarray(d_lambda, dtype=float))
    return np.linalg.solve(K[:3, :3], d2[:, :3].T).T


def noise_floor(K: np.ndarray, sigma_pm: float) -> np.ndarray:
    """Output standard deviation per state for white wavelength noise sigma_pm (pm)."""
    Kinv = np.linalg.inv(K)
    return sigma_pm * np.sqrt((Kinv**2).sum(axis=1))


class PolyDecoupler:
    """Second-order polynomial inverse model, fitted on calibration data."""

    def __init__(self, scale_pm: float = 100.0):
        self.scale_pm = scale_pm
        self.W: np.ndarray | None = None

    def _features(self, d_lambda: np.ndarray) -> np.ndarray:
        z = np.atleast_2d(d_lambda) / self.scale_pm
        iu = np.triu_indices(z.shape[1])
        quad = (z[:, :, None] * z[:, None, :])[:, iu[0], iu[1]]
        return np.hstack([np.ones((z.shape[0], 1)), z, quad])

    def fit(self, d_lambda: np.ndarray, x: np.ndarray) -> "PolyDecoupler":
        F = self._features(d_lambda)
        self.W = np.linalg.lstsq(F, np.asarray(x, dtype=float), rcond=None)[0]
        return self

    def predict(self, d_lambda: np.ndarray) -> np.ndarray:
        if self.W is None:
            raise RuntimeError("fit() first")
        return self._features(d_lambda) @ self.W
