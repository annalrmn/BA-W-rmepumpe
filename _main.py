"""
MAIN - Bachelor-Arbeit Wärmepumpen-Modellierung
================================================

Haupt-Script das alle Modelle ausführt

Verwendung:
    python main.py                    # Alles ausführen
    python main.py --basic-only       # Nur Basic Model
    python main.py --device "Daikin"  # Anderes Gerät

Autor: A. Lohrmann
Bachelor-Arbeit 2025
"""

import sys
from pathlib import Path
import argparse

# Füge src zum Pfad hinzu (funktioniert ohne __init__.py!)
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'models'))
sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'utils'))

# Prüfe ob Pfade existieren
models_path = PROJECT_ROOT / 'src' / 'models'
utils_path = PROJECT_ROOT / 'src' / 'utils'

if not models_path.exists():
    print(f"❌ FEHLER: Ordner nicht gefunden: {models_path}")
    print("   → Stelle sicher dass du die Dateien richtig kopiert hast!")
    sys.exit(1)

if not utils_path.exists():
    print(f"❌ FEHLER: Ordner nicht gefunden: {utils_path}")
    print("   → Stelle sicher dass du die Dateien richtig kopiert hast!")
    sys.exit(1)

try:
    from basic_design_model import BasicDesignModel
    from plotting import plot_basic_validation
except ImportError as e:
    print(f"❌ FEHLER beim Importieren: {e}")
    print("\n💡 Prüfe:")
    print(f"   - Existiert {models_path / 'basic_design_model.py'}?")
    print(f"   - Existiert {utils_path / 'plotting.py'}?")
    print(f"   - Existiert {utils_path / 'data_loader.py'}?")
    sys.exit(1)


def print_header(text):
    """Schöner Header"""
    print("\n" + "="*70)
    print(text.center(70))
    print("="*70)


def print_section(text):
    """Schöner Abschnitt"""
    print("\n" + "-"*70)
    print(text)
    print("-"*70)


def main():
    """Haupt-Funktion"""

    # Argument Parser
    parser = argparse.ArgumentParser(
        description='Bachelor-Arbeit: Wärmepumpen-Modellierung'
    )
    parser.add_argument('--device', type=str, default='Vitocal',
                       help='Gerätename aus hplib (z.B. "Vitocal", "Daikin")')
    parser.add_argument('--hplib', type=str,
                       default='data/raw/hplib_database.csv',
                       help='Pfad zur hplib-Datenbank')
    parser.add_argument('--basic-only', action='store_true',
                       help='Nur Basic Model ausführen')
    parser.add_argument('--no-plots', action='store_true',
                       help='Plots nicht erstellen')

    args = parser.parse_args()

    # Start
    print_header("BACHELOR-ARBEIT: WÄRMEPUMPEN-MODELLIERUNG")
    print(f"\nWärmepumpe:  {args.device}")
    print(f"Datenbank:   {args.hplib}")

    try:
        # ====================================================================
        # TEIL 1: BASIC DESIGN MODEL
        # ====================================================================
        print_header("TEIL 1: BASIC DESIGN MODEL")

        print_section("Schritt 1: Modell initialisieren")

        model_basic = BasicDesignModel(
            device_name=args.device,
            hplib_path=args.hplib
        )

        print_section("Schritt 2: 6 Betriebspunkte simulieren")

        df_basic = model_basic.run_validation_study(
            output_dir='data/results/basic_model'
        )

        print(f"\n✓ Basic Model abgeschlossen!")
        print(f"  → {len(df_basic)} Betriebspunkte erfolgreich")
        print(f"  → Daten: data/results/basic_model/validation_6points.csv")

        # Plots erstellen
        if not args.no_plots:
            print_section("Schritt 3: Plots erstellen")

            plot_basic_validation(
                df=df_basic,
                df_ref=model_basic.manufacturer_data,
                output_dir='results/plots'
            )

            print(f"\n✓ 3 Plots erstellt in results/plots/")

        # Zeige Ergebnis-Tabelle
        print_section("Ergebnis-Tabelle")

        if len(df_basic) > 0:
            cols_to_show = ['testpoint', 'T_source', 'COP', 'P_th_kW', 'P_el_kW']
            if 'COP_ref' in df_basic.columns:
                cols_to_show.extend(['COP_ref', 'COP_deviation_%'])

            print("\n" + df_basic[cols_to_show].to_string(index=False))
        else:
            print("\n⚠️  Keine Ergebnisse zum Anzeigen (DataFrame leer)")
            print("   → Simulation nicht erfolgreich")

        # ====================================================================
        # TEIL 2: OFF-DESIGN MODEL (optional, später)
        # ====================================================================
        if not args.basic_only:
            print_header("TEIL 2: OFF-DESIGN MODEL")
            print("\n⏭️  Noch nicht implementiert.")
            print("   → Wird in Woche 3-5 hinzugefügt")
            print("   → Für jetzt: Nur Basic Model fertig!")

        # ====================================================================
        # ZUSAMMENFASSUNG
        # ====================================================================
        print_header("ZUSAMMENFASSUNG")

        print(f"\n✓ Basic Model:    {len(df_basic)} Punkte simuliert")

        if 'COP_deviation_%' in df_basic.columns:
            mean_dev = df_basic['COP_deviation_%'].abs().mean()
            print(f"✓ Mittl. Abw.:    {mean_dev:.1f}%", end="")
            if mean_dev < 10:
                print(" (sehr gut! ✓)")
            elif mean_dev < 20:
                print(" (akzeptabel ⚠️)")
            else:
                print(" (zu hoch ❌)")

        print(f"\n✓ Ergebnisse:")
        print(f"  → CSV:  data/results/basic_model/validation_6points.csv")
        if not args.no_plots:
            print(f"  → Plots: results/plots/ (3 Stück)")

        print(f"\n✓ Bereit für BA-Kapitel 3 (Grundmodell)!")

        print("\n" + "="*70)
        print("ERFOLG! 🎉".center(70))
        print("="*70)

    except FileNotFoundError as e:
        print(f"\n\n❌ FEHLER: Datei nicht gefunden")
        print(f"   {e}")
        print(f"\n💡 Prüfe:")
        print(f"   - Liegt hplib_database.csv in data/raw/?")
        print(f"   - Existieren alle Ordner? (data/results/basic_model, results/plots)")
        return 1

    except Exception as e:
        print(f"\n\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen durch Benutzer")
        sys.exit(1)