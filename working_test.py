"""
MIT R134a - Einfacher!
======================

R134a ist einfacher zu berechnen als R410A

Autor: A. Lohrmann
"""

from tespy.networks import Network
from tespy.components import (Compressor, Valve, CycleCloser,
                             Condenser, HeatExchanger, Sink, Source)
from tespy.connections import Connection

print("="*70)
print("TEST MIT R134a - B0/W35".center(70))
print("="*70)

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

# Verbindungen
c0 = Connection(cycle, 'out1', evap, 'in1')
c1 = Connection(evap, 'out1', comp, 'in1')
c2 = Connection(comp, 'out1', cond, 'in1')
c3 = Connection(cond, 'out1', valve, 'in1')
c4 = Connection(valve, 'out1', cycle, 'in1')
nw.add_conns(c0, c1, c2, c3, c4)

h1 = Connection(src_heat, 'out1', cond, 'in2')
h2 = Connection(cond, 'out2', snk_heat, 'in1')
nw.add_conns(h1, h2)

q1 = Connection(src_source, 'out1', evap, 'in2')
q2 = Connection(evap, 'out2', snk_source, 'in1')
nw.add_conns(q1, q2)

print("✓ Netzwerk erstellt")

# Fluide - R134a statt R410A!
c0.set_attr(fluid={'R134a': 1.0})
h1.set_attr(fluid={'water': 1.0})
q1.set_attr(fluid={'water': 1.0})

print("✓ Fluide gesetzt (R134a)")

# Parameter
h1.set_attr(T=30, m=0.24)
h2.set_attr(T=35)
q1.set_attr(T=0, m=0.30)
q2.set_attr(T=-3)

evap.set_attr(pr1=0.99, pr2=0.99, ttd_l=5)
cond.set_attr(pr1=0.99, pr2=0.99, ttd_u=5)
comp.set_attr(eta_s=0.80)
valve.set_attr(pr=1.0)

c1.set_attr(Td_bp=5)

print("✓ Parameter gesetzt")

# Startwerte für R134a (andere Drücke als R410A!)
c0.set_attr(p0=3, T0=-5)
c1.set_attr(p0=3, T0=0)
c2.set_attr(p0=10, T0=70)
c3.set_attr(p0=10, T0=35)
c4.set_attr(p0=3, T0=-5)

c0.set_attr(m0=0.05)

print("✓ Startwerte gesetzt (R134a)")

print("\n→ Starte Berechnung...")

try:
    nw.solve('design')

    Q_heat = abs(cond.Q.val)
    Q_cool = abs(evap.Q.val)
    P_el = abs(comp.P.val)
    COP = Q_heat / P_el

    print("\n" + "="*70)
    print("ERFOLG!".center(70))
    print("="*70)
    print(f"\n✓ Mit R134a funktioniert es!")
    print(f"\nErgebnisse B0/W35:")
    print(f"  COP:        {COP:.2f}")
    print(f"  P_th:       {Q_heat:.2f} kW")
    print(f"  P_el:       {P_el:.2f} kW")
    print(f"  Q_source:   {Q_cool:.2f} kW")

    T_evap = c1.T.val
    T_cond = c2.T.val
    p_evap = c1.p.val
    p_cond = c2.p.val

    print(f"\n  T_evap:     {T_evap:.1f} °C")
    print(f"  T_cond:     {T_cond:.1f} °C")
    print(f"  p_evap:     {p_evap:.2f} bar")
    print(f"  p_cond:     {p_cond:.2f} bar")

    print("\n" + "="*70)
    print("✓ FUNKTIONIERT!".center(70))
    print("="*70)
    print("\n💡 R134a ist einfacher als R410A")
    print("   → Für Tests: Nutze R134a")
    print("   → Für BA: Dann zurück zu R410A")
    print("="*70)

except Exception as e:
    print(f"\n❌ Fehler: {e}")
    import traceback
    traceback.print_exc()















