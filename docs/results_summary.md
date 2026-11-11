# Simulation results at a glance

> **Simulation with assumed parameters. Not a measurement.** Generated from `results/results.json` by `scripts/make_results_summary.py`. Re-run `python scripts/run_simulation.py`, then that script, to reproduce the numbers. Forces are given in newtons (N) and in gram-force (g, 1 N = 101.97 g). The model creates its signals and inverts them with the same matrix, so it is optimistic.

## Noise floor (one standard deviation of the force estimate caused by wavelength noise)

| Scenario | Lateral sensitivity | Wavelength noise | Lateral noise floor | Axial noise floor | Condition number |
|---|---|---|---|---|---|
| 8 mm tube, fibers 3.5 mm from the axis (`tube8_baseline`) | 15.7 pm/N | 1.0 pm | 52.0 mN (5.3 g) | 5.34 N (545 g) | 284 |
| 5 mm shaft, beam theory, 1 pm noise (`tube5_beam_assumed`) | 84.5 pm/N | 1.0 pm | 9.7 mN (1.0 g) | 3.07 N (313 g) | 318 |
| 5 mm shaft, low-cost readout, 3 pm noise (`tube5_lowcost_readout`) | 84.5 pm/N | 3.0 pm | 29.0 mN (3.0 g) | 9.21 N (939 g) | 318 |
| 5 mm shaft + hypothetical flexure (x10), 3 pm noise (`flexure_x10_assumed`) | 845.0 pm/N | 3.0 pm | 2.9 mN (0.3 g) | 0.92 N (94 g) | 330 |

Target used in the articles: 0.375 N (38 g), 12.5 % of a 3 N range in a published sensor. The axial force is not readable with a plain tube.

## Sensitivity to the problems the model can represent

| Scenario | Uneven heating: lateral error per degree of amplitude | Largest amplitude that keeps the lateral error under 0.375 N | Reference fiber 1 °C off: axial error | 5 % calibration error: lateral error | 5 % curvature: linear vs second-order model |
|---|---|---|---|---|---|
| `tube8_baseline` | 1.376 N (140 g) | 0.28 °C | 60.0 N | 0.558 to 0.675 N | 0.132 N to 0.058 N |
| `tube5_beam_assumed` | 0.256 N (26 g) | 1.49 °C | 34.5 N | 0.149 to 0.171 N | 0.121 N to 0.028 N |
| `tube5_lowcost_readout` | 0.256 N (26 g) | 1.49 °C | 34.5 N | 0.149 to 0.171 N | 0.124 N to 0.039 N |
| `flexure_x10_assumed` | 0.026 N (3 g) | 14.94 °C | 3.4 N | 0.096 to 0.100 N | 0.121 N to 0.026 N |

**Amplitude of uneven heating.** Each strained fiber sees the mean temperature rise plus `amp * cos(theta - phi)`. The warmest side is therefore `amp` above the mean, and the temperature difference between the warmest and the coolest side is `2 * amp`. The reference fiber is assumed to see the mean.

## Effect of the reference (thermometer) fiber: temperature step, with and without separation

| Scenario | Axial force error, temperature ignored | Axial force error, separated | Lateral force error, temperature ignored | Lateral force error, separated | Temperature error, separated |
|---|---|---|---|---|---|
| `tube8_baseline` | 620.3 N | 5.70 N | 0.0507 N | 0.0507 N | 0.09 °C |
| `tube5_beam_assumed` | 356.5 N | 3.27 N | 0.0094 N | 0.0094 N | 0.09 °C |
| `tube5_lowcost_readout` | 356.4 N | 9.82 N | 0.0283 N | 0.0283 N | 0.28 °C |
| `flexure_x10_assumed` | 35.6 N | 0.98 N | 0.0028 N | 0.0028 N | 0.28 °C |

Root-mean-square errors over a 10 s run with a 15 °C temperature step. The reference fiber removes the heat from the **axial** force and gives the temperature. The **lateral** error is the same with and without it: uniform heating already cancels among three strained fibers placed 120 degrees apart. The reference fiber does not correct uneven heating across the section.

## Assumptions behind these numbers

- 5 mm steel tube, 0.5 mm wall, lever arm 100 mm (assumed; beam theory with E = 196 GPa, 1.2 pm per microstrain).
- Fiber bonded to steel: about 30 pm/°C (an estimate from the expansion of steel; no direct measurement found). Free reference fiber: 11.5 pm/°C.
- Wavelength noise: 1 pm (laboratory reader, no source) and 3 pm (inside the 2.4 to 3.6 pm reported for published low-cost edge-filter readouts).
- The factor 10 of the flexure scenario is arbitrary. The quadratic crosstalk (5 %) is assumed.
- Replace these values after calibration on a real sleeve and re-run the script.
