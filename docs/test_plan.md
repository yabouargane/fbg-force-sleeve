# Bench test plan (draft, not run)

Seven tests, in the order in which they decide whether the rest is worth building. The detailed steps of the calibration are in `docs/calibration_procedure.md`. Report poor results as well as good ones.

| # | Test | What it measures | What it decides | Simulation value to compare with |
|---|---|---|---|---|
| 1 | Noise at rest | Standard deviation of each channel with no load at constant temperature, in pm and converted to mN with `K^-1` | Whether the readout noise is near the assumed 1 pm (laboratory) or 3 pm (low-cost) | 9.7 mN lateral at 1 pm; 29 mN at 3 pm |
| 2 | Calibration of each axis | Wavelength shifts against a reference load cell, loading and unloading, three repeats | The matrix `K`, its condition number, linearity, hysteresis, repeatability | Condition number about 300; lateral sensitivity 84.5 pm/N (assumed) |
| 3 | Controlled heating, with and without force | Thermal response of the bonded fibers and of the free fiber | The 30 pm/°C estimate (largest single assumption) | 30 and 11.5 pm/°C |
| 4 | Reference fiber offset | Heat the sleeve so the reference lags, or offset it on purpose | How a reference error spreads into the axial channel | 34.5 N per °C on the axial channel; lateral channels stay clean |
| 5 | Heating one side only | Lateral reading while one side of the shaft is heated | The largest tolerated uneven heating | about 0.26 N (26 g) per °C of amplitude; limit about 1.5 °C for 0.375 N |
| 6 | Two sensor positions | Repeat test 2 with the load at three positions along the sensing zone | Position dependence of the response | Not modeled |
| 7 | Simulated port | Same load with and without a bushing that simulates the port (about 5.5 mm bore, to define) | Whether a model of the pivot point is needed and feasible | Not modeled |

## Pass / fail logic used in the articles

- If the lateral error after calibration stays above 0.375 N (38 g), or if the reference fiber does not follow the shaft temperature, the idea fails as designed. Publish the result either way.
- Tests 3 and 5 decide the most, because the whole design depends on how heat acts on the bonded fibers.

## Equipment

Reference load cell (known range and resolution), fixture that holds the instrument and loads each axis, controlled heat source, reference thermometer (a second thermometer for cross-checking the reference fiber), the interrogator or the low-cost readout under test.

## What to send back

See `CONTRIBUTING.md` for the CSV format and the issue template.
