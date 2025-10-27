"""
DEBUG-TEST - Findet heraus warum TESPy nicht konvergiert
=========================================================

Zeigt alle Parameter und hilft beim Debuggen

Verwendung:
    python debug_test.py

Autor: A. Lohrmann
"""

import sys
from pathlib import Path

# Füge Pfade hinzu (aus tests/ Ordner)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'models'))
sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'utils'))

from basic_design_model import BasicDesignModel

print("=" * 70)
print("DEBUG-TEST: TESPy Parameter".center(70))
print("=" * 70)

# Erstelle Modell
print("\n→ Erstelle Modell...")
model = BasicDesignModel(
    device_name="Vitocal",
    hplib_path=str(PROJECT_ROOT / "data" / "raw" / "hplib_database.csv")
)

print("\n→ Parameter:")
for key, val in model.params.items():
    print(f"  {key:20} = {val}")

# Teste EINEN Punkt mit Debug-Info
print("\n" + "=" * 70)
print("TEST: B0/W35 (Nennpunkt)")
print("=" * 70)

model.build_network()
model.set_operating_point(T_source=0, T_supply=35)

# Zeige alle Verbindungen
print("\n→ Kältemittel-Verbindungen:")
for label, conn in model.connections['refrigerant'].items():
    print(f"\n  {label}:")
    # Zeige gesetzte Parameter
    attrs = []
    if conn.T.is_set: attrs.append(f"T={conn.T.val:.1f}°C")
    if conn.p.is_set: attrs.append(f"p={conn.p.val:.1f}bar")
    if conn.m.is_set: attrs.append(f"m={conn.m.val:.3f}kg/s")
    if conn.h.is_set: attrs.append(f"h={conn.h.val:.1f}kJ/kg")
    if hasattr(conn, 'Td_bp') and conn.Td_bp.is_set:
        attrs.append(f"Td_bp={conn.Td_bp.val:.1f}K")

    if attrs:
        print(f"    " + ", ".join(attrs))
    else:
        print(f"    (keine Parameter gesetzt)")

print("\n→ Heizkreis:")
for label, conn in model.connections['heating'].items():
    print(f"  {label}: T={conn.T.val:.1f}°C, m={conn.m.val:.3f}kg/s, p={conn.p.val:.1f}bar")

print("\n→ Quellkreis:")
for label, conn in model.connections['source'].items():
    print(f"  {label}: T={conn.T.val:.1f}°C, m={conn.m.val:.3f}kg/s, p={conn.p.val:.1f}bar")

# Zähle Parameter
print("\n→ Zähle Parameter...")
total_params = 0

# Kältemittel (5 Verbindungen × ~3-4 Parameter)
for conn in model.connections['refrigerant'].values():
    params = sum([
        conn.T.is_set,
        conn.p.is_set,
        conn.m.is_set,
        conn.h.is_set,
        hasattr(conn, 'Td_bp') and conn.Td_bp.is_set,
        hasattr(conn, 'x') and conn.x.is_set,
    ])
    total_params += params

# Heizkreis (2 Verbindungen)
for conn in model.connections['heating'].values():
    params = sum([conn.T.is_set, conn.p.is_set, conn.m.is_set])
    total_params += params

# Quellkreis (2 Verbindungen)
for conn in model.connections['source'].values():
    params = sum([conn.T.is_set, conn.p.is_set, conn.m.is_set])
    total_params += params

# Komponenten-Parameter
comp_params = 0
comp_params += 1 if model.components['evaporator'].kA.is_set else 0
comp_params += 1 if model.components['condenser'].kA.is_set else 0
comp_params += 1 if model.components['compressor'].eta_s.is_set else 0

total_params += comp_params

print(f"\n  Verbindungen: {total_params - comp_params}")
print(f"  Komponenten:  {comp_params}")
print(f"  GESAMT:       {total_params}")

# TESPy braucht 19 - wir haben nur 18!
print(f"\n{'=' * 70}")
if total_params < 19:
    print(f"⚠️  NUR {total_params}/19 Parameter gesetzt!")
    print(f"   → Es fehlt 1 Parameter!")
    print(f"\n💡 Lösung: Füge noch einen Parameter hinzu")
    print(f"   Z.B.: Überhitzung, Unterkühlung, oder Druck")
else:
    print(f"✓ Genug Parameter: {total_params}/19")

print("=" * 70)

# Versuche zu lösen
print("\n→ Versuche zu lösen...")
try:
    success = model.solve()
    if success:
        print("✓ ERFOLG! Simulation konvergiert!")
        results = model.get_results()
        print(f"\n  COP:  {results['COP']:.2f}")
        print(f"  P_th: {results['P_th_kW']:.2f} kW")
    else:
        print("❌ Nicht konvergiert")
except Exception as e:
    print(f"❌ Fehler: {e}")

print("\n" + "=" * 70)