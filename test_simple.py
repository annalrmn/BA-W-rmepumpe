"""
ULTRA-SIMPLER TEST - Nur ein Betriebspunkt
===========================================
"""

from tespy.networks import Network
from tespy.components import (Compressor, Valve, CycleCloser,
                              Condenser, HeatExchanger, Sink, Source)
from tespy.connections import Connection
import CoolProp.CoolProp as CP

print("\n" + "="*70)
print("ULTRA-SIMPLER TEST - R410A B5/W35".center(70))
print("="*70 + "\n")

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

# Fluide
c0.set_attr(fluid={'R410A': 1.0})
h1.set_attr(fluid={'water': 1.0})
q1.set_attr(fluid={'water': 1.0})

print("✓ Netzwerk aufgebaut")

# Betriebspunkt B5/W35
T_source = 5
T_supply = 35

# Heizkreis
h1.set_attr(T=30, m=0.24)
h2.set_attr(T=35)

# Quellkreis
q1.set_attr(T=5, m=0.30)
q2.set_attr(T=2)

# Komponenten - VEREINFACHT!
evap.set_attr(pr1=1.0)
comp.set_attr(pr=3.0)  # Druckverhältnis statt eta_s!

# Kältemittel - Massenstrom
c0.set_attr(m=0.05)

# Temperaturen am Kältemittelkreis
c1.set_attr(T=0)  # Verdampferausgang

# Heizleistung
cond.set_attr(Q=-5)  # 5 kW Heizleistung (negativ = Wärmeabgabe)

print("✓ Parameter gesetzt")

# Startwerte
try:
    p_evap = CP.PropsSI('P', 'T', 273.15, 'Q', 0, 'R410A') / 1e5
    p_cond = CP.PropsSI('P', 'T', 313.15, 'Q', 0, 'R410A') / 1e5
except:
    p_evap, p_cond = 8, 24

c0.set_attr(p0=p_evap)
c1.set_attr(p0=p_evap)
c2.set_attr(p0=p_cond)
c3.set_attr(p0=p_cond)
c4.set_attr(p0=p_evap)

print(f"✓ Startwerte: p_evap={p_evap:.1f} bar, p_cond={p_cond:.1f} bar\n")

# Lösen
print("→ Starte Berechnung...\n")
try:
    nw.solve('design')

    if nw.status == 0:
        Q_heat = abs(cond.Q.val)
        P_el = abs(comp.P.val)
        COP = Q_heat / P_el

        print("="*70)
        print("ERFOLG!".center(70))
        print("="*70)
        print(f"\n✓ Simulation erfolgreich!")
        print(f"\nErgebnisse:")
        print(f"  COP:     {COP:.2f}")
        print(f"  P_th:    {Q_heat:.2f} kW")
        print(f"  P_el:    {P_el:.2f} kW")
        print(f"\n  p_evap:  {c1.p.val:.2f} bar")
        print(f"  p_cond:  {c2.p.val:.2f} bar")
        print(f"  T_comp_out: {c2.T.val:.1f} °C")
        print("="*70 + "\n")
    else:
        print(f"❌ Nicht konvergiert (Status: {nw.status})")

except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
