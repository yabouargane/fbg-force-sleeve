import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fbg_sim import SleeveParams, forward, sensitivity_matrix  # noqa: E402
from fbg_sim.calibration import (  # noqa: E402
    drift_per_hour,
    errors,
    fit_sensitivity,
    hysteresis_percent,
    linearity_error_percent,
    noise_floor_from_rest,
)

K = sensitivity_matrix(SleeveParams())


def states(rng, n):
    x = np.empty((n, 4))
    x[:, :3] = rng.uniform(-5, 5, size=(n, 3))
    x[:, 3] = rng.uniform(-5, 20, size=n)
    return x


class CalibrationTests(unittest.TestCase):
    def test_fit_recovers_K_without_noise(self):
        rng = np.random.default_rng(0)
        x = states(rng, 80)
        np.testing.assert_allclose(fit_sensitivity(forward(K, x), x), K, atol=1e-9)

    def test_fit_recovers_K_with_noise(self):
        rng = np.random.default_rng(1)
        x = states(rng, 400)
        d = forward(K, x) + rng.normal(0, 0.5, size=(400, 4))
        np.testing.assert_allclose(fit_sensitivity(d, x), K, rtol=0.05, atol=0.2)

    def test_fit_refuses_data_that_does_not_excite_all_unknowns(self):
        rng = np.random.default_rng(2)
        x = states(rng, 50)
        x[:, 3] = 0.0  # temperature never varied
        with self.assertRaises(ValueError):
            fit_sensitivity(forward(K, x), x)

    def test_errors(self):
        truth = np.zeros((4, 2))
        est = np.array([[1, -1], [1, -1], [1, -1], [1, 3]], dtype=float)
        e = errors(est, truth)
        np.testing.assert_allclose(e["mae"], [1.0, 1.5])
        np.testing.assert_allclose(e["max_abs"], [1.0, 3.0])

    def test_linearity_zero_for_a_line_and_positive_for_a_curve(self):
        t = np.linspace(0, 5, 21)
        self.assertAlmostEqual(linearity_error_percent(t, 2 * t + 1, 5.0), 0.0, places=9)
        self.assertGreater(linearity_error_percent(t, t + 0.1 * t**2, 5.0), 0.1)

    def test_hysteresis(self):
        up = np.array([0.0, 1.0, 2.0])
        down = np.array([0.1, 1.2, 2.0])
        self.assertAlmostEqual(hysteresis_percent(up, down, 10.0), 2.0, places=9)

    def test_noise_floor_and_drift(self):
        rng = np.random.default_rng(3)
        t = np.arange(0, 600.0)
        y = 0.002 * (t / 3600.0) * 3600.0 / 600.0 * 0 + rng.normal(0, 0.03, size=t.size)
        self.assertAlmostEqual(float(noise_floor_from_rest(y)), 0.03, delta=0.005)
        ramp = 0.5 * t / 3600.0  # 0.5 per hour
        self.assertAlmostEqual(float(drift_per_hour(t, ramp)[0]), 0.5, places=6)


if __name__ == "__main__":
    unittest.main()
