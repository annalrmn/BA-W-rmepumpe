"""
Plotting Functions für Basic Design Model
==========================================

Erstellt 3 Plots für Basic Model Validierung:
1. COP vs. T_source
2. P_th vs. T_source
3. Abweichung

Verwendung:
    from src.utils.plotting import plot_basic_validation

    plot_basic_validation(df_results, df_manufacturer)

Autor: A. Lohrmann
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================================
# KONFIGURATION
# ============================================================================

plt.style.use('seaborn-v0_8-darkgrid')

COLORS = {
    'simulation': '#2E86AB',
    'reference': '#A23B72',
}

FIGSIZE = (10, 6)
DPI = 150


# ============================================================================
# BASIC MODEL PLOTS
# ============================================================================

def plot_basic_validation(df: pd.DataFrame,
                          df_ref: pd.DataFrame = None,
                          output_dir: str = 'results/plots'):
    """
    Erstellt 3 Plots für Basic Model Validierung

    Parameters:
    -----------
    df : pd.DataFrame
        Simulationsergebnisse (6 Punkte)
        Benötigte Spalten: T_source, COP, P_th_kW
    df_ref : pd.DataFrame, optional
        Herstellerdaten zum Vergleich
        Spalten: T_source, COP_ref, P_th_ref_kW
    output_dir : str
        Ausgabe-Verzeichnis
    """
    # Prüfe ob DataFrame leer oder ungültig ist
    if df is None or len(df) == 0:
        print("\n⚠️  Keine Daten zum Plotten!")
        print("   → Simulation muss erst erfolgreich sein")
        return

    # Prüfe ob benötigte Spalten vorhanden sind
    required_cols = ['T_source', 'COP', 'P_th_kW']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"\n⚠️  Fehlende Spalten: {missing_cols}")
        print("   → Kann keine Plots erstellen")
        return

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("\n→ Erstelle Basic Model Plots...")

    # ========================================================================
    # PLOT 1: COP vs. T_source
    # ========================================================================
    print("  → Plot 1: COP vs. T_source...")
    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)

    # Simulation
    ax.plot(df['T_source'], df['COP'],
            marker='o', linewidth=2.5, markersize=10,
            color=COLORS['simulation'], label='Simulation',
            zorder=3)

    # Hersteller (falls vorhanden)
    if df_ref is not None and 'COP_ref' in df_ref.columns:
        ax.plot(df_ref['T_source'], df_ref['COP_ref'],
                marker='s', linewidth=2.5, markersize=9,
                color=COLORS['reference'], label='Hersteller',
                linestyle='--', alpha=0.8, zorder=2)

    ax.set_xlabel('Quelltemperatur [°C]', fontsize=13, fontweight='bold')
    ax.set_ylabel('COP [-]', fontsize=13, fontweight='bold')
    ax.set_title('Leistungszahl vs. Quelltemperatur (W35)',
                 fontsize=15, fontweight='bold', pad=15)
    ax.legend(fontsize=12, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(df['T_source'].min() - 1, df['T_source'].max() + 1)

    plt.tight_layout()
    filename = Path(output_dir) / 'basic_cop_vs_temp.png'
    plt.savefig(filename, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"    ✓ {filename}")

    # ========================================================================
    # PLOT 2: P_th vs. T_source
    # ========================================================================
    print("  → Plot 2: P_th vs. T_source...")
    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)

    # Simulation
    ax.plot(df['T_source'], df['P_th_kW'],
            marker='o', linewidth=2.5, markersize=10,
            color=COLORS['simulation'], label='Simulation',
            zorder=3)

    # Hersteller (falls vorhanden)
    if df_ref is not None and 'P_th_ref_kW' in df_ref.columns:
        ax.plot(df_ref['T_source'], df_ref['P_th_ref_kW'],
                marker='s', linewidth=2.5, markersize=9,
                color=COLORS['reference'], label='Hersteller',
                linestyle='--', alpha=0.8, zorder=2)

    ax.set_xlabel('Quelltemperatur [°C]', fontsize=13, fontweight='bold')
    ax.set_ylabel('Heizleistung [kW]', fontsize=13, fontweight='bold')
    ax.set_title('Heizleistung vs. Quelltemperatur (W35)',
                 fontsize=15, fontweight='bold', pad=15)
    ax.legend(fontsize=12, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(df['T_source'].min() - 1, df['T_source'].max() + 1)

    plt.tight_layout()
    filename = Path(output_dir) / 'basic_pth_vs_temp.png'
    plt.savefig(filename, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"    ✓ {filename}")

    # ========================================================================
    # PLOT 3: Abweichung (nur wenn Referenz vorhanden)
    # ========================================================================
    if df_ref is not None and 'COP_ref' in df.columns:
        print("  → Plot 3: Abweichungs-Analyse...")
        fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)

        # Berechne Abweichung
        cop_dev = ((df['COP'] - df['COP_ref']) / df['COP_ref'] * 100)

        # Balken
        colors = [COLORS['simulation'] if x >= 0 else COLORS['reference']
                  for x in cop_dev]
        bars = ax.bar(df['T_source'], cop_dev,
                      color=colors, alpha=0.7,
                      edgecolor='black', linewidth=1.5)

        # Referenzlinien
        ax.axhline(y=0, color='black', linewidth=2, linestyle='-', zorder=1)
        ax.axhline(y=10, color='gray', linewidth=1, linestyle='--',
                   alpha=0.5, label='±10% Grenze')
        ax.axhline(y=-10, color='gray', linewidth=1, linestyle='--', alpha=0.5)

        ax.set_xlabel('Quelltemperatur [°C]', fontsize=13, fontweight='bold')
        ax.set_ylabel('COP Abweichung [%]', fontsize=13, fontweight='bold')
        ax.set_title('Abweichung: Simulation vs. Hersteller',
                     fontsize=15, fontweight='bold', pad=15)
        ax.legend(fontsize=11, framealpha=0.9)
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')
        ax.set_xlim(df['T_source'].min() - 1, df['T_source'].max() + 1)

        # Werte auf Balken schreiben
        for i, (temp, dev) in enumerate(zip(df['T_source'], cop_dev)):
            ax.text(temp, dev + (1 if dev > 0 else -1),
                    f'{dev:.1f}%',
                    ha='center', va='bottom' if dev > 0 else 'top',
                    fontsize=10, fontweight='bold')

        plt.tight_layout()
        filename = Path(output_dir) / 'basic_deviation.png'
        plt.savefig(filename, dpi=DPI, bbox_inches='tight')
        plt.close()
        print(f"    ✓ {filename}")

    print("\n✓ Alle Basic Model Plots erstellt!")
    print(f"  Gespeichert in: {output_dir}/")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def quick_plot(df: pd.DataFrame, x_col: str, y_col: str,
               title: str, output_file: str):
    """
    Schneller Plot (für Tests)

    Parameters:
    -----------
    df : pd.DataFrame
        Daten
    x_col, y_col : str
        Spaltennamen
    title : str
        Titel
    output_file : str
        Ausgabe-Datei
    """
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)

    ax.plot(df[x_col], df[y_col],
            marker='o', linewidth=2, markersize=8,
            color='#2E86AB')

    ax.set_xlabel(x_col, fontsize=12)
    ax.set_ylabel(y_col, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Plot gespeichert: {output_file}")


# ============================================================================
# MAIN (für Tests)
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("PLOTTING TEST")
    print("=" * 70)

    # Test-Daten erstellen
    df_sim = pd.DataFrame({
        'T_source': [-10, -7, -5, 0, 5, 10],
        'COP': [2.50, 2.70, 2.85, 3.15, 3.40, 3.65],
        'P_th_kW': [3.85, 4.25, 4.55, 5.25, 5.85, 6.45],
        'COP_ref': [2.45, 2.65, 2.80, 3.01, 3.35, 3.60],
        'P_th_ref_kW': [3.80, 4.20, 4.50, 5.23, 5.80, 6.40],
    })

    df_ref = df_sim[['T_source', 'COP_ref', 'P_th_ref_kW']].copy()

    # Plots erstellen
    plot_basic_validation(df_sim, df_ref, output_dir='results/plots')

    print("\n" + "=" * 70)
    print("✓ TEST ERFOLGREICH")
    print("  Plots in: results/plots/")
    print("=" * 70)