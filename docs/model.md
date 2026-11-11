# Model: equations, assumptions, experiments

> Simulation only. Parameters are assumed unless a source is named. See `docs/results_summary.md` for the numbers.

## 1. Physics in one line each

- A fiber Bragg grating reflects the wavelength `lambda_B = 2 * n_eff * Lambda`. Strain and temperature both change it.
- For a bare fiber: about 1.2 pm per microstrain and about 10 to 13 pm/°C.
- A fiber bonded to steel stretches with the steel, so its thermal response is higher: **about 30 pm/°C is an estimate**, not a measurement. A free fiber keeps 11.5 pm/°C.

## 2. Linear model

State: `x = [Fx, Fy, Fz, dT]` (lateral forces, axial force, temperature rise).
Readings: `d_lambda = K @ x`, four wavelength shifts in pm.

Rows of `K` (code: `sensitivity_matrix` in `src/fbg_sim/model.py`):

| Fiber | Row |
|---|---|
| Strained, angle `theta` = 0, 120, 240° | `[k_L cos(theta), k_L sin(theta), k_A, k_T_bonded]` |
| Reference (free) | `[0, 0, 0, k_T_reference]` |

- `k_L`: lateral sensitivity (pm/N). `k_A`: axial sensitivity (pm/N). Both come from beam theory for the assumed tube (E = 196 GPa, 0.5 mm wall, load 100 mm from the sleeve).
- With four strained fibers and no reference, an axial push and a temperature rise produce the same column pattern: `K` has rank 3. `decouple_linear` refuses any matrix with a condition number above 1000. The proposed layout has a condition number of about 300.

## 3. Noise floor

If every fiber has independent wavelength noise `sigma` (pm), the noise on unknown `i` is

`sigma_i = sigma * || row_i of K^-1 ||`

This is a one-standard-deviation noise floor, not a guaranteed resolution. A Monte Carlo run in the script agrees with it within about 1 %.

## 4. Experiments (`scripts/run_simulation.py`)

1. **Temperature step:** force estimate with and without separating temperature. Result: the axial error falls from hundreds of newtons to the noise, and the temperature is recovered; the lateral estimate is unchanged, because uniform heating already cancels among three strained fibers 120 degrees apart. So the reference fiber is justified for the axial channel and the temperature, not for the lateral force under uniform heating, and it does not correct uneven heating.
2. **Noise floor:** force noise after decoupling, for several wavelength noise values.
3. **Calibration error:** the estimate uses a `K` whose coefficients are off by 0, 1, 2, 5 or 10 %.
4. **Reference fiber offset:** the reference sees a temperature that is 0 to a few degrees away from the rest. The axial channel absorbs it (`k_T_bonded / k_A` newtons per degree), the lateral channels stay clean.
5. **Uneven heating:** strained fiber `i` sees `dT + amp * cos(theta_i - phi)`. The decoupler does not know this, so the gradient looks like a lateral force. The warm side is `amp` above the mean; the temperature difference between the warmest and the coolest side is `2 * amp`. The lateral error per axis is about `amp * k_T_bonded / (sqrt(2) * k_L)`, so the largest tolerated amplitude for a target force `F` is `sqrt(2) * k_L * F / k_T_bonded`.
6. **Linear versus second-order polynomial decoupling** for an assumed quadratic crosstalk (0 to 10 % at full scale).

## 5. What this model cannot tell you

- Signals are generated with `K` and inverted with `K` (except in experiment 3), so the reconstruction is exact apart from added noise. Real mismatch adds error.
- The shaft is an ideal tube. A real instrument has an inner rod, joints and play.
- Heat is a uniform rise plus a simple cosine gradient. Real heat moves along the shaft and in time.
- The glue is perfect (it passes on all the strain, with no creep).
- The port, the hand and the position of the sleeve on the handle side are not modeled, so the force at the tip is not estimated.
- The flexure scenario multiplies every strain sensitivity by 10, an arbitrary factor, and keeps the thermal response fixed.

## 6. How to replace the assumptions

Calibrate a real sleeve (`docs/calibration_procedure.md`, `scripts/fit_calibration.py`), then put the fitted values in `SleeveParams` (`src/fbg_sim/model.py`), re-run `scripts/run_simulation.py` and `scripts/make_results_summary.py`.
