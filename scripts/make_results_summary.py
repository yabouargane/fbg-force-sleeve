"""Write docs/results_summary.md from results/results.json.

Run after scripts/run_simulation.py, from anywhere:  python scripts/make_results_summary.py
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = json.load(open(ROOT / "results" / "results.json", encoding="utf-8"))["scenarios"]
GF = 101.97  # gram-force per newton
TARGET = 0.375  # N

order = [
    ("tube8_baseline", "8 mm tube, fibers 3.5 mm from the axis"),
    ("tube5_beam_assumed", "5 mm shaft, beam theory, 1 pm noise"),
    ("tube5_lowcost_readout", "5 mm shaft, low-cost readout, 3 pm noise"),
    ("flexure_x10_assumed", "5 mm shaft + hypothetical flexure (x10), 3 pm noise"),
]


def f(x, d=1):
    return f"{x:.{d}f}"


rows = []
for key, label in order:
    s = R[key]
    p = s["assumed_parameters"]
    nf = s["noise"]["scenario_noise_floor_mN"]
    grad = max(s["transverse_gradient"]["1.0"]["Fx"], s["transverse_gradient"]["1.0"]["Fy"])
    amp_max = TARGET * math.sqrt(2) * p["k_lateral_pm_per_N"] / p["k_temp_bonded_pm_per_C"]
    ref = s["thermal_mismatch"]["1.0"]["Fz"]
    cal = s["calibration_error"]["0.05"]["mean_rmse"]
    nl = s["nonlinear"]["0.05"]
    nl_lin = (nl["linear_rmse"]["Fx"] + nl["linear_rmse"]["Fy"]) / 2
    nl_pol = (nl["poly_rmse"]["Fx"] + nl["poly_rmse"]["Fy"]) / 2
    rows.append((key, label, p, nf, grad, amp_max, ref, cal, nl_lin, nl_pol, s["conditioning"]["proposed_layout_cond"]))

out = []
out.append("# Simulation results at a glance\n")
out.append("> **Simulation with assumed parameters. Not a measurement.** Generated from `results/results.json` by `scripts/make_results_summary.py`. Re-run `python scripts/run_simulation.py`, then that script, to reproduce the numbers. Forces are given in newtons (N) and in gram-force (g, 1 N = 101.97 g). The model creates its signals and inverts them with the same matrix, so it is optimistic.\n")
out.append("## Noise floor (one standard deviation of the force estimate caused by wavelength noise)\n")
out.append("| Scenario | Lateral sensitivity | Wavelength noise | Lateral noise floor | Axial noise floor | Condition number |")
out.append("|---|---|---|---|---|---|")
for key, label, p, nf, grad, amp_max, ref, cal, nl_lin, nl_pol, cond in rows:
    out.append(f"| {label} (`{key}`) | {f(p['k_lateral_pm_per_N'])} pm/N | {f(p['sigma_pm'])} pm | {f(nf['Fx'])} mN ({f(nf['Fx']/1000*GF)} g) | {f(nf['Fz']/1000, 2)} N ({f(nf['Fz']/1000*GF, 0)} g) | {f(cond, 0)} |")
out.append("")
out.append("Target used in the articles: 0.375 N (38 g), 12.5 % of a 3 N range in a published sensor. The axial force is not readable with a plain tube.\n")
out.append("## Sensitivity to the problems the model can represent\n")
out.append("| Scenario | Uneven heating: lateral error per degree of amplitude | Largest amplitude that keeps the lateral error under 0.375 N | Reference fiber 1 °C off: axial error | 5 % calibration error: lateral error | 5 % curvature: linear vs second-order model |")
out.append("|---|---|---|---|---|---|")
for key, label, p, nf, grad, amp_max, ref, cal, nl_lin, nl_pol, cond in rows:
    out.append(f"| `{key}` | {f(grad, 3)} N ({f(grad*GF, 0)} g) | {f(amp_max, 2)} °C | {f(ref, 1)} N | {f(min(cal['Fx'], cal['Fy']), 3)} to {f(max(cal['Fx'], cal['Fy']), 3)} N | {f(nl_lin, 3)} N to {f(nl_pol, 3)} N |")
out.append("")
out.append("**Amplitude of uneven heating.** Each strained fiber sees the mean temperature rise plus `amp * cos(theta - phi)`. The warmest side is therefore `amp` above the mean, and the temperature difference between the warmest and the coolest side is `2 * amp`. The reference fiber is assumed to see the mean.\n")
out.append("## Effect of the reference (thermometer) fiber: temperature step, with and without separation\n")
out.append("| Scenario | Axial force error, temperature ignored | Axial force error, separated | Lateral force error, temperature ignored | Lateral force error, separated | Temperature error, separated |")
out.append("|---|---|---|---|---|---|")
for key, label in order:
    ts = R[key]["temperature_step"]
    ign, dec = ts["rmse_N_ignoring_temperature"], ts["rmse_N_decoupled"]
    out.append(f"| `{key}` | {f(ign['Fz'], 1)} N | {f(dec['Fz'], 2)} N | {f(ign['Fx'], 4)} N | {f(dec['Fx'], 4)} N | {f(ts['rmse_C_dT_decoupled'], 2)} °C |")
out.append("")
out.append("Root-mean-square errors over a 10 s run with a 15 °C temperature step. The reference fiber removes the heat from the **axial** force and gives the temperature. The **lateral** error is the same with and without it: uniform heating already cancels among three strained fibers placed 120 degrees apart. The reference fiber does not correct uneven heating across the section.\n")
out.append("## Assumptions behind these numbers\n")
out.append("- 5 mm steel tube, 0.5 mm wall, lever arm 100 mm (assumed; beam theory with E = 196 GPa, 1.2 pm per microstrain).")
out.append("- Fiber bonded to steel: about 30 pm/°C (an estimate from the expansion of steel; no direct measurement found). Free reference fiber: 11.5 pm/°C.")
out.append("- Wavelength noise: 1 pm (laboratory reader, no source) and 3 pm (inside the 2.4 to 3.6 pm reported for published low-cost edge-filter readouts).")
out.append("- The factor 10 of the flexure scenario is arbitrary. The quadratic crosstalk (5 %) is assumed.")
out.append("- Replace these values after calibration on a real sleeve and re-run the script.")
open(ROOT / "docs" / "results_summary.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("ok")
