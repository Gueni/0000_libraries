#!/usr/bin/env python
# coding=utf-8
#? -------------------------------------------------------------------------------
#?
#? Name:        ctest.py
#? Purpose:     Component tests (standalone): runs the PLECS test models of models/ through the XML-RPC server with a
#?              device of parameters.DEVICES in each model mode, prints the figures of every run and writes the
#?              waveforms of all runs to data/html/ComponentTest_<time>.html.
#?              usage: python lib/ctest.py [test ...] [mode ...] [--device NAME]   (default: every test, every mode)
#?
#? Author:      Mohamed Gueni ( mohamedgueni@outlook.com)
#?
#? Created:     10/21/2026
#? Licence:     Refer to the LICENSE file
#? -------------------------------------------------------------------------------
#? -------------------------------------------------------------------------------
import  sys
import  copy
import  time
import  xmlrpc.client

import  numpy                       as      np
import  plotly.graph_objects        as      go

import  parameters                  as      prm
from    plotly.subplots             import  make_subplots
#?----------------------------------------------------------------------------------------------------------------------------------------
class ComponentTest:
    """Runs the component test models and evaluates their waveforms (one <test>_figures method per test of prm.TESTS)."""

    def __init__(self, device=prm.DEVICE):
        self.server     = xmlrpc.client.ServerProxy(prm.URL)
        self.device     = device

    #?------------------------------------------------------------------------------------------------------------------------------------
    #? Model variables and simulation
    #?------------------------------------------------------------------------------------------------------------------------------------
    def model_vars(self, test, mode):
        """ModelVars of a test in a mode: the device (or its body diode) with the configurations of MODES[mode]."""
        cfg             = prm.MODES[mode]
        if 'choke' in prm.TESTS[test]:                                          # choke: DUT struct CH, PLECS reference struct CHR
            bench       = dict(prm.Bench)
            ch          = copy.deepcopy(prm.CHOKES[prm.TESTS[test]['choke']])
            ch.update(Config=cfg['Choke'], i1=bench['Ch_i1'], i2=bench['Ch_i2'])
            ref         = dict(ch)
            if cfg['Choke'] == 1:                                               # Ideal choke: no winding / mutual resistance
                ref.update(R1=0, R2=0, Rm=0)
            return {'Bench': bench, 'CH': ch, 'CHR': ref}
        sw              = copy.deepcopy(prm.DEVICES[self.device])
        sw['Config']    = cfg['FET']
        sw['Coss']['Config']             = cfg['Coss']
        sw['therm_body_diode']['Config'] = cfg['BD']
        bench           = dict(prm.Bench)
        if test == 'diode':                                                     # body diode alone: it keeps the device output capacitance
            bd          = sw['therm_body_diode']
            bd['Cj']    = {'V': sw['Cap']['V'], 'C': sw['Cap']['Coss']}
            return {'Bench': bench, 'BD': bd}
        bench['Rs_FET'] = prm.Bench['Rs_FET_phys'] if mode == 'real' else prm.Bench['Rs_FET']
        return {'Bench': bench, 'SW': sw}

    def run(self, test, mode):
        """Simulate one test: {'t': time, <signal>: values} (the model's To File writes time + signals to a CSV)."""
        t               = prm.TESTS[test]
        csv             = prm.DATA_DIR / "csv" / f"{test}_{self.device}_{mode}.csv"
        csv.parent.mkdir(parents=True, exist_ok=True)
        mv              = dict(self.model_vars(test, mode), Out={'file': csv.as_posix()})
        self.server.plecs.load((prm.MODEL_DIR / f"{t['model']}.plecs").as_posix())
        try:
            self.server.plecs.simulate(t['model'], {'ModelVars': mv})
        finally:
            if not prm.KEEP_OPEN:
                self.server.plecs.close(t['model'])                             # closed: the model file is reloaded on the next run
        d               = np.loadtxt(csv, delimiter=',', ndmin=2)
        r               = dict({'t': d[:, 0]}, **{s: d[:, i + 1] for i, s in enumerate(t['signals'])})
        if 'choke' in t:
            r['par']    = mv['CHR']                                             # parameters of the analytic solution (R = 0 in ideal mode)
        return r

    #?------------------------------------------------------------------------------------------------------------------------------------
    #? Evaluation
    #?------------------------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def events():
        """Pulse times: end of pulse 1 (T1), start of pulse 2 (T2), end of pulse 2 (T3)."""
        b               = prm.Bench
        T1              = b['IF'] * b['Lload'] / b['Vdc']
        return T1, T1 + b['t_off'], T1 + b['t_off'] + b['t_on2']

    @staticmethod
    def window(t, a, b):
        return (t >= a) & (t <= b)

    @staticmethod
    def integral(t, y, m):
        return float(np.trapezoid(y[m], t[m])) if m.sum() > 1 else 0.0

    @staticmethod
    def diode_figures(r):
        """Forward drop, blocking voltage and reverse recovery (Irrm, Qrr, trr to 25 % of Irrm) at the second turn-on."""
        t, T                            = r['t'], ComponentTest.events()
        fw                              = ComponentTest.window(t, T[1] - 0.2 * prm.Bench['t_off'], T[1])  # end of freewheeling
        blk                             = ComponentTest.window(t, 0.2 * T[0], 0.9 * T[0])                 # pulse 1: diode blocks
        i                               = r['Id'] * np.sign(np.mean(r['Id'][fw]) or 1)                    # forward current > 0
        v                               = r['Vd'] * -np.sign(np.mean(r['Vd'][blk]) or 1)                  # anode - cathode
        rec                             = ComponentTest.window(t, T[1], T[2])
        tr, ir                          = t[rec], i[rec]
        irr, qrr, trr                   = 0.0, 0.0, 0.0
        if tr.size > 2 and ir.min() < 0:
            k                           = int(np.argmin(ir))                                              # reverse peak
            irr                         = -ir[k]
            z                           = np.where(ir[:k] >= 0)[0]                                        # last zero crossing before it
            a                           = z[-1] if z.size else 0
            b                           = k + int(np.argmax(ir[k:] > -0.25 * irr))                        # back to 25 % of Irrm
            trr                         = tr[b] - tr[a]
            qrr                         = ComponentTest.integral(tr, np.maximum(-ir, 0), np.arange(tr.size) <= b)
        return {'IF [A]': i[fw].mean(), 'Vf [V]': v[fw].mean(), 'Vr [V]': -v[blk].mean(),
                'Irrm [A]': irr, 'Qrr [nC]': qrr * 1e9, 'trr [ns]': trr * 1e9}

    @staticmethod
    def mosfet_figures(r):
        """Conduction, turn-on / turn-off energies and peaks, and the recovery of the high-side (body diode) current."""
        t, T                            = r['t'], ComponentTest.events()
        on                              = ComponentTest.window(t, 0.5 * T[0], T[0])                       # pulse 1, DUT on
        off                             = ComponentTest.window(t, T[0] + 0.5 * prm.Bench['t_off'], T[1])  # DUT off
        i                               = r['Id'] * np.sign(np.mean(r['Id'][on]) or 1)
        v                               = r['Vds'] * np.sign(np.mean(r['Vds'][off]) or 1)
        ih                              = r['Ihs'] * -np.sign(np.mean(r['Ihs'][off]) or 1)                # freewheeling < 0
        won                             = ComponentTest.window(t, T[1], T[1] + 1e-6)
        woff                            = ComponentTest.window(t, T[2], T[2] + 1e-6)
        return {'Id on [A]': i[on][-1], 'Vds off [V]': v[off].mean(), 'Rds_on [mOhm]': 1e3 * v[on][-1] / i[on][-1],
                'Eon [uJ]': ComponentTest.integral(t, v * i, won) * 1e6, 'Eoff [uJ]': ComponentTest.integral(t, v * i, woff) * 1e6,
                'Id peak on [A]': i[won].max() if won.any() else 0.0, 'Vds peak off [V]': v[woff].max() if woff.any() else 0.0,
                'HS Irrm [A]': ih[won].max() if won.any() else 0.0}

    @staticmethod
    def choke_analytic(t, v1, v2, p):
        """Exact 2-winding currents for the measured terminal voltages: L di/dt = v - R i, L = [L1 Lm; Lm L2],
        R = [R1 Rm; Rm R2], i(0) = [i1 i2], integrated with the trapezoidal rule (A-stable) between the output samples."""
        L                               = np.array([[p['L1'], p['Lm']], [p['Lm'], p['L2']]])
        R                               = np.array([[p['R1'], p['Rm']], [p['Rm'], p['R2']]])
        Li, I2                          = np.linalg.inv(L), np.eye(2)
        A, v                            = Li @ R, np.column_stack((v1, v2))
        i                               = np.zeros((t.size, 2))
        i[0]                            = [p['i1'], p['i2']]
        for k in range(t.size - 1):
            h                           = t[k + 1] - t[k]
            i[k + 1]                    = i[k] if h <= 0 else np.linalg.solve(I2 + 0.5 * h * A, (I2 - 0.5 * h * A) @ i[k] + 0.5 * h * Li @ (v[k] + v[k + 1]))
        return i[:, 0], i[:, 1]

    @staticmethod
    def choke_figures(r):
        """Winding currents vs the analytic solution (driven by the voltages the choke saw) and vs PLECS Mutual Ind. 2 on the
        same bench; errors in % of the peak current. The PLECS reference vs analytic row checks the method itself."""
        t, p                            = r['t'], r['par']
        err                             = lambda x, y: 100 * np.max(np.abs(x - y)) / max(np.max(np.abs(y)), 1e-12)
        a1, a2                          = ComponentTest.choke_analytic(t, r['v1'], r['v2'], p)
        b1, b2                          = ComponentTest.choke_analytic(t, r['v1_ref'], r['v2_ref'], p)
        e_ana                           = max(err(r['i1'], a1), err(r['i2'], a2))
        return {'i1 vs analytic [%]': err(r['i1'], a1), 'i2 vs analytic [%]': err(r['i2'], a2),
                'i1 vs PLECS [%]': err(r['i1'], r['i1_ref']), 'i2 vs PLECS [%]': err(r['i2'], r['i2_ref']),
                'PLECS vs analytic [%]': max(err(r['i1_ref'], b1), err(r['i2_ref'], b2)),
                'i1(0) [A]': r['i1'][0], 'i2(0) [A]': r['i2'][0], 'k [-]': p['Lm'] / np.sqrt(p['L1'] * p['L2']),
                'pass [1/0]': float(e_ana <= prm.Bench['Ch_tol'])}

    choke_pfc_figures                   = choke_figures
    choke_cmc_figures                   = choke_figures

    #?------------------------------------------------------------------------------------------------------------------------------------
    #? Report
    #?------------------------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def figure(test, device, results):
        """Waveforms of a test, one row per signal, every mode overlaid."""
        signals                         = prm.TESTS[test]['signals']
        fig                             = make_subplots(rows=len(signals), cols=1, shared_xaxes=True, subplot_titles=signals)
        for mode, r in results.items():
            for k, s in enumerate(signals, start=1):
                fig.add_trace(go.Scatter(x=r['t'] * 1e6, y=r[s], name=f'{mode} {s}', legendgroup=mode), row=k, col=1)
        fig.update_layout(title=f'{test} test, {device}', height=250 * len(signals))
        fig.update_xaxes(title_text='t [us]', row=len(signals), col=1)
        return fig

    @staticmethod
    def write_html(path, title, figures, tables):
        """Figures (first one loads plotly.js) and the figure tables of every run in one HTML page."""
        rows                            = ''.join(f'<h3>{name}</h3><table border="1" cellpadding="4"><tr>'
                                                  + ''.join(f'<th>{k}</th>' for k in ['mode'] + list(next(iter(tab.values()))))
                                                  + '</tr>' + ''.join('<tr><td>' + m + '</td>' + ''.join(f'<td>{v:.2f}</td>' for v in f.values()) + '</tr>'
                                                                      for m, f in tab.items()) + '</table>'
                                                  for name, tab in tables.items() if tab)
        plots                           = ''.join(f.to_html(full_html=False, include_plotlyjs='cdn' if i == 0 else False)
                                                  for i, f in enumerate(figures))
        path.write_text(f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>{title}</title></head>'
                        f'<body style="font-family:sans-serif"><h2>{title}</h2>{rows}{plots}</body></html>', encoding='utf-8')

    #?------------------------------------------------------------------------------------------------------------------------------------
    def main(self, tests, modes):
        figures, tables                 = [], {}
        for test in tests:
            results, tab                = {}, {}
            for mode in modes:
                t0                      = time.time()
                try:
                    r                   = self.run(test, mode)
                except xmlrpc.client.Fault as f:
                    print(f"{test:7s} {mode:9s} FAILED: {f.faultString.splitlines()[0][:200]}")
                    continue
                results[mode]           = r
                tab[mode]               = getattr(ComponentTest, f'{test}_figures')(r)
                print(f"{test:7s} {mode:9s} {time.time() - t0:5.1f} s | " + ' | '.join(f'{k} {v:8.2f}' for k, v in tab[mode].items()))
            if results:
                figures.append(ComponentTest.figure(test, self.device, results))
                tables[f'{test} test, {self.device}'] = tab
        if figures:
            html                        = prm.DATA_DIR / "html" / f"ComponentTest_{time.strftime('%Y%m%d%H%M%S')}.html"
            html.parent.mkdir(parents=True, exist_ok=True)
            ComponentTest.write_html(html, f'Component tests, {self.device}', figures, tables)
            print(f"Report: {html}")
#?----------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    args                                = sys.argv[1:]
    device                              = args[args.index('--device') + 1] if '--device' in args else prm.DEVICE
    words                               = [a.lower() for a in args if not a.startswith('--') and a != device]
    tests                               = [a for a in words if a in prm.TESTS] or list(prm.TESTS)
    modes                               = [a for a in words if a in prm.MODES] or list(prm.MODES)
    ComponentTest(device).main(tests, modes)
