# fbg-force-sleeve

An open design study for a **clip-on sleeve with four optical fibers** that could measure the **lateral force on the shaft** of a manual laparoscopic instrument, and separate it from the heat of electrosurgery.

> **Research use only. Not a medical device. No sensor has been built or tested.**
> Everything in `results/` comes from a simulation with assumed parameters. It shows how the method behaves inside a model. It does not show that a built sleeve works.

Français : [README.fr.md](README.fr.md)

## The idea in one minute

- A fiber Bragg grating (FBG) is a pattern in an optical fiber that reflects one color. The color shifts when the fiber stretches and also when it warms.
- Three fibers are glued on the shaft, 120° apart. They feel bending and heat. A fourth fiber lies loose against the shaft and feels heat only: it is the thermometer.
- Four readings give four unknowns: the force in two lateral directions, the force along the shaft, and the temperature. Without the thermometer fiber, the matrix loses one rank and the code refuses to solve it. In the simulation, the thermometer fiber separates heat from the axial force and gives the temperature; for the lateral force, uniform heat already cancels because the three strained fibers sit 120° apart, and uneven heating is not corrected by the thermometer fiber.
- The sleeve is a 3D-printed clip that holds the fibers against the shaft. It measures nothing itself. The fibers leave the sleeve as a thin cable to a readout instrument.

## What the simulation shows (5 mm shaft, assumed parameters)

| Question | Result |
|---|---|
| Smallest lateral force change above the noise | about 1 g with a laboratory reader (1 pm), about 3 g with a low-cost reader (3 pm). Target used in the articles: 38 g (0.375 N) |
| Force along the shaft | Not readable with a plain tube: about 310 g (laboratory) to 0.9 kg (low-cost) |
| Uneven heating around the shaft | Fakes a lateral force of about 26 g per degree of amplitude. The warm side must stay within about 1.5 °C of the mean (0.28 °C for an 8 mm tube) |
| Reference fiber 1 °C behind the shaft | 34 N error on the axial channel, lateral channels stay clean |
| 5 % calibration error | 15 to 17 g of lateral error |
| 5 % curved response | A second-order model cuts the lateral error from 12 g to 3 g |

Full tables: [docs/results_summary.md](docs/results_summary.md). Equations and assumptions: [docs/model.md](docs/model.md).

## Status

| Part | State |
|---|---|
| Simulation and decoupling code (`src/`, `scripts/`) | Written and tested against its own model (13 unit tests, four scenarios). Results are reproducible: a re-run gives identical output |
| Calibration fit and metrics (`src/fbg_sim/calibration.py`, `scripts/fit_calibration.py`) | Written and tested on synthetic data only. Never run on measured data |
| 3D model of the sleeve (`hardware/generate_sleeve.py`, STL, `docs/plan_technique.md`) | Built and geometry-checked (watertight, one body, no overlap). Never printed or tested. No flexure |
| OpenSCAD version (`hardware/sleeve.scad`) | Same geometry, **not rendered** (OpenSCAD was not available) |
| Cable routing, connector, fiber protection | Not designed |
| Firmware | Not written |
| Bench test plan (`docs/test_plan.md`, `docs/calibration_procedure.md`) | Draft, not run |
| Bill of materials (`docs/bom_template.csv`) | Empty template. No supplier quotes yet |
| Bench validation | Not done |

## Quick start

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/run_simulation.py
python scripts/make_results_summary.py
```

The 3D model needs the extra packages in `hardware/requirements-hardware.txt`:

```bash
pip install -r hardware/requirements-hardware.txt
python hardware/generate_sleeve.py
```

## Layout

```
src/fbg_sim/model.py        forward model, scenarios, linear and polynomial decoupling, noise floor
src/fbg_sim/calibration.py  K fit, error, linearity, hysteresis, noise floor and drift metrics
scripts/run_simulation.py   six experiments per scenario, writes results/<scenario>/*.png and results/results.json
scripts/make_results_summary.py  writes docs/results_summary.md from results.json
scripts/fit_calibration.py  fits K from a bench CSV (columns documented in the script)
tests/                      unit tests (standard library unittest)
hardware/generate_sleeve.py builds the 3D model, STL files and technical drawings
hardware/sleeve_v0.stl      sleeve only (concept, not printed)
hardware/sleeve.scad        same geometry in OpenSCAD (not rendered)
docs/model.md               equations, assumptions, how each experiment works
docs/results_summary.md     results in newtons and grams-force
docs/test_plan.md           seven bench tests, with what each one decides
docs/plan_technique.md      3D plan, dimensions, assembly, open points (French)
docs/calibration_procedure.md
docs/bom_template.csv
results/                    simulation outputs (figures and JSON)
```

## What would change the conclusions

The results depend on assumptions that only a bench can settle. The most important ones:

1. The thermal response of a fiber bonded to steel (30 pm/°C here is an estimate with no measurement behind it).
2. The real noise of the readout (1 pm has no source; 3 pm matches published low-cost designs).
3. Wall thickness, lever arm and stiffness of a real instrument.
4. How much strain the glue really passes on, and how it creeps.
5. How the port (trocar) and the hand change the strain at the handle side. The sleeve stays outside the port, so the force at the tip needs a model of the pivot point, which does not exist here.

If you can run any of these, see [CONTRIBUTING.md](CONTRIBUTING.md). A negative result is as useful as a positive one.

## Patents and safety

- A patent family on ribbed force sensors built into an instrument shaft as separately manufactured modules exists (for example US 9,952,107). **Its claims have not been read.** Read them before building or redistributing derivatives. This is not legal advice.
- The design claims no sterility and no medical use. Nothing here is validated for patients.

## How this repository was made

The code, the figures and the documents were written with the help of an AI model (Claude, by Anthropic), then run and checked with the tests in `tests/`. Read the code before relying on it. The author is responsible for what is published here.

## Licences

- Software: MIT (`LICENSE`).
- Hardware files (`hardware/`): to be released under a CERN Open Hardware Licence. The variant is not chosen yet. See `LICENSES/CERN-OHL-NOTE.md`.
- Gratings, light source and other components are bought, not made.

## Cite

See `CITATION.cff`.

<!-- Add the link to the companion Medium article here when it is published. -->
