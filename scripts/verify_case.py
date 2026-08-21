"""Verifica geometrica: rigenera e sonda punti campione dentro/fuori il solido."""
import bpy, bmesh, math, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(SCRIPT_DIR, "build_case.py")).read()
g = {"__name__": "__main__",
     "__file__": os.path.join(SCRIPT_DIR, "build_case.py")}
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, "build_case.py", "exec"), g)

base, lid = g["base"], g["lid"]


def tree(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    t = BVHTree.FromBMesh(bm)
    return t, bm


def inside(t, p, d=Vector((0.0, 0.0, 1.0))):
    """conteggio intersezioni lungo d: dispari = dentro il solido"""
    n, org = 0, Vector(p) + d * 1e-4
    while True:
        hit = t.ray_cast(org, d)
        if hit[0] is None:
            return n % 2 == 1
        n += 1
        org = hit[0] + d * 1e-4


def stats(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    vol = bm.calc_volume(signed=True)
    # numero di gusci separati
    seen, shells = set(), 0
    for v in bm.verts:
        if v in seen:
            continue
        shells += 1
        stack = [v]
        while stack:
            w = stack.pop()
            if w in seen:
                continue
            seen.add(w)
            for e in w.link_edges:
                stack.append(e.other_vert(w))
    bm.free()
    return non_manifold, vol, shells


HX, HY = g["HX"], g["HY"]
RIM_Z, WALL, INNER_R = g["RIM_Z"], g["WALL"], g["INNER_R"]
GM, GW, GL = g["GROOVE_MID"], g["GROOVE_W"], g["GROOVE_LAND"]
rr = g["rounded_rect"]

tb, bmb = tree(base)
tl, bml = tree(lid)

fails, total = [], 0


def check(name, cond):
    global total
    total += 1
    print(("  OK  " if cond else "  FAIL") + "  " + name)
    if not cond:
        fails.append(name)


print("--- base: cava O-ring (z = RIM_Z-1 = %.1f)" % (RIM_Z - 1))
mid = rr(HX + GM, HY + GM, INNER_R + GM, seg=24)
check("mezzeria cava vuota su tutti i %d campioni" % len(mid),
      all(not inside(tb, (x, y, RIM_Z - 1.0)) for x, y in mid))
land_in = rr(HX + GL / 2, HY + GL / 2, INNER_R + GL / 2, seg=24)
check("spalla interna piena su tutti i campioni",
      all(inside(tb, (x, y, RIM_Z - 1.0)) for x, y in land_in))
o = GL + GW + (WALL - GL - GW) / 2
land_out = rr(HX + o, HY + o, INNER_R + o, seg=24)
check("spalla esterna piena su tutti i campioni",
      all(inside(tb, (x, y, RIM_Z - 1.0)) for x, y in land_out))
check("fondo cava a z=%.1f pieno appena sotto" % g["GROOVE_Z0"],
      all(inside(tb, (x, y, g["GROOVE_Z0"] - 0.3)) for x, y in mid))

print("--- base: interno")
check("cavita' vuota (0,0,20)", not inside(tb, (0, 0, 20)))
check("pavimento pieno (0,0,1)", inside(tb, (0, 0, 1)))
check("solco cella vuoto", not inside(tb, (g["CELL_CX"], g["CELL_CY"], 13.4)))
# sotto la culla resta solo il pavimento: si sonda sotto la sua faccia superiore
check("pavimento pieno sotto la cella",
      inside(tb, (g["CELL_CX"], g["CELL_CY"], g["FLOOR"] - 0.5)))

print("--- base: sella a bande")
# Gli smussi della banda si sommano proprio dove il fianco e` piu` sottile (in
# cima, al labbro): se la somma si avvicina allo spessore del fianco, l'angolo
# diventa un cuneo che la stampante non fa.
check("labbro: piano minimo %.2f >= 0.8 mm" % g["CRADLE_LIP_MIN"],
      g["CRADLE_LIP_MIN"] >= 0.8)
CY, HW, TOP = g["CELL_CY"], g["CRADLE_HW"], g["CRADLE_TOP"]
CELL_D, CELL_CLR, CELL_R = g["CELL_D"], g["CELL_CLR"], g["CELL_R"]
BW, RW = g["CRADLE_BAND_W"], g["CRADLE_RELIEF_W"]
for i, bx in enumerate(g["CRADLE_BAND_X"]):
    check("banda %d: fianco +Y pieno" % i,
          inside(tb, (bx, CY + HW - 0.4, g["FLOOR"] + 3)))
    check("banda %d: fianco pieno appena sotto il labbro" % i,
          inside(tb, (bx, CY + HW - 0.4, TOP - 0.5)))
    check("banda %d: niente materiale sopra il labbro" % i,
          not inside(tb, (bx, CY + HW - 0.4, TOP + 0.5)))
    # la bocca deve essere libera per tutto il diametro dello scavo: se la culla
    # stringesse, questo punto al labbro sarebbe dentro il materiale
    check("banda %d: bocca libera a filo scavo" % i,
          not inside(tb, (bx, CY + CELL_R - 0.05, TOP - 0.05)))
    # niente invito: subito sotto il labbro il fianco deve essere pieno fino
    # allo scavo, senza faccette a spillo
    check("banda %d: labbro a spigolo netto, nessuna faccetta" % i,
          inside(tb, (bx, CY + CELL_R + 0.2, TOP - 0.15)))
    check("banda %d: gola di sfogo vuota" % i,
          not inside(tb, (bx, CY, g["FLOOR"] + 0.2)))
    check("banda %d: gola larga %.0f, fuori e` pieno" % (i, RW),
          inside(tb, (bx, CY + RW / 2.0 + 1.2, g["FLOOR"] + 0.2)))
# fra una banda e l'altra la sella non c'e': solo pavimento
for i in range(len(g["CRADLE_BAND_X"]) - 1):
    xm = (g["CRADLE_BAND_X"][i] + g["CRADLE_BAND_X"][i + 1]) / 2.0
    check("vuoto fra le bande a x=%.1f" % xm,
          not inside(tb, (xm, CY + HW - 0.4, g["FLOOR"] + 3)))
    check("pavimento intatto fra le bande a x=%.1f" % xm,
          inside(tb, (xm, CY, g["FLOOR"] - 0.5)))
# lo smusso d'invito non deve incidere la parete -Y fra una banda e l'altra
check("parete -Y intatta fra le bande",
      inside(tb, (g["CRADLE_BAND_X"][0] + BW, -g["HY"] - 0.3, TOP - 0.4)))
for s in (-1, 1):
    x = g["BOARD_CX"] + s * 10.15
    check("nessun dentino scheda a x=%.1f" % x, not inside(tb, (x, 5.0, 8.0)))
check("nessun dentino scheda (angolo +Y)",
      not inside(tb, (g["BOARD_CX"] + 10.15, 20.0, 8.0)))

print("--- base: fori")
check("passacavo passante (parete +X)",
      not inside(tb, (HX + WALL / 2, g["GLAND_CY"], g["GLAND_CZ"]), Vector((0, 0, 1.0))))
check("passacavo: parete piena 6 mm piu' in su",
      inside(tb, (HX + WALL / 2, g["GLAND_CY"], g["GLAND_CZ"] + 6)))
check("foro N passante", not inside(tb, (-HX - WALL / 2, 0, g["CONN_CZ"])))
check("scasso interno N vuoto (sopra il foro)",
      not inside(tb, (-HX - g["CONN_RELIEF_DEPTH"] / 2, 0, g["CONN_CZ"] + 10)))
check("parete -X piena a filo attorno al foro (appoggio del dado)",
      inside(tb, (-g["OUT_X"] / 2 + 1, 0, g["CONN_CZ"] + 10)))
check("parete -X piena fuori dallo scasso", inside(tb, (-g["OUT_X"] / 2 + 1, 15, 20)))
check("materiale sotto la cava sopra lo scasso",
      inside(tb, (-HX - g["CONN_RELIEF_DEPTH"] / 2, 0,
                  (g["CONN_CZ"] + g["CONN_RELIEF_D"] / 2 + g["GROOVE_Z0"]) / 2)))
for lx, ly in g["LUG_XY"]:
    check("inserto M3 vuoto a (%.0f,%.1f)" % (lx, ly),
          not inside(tb, (lx, ly, RIM_Z - 2)))
    check("lug pieno sotto l'inserto a (%.0f,%.1f)" % (lx, ly),
          inside(tb, (lx, ly, RIM_Z - g["INSERT_DEPTH"] - 3)))
    check("lug: 1.5mm di parete attorno all'inserto (%.0f,%.1f)" % (lx, ly),
          inside(tb, (lx, ly + math.copysign(g["INSERT_D"] / 2 + 0.5, ly), RIM_Z - 2)))
print("--- base: alette M4")
EHY, ET, EW = g["EAR_HOLE_Y"], g["EAR_T"], g["EAR_W"]
GT, GOFF, GH = g["EAR_GUSSET_T"], g["EAR_GUSSET_OFF"], g["EAR_GUSSET_H"]
CH, OHY = g["EAR_CHAMF"], g["OUT_HY"]
for sx, sy in g["EAR_XY"]:
    hy = sy * EHY
    check("foro M4 aletta (%+.0f,%+.0f)" % (sx, sy), not inside(tb, (sx, hy, ET / 2)))
    # il foro deve restare scoperto: la vecchia nervatura unica ci passava sopra
    check("foro M4 sgombro sopra (%+.0f,%+.0f)" % (sx, sy),
          all(not inside(tb, (sx, hy, z)) for z in (ET + 1, ET + 3, ET + GH - 1)))
    check("testa M4 r=3.5 libera (%+.0f,%+.0f)" % (sx, sy),
          all(not inside(tb, (sx + kx * 3.5, hy + ky * 3.5, ET + 0.5))
              for kx, ky in ((1, 0), (-1, 0), (0, 1), (0, -1))))
    for k in (-1, 1):
        check("nervatura piena a x=%+.1f (%+.0f,%+.0f)" % (sx + k * GOFF, sx, sy),
              inside(tb, (sx + k * GOFF, sy * (OHY + 1.0), ET + GH / 2)))
        # piede della nervatura: deve poggiare sull'aletta, non sul vuoto
        check("nervatura appoggiata sull'aletta (%+.1f)" % (sx + k * GOFF),
              inside(tb, (sx + k * (GOFF + GT / 2 - 0.2),
                          sy * (OHY + GH - 0.5), ET / 2)))
    check("spigolo esterno smussato (%+.0f,%+.0f)" % (sx, sy),
          all(not inside(tb, (sx + k * (g["EAR_L"] / 2 - CH / 2),
                              sy * (OHY + EW - CH / 2 + 0.4), ET / 2))
              for k in (-1, 1)))
    check("punta dell'aletta piena in mezzeria (%+.0f,%+.0f)" % (sx, sy),
          inside(tb, (sx, sy * (OHY + EW - 0.4), ET / 2)))

print("--- base: raccordi lug/parete")
M, OHY = g["LUG_FIL_M"], g["OUT_HY"]
for lx, ly in g["LUG_XY"]:
    s = math.copysign(1.0, ly)
    for k in (-1, 1):
        check("raccordo pieno a %.1f dal lug (%.0f,%.1f)" % (k * (M - 1.5), lx, ly),
              inside(tb, (lx + k * (M - 1.5), s * (OHY + 0.25), RIM_Z / 2)))
        x = lx + k * (M + 1.5)
        check("niente materiale oltre il raccordo a x=%.1f (%.0f,%.1f)" % (x, lx, ly),
              abs(x) > g["OUT_X"] / 2 or
              not inside(tb, (x, s * (OHY + 0.25), RIM_Z / 2)))
    # sonda sulla faccia interna, riportata dentro il tratto rettilineo della
    # cavita' (agli x dei lug d'angolo li' c'e' lo spigolo pieno della scatola)
    xi = math.copysign(min(abs(lx), HX - INNER_R - 1), lx)
    check("il raccordo non entra in cavita' (%.0f,%.1f)" % (lx, ly),
          not inside(tb, (xi, s * (HY - 0.3), RIM_Z / 2)))
    check("coperchio: stesso raccordo (%.0f,%.1f)" % (lx, ly),
          inside(tl, (lx + M - 1.5, s * (OHY + 0.25), RIM_Z + g["LID_T"] / 2)))

print("--- lid")
check("nessuna costola ferma-cella",
      not inside(tl, (g["CELL_CX"], g["CELL_CY"], RIM_Z - 1.5)))
check("piastra piena al centro", inside(tl, (0, 0, RIM_Z + 1.5)))
lip = rr(HX - g["LIP_CLR"] - g["LIP_W"] / 2, HY - g["LIP_CLR"] - g["LIP_W"] / 2,
         INNER_R - g["LIP_CLR"] - g["LIP_W"] / 2, seg=24)
check("labbro continuo su tutti i campioni",
      all(inside(tl, (x, y, RIM_Z - 1.5)) for x, y in lip))
for lx, ly in g["LUG_XY"]:
    check("passante vite coperchio (%.0f,%.1f)" % (lx, ly),
          not inside(tl, (lx, ly, RIM_Z + 1.5)))
check("coperchio: niente materiale sopra la cava (deve appoggiare piano)",
      all(inside(tl, (x, y, RIM_Z + 1.0)) for x, y in mid))

print("--- topologia")
for name, ob in (("base", base), ("lid", lid)):
    nm, vol, shells = stats(ob)
    check("%s: manifold (%d spigoli non-manifold)" % (name, nm), nm == 0)
    check("%s: un solo guscio (%d)" % (name, shells), shells == 1)
    print("        volume %.1f cm3  (~%.0f g in PETG solido)" % (vol / 1000, vol * 1.27 / 1000))

print("\n%d test falliti su %d" % (len(fails), total))
if fails:
    print("FAILED:", fails)
