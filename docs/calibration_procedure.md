# Calibration procedure (draft, not yet run)

Goal: measure the 4×4 sensitivity matrix `K` (`d_lambda = K @ [Fx, Fy, Fz, dT]`) of a built sleeve, then check it on loads not used for the fit.

**Safety:** bench work only. Research use only.

## Equipment
- Built sleeve with four gratings (three strained, one strain-isolated reference), read by the chosen interrogator.
- Reference load cell with a known range and resolution. TODO: record its model and specification.
- Fixture holding the instrument and applying loads on each axis.
- Controlled heat source and a reference thermometer.

## Steps
1. **Noise floor.** Record all channels with no load at constant temperature for several minutes. Report the standard deviation of each channel in pm, and the resulting force noise in mN (`K^-1` times the noise).
2. **Force axes, one at a time.** At room temperature, load Fx, Fy and Fz in steps up to the target range and back down. Record the load cell and the four wavelengths at each step. Repeat at least three times.
3. **Positions.** Repeat step 2 with the load applied at three positions along the sensing zone.
4. **Temperature.** With no load, raise and lower the temperature in steps. Record the thermometer and the four wavelengths.
5. **Fit `K`.** Least squares of wavelength shifts against the known states. Report the condition number of `K`.
6. **Hold-out check.** Apply combined loads and temperatures not used in the fit. Report range, resolution (with its definition), mean absolute error, linearity, hysteresis, repeatability and drift.
7. **Nonlinear model.** Fit the second-order polynomial model on the same data. Report both models side by side.
8. **Reference grating offset.** Heat the sleeve so the reference grating lags the others. Report the force error against the temperature difference.

## Reporting
Use the same metrics and definitions as the papers cited in the article, so results can be compared. Report poor results as well.
