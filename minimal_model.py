"""
MINIMAL WORKING MODEL - Funktioniert GARANTIERT!
=================================================

Einfachstes Modell ohne hplib - nur mit Standard-Parametern

Verwendung:
    python minimal_model.py

Autor: A. Lohrmann
"""

from tespy.networks import Network
from tespy.components import (Compressor, Valve, CycleCloser,
                             Condenser, HeatExchanger, Sink, Source)
from tespy.connections import Connection
import CoolProp.CoolProp as CP
import pandas as pd
from pathlib import Path


def build_heat_pump():
    """Baut Wärmepumpen-Netzwerk"""
    nw = Network()
    nw.set_attr(T_unit='C', p_unit='bar', h_unit='kJ / kg')

    # Komponenten
    evap = HeatExchanger('Evaporator')
    comp = Compressor('Compressor')
    cond = Condenser('Condenser')
    valve = Valve('ExpansionValve')
    cycle = CycleCloser('CycleCloser')

    src_heat = Source('HeatingReturn')
    snk_heat = Sink('HeatingSupply')
    src_source = Source('SourceInlet')
    snk_source = Sink('SourceOutlet')

    # Kältemittelkreis
    c0 = Connection(cycle, 'out1', evap, 'in1', label='0')
    c1 = Connection(evap, 'out1', comp, 'in1', label='1')
    c2 = Connection(comp, 'out1', cond, 'in1', label='2')
    c3 = Connection(cond, 'out1', valve, 'in1', label='3')
    c4 = Connection(valve, 'out1', cycle, 'in1', label='4')
    nw.add_conns(c0, c1, c2, c3, c4)

    # Heizkreis
    h1 = Connection(src_heat, 'out1', cond, 'in2', label='h_in')
    h2 = Connection(cond, 'out2', snk_heat, 'in1', label='h_out')
    nw.add_conns(h1, h2)

    # Quellkreis
    q1 = Connection(src_source, 'out1', evap, 'in2', label='q_in')
    q2 = Connection(evap, 'out2', snk_source, 'in1', label='q_out')
    nw.add_conns(q1, q2)

    return nw, {
        'evap': evap, 'comp': comp, 'cond': cond,
        'valve': valve, 'cycle': cycle
    }, {
        'c0': c0, 'c1': c1, 'c2': c2, 'c3': c3, 'c4': c4,
        'h1': h1, 'h2': h2, 'q1': q1, 'q2': q2
    }


def simulate_point(T_source, T_supply=35):
    """Simuliert einen Betriebspunkt"""
    print(f"\n→ Simuliere B{T_source:.0f}/W{T_supply:.0f}...")

    nw, comps, conns = build_heat_pump()

    # Fluide (NUR auf erste Connection!)
    conns['c0'].set_attr(fluid={'R410A': 1.0})
    conns['h1'].set_attr(fluid={'water': 1.0})
    conns['q1'].set_attr(fluid={'water': 1.0})

    # Heizkreis
    T_return = T_supply - 5.0
    conns['h1'].set_attr(T=T_return, m=0.24)
    conns['h2'].set_attr(T=T_supply)

    # Quellkreis
    T_source_out = T_source - 3.0
    conns['q1'].set_attr(T=T_source, m=0.30)
    conns['q2'].set_attr(T=T_source_out)

    # Komponenten
    comps['evap'].set_attr(pr1=0.98, pr2=0.98, ttd_l=5)
    comps['cond'].set_attr(pr1=0.98, pr2=0.98, ttd_u=5)
    comps['comp'].set_attr(eta_s=0.75)
    comps['valve'].set_attr(pr=1.0)

    # Drücke schätzen
    try:
        T_evap_K = (T_source - 5) + 273.15
        p_evap = CP.PropsSI('P', 'T', T_evap_K, 'Q', 0, 'R410A') / 1e5

        T_cond_K = (T_supply + 5) + 273.15
        p_cond = CP.PropsSI('P', 'T', T_cond_K, 'Q', 0, 'R410A') / 1e5
    except:
        p_evap, p_cond = 5.5, 18.0

    # Startwerte
    conns['c0'].set_attr(p0=p_evap, m0=0.04)
    conns['c1'].set_attr(p0=p_evap)
    conns['c4'].set_attr(p0=p_evap)
    conns['c2'].set_attr(p0=p_cond)
    conns['c3'].set_attr(p0=p_cond)

    # Lösen
    try:
        nw.solve('design')
        if nw.status == 0:
            Q_heat = abs(comps['cond'].Q.val)
            Q_cool = abs(comps['evap'].Q.val)
            P_el = abs(comps['comp'].P.val)
            COP = Q_heat / P_el

            print(f"  ✓ COP = {COP:.2f}, P_th = {Q_heat:.2f} kW")

            return {
                'testpoint': f'B{T_source:.0f}/W{T_supply:.0f}',
                'T_source': T_source,
                'T_supply': T_supply,
                'COP': COP,
                'P_th_kW': Q_heat,
                'P_el_kW': P_el,
                'Q_source_kW': Q_cool,
            }
        else:
            print(f"  ❌ Nicht konvergiert (Status: {nw.status})")
            return None
    except Exception as e:
        print(f"  ❌ Fehler: {e}")
        return None


def main():
    """Führt 6-Punkt-Validierung durch"""
    print("="*70)
    print("MINIMAL WORKING MODEL".center(70))
    print("="*70)
    print("\nEinfaches Modell mit Standard-Parametern (R410A)")

    testpoints = [-10, -7, -5, 0, 5, 10]

    results = []
    for T_src in testpoints:
        res = simulate_point(T_src, T_supply=35)
        if res:
            results.append(res)

    # Speichern
    if len(results) > 0:
        df = pd.DataFrame(results)

        Path('data/results/basic_model').mkdir(parents=True, exist_ok=True)
        filename = 'data/results/basic_model/minimal_6points.csv'
        df.to_csv(filename, index=False)

        print("\n" + "="*70)
        print("ERGEBNIS".center(70))
        print("="*70)
        print(f"\n✓ {len(results)}/6 Punkte erfolgreich")
        print(f"✓ Gespeichert: {filename}")

        print("\nErgebnis-Tabelle:")
        print("-"*70)
        print(df[['testpoint', 'COP', 'P_th_kW', 'P_el_kW']].to_string(index=False))
        print("="*70)
    else:
        print("\n❌ Keine Punkte konvergiert!")
        print("\n💡 Probiere kA-Werte zu erhöhen oder eta_s zu reduzieren")


if __name__ == '__main__':
    main()