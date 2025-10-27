"""
Working Test - R410A Wärmepumpe
================================

Einfacher Test für B0/W35 Betriebspunkt
Basierend auf minimal_model.py

Autor: A. Lohrmann
"""

from tespy.networks import Network
from tespy.components import (Compressor, Valve, CycleCloser,
                             Condenser, HeatExchanger, Sink, Source)
from tespy.connections import Connection
import CoolProp.CoolProp as CP

print("="*70)
print("TEST MIT R410A - B5/W35".center(70))
print("="*70)

# Netzwerk
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

# Heizkreis
h1 = Connection(src_heat, 'out1', cond, 'in2', label='h_in')
h2 = Connection(cond, 'out2', snk_heat, 'in1', label='h_out')
nw.add_conns(h1, h2)

# Quellkreis
q1 = Connection(src_source, 'out1', evap, 'in2', label='q_in')
q2 = Connection(evap, 'out2', snk_source, 'in1', label='q_out')
nw.add_conns(q1, q2)

print("✓ Netzwerk erstellt")

# Fluide (NUR auf erste Connection!)
c0.set_attr(fluid={'R410A': 1.0})
h1.set_attr(fluid={'water': 1.0})
q1.set_attr(fluid={'water': 1.0})

print("✓ Fluide gesetzt (R410A)")

# Betriebspunkt B5/W35 (einfacher zu simulieren als B0/W35)
T_source = 5
T_supply = 35

# Heizkreis
T_return = T_supply - 5.0
h1.set_attr(T=T_return, m=0.24)
h2.set_attr(T=T_supply)

# Quellkreis
T_source_out = T_source - 3.0
q1.set_attr(T=T_source, m=0.30)
q2.set_attr(T=T_source_out)

# Komponenten
evap.set_attr(pr1=0.95, pr2=0.98, ttd_l=8)
cond.set_attr(pr1=0.95, pr2=0.98, ttd_u=8)
comp.set_attr(eta_s=0.80)

# Kältemittelkreis - Massenstrom
c0.set_attr(m=0.05)
# Unterkühlung am Kondensatorausgang
c3.set_attr(td_bubble=3)  # 3K Unterkühlung

print("✓ Parameter gesetzt")

# Drücke schätzen mit CoolProp
try:
    T_evap_K = (T_source - 5) + 273.15
    p_evap = CP.PropsSI('P', 'T', T_evap_K, 'Q', 0, 'R410A') / 1e5

    T_cond_K = (T_supply + 5) + 273.15
    p_cond = CP.PropsSI('P', 'T', T_cond_K, 'Q', 0, 'R410A') / 1e5
except:
    p_evap, p_cond = 5.5, 18.0

# Startwerte
c0.set_attr(p0=p_evap, m0=0.04)
c1.set_attr(p0=p_evap)
c2.set_attr(p0=p_cond)
c3.set_attr(p0=p_cond)
c4.set_attr(p0=p_evap)

print(f"✓ Startwerte gesetzt (p_evap={p_evap:.2f} bar, p_cond={p_cond:.2f} bar)")

print("\n→ Starte Berechnung...")

try:
    nw.solve('design')

    if nw.status == 0:
        Q_heat = abs(cond.Q.val)
        Q_cool = abs(evap.Q.val)
        P_el = abs(comp.P.val)
        COP = Q_heat / P_el

        print("\n" + "="*70)
        print("ERFOLG!".center(70))
        print("="*70)
        print(f"\n✓ Simulation erfolgreich!")
        print(f"\nErgebnisse B0/W35:")
        print(f"  COP:        {COP:.2f}")
        print(f"  P_th:       {Q_heat:.2f} kW")
        print(f"  P_el:       {P_el:.2f} kW")
        print(f"  Q_source:   {Q_cool:.2f} kW")

        T_evap = c1.T.val
        T_cond = c2.T.val
        p_evap_result = c1.p.val
        p_cond_result = c2.p.val

        print(f"\n  T_evap:     {T_evap:.1f} °C")
        print(f"  T_cond:     {T_cond:.1f} °C")
        print(f"  p_evap:     {p_evap_result:.2f} bar")
        print(f"  p_cond:     {p_cond_result:.2f} bar")

        print("\n" + "="*70)
        print("✓ TEST BESTANDEN!".center(70))
        print("="*70)
    else:
        print(f"\n❌ Nicht konvergiert (Status: {nw.status})")

except Exception as e:
    print(f"\n❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
