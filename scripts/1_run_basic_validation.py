"""
Script 1: Basic Design Model Validierung
=========================================

Führt 6-Punkte-Validierung durch und erstellt Plots

Verwendung:
    python scripts/1_run_basic_validation.py
    python scripts/1_run_basic_validation.py --device "Daikin"

Autor: A. Lohrmann
"""

import sys
from pathlib import Path

# Füge src zum Pfad hinzu
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'models'))
sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'utils'))

from basic_design_model import BasicDesignModel
from plotting import plot_basic_validation
import pandas as pd
import argparse


def main():
    parser = argparse.ArgumentParser(description='Basic Design Model Validierung')
    parser.add_argument('--device', type=str, default='Vitocal',
                        help='Gerätename aus hplib')
    parser.add_argument('--hplib', type=str,
                        default='data/raw/hplib_database.csv',
                        help='Pfad zur hplib-Datenbank')
    parser.add_argument('--no-plots', action='store_true',
                        help='Plots nicht erstellen')

    args = parser.parse_args()

    print("=" * 70)
    print("SCRIPT 1: BASIC DESIGN MODEL VALIDIERUNG")
    print("=" * 70)

    # ========================================================================
    # SCHRITT 1: MODELL ERSTELLEN UND SIMULIEREN
    # ========================================================================
    print("\nSCHRITT 1: Modell erstellen und simulieren")
    print("-" * 70)

    model = BasicDesignModel(
        device_name=args.device,
        hplib_path=args.hplib
    )

    df_results = model.run_validation_study()

    # ========================================================================
    # SCHRITT 2: PLOTS ERSTELLEN
    # ========================================================================
    if not args.no_plots:
        print("\n\nSCHRITT 2: Plots erstellen")
        print("-" * 70)

        # Lade Herstellerdaten (falls vorhanden)
        df_ref = model.manufacturer_data

        plot_basic_validation(
            df=df_results,
            df_ref=df_ref,
            output_dir='results/plots'
        )

        print("\n✓ 3 Plots erstellt in results/plots/")

    # ========================================================================
    # SCHRITT 3: ZUSAMMENFASSUNG
    # ========================================================================
    print("\n\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"✓ Simuliert:  {len(df_results)} Punkte")
    print(f"✓ Daten:      data/results/basic_model/validation_6points.csv")
    if not args.no_plots:
        print(f"✓ Plots:      results/plots/ (3 Stück)")

    print("\nNächster Schritt:")
    print("  → python scripts/2_run_offdesign_study.py")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen")
    except Exception as e:
        print(f"\n\n❌ FEHLER: {e}")
        import traceback

        traceback.print_exc()