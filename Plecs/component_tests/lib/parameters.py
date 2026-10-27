#!/usr/bin/env python
# coding=utf-8
#? -------------------------------------------------------------------------------
#?
#? Name:        parameters.py
#? Purpose:     Component test project (standalone): device library, test bench settings, model modes and the test
#?              registry. Every value of DEVICES / Bench is passed to the PLECS test models as ModelVars.
#?              To test another component: add its parameter set to DEVICES, its model to models/ and an entry to TESTS
#?              (see README.md).
#?
#? Author:      Mohamed Gueni ( mohamedgueni@outlook.com)
#?
#? Created:     10/21/2026
#? Licence:     Refer to the LICENSE file
#? -------------------------------------------------------------------------------
#? -------------------------------------------------------------------------------
from     pathlib     import   Path
#!----------------------------------------------------------------------------------------------------------------------------------------
LIB_DIR        =  Path(__file__).resolve().parent                    # <project>/lib
ROOT_DIR       =  LIB_DIR.parent                                     # <project>
MODEL_DIR      =  ROOT_DIR / "models"                                # test models (reference the Switches / Passives ... libraries)
DATA_DIR       =  ROOT_DIR / "data"                                  # results: data/csv, data/html
URL            =  "http://localhost:1080/RPC2"                       # PLECS XML-RPC server
KEEP_OPEN      =  True                                               # leave the test models open in PLECS after a run (to look at the scopes)
#!----------------------------------------------------------------------------------------------------------------------------------------
#! Device library: one parameter set per device (Switches/FET struct; its body diode is the Switches/D struct therm_body_diode).
#! The block configurations ('Config') are set by the mode of each run (MODES), the values here are the defaults.
DEVICES        =  {
                  'C3M0021120K'    : {                                                                                                                # Wolfspeed C3M0021120K, 1200 V / 100 A / 21 mOhm SiC MOSFET 
                     'Config'         : 1,                                                                                            #? [/]      - FET config: 1 Ideal, 2 Real (physical equivalent circuit, fields Drv ... Th below)
                     'therm_mosfet'   : 'file:C3M0021120K',                                                                                           #? [/]      - Thermal description of the switch (Thermal Lib)
                     'Rgon'           : 2.5,                                                                                                          #? [Ohm]    - External turn-on gate resistance
                     'Rgoff'          : 2.5,                                                                                                          #? [Ohm]    - External turn-off gate resistance
                     'ron_mosfet'     : 21e-3,                                                                                                        #? [Ohm]    - R_DS(on) at 25 °C (C3M0021120K: 21 mOhm typ, 1200 V / 100 A)
                     'Iinit'          : 0,                                                                                                            #? [A]      - Initial current through the switch
                     'Coss'           : {                                                                                                             # output capacitance (Passives/C)
                        'Config'  : 1,                                                                                             #? [/]     - Coss config (Passives/C, not used by the FET configs): 1 Ideal, 2 Real (ESR + ESL)
                        'Cap_s'   : 180e-12,                                                                                                          #? [F]      - Coss at 800 V (C3M0021120K: 180 pF)
                        'Resr_s'  : 0.5,                                                                                                              #? [Ohm]    - Equivalent series resistance (damps the Coss loop)
                        'Lesl_s'  : 2e-9,                                                                                                             #? [H]      - Equivalent series inductance (package / power loop)
                        'Npara'   : 1,                                                                                                                #? [/]      - Number of parallel capacitors
                        'Nseri'   : 1,                                                                                                                #? [/]      - Number of series capacitors
                        'Vinit'   : 0,                                                                                                                #? [V]      - Initial voltage
                        'Iinit'   : 0                                                                                                                 #? [A]      - Initial current
                     },
                     'therm_body_diode': {                                                                                                            # body diode (Switches/D), used by FET config 2 (Real)
                        'Config'        : 1,                                                                                         #? [/]     - Diode config: 1 Ideal (vf_diode, ron_diode), 2 Real (charge-control recovery)
                        #! ---- config 1: Ideal (vf_diode, ron_diode)
                        'therm_diode'   : 'file:C3M0021120K_bodydiode',                                                                               #? [/]      - Thermal description of the body diode (Thermal Lib)
                        'vf_diode'      : 4.5,                                                                                                        #? [V]      - Body diode forward voltage
                        'ron_diode'     : 5e-3,                                                                                                       #? [Ohm]    - Body diode on-state resistance
                        't_init'        : 25,                                                                                                         #? [°C]     - Initial junction temperature of the body diode
                        'num_par_diode' : 1,                                                                                                          #? [/]      - Number of parallel diodes
                        'Case_Cth'      : 0,                                                                                                          #? [J/K]    - Thermal capacitance of the diode case node (0: no extra thermal state, ~4x faster)
                        'Case_Tinit'    : 25,                                                                                                         #? [°C]     - Initial temperature of the diode case node
                        'Case_Amb_rth'  : 0.1,                                                                                                        #? [K/W]    - Thermal resistance diode case -> switch thermal port
                        #! ---- config 2: Real (charge-control reverse recovery), used as a die-level body diode
                        'nPara'         : 1,                                                                                                          #? [/]      - Number of parallel diodes (= nPara of the switch)
                        'VI'            : {                                                                                                           # forward curve at Vgs = -4 V (vendor table), I = 0 column = knee voltage
                           'T'          : [-40, 25, 175],                                                                                             #? [°C]     - Temperature axis
                           'I'          : [0, 0.5, 2, 5, 8, 15, 20, 30, 40, 60, 80, 100, 120, 140, 160, 180, 200],                                    #? [A]      - Current axis
                           'V'          : [[2.85, 3.00, 3.50, 3.90, 4.15, 4.60, 4.77, 5.10, 5.42, 5.90, 6.30, 6.59, 6.90, 7.14, 7.40, 7.60, 7.84],    #? [V]      - Forward voltage, one row per temperature
                                           [2.75, 2.90, 3.15, 3.50, 3.75, 4.10, 4.30, 4.66, 4.89, 5.37, 5.77, 6.10, 6.40, 6.65, 6.90, 7.13, 7.35],
                                           [2.30, 2.45, 2.74, 3.10, 3.30, 3.60, 3.80, 4.12, 4.40, 4.78, 5.16, 5.46, 5.75, 6.00, 6.25, 6.47, 6.70]]
                        },
                        'Ron'           : 0.012,                                                                                                      #? [Ohm]    - Storage-phase branch resistance
                        'RR'            : {                                                                                                           # datasheet recovery test (its Qrr of 928 nC includes Coss -> trr + Irrm used)
                           'IF'         : 50,                                                                                                         #? [A]      - Forward current
                           'didt'       : 2600e6,                                                                                                     #? [A/s]    - Turn-off slope
                           'Irrm'       : 42,                                                                                                         #? [A]      - Peak reverse current (0 = no stored charge)
                           'trr'        : 34e-9,                                                                                                      #? [s]      - Reverse recovery time (0 -> Qrr used)
                           'Qrr'        : 0,                                                                                                          #? [C]      - Junction recovery charge
                           'Tmeas'      : 175,                                                                                                        #? [°C]     - Test junction temperature
                           'ktau'       : 2.0                                                                                                         #? [/]      - Lifetime temperature exponent
                        },
                        'Cj'            : {'V': [0], 'C': [1e-12]},                                                                                   #? [V],[F]  - Junction capacitance (already part of Coss)
                        'Roff'          : 1e9,                                                                                                        #? [Ohm]    - Leakage resistance
                        'Aval'          : {'Vbr': 0, 'Rav': 1},                                                                                       #? [V],[Ohm] - Disabled (avalanche is in the channel model)
                        'FR'            : {'Vfr': 0, 'IF': 1, 'tfr': 0},                                                                              #? [V],[A],[s] - No forward recovery
                        'Pkg'           : {'La': 0, 'Lk': 0, 'Rp': 100},                                                                              #? [H],[H],[Ohm] - No package: the FET package is in series
                        'Th'            : {'Rth': [1e-3], 'Cth': [1e-4], 'Tinit': 25}                                                                 #? [K/W],[J/K],[°C] - Die -> FET junction (same die: near zero)
                     },
                     'nPara'          : 1,                                                                                                            #? [/]      - Number of parallel switches
                     'T_init'         : 25,                                                                                                           #? [°C]     - Initial junction temperature
                     'Tamb'           : 25,                                                                                                           #? [°C]     - Ambient temperature
                     't_init'         : 25,                                                                                                           #? [°C]     - Initial temperature of the thermal chain
                     'rth_sw'         : 0.1,                                                                                                          #? [K/W]    - Thermal resistance junction -> case
                     'rth_ch'         : 0.1,                                                                                                          #? [K/W]    - Thermal resistance case -> heatsink (TIM)
                     'Rth'            : 0.2,                                                                                                          #? [K/W]    - Total thermal resistance junction -> heatsink
                     'foster_rth'     : [0.0472 ,0.0688],                                                                                             #? [/]      - Foster representation of the thermal resistance
                     'foster_cth'     : [0.95 , 2.4],                                                                                                 #? [/]      - Foster representation of the thermal capacitance
                     #! ---- FET config 2 (Real): physical equivalent circuit (datasheet Rev.4 + vendor Thermal Lib model)
                     'Drv'            : {                                                                                                             # gate driver (totem pole, separate on/off paths)
                        'Von'     : 15,                                                                                                               #? [V]      - Turn-on gate voltage
                        'Voff'    : -4,                                                                                                               #? [V]      - Turn-off gate voltage
                        'Rgon'    : 2.5,                                                                                                              #? [Ohm]    - External turn-on resistance incl. driver
                        'Rgoff'   : 2.5                                                                                                               #? [Ohm]    - External turn-off resistance incl. driver
                     },
                     'Pkg'            : {                                                                                                             # package parasitics (TO-247-4 estimates)
                        'Lg'      : 7e-9,                                                                                                             #? [H]      - Gate lead + bond wire
                        'Ld'      : 4.5e-9,                                                                                                           #? [H]      - Drain tab + bond
                        'Ls'      : 6e-9,                                                                                                             #? [H]      - Power source lead
                        'Lcs'     : 1e-9,                                                                                                             #? [H]      - Common source (gate + power loop); ~7 nH for a TO-247-3
                        'Lk'      : 6e-9,                                                                                                             #? [H]      - Kelvin source lead
                        'Rp'      : 100                                                                                                               #? [Ohm]    - Damping resistance across each lead inductance
                     },
                     'Rg_int'         : 3.3,                                                                                                          #? [Ohm]    - Internal gate resistance
                     'Ch'             : {                                                                                                             # channel (fitted to Fig. 1-3, 6, 11 and the vendor Vds(Id, Tj) tables)
                        'Vt0'     : 3.1058,                                                                                                           #? [V]      - Effective threshold at 25 °C
                        'aVt'     : 0,                                                                                                                #? [V/K]    - Threshold temperature coefficient
                        'nphi0'   : 0.38494,                                                                                                          #? [V]      - Subthreshold slope voltage at 25 °C
                        'K0'      : 4.9771,                                                                                                           #? [A/V²]   - Transconductance factor at 25 °C
                        'bK'      : 0.94102,                                                                                                          #? [/]      - K ~ (T/298 K)^bK
                        'Rd0'     : 3.2856e-3,                                                                                                        #? [Ohm]    - JFET/drift resistance at 25 °C
                        'bRd'     : 4.89,                                                                                                             #? [/]      - Rd ~ (T/298 K)^bRd
                        'Iq0'     : 220.62,                                                                                                           #? [A]      - Drift quasi-saturation current at 25 °C
                        'bIq'     : 0.09561,                                                                                                          #? [/]      - Iq ~ (T/298 K)^bIq
                        'theta'   : 0,                                                                                                                #? [1/V]    - Mobility degradation
                        'lambda'  : 1.1658e-4,                                                                                                        #? [1/V]    - Channel length modulation
                        'm'       : 2.7144                                                                                                            #? [/]      - Linear/saturation transition sharpness
                     },
                     'Cap'            : {                                                                                                             # capacitances (Fig. 17/18 at Vgs = 0 V)
                        'V'       : [0, 1, 2, 5, 10, 20, 30, 50, 75, 100, 150, 200, 300, 400, 600, 800, 1000, 1200],                                  #? [V]      - Voltage axis
                        'Coss'    : [c * 1e-12 for c in [4300, 3300, 2700, 1900, 1300, 950, 820, 650, 560, 500, 420, 360, 280, 235, 195, 182, 180, 180]], #? [F] - Output capacitance
                        'Crss'    : [c * 1e-12 for c in [1000, 800, 600, 250, 80, 45, 38, 30, 26, 23, 19, 17, 14.5, 13, 12, 12, 12, 12.3]],           #? [F]      - Reverse transfer capacitance
                        'Ciss'    : 4818e-12,                                                                                                         #? [F]      - Input capacitance ...
                        'Vciss'   : 1000,                                                                                                             #? [V]      - ... measured at this Vds
                        'Cgd_ox'  : 3.4e-9,                                                                                                           #? [F]      - Gate-drain oxide capacitance for Vdg < 0 (from Fig. 12)
                        'kdyn'    : 1.7,                                                                                                              #? [/]      - Large-signal Cgd factor with inverted channel (from Fig. 25/27)
                        'Vacc'    : 1.0                                                                                                               #? [V]      - Cgd accumulation transition width
                     },
                     'Leak'           : {
                        'Idss'    : 1e-6,                                                                                                             #? [A]      - Drain leakage ...
                        'Vdss'    : 1200,                                                                                                             #? [V]      - ... at this Vds
                        'Igss'    : 10e-9,                                                                                                            #? [A]      - Gate leakage ...
                        'Vgss'    : 15                                                                                                                #? [V]      - ... at this Vgs
                     },
                     'Aval'           : {
                        'Vbr'     : 1500,                                                                                                             #? [V]      - Avalanche onset (datasheet guarantees >= 1200 V)
                        'Rav'     : 0.5                                                                                                               #? [Ohm]    - Avalanche dynamic resistance
                     },
                     'Th'             : {                                                                                                             # junction -> Ambient port (vendor Cauer chain, sum 0.324 K/W)
                        'Rth'     : [0.0441, 0.104, 0.06378, 0.1121],                                                                                 #? [K/W]    - Cauer resistances
                        'Cth'     : [0.002214, 0.0126, 0.03416, 0.1294],                                                                              #? [J/K]    - Cauer capacitances
                        'Tinit'   : 25                                                                                                                #? [°C]     - Initial temperature
                     }
                  }
               }
#!----------------------------------------------------------------------------------------------------------------------------------------
#! Model depth of a run: block configurations per mode.
#!    FET: Switches/FET 1 Ideal, 2 Real (physical equivalent circuit) | Coss: Passives/C 1 Ideal, 2 Real (ESR + ESL)
#!    BD : Switches/D 1 Ideal, 2 Real (charge-control reverse recovery)
#!    Choke: Magnatic Components/Choke 1 Ideal (L1, L2, Lm), 2 Real (+ R1, R2, Rm)
MODES          =  {
                  'ideal'           : {'FET': 1, 'Coss': 1, 'BD': 1, 'Choke': 1},                                                                       #? [/]     - Ideal switch, ideal diode (no recovery), ideal choke
                  'real'            : {'FET': 2, 'Coss': 2, 'BD': 2, 'Choke': 2}                                                                        #? [/]     - Physical equivalent circuit, physical diode (charge-control recovery), real choke
               }
#!----------------------------------------------------------------------------------------------------------------------------------------
#! Choke library (Magnatic Components/Choke struct). Coupled 2-winding inductor: v = R*i + L*di/dt with
#! L = [L1 Lm; Lm L2], R = [R1 Rm; Rm R2] (Ideal: R = 0), currents into the dotted terminals w1a / w2a.
CHOKES         =  {
                  'PFC_Choke'      : {                                                                                                                # PFC boost choke of the 1 kW TPB PFC (weak coupling, k = 0.02)
                     'Config'       : 2,                                                                                                              #? [/]      - Set by the mode (MODES)
                     'L1'           : 240e-6,                                                                                                         #? [H]      - Self inductance of winding 1
                     'L2'           : 10e-6,                                                                                                          #? [H]      - Self inductance of winding 2
                     'R1'           : 0.01,                                                                                                           #? [Ohm]    - Resistance of winding 1
                     'R2'           : 0.01,                                                                                                           #? [Ohm]    - Resistance of winding 2
                     'Lm'           : 1e-6,                                                                                                           #? [H]      - Mutual inductance
                     'Rm'           : 0.001,                                                                                                          #? [Ohm]    - Mutual resistance
                     'i1'           : 0,                                                                                                              #? [A]      - Initial current of winding 1 (the test sets Bench.Ch_i1)
                     'i2'           : 0                                                                                                               #? [A]      - Initial current of winding 2 (the test sets Bench.Ch_i2)
                  },
                  'CMC'            : {                                                                                                                # EMI common-mode choke of the 1 kW TPB PFC (tight coupling, k = 0.995)
                     'Config'       : 2,                                                                                                              #? [/]      - Set by the mode (MODES)
                     'L1'           : 4.7e-3,                                                                                                         #? [H]      - Self inductance of winding 1
                     'L2'           : 4.7e-3,                                                                                                         #? [H]      - Self inductance of winding 2
                     'R1'           : 30e-3,                                                                                                          #? [Ohm]    - Resistance of winding 1
                     'R2'           : 30e-3,                                                                                                          #? [Ohm]    - Resistance of winding 2
                     'Lm'           : 0.995 * 4.7e-3,                                                                                                 #? [H]      - Mutual inductance
                     'Rm'           : 0,                                                                                                              #? [Ohm]    - Mutual resistance
                     'i1'           : 0,                                                                                                              #? [A]      - Initial current of winding 1 (the test sets Bench.Ch_i1)
                     'i2'           : 0                                                                                                               #? [A]      - Initial current of winding 2 (the test sets Bench.Ch_i2)
                  }
               }
#!----------------------------------------------------------------------------------------------------------------------------------------
#! Test benches: double pulse on an inductive load. Pulse 1 ramps the load current to IF, the DUT then freewheels / is
#! off for t_off, pulse 2 turns on against it (diode reverse recovery, FET turn-on) for t_on2, then the FET turns off at IF.
Bench          =  {
                  'Vdc'             : 400,                                                                                                               #? [V]     - DC bus voltage
                  'IF'              : 50,                                                                                                                #? [A]     - Load current at the switching events (pulse 1 length = IF * Lload / Vdc)
                  'Lload'           : 100e-6,                                                                                                            #? [H]     - Load inductance
                  'Ls_D'            : 154e-9,                                                                                                            #? [H]     - Diode test loop inductance: Vdc / Ls = 2.6 A/ns, the datasheet recovery di/dt (ideal switch)
                  'Ls_FET'          : 20e-9,                                                                                                             #? [H]     - MOSFET test power loop inductance
                  'Rs_FET'          : 1,                                                                                                                 #? [Ohm]   - Damping resistor across Ls_FET, ideal mode (path for its current when the switch opens instantly)
                  'Rs_FET_phys'     : 100,                                                                                                               #? [Ohm]   - Same, real mode (>> loop impedance, does not bypass Ls during the ns transitions)
                  'Rsn'             : 3.9,                                                                                                               #? [Ohm]   - Diode test: RC snubber across the ideal switch (takes the Ls_D current when it opens) ...
                  'Csn'             : 10e-9,                                                                                                             #? [F]     - ... snubber capacitance (damping ~0.5 with Ls_D)
                  'Rd'              : 22,                                                                                                                #? [Ohm]   - Diode test: RC damper across the diode (outside its ammeter) ~ sqrt(Ls_D / Coss) ...
                  'Cd'              : 1e-9,                                                                                                              #? [F]     - ... damper capacitance (> Coss)
                  't_off'           : 5e-6,                                                                                                              #? [s]     - Time between the two pulses
                  't_on2'           : 3e-6,                                                                                                              #? [s]     - Length of pulse 2
                  't_tail'          : 3e-6,                                                                                                              #? [s]     - Simulated time after pulse 2
                  'Tamb'            : 25,                                                                                                                #? [°C]    - Ambient (heat port) temperature
                  'maxStep'         : 1e-7,                                                                                                              #? [s]     - Maximum solver step
                  'relTol'          : 1e-4,                                                                                                              #? [/]     - Solver relative tolerance
                  #! Choke test: winding 1 driven by Ch_V0 + Ch_Va*sin(2*pi*Ch_f*t) through Ch_Rs, winding 2 loaded with Ch_Rload,
                  #! both windings start with a current (Ch_i1, Ch_i2). DUT and the PLECS reference (Mutual Ind. 2) run side by side.
                  'Ch_V0'           : 10,                                                                                                                #? [V]     - DC part of the winding 1 source
                  'Ch_Va'           : 20,                                                                                                                #? [V]     - Amplitude of the AC part
                  'Ch_f'            : 10e3,                                                                                                              #? [Hz]    - Frequency of the AC part
                  'Ch_Rs'           : 1,                                                                                                                 #? [Ohm]   - Source resistance (bounds the DC current of the ideal choke)
                  'Ch_Rload'        : 1,                                                                                                                 #? [Ohm]   - Load of winding 2 (L2 / Rload >> solver step: the fast winding-2 transient stays resolved)
                  'Ch_i1'           : 1,                                                                                                                 #? [A]     - Initial current of winding 1 (into w1a)
                  'Ch_i2'           : -0.5,                                                                                                              #? [A]     - Initial current of winding 2 (into w2a)
                  't_choke'         : 2e-3,                                                                                                              #? [s]     - Simulated time (20 periods)
                  'Ch_maxStep'      : 2e-7,                                                                                                              #? [s]     - Maximum solver step (0.2 % of the period)
                  'Ch_relTol'       : 1e-6,                                                                                                              #? [/]     - Solver relative tolerance (the analytic comparison resolves < 0.1 %)
                  'Ch_tol'          : 0.5                                                                                                                #? [%]     - Pass limit of the current error vs the analytic solution
               }
#!----------------------------------------------------------------------------------------------------------------------------------------
#! Test registry: test -> model (models/<model>.plecs), ModelVars name of the device struct, signals written by the
#! model's To File (in order, after time). The evaluation is ComponentTest.<test>_figures in ctest.py.
TESTS          =  {
                  'diode'           : {'model': 'test_diode',  'struct': 'BD', 'signals': ['Id', 'Vd', 'g']},                                           #? [/]     - Switches/D: forward drop, blocking, reverse recovery
                  'mosfet'          : {'model': 'test_mosfet', 'struct': 'SW', 'signals': ['Id', 'Vds', 'Ihs', 'g']},                                   #? [/]     - Switches/FET: conduction, Eon / Eoff, peaks, body-diode recovery
                  'choke_pfc'       : {'model': 'test_choke',  'struct': 'CH', 'choke': 'PFC_Choke',                                                    #? [/]     - Magnatic Components/Choke (PFC boost choke) vs analytic solution and PLECS Mutual Ind. 2
                                       'signals': ['v1', 'i1', 'v2', 'i2', 'v1_ref', 'i1_ref', 'v2_ref', 'i2_ref']},
                  'choke_cmc'       : {'model': 'test_choke',  'struct': 'CH', 'choke': 'CMC',                                                          #? [/]     - Same, EMI common-mode choke (k = 0.995)
                                       'signals': ['v1', 'i1', 'v2', 'i2', 'v1_ref', 'i1_ref', 'v2_ref', 'i2_ref']}
               }
DEVICE         =  'C3M0021120K'                                                                                                                         # default device (python lib/ctest.py ... --device NAME)
#!----------------------------------------------------------------------------------------------------------------------------------------
