"""
MINIMAL WORKING MODEL - Basierend auf working_test.py
=======================================================

Einfachstes Modell mit SimpleHeatExchanger und R134a
6-Punkt-Validierung für verschiedene Quellentemperaturen

Verwendung:
    python minimal_model.py

Autor: A. Lohrmann
"""

from tespy.networks import Network
from tespy.components import CycleCloser, Compressor, Valve, SimpleHeatExchanger
from tespy.connections import Connection
import pandas as pd
from pathlib import Path


def build_heat_pump():
    """Baut einfaches Wärmepumpen-Netzwerk mit SimpleHeatExchanger"""
    hp = Network()
    hp.set_attr(T_unit="C", p_unit="bar", h_unit="kJ / kg", iterinfo=False)

    # Komponenten
    cc = CycleCloser("cycle")
    co = SimpleHeatExchanger("condenser")
    ev = SimpleHeatExchanger("evaporator")
    va = Valve("expansion")
    cp = Compressor("compressor")

    # Verbindungen
    c1 = Connection(cc, "out1", ev, "in1")
    c2 = Connection(ev, "out1", cp, "in1")
    c3 = Connection(cp, "out1", co, "in1")
    c4 = Connection(co, "out1", va, "in1")
    c0 = Connection(va, "out1", cc, "in1")
    hp.add_conns(c1, c2, c3, c4, c0)

    return hp, {
        'cc': cc, 'co': co, 'ev': ev, 'va': va, 'cp': cp
    }, {
        'c0': c0, 'c1': c1, 'c2': c2, 'c3': c3, 'c4': c4
    }


def simulate_point(T_evap, T_cond=80, Q_cond_kW=5):
    """
    Simuliert einen Betriebspunkt

    Args:
        T_evap: Verdampfungstemperatur in °C (entspricht ca. Quellentemperatur)
        T_cond: Kondensationstemperatur in °C (default 80°C)
        Q_cond_kW: Kondensatorleistung in kW (default 5 kW)

    Returns:
        dict mit Ergebnissen oder None bei Fehler
    """
    print(f"\n→ Simuliere T_evap={T_evap:.0f}°C / T_cond={T_cond:.0f}°C...")

    hp, comps, conns = build_heat_pump()

    # Specs - basierend auf working_test.py
    comps['co'].set_attr(pr=0.98, Q=-Q_cond_kW * 1000)  # Heizleistung (negativ = Wärmeabgabe)
    comps['ev'].set_attr(pr=0.98)
    comps['cp'].set_attr(eta_s=0.85)  # isentroper Wirkungsgrad

    # Verdampfer: gesättigter Dampf bei T_evap
    conns['c2'].set_attr(T=T_evap, x=1, fluid={"R134a": 1})

    # Kondensator: gesättigte Flüssigkeit bei T_cond
    conns['c4'].set_attr(T=T_cond, x=0)

    # Lösen
    try:
        hp.solve('design')

        if hp.status == 0:
            Qc = abs(comps['co'].Q.val) / 1000  # W -> kW
            Pel = comps['cp'].P.val / 1000  # W -> kW
            Qe = abs(comps['ev'].Q.val) / 1000  # W -> kW
            COP = Qc / Pel if Pel > 0 else float('nan')

            print(f"  ✓ COP = {COP:.2f}, P_th = {Qc:.2f} kW, P_el = {Pel:.2f} kW")

            return {
                'T_evap': T_evap,
                'T_cond': T_cond,
                'COP': COP,
                'P_th_kW': Qc,
                'P_el_kW': Pel,
                'Q_source_kW': Qe,
                'p_evap_bar': conns['c2'].p.val,
                'p_cond_bar': conns['c3'].p.val,
                'm_dot_kg_s': conns['c1'].m.val
            }
        else:
            print(f"  ❌ Nicht konvergiert (Status: {hp.status})")
            return None

    except Exception as e:
        print(f"  ❌ Fehler: {e}")
        return None


def main():
    """Führt 6-Punkt-Validierung durch"""
    print("="*70)
    print("MINIMAL WORKING MODEL".center(70))
    print("="*70)
    print("\nEinfaches Modell mit SimpleHeatExchanger (R134a)")
    print("Basierend auf working_test.py")

    # Test-Temperaturen (Verdampfung)
    # Verdampfung bei niedrigeren Temperaturen als Quelle
    # Typisch: T_evap = T_source - 5K
    testpoints = [
        ('B-10/W35', -15, 80),  # B-10 -> T_evap ~ -15°C
        ('B-7/W35', -12, 80),   # B-7 -> T_evap ~ -12°C
        ('B-5/W35', -10, 80),   # B-5 -> T_evap ~ -10°C
        ('B0/W35', -5, 80),     # B0 -> T_evap ~ -5°C
        ('B5/W35', 0, 80),      # B5 -> T_evap ~ 0°C
        ('B10/W35', 5, 80),     # B10 -> T_evap ~ 5°C
    ]

    results = []
    for label, T_evap, T_cond in testpoints:
        res = simulate_point(T_evap, T_cond, Q_cond_kW=5)
        if res:
            res['testpoint'] = label
            results.append(res)

    # Speichern
    if len(results) > 0:
        df = pd.DataFrame(results)
        # Spalten sortieren
        cols = ['testpoint', 'T_evap', 'T_cond', 'COP', 'P_th_kW', 'P_el_kW',
                'Q_source_kW', 'p_evap_bar', 'p_cond_bar', 'm_dot_kg_s']
        df = df[cols]

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
        print(df[['testpoint', 'COP', 'P_th_kW', 'P_el_kW']].to_string(index=False))
        print("="*70)
    else:
        print("\n❌ Keine Punkte konvergiert!")


if __name__ == '__main__':
    main()
