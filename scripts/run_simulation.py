"""Run the simulation experiments for each scenario and write figures and results.json.

SIMULATION ONLY. Sensitivities, noise and nonlinearity are ASSUMED values (see
SCENARIOS in src/fbg_sim/model.py). These results show how the decoupling method
behaves inside a model. They are not measurements and not a validation of any hardware.

Note on method: signals are generated with the same matrix K that is used to invert
them (except in the calibration-error experiment, where the inverse uses a perturbed K).
The reconstruction is therefore exact apart from the added noise.

Usage (from the repository root):
    python scripts/run_simulation.py
"""
from __future__ import annotations

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

matplotlib.rcParams.update({
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb",
    "text.color": "#0b0b0b", "axes.labelcolor": "#52514e", "axes.edgecolor": "#c9c8c3", "xtick.color": "#52514e", "ytick.color": "#52514e",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.prop_cycle": matplotlib.cycler(color=["#2a78d6", "#eb6834", "#1baf7a"]),
})

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))

from fbg_sim import (  # noqa: E402
    SCENARIOS,
    STATE_LABELS,
    PolyDecoupler,
    decouple_linear,
    forward,
    naive_force_estimate,
    noise_floor,
    sensitivity_matrix,
    symmetric_matrix,
)

OUT = os.path.join(ROOT, "results")
SEED = 12345


def random_states(rng, p, n):
    x = np.empty((n, 4))
    x[:, :3] = rng.uniform(-p.force_full_scale_n, p.force_full_scale_n, size=(n, 3))
    x[:, 3] = rng.uniform(-5.0, 20.0, size=n)
    return x


def rmse(est, true):
    return np.sqrt(np.mean((est - true) ** 2, axis=0))


def save(fig, outdir, name):
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, name), dpi=150)
    plt.close(fig)


def exp_time_series(rng, ctx):
    p, K, sigma, tag, outdir = ctx["p"], ctx["K"], ctx["sigma"], ctx["tag"], ctx["outdir"]
    t = np.linspace(0, 10, 1000)
    Fx = 3.0 * np.sin(2 * np.pi * 0.5 * t)
    Fy = 1.5 * np.sin(2 * np.pi * 0.3 * t + 1.0)
    Fz = 2.0 * t / 10.0
    dT = 15.0 / (1.0 + np.exp(-(t - 5.0) * 4.0))
    x = np.column_stack([Fx, Fy, Fz, dT])
    dl = forward(K, x) + rng.normal(0, sigma, size=(len(t), 4))
    dec = decouple_linear(K, dl)
    naive = naive_force_estimate(K, dl)

    fig, ax = plt.subplots(3, 1, figsize=(7, 8), sharex=True)
    for a, (lab, idx, truth) in zip(ax[:2], [("Fz", 2, Fz), ("Fx", 0, Fx)]):
        a.plot(t, truth, "k", label=f"true {lab}")
        a.plot(t, naive[:, idx], label="ignoring temperature", alpha=0.8)
        a.plot(t, dec[:, idx], label="decoupled", alpha=0.8)
        a.set_ylabel(f"{lab} (N)")
        a.legend(loc="upper left")
    ax[2].plot(t, dT, "k", label="true dT")
    ax[2].plot(t, dec[:, 3], label="estimated dT", alpha=0.8)
    ax[2].set_ylabel("dT (°C)")
    ax[2].set_xlabel("time (s)")
    ax[2].legend(loc="upper left")
    ax[0].set_title(f"Temperature step with and without decoupling\n[{tag}]")
    save(fig, outdir, "fig1_temperature_step.png")

    return {
        "rmse_N_ignoring_temperature": dict(zip(STATE_LABELS[:3], rmse(naive, x[:, :3]).tolist())),
        "rmse_N_decoupled": dict(zip(STATE_LABELS[:3], rmse(dec[:, :3], x[:, :3]).tolist())),
        "rmse_C_dT_decoupled": float(rmse(dec[:, 3], x[:, 3])),
    }


def exp_noise(rng, ctx):
    K, sigma, tag, outdir = ctx["K"], ctx["sigma"], ctx["tag"], ctx["outdir"]
    sigmas = np.array([0.5, 1.0, 2.0, 5.0, 10.0, 20.0])
    floor = np.array([noise_floor(K, s) for s in sigmas])
    x0 = np.zeros((1, 4))
    dl = forward(K, x0) + rng.normal(0, sigma, size=(20000, 4))
    mc = (decouple_linear(K, dl) - x0).std(axis=0)

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for i, lab in enumerate(STATE_LABELS[:3]):
        ax.plot(sigmas, floor[:, i] * 1000.0, "o-", label=lab)
    ax.axhline(260.0, color="gray", ls="--", lw=1, label="0.26 N (proposed stretch target)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("wavelength noise, sigma (pm)")
    ax.set_ylabel("force noise floor (mN)")
    ax.set_title(f"Noise floor after decoupling\n[{tag}]")
    ax.legend()
    save(fig, outdir, "fig2_noise_floor.png")

    return {
        "sigma_pm": sigmas.tolist(),
        "noise_floor_mN": {lab: (floor[:, i] * 1000.0).tolist() for i, lab in enumerate(STATE_LABELS)},
        "scenario_sigma_pm": sigma,
        "scenario_noise_floor_mN": dict(zip(STATE_LABELS, (noise_floor(K, sigma) * 1000.0).tolist())),
        "monte_carlo_std_mN": dict(zip(STATE_LABELS, (mc * 1000.0).tolist())),
    }


def exp_calibration_error(rng, ctx):
    p, K, tag, outdir = ctx["p"], ctx["K"], ctx["tag"], ctx["outdir"]
    eps_list = [0.0, 0.01, 0.02, 0.05, 0.10]
    xte = random_states(rng, p, 500)
    dl = forward(K, xte)
    res = {}
    for eps in eps_list:
        errs, conds = [], []
        for _ in range(200):
            Kest = K * (1.0 + eps * rng.normal(size=K.shape))  # zero entries stay zero
            try:
                est = np.linalg.solve(Kest, dl.T).T
            except np.linalg.LinAlgError:
                continue
            errs.append(rmse(est, xte))
            conds.append(np.linalg.cond(Kest))
        res[str(eps)] = {
            "mean_rmse": dict(zip(STATE_LABELS, np.mean(errs, axis=0).tolist())),
            "mean_cond": float(np.mean(conds)),
        }

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for lab in STATE_LABELS[:3]:
        ax.plot([e * 100 for e in eps_list], [res[str(e)]["mean_rmse"][lab] for e in eps_list], "o-", label=lab)
    ax.axhline(0.375, color="gray", ls="--", lw=1, label="0.375 N (proposed accuracy target)")
    ax.set_xlabel("relative error on each calibration coefficient (%)")
    ax.set_ylabel("force RMSE (N), no noise")
    ax.set_title(f"Effect of calibration error\n[{tag}]")
    ax.legend()
    save(fig, outdir, "fig3_calibration_error.png")
    return res


def exp_thermal_mismatch(rng, ctx):
    p, K, tag, outdir = ctx["p"], ctx["K"], ctx["tag"], ctx["outdir"]
    deltas = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0]
    xte = random_states(rng, p, 500)
    res = {}
    for d in deltas:
        dl = forward(K, xte)
        dl[:, 3] -= p.k_temp_ref * d
        est = decouple_linear(K, dl)
        res[str(d)] = dict(zip(STATE_LABELS, rmse(est, xte).tolist()))

    # Only the axial channel moves; the lateral channels stay at zero, so they are named in the
    # title instead of being drawn as flat lines on a log axis.
    pos = [d for d in deltas if d > 0]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(pos, [res[str(d)]["Fz"] for d in pos], "o-", lw=2, ms=6, label="axial force Fz")
    ax.text(pos[-1] + 0.2, res[str(pos[-1])]["Fz"], "axial force", fontsize=8, va="center")
    ax.axhline(0.061, color="#0b0b0b", ls="--", lw=1)
    ax.text(0.55, 0.075, "0.061 N (proposed thermal target)", fontsize=8, color="#52514e")
    ax.set_yscale("log")
    ax.set_xlim(0.4, 12.5)
    ax.set_xlabel("temperature offset of the reference grating (°C)")
    ax.set_ylabel("axial force RMSE (N), no noise")
    ax.set_title(f"Reference grating not at the same temperature (lateral channels unchanged)\n[{tag}]", fontsize=9)
    save(fig, outdir, "fig4_thermal_mismatch.png")
    return res


def exp_transverse_gradient(rng, ctx):
    """Uneven heating across the section: each strained grating sees dT + amp*cos(theta_i - phi).

    The reference grating sees dT. The decoupling does not know about the gradient, so the
    gradient looks like a lateral force.
    """
    p, K, tag, outdir = ctx["p"], ctx["K"], ctx["tag"], ctx["outdir"]
    amps = [0.0, 0.25, 0.5, 1.0, 2.0]
    angles = np.deg2rad(p.angles_deg)
    xte = random_states(rng, p, 500)
    phis = rng.uniform(0, 2 * np.pi, size=len(xte))
    res = {}
    for a in amps:
        dl = forward(K, xte)
        for i, th in enumerate(angles):
            dl[:, i] += p.k_temp * a * np.cos(th - phis)
        est = decouple_linear(K, dl)
        res[str(a)] = dict(zip(STATE_LABELS, rmse(est, xte).tolist()))

    # Fx and Fy overlap and Fz stays at zero, so one lateral series is drawn (the larger of Fx and Fy).
    pos = [a for a in amps if a > 0]
    lat = [max(res[str(a)]["Fx"], res[str(a)]["Fy"]) for a in pos]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(pos, lat, "o-", lw=2, ms=6)
    ax.text(pos[-1] + 0.05, lat[-1], "lateral force", fontsize=8, va="center")
    ax.axhline(0.375, color="#0b0b0b", ls="--", lw=1)
    ax.text(0.27, 0.375 * 1.12, "0.375 N (proposed accuracy target)", fontsize=8, color="#52514e")
    ax.set_yscale("log")
    ax.set_xlim(0.2, 2.5)
    ax.set_xlabel("uneven heating: warm side above the mean, amplitude (°C)")
    ax.set_ylabel("lateral force RMSE per axis (N), no noise")
    ax.set_title(f"Uneven heating looks like a lateral force (axial channel unchanged)\n[{tag}]", fontsize=9)
    save(fig, outdir, "fig6_transverse_gradient.png")
    return res


def exp_nonlinear(rng, ctx):
    p, K, sigma, tag, outdir = ctx["p"], ctx["K"], ctx["sigma"], ctx["tag"], ctx["outdir"]
    betas = [0.0, 0.02, 0.05, 0.10]
    res = {}
    for b in betas:
        xtr, xte = random_states(rng, p, 2000), random_states(rng, p, 2000)
        dltr = forward(K, xtr, beta=b, p=p) + rng.normal(0, sigma, size=(2000, 4))
        dlte = forward(K, xte, beta=b, p=p) + rng.normal(0, sigma, size=(2000, 4))
        lin = decouple_linear(K, dlte)
        poly = PolyDecoupler(scale_pm=max(10.0, 2.0 * p.k_lateral * p.force_full_scale_n)).fit(dltr, xtr).predict(dlte)
        res[str(b)] = {
            "linear_rmse": dict(zip(STATE_LABELS[:3], rmse(lin[:, :3], xte[:, :3]).tolist())),
            "poly_rmse": dict(zip(STATE_LABELS[:3], rmse(poly[:, :3], xte[:, :3]).tolist())),
        }

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    lin_mean = [np.mean(list(res[str(b)]["linear_rmse"].values())) for b in betas]
    poly_mean = [np.mean(list(res[str(b)]["poly_rmse"].values())) for b in betas]
    ax.plot([b * 100 for b in betas], lin_mean, "o-", label="linear model")
    ax.plot([b * 100 for b in betas], poly_mean, "s-", label="second-order polynomial model")
    ax.set_xlabel("assumed quadratic crosstalk at full scale (%)")
    ax.set_ylabel("mean force RMSE (N), with noise")
    ax.set_title(f"Linear versus nonlinear decoupling\n[{tag}]")
    ax.legend()
    save(fig, outdir, "fig5_nonlinear.png")
    return res


def run_scenario(name, spec):
    p, sigma = spec["params"], spec["sigma_pm"]
    K = sensitivity_matrix(p)
    S = symmetric_matrix(p)
    outdir = os.path.join(OUT, name)
    os.makedirs(outdir, exist_ok=True)
    ctx = {"p": p, "K": K, "sigma": sigma, "tag": f"SIMULATION, assumed parameters: {name}", "outdir": outdir}
    rng = np.random.default_rng(SEED)
    cond_sym = np.linalg.cond(S)
    return {
        "assumed_parameters": {
            "k_lateral_pm_per_N": p.k_lateral,
            "k_axial_pm_per_N": p.k_axial,
            "k_temp_bonded_pm_per_C": p.k_temp,
            "k_temp_reference_pm_per_C": p.k_temp_ref,
            "sigma_pm": sigma,
            "force_full_scale_N": p.force_full_scale_n,
        },
        "conditioning": {
            "proposed_layout_cond": float(np.linalg.cond(K)),
            "proposed_layout_rank": int(np.linalg.matrix_rank(K)),
            "symmetric_layout_rank": int(np.linalg.matrix_rank(S)),
            "symmetric_layout_cond": float(cond_sym) if np.isfinite(cond_sym) else "infinite (singular matrix)",
        },
        # Errors per degree C do not depend on the arbitrary size of a temperature step.
        "per_degree": {
            "axial_error_N_per_C_if_temperature_is_ignored": float(p.k_temp / p.k_axial),
            "axial_error_N_per_C_of_reference_offset": float(p.k_temp / p.k_axial),
            "lateral_error_N_per_C_of_gradient_amplitude_worst_case": float(p.k_temp / p.k_lateral),
        },
        "temperature_step": exp_time_series(rng, ctx),
        "noise": exp_noise(rng, ctx),
        "calibration_error": exp_calibration_error(rng, ctx),
        "thermal_mismatch": exp_thermal_mismatch(rng, ctx),
        "transverse_gradient": exp_transverse_gradient(rng, ctx),
        "nonlinear": exp_nonlinear(rng, ctx),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    results = {
        "disclaimer": "SIMULATION ONLY. Assumed parameters. Not a measurement, not a hardware validation.",
        "seed": SEED,
        "scenarios": {name: run_scenario(name, spec) for name, spec in SCENARIOS.items()},
    }
    with open(os.path.join(OUT, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("written", os.path.join(OUT, "results.json"))


if __name__ == "__main__":
    main()
