%% C3M0021120K - Wolfspeed SiC MOSFET 1200 V / 21 mOhm, TO-247-4
% Parameter set for the physical models in Switches.plecs:
%   C3M0021120K     -> FET block, configuration 3 "Physical Equivalent Circuit"
%   C3M0021120K_BD  -> the body diode (used by the FET block, D configuration 5)
%   C3M0021120K_D   -> the same diode data as a discrete D block (configuration 4)
%
% Sources: datasheet Rev. 4 (June 2025) and the vendor PLECS thermal model
% (Thermal Lib/C3M0021120K.xml, C3M0021120K_bodydiode.xml).
% Channel parameters were least-squares fitted to the output characteristics
% (Fig. 1-3, 6, 11) and the vendor Vds(Id, Tj) tables at Vgs = 15 V.
% kdyn and Cgd_ox were calibrated against the gate charge (Fig. 12) and the
% switching times / energies vs. Rg (Fig. 25, 27). Package inductances are
% typical TO-247-4 estimates, not datasheet values.
%
% Usage (PLECS initialization commands, path relative to the model):
%   run('Device Models/C3M0021120K.m');
%   PFC.SW = C3M0021120K;            % FET block parameter "Switch"

%% ---------------- body diode (die level, D configuration 5) ----------------
BD = struct();
BD.Config = 5;
BD.nPara  = 1;
% forward characteristic at Vgs = -4 V (vendor table); first current entry
% must be 0 and holds the knee voltage below which the junction blocks
BD.VI.T = [-40 25 175];                                          % [degC]
BD.VI.I = [0 0.5 2 5 8 15 20 30 40 60 80 100 120 140 160 180 200]; % [A]
BD.VI.V = [2.85 3.00 3.50 3.90 4.15 4.60 4.77 5.10 5.42 5.90 6.30 6.59 6.90 7.14 7.40 7.60 7.84;
           2.75 2.90 3.15 3.50 3.75 4.10 4.30 4.66 4.89 5.37 5.77 6.10 6.40 6.65 6.90 7.13 7.35;
           2.30 2.45 2.74 3.10 3.30 3.60 3.80 4.12 4.40 4.78 5.16 5.46 5.75 6.00 6.25 6.47 6.70]; % [V]
BD.Ron  = 0.012;      % storage-phase branch resistance (<= smallest slope of the curve) [Ohm]
% reverse recovery test (datasheet: VR = 800 V, IF = 50 A, 2600 A/us, Tj = 175 degC).
% The datasheet Qrr (928 nC) includes the Coss charge, so trr and Irrm are used.
BD.RR.IF    = 50;     % forward current before turn-off [A]
BD.RR.didt  = 2600e6; % turn-off current slope [A/s]
BD.RR.Irrm  = 42;     % peak reverse recovery current [A] (0 = no stored charge, Schottky)
BD.RR.trr   = 34e-9;  % reverse recovery time [s] (0 -> use Qrr)
BD.RR.Qrr   = 0;      % junction recovery charge [C] (used only if trr = 0)
BD.RR.Tmeas = 175;    % junction temperature of the recovery test [degC]
BD.RR.ktau  = 2.0;    % carrier lifetime temperature exponent, tau ~ T^ktau
BD.Cj.V  = 0;         % junction capacitance is part of the MOSFET Coss
BD.Cj.C  = 1e-12;
BD.Roff  = 1e9;       % leakage resistance [Ohm]
BD.Aval.Vbr = 0;      % avalanche handled by the MOSFET channel model
BD.Aval.Rav = 1;
BD.FR.Vfr = 0;        % no forward recovery for the SiC body diode
BD.FR.IF  = 1;
BD.FR.tfr = 0;
C3M0021120K_BD = BD;

%% ---------------- MOSFET (FET configuration 3) ----------------
SW = struct();
SW.Config = 3;
SW.nPara  = 1;        % number of devices in parallel

% gate driver (separate turn-on / turn-off paths, totem-pole output)
SW.Drv.Von   = 15;    % [V]
SW.Drv.Voff  = -4;    % [V]
SW.Drv.Rgon  = 2.5;   % external turn-on resistance incl. driver [Ohm]
SW.Drv.Rgoff = 2.5;   % external turn-off resistance incl. driver [Ohm]

% package parasitics (TO-247-4 estimates)
SW.Pkg.Lg  = 7e-9;    % gate lead + bond wire [H]
SW.Pkg.Ld  = 4.5e-9;  % drain tab + bond [H]
SW.Pkg.Ls  = 6e-9;    % power source lead [H]
SW.Pkg.Lcs = 1e-9;    % common source (shared bond wires) [H]; ~7 nH for TO-247-3
SW.Pkg.Lk  = 6e-9;    % Kelvin source lead [H]
SW.Pkg.Rp  = 100;     % damping resistance in parallel to each lead inductance [Ohm]

SW.Rg_int = 3.3;      % internal gate resistance [Ohm]

% channel model (fitted): Vt0 aVt nphi0 K0 bK Rd0 bRd Iq0 bIq theta lambda m
SW.Ch.Vt0    = 3.1058;    % effective threshold at 25 degC [V]
SW.Ch.aVt    = 0;         % threshold temperature coefficient [V/K]
SW.Ch.nphi0  = 0.38494;   % subthreshold slope voltage at 25 degC [V]
SW.Ch.K0     = 4.9771;    % transconductance factor at 25 degC [A/V^2]
SW.Ch.bK     = 0.94102;   % K ~ (T/298 K)^bK
SW.Ch.Rd0    = 3.2856e-3; % JFET/drift resistance at 25 degC [Ohm]
SW.Ch.bRd    = 4.8900;    % Rd ~ (T/298 K)^bRd
SW.Ch.Iq0    = 220.62;    % drift quasi-saturation current at 25 degC [A]
SW.Ch.bIq    = 0.095610;  % Iq ~ (T/298 K)^bIq
SW.Ch.theta  = 0;         % mobility degradation [1/V]
SW.Ch.lambda = 1.1658e-4; % channel length modulation [1/V]
SW.Ch.m      = 2.7144;    % linear/saturation transition sharpness

% capacitances (Fig. 17/18, Vgs = 0 V, f = 100 kHz)
SW.Cap.V    = [0 1 2 5 10 20 30 50 75 100 150 200 300 400 600 800 1000 1200];                      % [V]
SW.Cap.Coss = [4300 3300 2700 1900 1300 950 820 650 560 500 420 360 280 235 195 182 180 180]*1e-12; % [F]
SW.Cap.Crss = [1000 800 600 250 80 45 38 30 26 23 19 17 14.5 13 12 12 12 12.3]*1e-12;              % [F]
SW.Cap.Ciss   = 4818e-12; % input capacitance [F] ...
SW.Cap.Vciss  = 1000;     % ... measured at this Vds [V]
SW.Cap.Cgd_ox = 3.4e-9;   % gate-drain oxide capacitance for Vdg < 0 [F]
SW.Cap.kdyn   = 1.7;      % large-signal Cgd factor with inverted channel
SW.Cap.Vacc   = 1.0;      % Cgd accumulation transition width [V]

% leakage and avalanche
SW.Leak.Idss = 1e-6;  SW.Leak.Vdss = 1200;  % [A] at [V]
SW.Leak.Igss = 10e-9; SW.Leak.Vgss = 15;    % [A] at [V]
SW.Aval.Vbr  = 1500;  % avalanche onset [V] (datasheet guarantees >= 1200 V)
SW.Aval.Rav  = 0.5;   % avalanche dynamic resistance [Ohm]

% junction-to-case thermal impedance (vendor Cauer chain, sum = 0.324 K/W)
SW.Th.Rth   = [0.0441 0.104 0.06378 0.1121];     % [K/W]
SW.Th.Cth   = [0.002214 0.0126 0.03416 0.1294];  % [J/K]
SW.Th.Tinit = 25;                                % [degC]

SW.BodyDiode = BD;
C3M0021120K = SW;

%% ---------------- the diode data as a discrete diode (D configuration 4) ----------------
% Example of a stand-alone diode. For another part replace VI (forward curve
% per temperature), RR (datasheet recovery test), Cj (capacitance vs reverse
% voltage), FR (forward recovery peak at IF and its duration) and Th.
D = BD;
D.Config = 4;
D.Cj.V = SW.Cap.V;                     % stand-alone: junction capacitance = Coss
D.Cj.C = SW.Cap.Coss;
D.Aval.Vbr = 1500;
D.Aval.Rav = 0.5;
D.Pkg.La = 5e-9;                       % anode lead [H]
D.Pkg.Lk = 5e-9;                       % cathode lead [H]
D.Pkg.Rp = 100;                        % damping resistance [Ohm]
D.Th = SW.Th;
C3M0021120K_D = D;

clear BD SW D
