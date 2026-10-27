# Component tests

A standalone PLECS project that tests the library components (`Switches/D`, `Switches/FET`, …) on their own. Each test model runs in two model depths (ideal, real) with a device parameter set. Python reports the figures of every run and writes all waveforms into one HTML report.

## Requirements

- **PLECS:**
  - the XML-RPC server on port 1080;
  - the libraries of `0000_libraries/Plecs` on the PLECS library path;
  - the `Thermal Lib` folder on the thermal description path.
- **Python:** numpy and plotly.

## Running

```bash
python lib/ctest.py                              # every test, every mode
python lib/ctest.py mosfet real                  # one test, one mode
python lib/ctest.py diode --device C3M0021120K   # another device of DEVICES
python lib/ctest.py choke_pfc choke_cmc          # the choke tests (chokes of CHOKES)
```

Each run prints one line of figures. The CSV of each run goes to `data/csv/<test>_<device>_<mode>.csv`. The report, with a table of figures and the waveforms of every mode, goes to `data/html/ComponentTest_<time>.html`.

The models also run from the PLECS GUI and include a scope. Their initialization commands hold the real-mode parameters (a snapshot of `lib/parameters.py`); `ctest.py` always passes the current values as ModelVars. `KEEP_OPEN` in `parameters.py` leaves the models open in PLECS after a run so you can look at the scopes.

> [!NOTE]
> PLECS caches libraries. After you edit a library file, restart PLECS before testing.

## Layout

```
lib/parameters.py   device library (DEVICES), bench settings (Bench), model modes (MODES), test registry (TESTS)
lib/ctest.py        class ComponentTest: runs a test model, evaluates it (<test>_figures), writes the report
models/             test models, one per test (reference the 0000_libraries/Plecs libraries)
data/               results (git-ignored)
```

## Model modes

| Mode | FET (`Switches/FET`) | Coss (`Passives/C`) | Diode (`Switches/D`) | Choke (`Magnatic Components/Choke`) |
|---|---|---|---|---|
| `ideal` | 1 Ideal | 1 Ideal | 1 Ideal | 1 Ideal (L1, L2, Lm) |
| `real` | 2 Real (physical equivalent circuit) | 2 Real (ESR + ESL) | 2 Real (charge-control recovery) | 2 Real (T-model + R1, R2, Rm) |

## Tests

The diode and MOSFET tests use a double pulse on an inductive load (`Bench`):
1. Pulse 1 ramps the load current to `IF`.
2. The current freewheels for `t_off`.
3. Pulse 2 turns on against the freewheeling diode (reverse recovery, turn-on) and then turns off at `IF`.

| Test | Device under test | Circuit | Figures |
|---|---|---|---|
| `diode` | `Switches/D` with the device's `therm_body_diode` (junction capacitance = the device's Coss table) | ideal switch with RC snubber (`Rsn`, `Csn`), loop inductance `Ls_D` (sets the datasheet di/dt), RC damper across the diode outside its ammeter (`Rd`, `Cd`) | forward current and drop, blocking voltage, Irrm, Qrr, trr (to 25 % of Irrm) |
| `mosfet` | low-side `Switches/FET`; the high-side FET of the same device is held off and freewheels through its body diode | loop inductance `Ls_FET` with damping resistor (`Rs_FET` = 1 Ω for ideal, `Rs_FET_phys` = 100 Ω for real) | on current, Rds(on), off voltage, Eon, Eoff, turn-on current peak, turn-off voltage peak, high-side recovery peak |
| `choke_pfc`, `choke_cmc` | `Magnatic Components/Choke` with a choke of `CHOKES` (PFC boost choke, k = 0.02; EMI CMC, k = 0.995) | winding 1: `Ch_V0` + `Ch_Va`·sin(2π·`Ch_f`·t) through `Ch_Rs`; winding 2: `Ch_Rload`; both windings start at `Ch_i1`, `Ch_i2`. The same bench with the PLECS block *Mutual Ind. 2* runs alongside. | winding current errors vs the analytic solution and vs PLECS, PLECS vs analytic, i1(0), i2(0), coupling k, pass |

#### Choke accuracy test

The choke must realize v = R·i + L·di/dt with L = [L1 Lm; Lm L2] and R = [R1 Rm; Rm R2] (Ideal: R = 0), currents into the dotted terminals w1a and w2a. `ComponentTest.choke_analytic` integrates this equation, from i(0) = [i1 i2], with the terminal voltages the choke actually saw in the run. The error to the simulated currents therefore tests the choke alone: inductances, resistances, coupling sign, and initial currents, independent of the sources and the load.

- `i1 / i2 vs analytic`: the verdict. `pass` is 1 when both stay below `Ch_tol` (0.5 % of the peak current). A correct model gives about 0.002 %. A 1 % error in L1 or Lm gives 1.4 % to 2 % (PFC choke) or 87 % to 193 % (CMC); a 20 % error in R1 gives 3 % to 5 %.
- `i1 / i2 vs PLECS`: the same bench with *Mutual Ind. 2*. Its Real model is the same T-network, so this mainly cross-checks the Ideal configuration (MutInductor).
- `PLECS vs analytic`: the reference block against the equation. It checks the test itself and should be ~0.

### Results (C3M0021120K, 400 V / 50 A, 25 °C)

| | ideal | real |
|---|---|---|
| Diode Vf / Irrm / trr / Qrr | 4.75 V / – / – / – | 5.12 V / 30 A / 45 ns / 606 nC |
| MOSFET Rds(on) / Eon / Eoff | – / – / – | 21.9 mΩ / 464 µJ / 199 µJ |

- In ideal mode the switches commute instantly, so the edge peaks only reflect the test circuit.
- In real mode the losses come from v·i of the physical model (switching and conduction together).
- Qrr includes the Coss charge, which is how the datasheet's 928 nC (at 175 °C) is measured too.

## Adding a component

1. **Device data:** add a parameter set to `DEVICES` in `lib/parameters.py`. Keep the struct the library block expects, and give every value a `#? [unit] - comment`.
2. **Model:** build `models/test_<name>.plecs`.
   - Reference the library block, with its mask parameter set to a ModelVars name (e.g. `SW`, `BD`) and its `Configuration` set to `<name>.Config`.
   - Take every bench value from `Bench`.
   - Write time + the signals to a To File block whose file name is `Out.file`, with *Evaluate* on.
   - Use local Goto/From tags (scope *Schematic*).
3. **Registry:** add the test to `TESTS`: model name, struct name and the signal order of the To File.
4. **Evaluation:** add a `<test>_figures(r)` method to `ComponentTest` that returns `{name [unit]: value}`. If the component's block configurations depend on the mode, extend `MODES` and `ComponentTest.model_vars`.
