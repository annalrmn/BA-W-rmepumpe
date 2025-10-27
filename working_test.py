# Minimal TESPy heat pump (R134a) — SimpleHeatExchanger
from tespy.networks import Network
from tespy.components import CycleCloser, Compressor, Valve, SimpleHeatExchanger
from tespy.connections import Connection

hp = Network()
hp.set_attr(T_unit="C", p_unit="bar", h_unit="kJ / kg", iterinfo=False)

# Komponenten
cc = CycleCloser("cycle")
co = SimpleHeatExchanger("condenser")
ev = SimpleHeatExchanger("evaporator")
va = Valve("expansion")
cp = Compressor("compressor")

# Verbindungen
c1 = Connection(cc, "out1", ev, "in1")
c2 = Connection(ev, "out1", cp, "in1")
c3 = Connection(cp, "out1", co, "in1")
c4 = Connection(co, "out1", va, "in1")
c0 = Connection(va, "out1", cc, "in1")
hp.add_conns(c1, c2, c3, c4, c0)

# Specs
co.set_attr(pr=0.98, Q=-1_000_000)   #Kältekreislauf gibt 1MW an Senke ab (an Heizsystem)
ev.set_attr(pr=0.98)
cp.set_attr(eta_s=0.85) #isentroper Wirkungsgrad
c2.set_attr(T=20, x=1, fluid={"R134a": 1}) #gesättigter Dampf bei 20 Grad -> Druck durch coolProp
c4.set_attr(T=80, x=0) #gesättigte Flüssigkeit bei 80Grad -> Druck durch coolProp

# Solve
hp.solve("design")

# kurze KPIs
Qc = abs(co.Q.val)         # W
Pel = cp.P.val             # W
COP = Qc / Pel if Pel else float("nan")
print(f"COP={COP:.3f} | Q_cond={Qc:.0f} W | P_el={Pel:.0f} W")
print(f"p_evap≈{c2.p.val:.2f} bar | p_cond≈{c3.p.val:.2f} bar | ṁ≈{c1.m.val:.3f} kg/s")
print(f"T_suction={c2.T.val:.1f} °C | T_liquid={c4.T.val:.1f} °C")

hp.solve("design")
hp.print_results()
