"""
MODEL 1: Basic Design Model (mit hplib Integration)
====================================================

Features:
- Lädt Gerät aus hplib-Datenbank
- Extrahiert automatisch Parameter
- Vergleicht mit Hersteller-Datenblatt
- 6 Betriebspunkte (B-10/W35 bis B10/W35)

Verwendung:
    from src.models.basic_design_model import BasicDesignModel

    model = BasicDesignModel(device_name="Vitocal")
    df = model.run_validation_study()

Autor: A. Lohrmann
Bachelor-Arbeit 2025
"""

from tespy.networks import Network
from tespy.components import (Compressor, Valve, CycleCloser,
                             Condenser, HeatExchanger, Sink, Source)
from tespy.connections import Connection
import CoolProp.CoolProp as CP
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Import data_loader (mehrere Fallbacks für verschiedene Ausführungs-Szenarien)
try:
    # Versuch 1: Direkter Import (wenn im Pfad)
    from data_loader import load_heatpump, load_manufacturer_data
except ImportError:
    # Versuch 2: Füge utils zum Pfad hinzu
    utils_path = Path(__file__).parent.parent / 'utils'
    if utils_path not in sys.path:
        sys.path.insert(0, str(utils_path))
    from data_loader import load_heatpump, load_manufacturer_data


class BasicDesignModel:
    """
    Basic Design Model mit hplib Integration

    Simuliert Wärmepumpe an 6 Betriebspunkten und vergleicht mit Herstellerdaten
    """

    def __init__(self, device_name: str = None,
                 hplib_path: str = 'data/raw/hplib_database.csv'):
        """
        Parameters:
        -----------
        device_name : str, optional
            Name der WP aus hplib (z.B. "Vitocal")
            Falls None: Nutze Standard-Parameter
        hplib_path : str
            Pfad zur hplib-Datenbank
        """
        self.device_name = device_name
        self.hplib_path = hplib_path

        self.network = None
        self.components = {}
        self.connections = {}
        self.wp_data = None
        self.manufacturer_data = None

        # Lade Gerät aus hplib (falls angegeben)
        if device_name:
            print(f"\n→ Lade Wärmepumpe: {device_name}")
            self.wp_data = load_heatpump(device_name, hplib_path)
            self.manufacturer_data = load_manufacturer_data(device_name)
            self._set_parameters_from_hplib()
        else:
            # Standard-Parameter (wenn kein Gerät angegeben)
            self._set_default_parameters()

        print(f"\n✓ Modell initialisiert")
        print(f"  Kältemittel: {self.params['refrigerant']}")
        print(f"  η_s:         {self.params['eta_s']:.2f}")
        print(f"  kA Verdampf: {self.params['kA_evap']:.2f} kW/K")
        print(f"  kA Kond.:    {self.params['kA_cond']:.2f} kW/K")

    def _set_parameters_from_hplib(self):
        """Setzt Parameter aus hplib-Daten"""
        # Kältemittel
        refrigerant = self.wp_data.get('refrigerant', 'R410A')

        # Nominelle Leistung für Massenstrom-Berechnung
        P_th_nom = self.wp_data.get('P_th_nom_kW')

        # Falls P_th_nom fehlt, nutze Standard-Wert
        if P_th_nom is None or P_th_nom == 0:
            print("  ⚠️  P_th_nom nicht gefunden, nutze Standard: 5.0 kW")
            P_th_nom = 5.0

        # kA-Werte aus Nennleistung schätzen
        # Faustformel: kA ≈ P_th / 7 für Verdampfer, P_th / 6 für Kondensator
        kA_evap = P_th_nom / 7.0
        kA_cond = P_th_nom / 6.0

        self.params = {
            'refrigerant': refrigerant,
            'eta_s': 0.75,           # Isentroper Wirkungsgrad
            'pr_evap': 0.98,         # Druckverlust Verdampfer
            'pr_cond': 0.98,         # Druckverlust Kondensator
            'kA_evap': kA_evap,      # kA Verdampfer
            'kA_cond': kA_cond,      # kA Kondensator
            'P_th_nom_kW': P_th_nom,
        }

    def _set_default_parameters(self):
        """Setzt Standard-Parameter (fallback)"""
        self.params = {
            'refrigerant': 'R410A',
            'eta_s': 0.75,
            'pr_evap': 0.98,
            'pr_cond': 0.98,
            'kA_evap': 0.7,
            'kA_cond': 0.8,
            'P_th_nom_kW': 5.0,
        }

    def build_network(self):
        """Baut TESPy-Netzwerk"""
        self.network = Network(iterinfo=False)
        self.network.set_attr(
            T_unit='C', p_unit='bar', h_unit='kJ / kg',
            Q_unit='kW', P_unit='kW'
        )

        # Komponenten
        evap = HeatExchanger('Evaporator')
        comp = Compressor('Compressor')
        cond = Condenser('Condenser')
        valve = Valve('ExpansionValve')
        cycle = CycleCloser('CycleCloser')

        src_heating = Source('HeatingReturn')
        snk_heating = Sink('HeatingSupply')
        src_source = Source('SourceInlet')
        snk_source = Sink('SourceOutlet')

        # Kältemittelkreis
        c0 = Connection(cycle, 'out1', evap, 'in1', label='0')
        c1 = Connection(evap, 'out1', comp, 'in1', label='1')
        c2 = Connection(comp, 'out1', cond, 'in1', label='2')
        c3 = Connection(cond, 'out1', valve, 'in1', label='3')
        c4 = Connection(valve, 'out1', cycle, 'in1', label='4')
        self.network.add_conns(c0, c1, c2, c3, c4)

        # Heizkreis
        h1 = Connection(src_heating, 'out1', cond, 'in2', label='h_in')
        h2 = Connection(cond, 'out2', snk_heating, 'in1', label='h_out')
        self.network.add_conns(h1, h2)

        # Quellkreis
        q1 = Connection(src_source, 'out1', evap, 'in2', label='q_in')
        q2 = Connection(evap, 'out2', snk_source, 'in1', label='q_out')
        self.network.add_conns(q1, q2)

        # Speichern
        self.components = {
            'evaporator': evap,
            'compressor': comp,
            'condenser': cond,
            'valve': valve,
            'cycle': cycle,
        }

        self.connections = {
            'refrigerant': {'c0': c0, 'c1': c1, 'c2': c2, 'c3': c3, 'c4': c4},
            'heating': {'h1': h1, 'h2': h2},
            'source': {'q1': q1, 'q2': q2},
        }

    def set_operating_point(self, T_source: float, T_supply: float = 35.0):
        """
        Setzt Betriebspunkt

        Parameters:
        -----------
        T_source : float
            Quelltemperatur [°C]
        T_supply : float
            Vorlauftemperatur [°C]
        """
        fluid = self.params['refrigerant']

        # Fluide setzen - NUR auf ERSTE Connection jedes Kreises!
        # Kältemittelkreis: Nur auf c0
        self.connections['refrigerant']['c0'].set_attr(fluid={fluid: 1.0, 'water': 0.0})

        # Heizkreis: Nur auf h1
        self.connections['heating']['h1'].set_attr(fluid={fluid: 0.0, 'water': 1.0})

        # Quellkreis: Nur auf q1
        self.connections['source']['q1'].set_attr(fluid={fluid: 0.0, 'water': 1.0})

        # Heizkreis (NUR Temperaturen und Massenströme!)
        T_return = T_supply - 5.0
        m_heating = self._calculate_mass_flow(self.params['P_th_nom_kW'], 5.0)

        self.connections['heating']['h1'].set_attr(T=T_return, m=m_heating)
        self.connections['heating']['h2'].set_attr(T=T_supply)

        # Quellkreis (NUR Temperaturen und Massenströme!)
        T_source_out = T_source - 3.0
        m_source = m_heating * 1.2  # Etwas höher als Heizkreis

        self.connections['source']['q1'].set_attr(T=T_source, m=m_source)
        self.connections['source']['q2'].set_attr(T=T_source_out)

        # Komponenten-Parameter
        self.components['evaporator'].set_attr(
            pr1=self.params['pr_evap'],
            pr2=self.params['pr_evap'],
            ttd_l=5
        )

        self.components['condenser'].set_attr(
            pr1=self.params['pr_cond'],
            pr2=self.params['pr_cond'],
            ttd_u=5
        )

        self.components['compressor'].set_attr(
            eta_s=self.params['eta_s']
        )

        self.components['valve'].set_attr(pr=1.0)

        # Druckschätzung
        p_evap, p_cond = self._estimate_pressures(fluid, T_source, T_supply)

        # Startwerte für Kältemittelkreis
        # Nur Drücke setzen - KEINE Temperaturen oder Überhitzung als Startwert!
        for conn in [self.connections['refrigerant']['c0'],
                     self.connections['refrigerant']['c1'],
                     self.connections['refrigerant']['c4']]:
            conn.set_attr(p0=p_evap)

        for conn in [self.connections['refrigerant']['c2'],
                     self.connections['refrigerant']['c3']]:
            conn.set_attr(p0=p_cond)

        # Massenstrom Kältemittel
        m_ref_guess = self.params['P_th_nom_kW'] / 200  # Faustformel
        self.connections['refrigerant']['c0'].set_attr(m0=m_ref_guess)

    def _calculate_mass_flow(self, P_th: float, dT: float) -> float:
        """Berechnet Massenstrom aus Leistung"""
        cp_water = 4.180  # kJ/(kg·K)
        return P_th / (cp_water * dT)

    def _estimate_pressures(self, fluid: str, T_evap: float, T_cond: float):
        """Schätzt Drücke für Startwerte"""
        try:
            T_evap_K = (T_evap - 5.0) + 273.15
            p_evap = CP.PropsSI('P', 'T', T_evap_K, 'Q', 0, fluid) / 1e5

            T_cond_K = (T_cond + 5.0) + 273.15
            p_cond = CP.PropsSI('P', 'T', T_cond_K, 'Q', 0, fluid) / 1e5

            return p_evap, p_cond
        except:
            # Fallback für R410A
            if 'R410A' in fluid.upper():
                return 5.5, 18.0
            return 3.0, 12.0

    def solve(self) -> bool:
        """Löst das Netzwerk"""
        try:
            self.network.solve('design')
            return self.network.status == 0
        except Exception as e:
            print(f"  Fehler: {e}")
            return False

    def get_results(self) -> dict:
        """Extrahiert Ergebnisse"""
        if not hasattr(self.network, 'status') or self.network.status != 0:
            return None

        Q_heating = abs(self.components['condenser'].Q.val)
        Q_cooling = abs(self.components['evaporator'].Q.val)
        P_el = abs(self.components['compressor'].P.val)
        COP = Q_heating / max(P_el, 1e-9)

        return {
            'P_th_kW': Q_heating,
            'Q_source_kW': Q_cooling,
            'P_el_kW': P_el,
            'COP': COP,
            'T_evap_C': self.connections['refrigerant']['c1'].T.val,
            'T_cond_C': self.connections['refrigerant']['c3'].T.val,
            'p_evap_bar': self.connections['refrigerant']['c1'].p.val,
            'p_cond_bar': self.connections['refrigerant']['c2'].p.val,
            'm_ref_kg_s': self.connections['refrigerant']['c1'].m.val,
            'energy_balance_kW': abs(Q_heating - Q_cooling - P_el),
        }

    def run_single_point(self, T_source: float, T_supply: float = 35.0) -> dict:
        """
        Simuliert einzelnen Betriebspunkt

        Returns:
        --------
        dict or None
        """
        testpoint_label = f"B{T_source:.0f}/W{T_supply:.0f}"
        print(f"\n→ Simuliere {testpoint_label}...")

        self.build_network()
        self.set_operating_point(T_source, T_supply)

        if self.solve():
            results = self.get_results()
            results['T_source'] = T_source
            results['T_supply'] = T_supply
            results['testpoint'] = testpoint_label

            # Vergleich mit Herstellerdaten (falls vorhanden)
            if self.manufacturer_data is not None:
                ref_row = self.manufacturer_data[
                    self.manufacturer_data['T_source'] == T_source
                ]
                if len(ref_row) > 0:
                    results['COP_ref'] = ref_row['COP_ref'].values[0]
                    results['P_th_ref_kW'] = ref_row['P_th_ref_kW'].values[0]
                    results['COP_deviation_%'] = (
                        (results['COP'] - results['COP_ref']) / results['COP_ref'] * 100
                    )
                    results['P_th_deviation_%'] = (
                        (results['P_th_kW'] - results['P_th_ref_kW']) /
                        results['P_th_ref_kW'] * 100
                    )

            print(f"  ✓ COP = {results['COP']:.2f}, P_th = {results['P_th_kW']:.2f} kW")
            if 'COP_ref' in results:
                print(f"    (Hersteller: COP = {results['COP_ref']:.2f}, "
                      f"Abweichung = {results['COP_deviation_%']:.1f}%)")

            return results
        else:
            print(f"  ❌ Nicht konvergiert")
            return None

    def run_validation_study(self,
                           output_dir: str = 'data/results/basic_model') -> pd.DataFrame:
        """
        Führt 6-Punkte-Validierung durch

        Returns:
        --------
        pd.DataFrame
            Ergebnisse
        """
        print("="*70)
        print("BASIC DESIGN MODEL - VALIDIERUNG")
        print("="*70)

        if self.device_name:
            print(f"\nWärmepumpe: {self.wp_data['name']}")
            print(f"Hersteller: {self.wp_data['manufacturer']}")

        # 6 Betriebspunkte
        testpoints = [
            (-10, 35),
            (-7, 35),
            (-5, 35),
            (0, 35),
            (5, 35),
            (10, 35),
        ]

        results = []
        for T_src, T_sup in testpoints:
            res = self.run_single_point(T_src, T_sup)
            if res:
                results.append(res)

        df = pd.DataFrame(results)

        # Prüfe ob überhaupt Ergebnisse da sind
        if len(results) == 0:
            print("\n❌ FEHLER: Keine Punkte konvergiert!")
            print("\n💡 Mögliche Lösungen:")
            print("   1. kA-Werte erhöhen (größerer Wärmetauscher)")
            print("   2. Anderen Betriebspunkt probieren")
            print("   3. Anderes Gerät probieren")
            return pd.DataFrame()  # Leerer DataFrame

        # Speichern
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        filename = Path(output_dir) / 'validation_6points.csv'
        df.to_csv(filename, index=False)
        print(f"\n✓ Ergebnisse gespeichert: {filename}")

        # Zusammenfassung
        print("\n" + "="*70)
        print("ZUSAMMENFASSUNG")
        print("="*70)
        print(f"Erfolgreich:  {len(results)}/6 Punkte")

        if len(df) > 0:
            print(f"COP Bereich:  {df['COP'].min():.2f} - {df['COP'].max():.2f}")
            print(f"P_th Bereich: {df['P_th_kW'].min():.2f} - {df['P_th_kW'].max():.2f} kW")

        if 'COP_deviation_%' in df.columns:
            mean_dev = df['COP_deviation_%'].abs().mean()
            print(f"\nMittlere Abweichung COP: {mean_dev:.1f}%")
            if mean_dev < 10:
                print("  ✓ Sehr gut! (<10%)")
            elif mean_dev < 20:
                print("  ⚠️  Akzeptabel (10-20%)")
            else:
                print("  ❌ Zu hoch (>20%)")

        print("="*70)

        return df


# ============================================================================
# STAND-ALONE EXECUTION
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Basic Design Model')
    parser.add_argument('--device', type=str, default='Vitocal',
                       help='Gerätename aus hplib (z.B. "Vitocal")')
    parser.add_argument('--hplib', type=str, default='data/raw/hplib_database.csv',
                       help='Pfad zur hplib-Datenbank')

    args = parser.parse_args()

    # Erstelle und führe Modell aus
    model = BasicDesignModel(
        device_name=args.device,
        hplib_path=args.hplib
    )

    df_results = model.run_validation_study()

    # Zeige Ergebnistabelle
    print("\n\nERGEBNIS-TABELLE:")
    print("="*70)
    cols_to_show = ['testpoint', 'T_source', 'COP', 'P_th_kW', 'P_el_kW']
    if 'COP_ref' in df_results.columns:
        cols_to_show.extend(['COP_ref', 'COP_deviation_%'])
    print(df_results[cols_to_show].to_string(index=False))