"""
QUICK-TEST - Testet einen einzelnen Betriebspunkt
==================================================

Version für ROOT-Verzeichnis (bachelor_thesis/)

Verwendung:
    python quick_test.py

Autor: A. Lohrmann
"""

import sys
from pathlib import Path

# Füge Pfade hinzu (aus Root-Ordner)
sys.path.insert(0, 'src/models')
sys.path.insert(0, 'src/utils')

print("=" * 70)
print("QUICK-TEST: Einzelner Betriebspunkt".center(70))
print("=" * 70)

try:
    from basic_design_model import BasicDesignModel

    # Erstelle Modell
    print("\n→ Erstelle Modell (Vitocal)...")
    model = BasicDesignModel(
        device_name="Vitocal",
        hplib_path="data/raw/hplib_database.csv"
    )

    # Teste B0/W35 (Nennpunkt - sollte am besten funktionieren)
    print("\n→ Teste B0/W35 (Nennpunkt)...")
    result = model.run_single_point(T_source=0, T_supply=35)

    if result:
        print("\n" + "=" * 70)
        print("ERFOLG!".center(70))
        print("=" * 70)
        print(f"\n✓ Simulation konvergiert!")
        print(f"\nErgebnisse:")
        print(f"  COP:        {result['COP']:.2f}")
        print(f"  P_th:       {result['P_th_kW']:.2f} kW")
        print(f"  P_el:       {result['P_el_kW']:.2f} kW")
        print(f"  T_evap:     {result['T_evap_C']:.1f} °C")
        print(f"  T_cond:     {result['T_cond_C']:.1f} °C")
        print(f"  p_evap:     {result['p_evap_bar']:.1f} bar")
        print(f"  p_cond:     {result['p_cond_bar']:.1f} bar")

        if 'COP_ref' in result:
            print(f"\nVergleich mit Hersteller:")
            print(f"  COP_ref:    {result['COP_ref']:.2f}")
            print(f"  Abweichung: {result['COP_deviation_%']:.1f}%")

        print("\n→ Jetzt kannst du alle 6 Punkte simulieren:")
        print("   python main.py")
        print("=" * 70)

    else:
        print("\n" + "=" * 70)
        print("FEHLER!".center(70))
        print("=" * 70)
        print("\n❌ Simulation konvergiert nicht!")
        print("\n💡 Mögliche Lösungen:")
        print("   1. Erhöhe kA-Werte:")
        print("      model.params['kA_evap'] = 1.0")
        print("      model.params['kA_cond'] = 1.2")
        print("   2. Probiere anderen Betriebspunkt:")
        print("      model.run_single_point(T_source=5, T_supply=35)")
        print("   3. Probiere anderes Gerät:")
        print("      BasicDesignModel('Daikin')")
        print("=" * 70)

except FileNotFoundError as e:
    print(f"\n❌ Datei nicht gefunden: {e}")
    print("\n💡 Prüfe:")
    print("   - Liegt hplib_database.csv in data/raw/?")
    print("   - Bist du im Root-Verzeichnis (bachelor_thesis/)?")

except Exception as e:
    print(f"\n❌ Fehler: {e}")
    import traceback

    traceback.print_exc()