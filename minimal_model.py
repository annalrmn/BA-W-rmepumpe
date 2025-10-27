"""
MINIMAL WORKING MODEL - Mit Condenser und HeatExchanger
========================================================

Modell mit vollständiger Struktur:
- Condenser für Kondensator mit Heizkreis
- HeatExchanger für Verdampfer mit Quellkreis
- R134a Kältemittel (bessere Konvergenz als R410A)

6-Punkt-Validierung für verschiedene Quellentemperaturen

Verwendung:
    python minimal_model.py

Autor: A. Lohrmann
"""

from tespy.networks import Network
from tespy.components import (Compressor, Valve, CycleCloser,
                             Condenser, HeatExchanger, Sink, Source)
from tespy.connections import Connection
import pandas as pd
from pathlib import Path


def build_heat_pump():
    """Baut Wärmepumpen-Netzwerk mit Condenser und HeatExchanger"""
    nw = Network()
    nw.set_attr(T_unit='C', p_unit='bar', h_unit='kJ / kg', iterinfo=False)

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

    # Heizkreis (Sekundärseite Kondensator)
    h1 = Connection(src_heat, 'out1', cond, 'in2', label='h_in')
    h2 = Connection(cond, 'out2', snk_heat, 'in1', label='h_out')
    nw.add_conns(h1, h2)

    # Quellkreis (Sekundärseite Verdampfer)
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


def simulate_point(T_source, T_supply=50):
    """
    Simuliert einen Betriebspunkt

    Args:
        T_source: Quellentemperatur (z.B. Sole-Eintritt) in °C
        T_supply: Vorlauftemperatur Heizung in °C (default 35°C)

    Returns:
        dict mit Ergebnissen oder None bei Fehler
    """
    print(f"\n→ Simuliere B{T_source:.0f}/W{T_supply:.0f}...")

    nw, comps, conns = build_heat_pump()

    # Fluide (NUR auf erste Connection jedes Kreises!)
    conns['c0'].set_attr(fluid={'R134a': 1.0})
    conns['h1'].set_attr(fluid={'water': 1.0})
    conns['q1'].set_attr(fluid={'water': 1.0})

    # Heizkreis (Vorlauf/Rücklauf)
    T_return = T_supply - 5.0
    conns['h1'].set_attr(T=T_return, m=0.24)  # Rücklauf 30°C bei 35°C Vorlauf
    conns['h2'].set_attr(T=T_supply)

    # Quellkreis (z.B. Sole)
    T_source_out = T_source - 3.0  # 3K Spreizung
    conns['q1'].set_attr(T=T_source, m=0.30)
    conns['q2'].set_attr(T=T_source_out)

    # Komponenten
    # Evaporator: pr1=Kältemittelseite, pr2=Wasserseite, kA=Wärmedurchgangskoeffizient
    comps['evap'].set_attr(pr1=0.98, pr2=0.98, kA=2)

    # Condenser: pr1=Kältemittelseite, pr2=Wasserseite, kA=Wärmedurchgangskoeffizient
    comps['cond'].set_attr(pr1=0.98, pr2=0.98, kA=2)

    # Compressor: isentroper Wirkungsgrad
    comps['comp'].set_attr(eta_s=0.85)

    # Kältemittelkreis - Massenstrom
    conns['c0'].set_attr(m=0.05)

    # Unterkühlung am Kondensatorausgang
    conns['c3'].set_attr(td_bubble=3)  # 3K Unterkühlung

    # Lösen
    try:
        nw.solve('design')

        if nw.status == 0:
            Q_heat = abs(comps['cond'].Q.val) / 1000  # W -> kW
            Q_cool = abs(comps['evap'].Q.val) / 1000  # W -> kW
            P_el = abs(comps['comp'].P.val) / 1000  # W -> kW
            COP = Q_heat / P_el if P_el > 0 else float('nan')

            print(f"  ✓ COP = {COP:.2f}, P_th = {Q_heat:.2f} kW, P_el = {P_el:.2f} kW")

            return {
                'testpoint': f'B{T_source:.0f}/W{T_supply:.0f}',
                'T_source': T_source,
                'T_supply': T_supply,
                'COP': COP,
                'P_th_kW': Q_heat,
                'P_el_kW': P_el,
                'Q_source_kW': Q_cool,
                'T_evap': conns['c1'].T.val,
                'T_cond': conns['c2'].T.val,
                'p_evap_bar': conns['c1'].p.val,
                'p_cond_bar': conns['c2'].p.val,
                'm_refrig_kg_s': conns['c0'].m.val
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
    print("\nModell mit Condenser + HeatExchanger + Wasserkreise")
    print("Kältemittel: R134a\n")

    # Test-Quellentemperaturen (erstmal nur wärmere Punkte)
    testpoints = [0, 5, 10]

    results = []
    for T_src in testpoints:
        res = simulate_point(T_src, T_supply=50)
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
        print(f"\n✓ {len(results)}/{len(testpoints)} Punkte erfolgreich")
        print(f"✓ Gespeichert: {filename}")

        print("\nErgebnis-Tabelle:")
        print("-"*70)
        cols = ['testpoint', 'COP', 'P_th_kW', 'P_el_kW', 'T_evap', 'T_cond']
        print(df[cols].to_string(index=False))
        print("="*70)
    else:
        print("\n❌ Keine Punkte konvergiert!")


if __name__ == '__main__':
    main()
