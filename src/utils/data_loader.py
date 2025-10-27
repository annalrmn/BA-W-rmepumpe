"""
Data Loader für hplib und Herstellerdaten
==========================================

Lädt Wärmepumpen aus hplib-Datenbank und Hersteller-Datenblätter

Verwendung:
    from src.utils.data_loader import load_heatpump, load_manufacturer_data

    wp_data = load_heatpump("Vitocal 200-G")
    mfr_data = load_manufacturer_data("Vitocal 200-G")

Autor: A. Lohrmann
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional


def load_hplib_database(path: str = 'data/raw/hplib_database.csv') -> pd.DataFrame:
    """
    Lädt komplette hplib-Datenbank

    Parameters:
    -----------
    path : str
        Pfad zur CSV-Datei

    Returns:
    --------
    pd.DataFrame
        Komplette Datenbank
    """
    try:
        df = pd.read_csv(path, encoding='utf-8')
        print(f"✓ hplib-Datenbank geladen: {len(df)} Geräte")
        return df
    except FileNotFoundError:
        print(f"❌ Datei nicht gefunden: {path}")
        print("   Bitte hplib_database.csv nach data/raw/ kopieren!")
        raise
    except Exception as e:
        print(f"❌ Fehler beim Laden: {e}")
        raise


def search_device(df: pd.DataFrame, search_term: str,
                 show_results: bool = True) -> pd.DataFrame:
    """
    Sucht Geräte in Datenbank

    Parameters:
    -----------
    df : pd.DataFrame
        hplib-Datenbank
    search_term : str
        Suchbegriff (z.B. "Vitocal", "Daikin")
    show_results : bool
        Zeige Suchergebnisse

    Returns:
    --------
    pd.DataFrame
        Gefundene Geräte
    """
    # Suche in verschiedenen Spalten
    mask = False
    for col in df.columns:
        if df[col].dtype == 'object':
            mask |= df[col].astype(str).str.contains(search_term, case=False, na=False)

    results = df[mask]

    if show_results:
        print(f"\nGefunden: {len(results)} Geräte für '{search_term}'")
        if len(results) > 0:
            print("\nErste 5 Ergebnisse:")
            display_cols = []
            for col in ['Model', 'Manufacturer', 'Type', 'Refrigerant', 'P_th [W]']:
                if col in results.columns:
                    display_cols.append(col)

            if display_cols:
                print(results[display_cols].head())

    return results


def load_heatpump(device_name: str,
                 db_path: str = 'data/raw/hplib_database.csv') -> Dict:
    """
    Lädt spezifische Wärmepumpe aus hplib

    Parameters:
    -----------
    device_name : str
        Name oder Teil des Namens (z.B. "Vitocal 200-G")
    db_path : str
        Pfad zur Datenbank

    Returns:
    --------
    dict
        Wärmepumpen-Parameter für Simulation
    """
    df = load_hplib_database(db_path)

    # Suche Gerät
    results = search_device(df, device_name, show_results=False)

    if len(results) == 0:
        print(f"\n❌ Kein Gerät gefunden für: '{device_name}'")
        print("\nVorschläge:")
        # Zeige ähnliche
        for term in device_name.split():
            similar = search_device(df, term, show_results=False)
            if len(similar) > 0:
                print(f"  Suche nach '{term}': {len(similar)} Geräte")
        raise ValueError(f"Gerät nicht gefunden: {device_name}")

    if len(results) > 1:
        print(f"\n⚠️  {len(results)} Geräte gefunden für '{device_name}'")
        print("   Verwende erstes Gerät. Für andere, präzisiere die Suche.\n")

    # Nimm erstes Gerät
    row = results.iloc[0]

    # Extrahiere Parameter
    wp_data = _extract_parameters(row)

    print(f"✓ Geladen: {wp_data['name']}")
    print(f"  Hersteller:  {wp_data['manufacturer']}")
    print(f"  Kältemittel: {wp_data['refrigerant']}")
    print(f"  P_th (nom):  {wp_data.get('P_th_nom_kW', 'N/A')} kW")

    return wp_data


def _extract_parameters(row: pd.Series) -> Dict:
    """
    Extrahiert Parameter aus hplib-Zeile
    """
    def safe_float(val, default=None):
        try:
            if pd.isna(val):
                return default
            return float(val)
        except:
            return default

    def safe_str(val, default='Unknown'):
        if pd.isna(val):
            return default
        return str(val).strip()

    # Basis-Info
    wp_data = {
        'name': safe_str(row.get('Model', row.get('model', 'Unknown'))),
        'manufacturer': safe_str(row.get('Manufacturer', row.get('manufacturer', 'Unknown'))),
        'refrigerant': safe_str(row.get('Refrigerant', row.get('refrigerant', 'R410A'))),
    }

    # Suche P_th und COP für verschiedene Testpunkte
    testpoints = {}

    for col in row.index:
        col_lower = str(col).lower()

        # B0/W35 Nennpunkt
        if 'b0' in col_lower and 'w35' in col_lower:
            if 'p_th' in col_lower or 'heating' in col_lower:
                P_th_W = safe_float(row[col])
                if P_th_W and P_th_W > 100:
                    testpoints['B0/W35_P_th_kW'] = P_th_W / 1000
            elif 'cop' in col_lower:
                testpoints['B0/W35_COP'] = safe_float(row[col])

        # Generische Werte
        if col_lower in ['p_th', 'p_th [w]', 'p_th [kw]']:
            P_th = safe_float(row[col])
            if P_th:
                wp_data['P_th_nom_kW'] = P_th / 1000 if P_th > 100 else P_th

        if col_lower == 'cop':
            wp_data['COP_nom'] = safe_float(row[col])

    # Füge Testpunkte hinzu
    wp_data.update(testpoints)

    # Defaults für fehlende Werte
    if 'P_th_nom_kW' not in wp_data and 'B0/W35_P_th_kW' in testpoints:
        wp_data['P_th_nom_kW'] = testpoints['B0/W35_P_th_kW']

    if 'COP_nom' not in wp_data and 'B0/W35_COP' in testpoints:
        wp_data['COP_nom'] = testpoints['B0/W35_COP']

    return wp_data


def load_manufacturer_data(device_name: str,
                          data_dir: str = 'data/raw/manufacturer') -> Optional[pd.DataFrame]:
    """
    Lädt Hersteller-Datenblatt (falls vorhanden)

    Parameters:
    -----------
    device_name : str
        Gerätename
    data_dir : str
        Verzeichnis mit Hersteller-Daten

    Returns:
    --------
    pd.DataFrame or None
        Datenblatt oder None falls nicht vorhanden
    """
    # Erstelle Dateinamen (z.B. "Vitocal_200-G.csv")
    filename = device_name.replace(' ', '_').replace('/', '-') + '.csv'
    filepath = Path(data_dir) / filename

    if not filepath.exists():
        print(f"ℹ️  Kein Hersteller-Datenblatt gefunden: {filepath}")
        print("   → Erstelle Beispiel-Daten für Vergleich")
        return _create_example_manufacturer_data()

    try:
        df = pd.read_csv(filepath)
        print(f"✓ Hersteller-Datenblatt geladen: {filepath}")
        return df
    except Exception as e:
        print(f"⚠️  Fehler beim Laden: {e}")
        return None


def _create_example_manufacturer_data() -> pd.DataFrame:
    """
    Erstellt Beispiel-Herstellerdaten (falls kein Datenblatt vorhanden)

    Basiert auf typischen Werten für Vitocal 200-G BWC 201.B06
    """
    return pd.DataFrame({
        'Testpoint': ['B-10/W35', 'B-7/W35', 'B-5/W35', 'B0/W35', 'B5/W35', 'B10/W35'],
        'T_source': [-10, -7, -5, 0, 5, 10],
        'T_supply': [35, 35, 35, 35, 35, 35],
        'COP_ref': [2.45, 2.65, 2.80, 3.01, 3.35, 3.60],
        'P_th_ref_kW': [3.80, 4.20, 4.50, 5.23, 5.80, 6.40],
        'P_el_ref_kW': [1.55, 1.58, 1.61, 1.74, 1.73, 1.78],
    })


def save_manufacturer_template(device_name: str,
                              output_dir: str = 'data/raw/manufacturer'):
    """
    Erstellt Template für Hersteller-Datenblatt

    Parameters:
    -----------
    device_name : str
        Gerätename
    output_dir : str
        Ausgabe-Verzeichnis
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    filename = device_name.replace(' ', '_').replace('/', '-') + '.csv'
    filepath = Path(output_dir) / filename

    template = pd.DataFrame({
        'Testpoint': ['B-10/W35', 'B-7/W35', 'B-5/W35', 'B0/W35', 'B5/W35', 'B10/W35'],
        'T_source': [-10, -7, -5, 0, 5, 10],
        'T_supply': [35, 35, 35, 35, 35, 35],
        'COP_ref': [np.nan] * 6,        # ← Vom Datenblatt eintragen
        'P_th_ref_kW': [np.nan] * 6,    # ← Vom Datenblatt eintragen
        'P_el_ref_kW': [np.nan] * 6,    # ← Vom Datenblatt eintragen
    })

    template.to_csv(filepath, index=False)
    print(f"✓ Template erstellt: {filepath}")
    print("  → Fülle die NaN-Werte mit Datenblatt-Werten!")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def list_all_devices(db_path: str = 'data/raw/hplib_database.csv',
                    max_show: int = 20) -> pd.DataFrame:
    """Listet alle Geräte in Datenbank"""
    df = load_hplib_database(db_path)

    print(f"\nAlle Geräte ({len(df)} insgesamt), zeige erste {max_show}:")
    print("-" * 70)

    display_cols = []
    for col in ['Model', 'Manufacturer', 'Refrigerant']:
        if col in df.columns:
            display_cols.append(col)

    if display_cols:
        print(df[display_cols].head(max_show))

    return df


def get_testpoint_data(wp_data: Dict, testpoint: str = 'B0/W35') -> Dict:
    """
    Extrahiert Daten für spezifischen Testpunkt

    Parameters:
    -----------
    wp_data : dict
        Daten von load_heatpump()
    testpoint : str
        z.B. 'B0/W35'

    Returns:
    --------
    dict
        {'P_th_kW': ..., 'COP': ..., 'P_el_kW': ...}
    """
    key_prefix = testpoint.replace('/', '_')

    result = {}
    for key, val in wp_data.items():
        if key.startswith(key_prefix):
            result[key.split('_', 2)[-1]] = val

    return result


# ============================================================================
# MAIN (für Tests)
# ============================================================================

if __name__ == '__main__':
    print("="*70)
    print("DATA LOADER TEST")
    print("="*70)

    # Test 1: Liste alle Geräte
    # list_all_devices()

    # Test 2: Suche spezifisches Gerät
    print("\nTest: Lade Vitocal 200-G")
    print("-"*70)
    try:
        wp_data = load_heatpump("Vitocal")
        print("\nExtrahierte Parameter:")
        for key, val in wp_data.items():
            print(f"  {key:20} {val}")
    except Exception as e:
        print(f"Fehler: {e}")

    # Test 3: Lade Herstellerdaten
    print("\n\nTest: Lade Hersteller-Datenblatt")
    print("-"*70)
    mfr_data = load_manufacturer_data("Vitocal 200-G")
    if mfr_data is not None:
        print(mfr_data)

    # Test 4: Erstelle Template
    print("\n\nTest: Erstelle Template")
    print("-"*70)
    save_manufacturer_template("Vitocal 200-G BWC 201.B06")

    print("\n" + "="*70)