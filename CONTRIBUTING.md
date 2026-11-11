# Contributing

This is a design study with no hardware validation yet. The most useful contributions are **tests and critiques**, not features.

## Most useful, in this order

1. **Bench data.** Any of the seven tests in `docs/test_plan.md`, even a partial one. Results that contradict the model are the most valuable.
2. **Critique of the assumptions.** Read `docs/model.md` and tell me which assumption is wrong and why, with a source if you have one. The 30 pm/°C thermal response of a bonded fiber and the 1 pm readout noise have no measurement behind them.
3. **Prior art and claims.** Missing papers, products or patents. In particular the claims of the patent family on ribbed force sensors built into the shaft, which have not been read.
4. **Bugs** in `src/` or `hardware/generate_sleeve.py`, with the smallest input that shows them.
5. **Reviews of the 3D model.** It has never been printed.

## Reporting bench data

Open an issue with the template `bench_result`, and attach a CSV with one row per steady-state point and a header:

```
Fx_N,Fy_N,Fz_N,dT_C,wl1_pm,wl2_pm,wl3_pm,wl4_pm
```

Wavelengths are shifts in pm relative to a zero-load recording at the reference temperature. `python scripts/fit_calibration.py your_file.csv --split 0.7` fits the matrix on 70 % of the rows and reports errors on the rest. Describe the shaft (material, diameter, wall), the fiber and the glue, the readout, and the reference load cell.

## Code changes

- Run `python -m unittest discover -s tests -v` before sending a change. All tests must pass.
- Keep claims honest: the repository says "simulation" wherever a number comes from the model. Do not rewrite a simulated result as a performance.
- No medical claims, no sterility claims.

## Safety and scope

Research use only. Do not use any file from this repository on a patient or in clinical practice.
