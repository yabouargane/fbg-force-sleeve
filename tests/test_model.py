import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fbg_sim import (  # noqa: E402
    PolyDecoupler,
    SleeveParams,
    decouple_linear,
    forward,
    naive_force_estimate,
    noise_floor,
    sensitivity_matrix,
    symmetric_matrix,
)

P = SleeveParams()
K = sensitivity_matrix(P)


def random_states(rng, n):
    x = np.empty((n, 4))
    x[:, :3] = rng.uniform(-5, 5, size=(n, 3))
    x[:, 3] = rng.uniform(-5, 20, size=n)
    return x


class ModelTests(unittest.TestCase):
    def test_roundtrip_without_noise(self):
        rng = np.random.default_rng(0)
        x = random_states(rng, 200)
        est = decouple_linear(K, forward(K, x))
        np.testing.assert_allclose(est, x, atol=1e-9)

    def test_proposed_layout_has_full_rank(self):
        self.assertEqual(np.linalg.matrix_rank(K), 4)

    def test_symmetric_layout_is_singular_and_refused(self):
        S = symmetric_matrix(P)
        self.assertLess(np.linalg.matrix_rank(S), 4)
        with self.assertRaises(ValueError):
            decouple_linear(S, np.zeros(4))

    def test_naive_estimate_mixes_temperature_into_axial_force(self):
        # Pure temperature step, no force: the naive estimate reads k_temp*dT/k_axial on Fz.
        x = np.array([[0.0, 0.0, 0.0, 10.0]])
        naive = naive_force_estimate(K, forward(K, x))
        self.assertAlmostEqual(naive[0, 2], P.k_temp * 10.0 / P.k_axial, places=9)
        self.assertAlmostEqual(naive[0, 0], 0.0, places=9)
        self.assertAlmostEqual(naive[0, 1], 0.0, places=9)

    def test_noise_floor_matches_monte_carlo(self):
        rng = np.random.default_rng(1)
        sigma = 2.0
        x = np.zeros((1, 4))
        dl = forward(K, x) + rng.normal(0, sigma, size=(40000, 4))
        err = decouple_linear(K, dl) - x
        mc = err.std(axis=0)
        np.testing.assert_allclose(mc, noise_floor(K, sigma), rtol=0.03)

    def test_polynomial_model_reduces_nonlinear_error(self):
        rng = np.random.default_rng(2)
        beta = 0.05
        xtr, xte = random_states(rng, 3000), random_states(rng, 3000)
        dltr, dlte = forward(K, xtr, beta=beta), forward(K, xte, beta=beta)
        lin = decouple_linear(K, dlte)
        poly = PolyDecoupler().fit(dltr, xtr).predict(dlte)
        rmse_lin = np.sqrt(np.mean((lin[:, :3] - xte[:, :3]) ** 2))
        rmse_poly = np.sqrt(np.mean((poly[:, :3] - xte[:, :3]) ** 2))
        self.assertLess(rmse_poly, rmse_lin)


if __name__ == "__main__":
    unittest.main()
