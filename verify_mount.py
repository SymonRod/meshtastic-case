"""Verifica geometrica della montatura: rigenera e sonda punti campione.

Stesso metodo di verify_case.py (BVHTree + conteggio intersezioni): sul telaio
e sulle clip il render non dice niente di utile, quello che conta e` se il
pannello ci sta, se le linguette sono davvero libere di flettere e se i
piedini cadono sui lug del coperchio.

    blender --background --factory-startup --python verify_mount.py
"""
import contextlib
import math
import io
import os

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "build_mount.py")).read()
g = {"__name__": "__main__", "__file__": os.path.join(HERE, "build_mount.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, "build_mount.py", "exec"), g)

frame, clip = g["frame"], g["clip"]


def tree(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    t = BVHTree.FromBMesh(bm)
    return t, bm


def inside(t, p, d=Vector((0.0, 0.0, 1.0))):
    n, org = 0, Vector(p) + d * 1e-4
    while True:
        hit = t.ray_cast(org, d)
        if hit[0] is None:
            return n % 2 == 1
        n += 1
        org = hit[0] + d * 1e-4


def stats(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    vol = bm.calc_volume(signed=True)
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


fails = []


def probe(t, label, pts, want):
    bad = [p for p in pts if inside(t, p) != want]
    tag = "dentro" if want else "fuori"
    ok = not bad
    print(f"  [{'ok ' if ok else 'FAIL'}] {label}: {len(pts)} punti, atteso {tag}"
          + ("" if ok else f" -- {len(bad)} sbagliati, es. {tuple(round(c, 2) for c in bad[0])}"))
    if not ok:
        fails.append(label)


# ------------------------------------------------------------------ topologia
print("topologia")
for name, ob in (("telaio", frame), ("clip", clip)):
    nm, vol, shells = stats(ob)
    ok = nm == 0 and shells == 1 and vol > 0
    print(f"  [{'ok ' if ok else 'FAIL'}] {name}: {len(ob.data.polygons)} facce, "
          f"spigoli non-manifold {nm}, gusci {shells}, volume {vol / 1000:.2f} cm3 "
          f"(~{vol * 1.27 / 1000:.0f} g in PETG)")
    if not ok:
        fails.append(f"topologia {name}")

# --------------------------------------------------------------------- clip
CZ0, PZ, PT = g["CLIP_Z0"], g["PANEL_Z"], g["PANEL_T"]
LIP_Z0, TZ1 = g["LIP_Z0"], g["TONGUE_Z1"]
CLR, T_T, BLK, TL = g["PANEL_CLR"], g["TONGUE_T"], g["CLIP_BLK"], g["TONGUE_L"]
LIP_START, LIP_OVER = g["LIP_START"], g["LIP_OVER"]
tc, bmc = tree(clip)
mid_z = (CZ0 + PZ) / 2.0
tongue_mid = -CLR - T_T / 2.0          # mezzeria dello spessore della linguetta
lip_z = (LIP_Z0 + TZ1) / 2.0
panel_z = PZ + PT / 2.0                # dentro lo spessore del pannello
us = [BLK + 2.0, BLK + 6.0, BLK + 10.0, BLK + 14.0, BLK + 18.0]

print("clip: linguette")
# la linguetta esiste per tutta la sua lunghezza, su entrambi i bordi
probe(tc, "corpo della linguetta", [(u, tongue_mid, z) for u in us for z in (CZ0 + 1, mid_z, TZ1 - 1)]
      + [(tongue_mid, u, z) for u in us for z in (CZ0 + 1, mid_z, TZ1 - 1)], True)
# ...ed e` SEPARATA dal piano: se l'unione l'avesse incollata al piano non
# flette piu` e lo scatto diventa una frattura.
gap = [(u, v, z) for u in us for v in (-CLR + 0.2, 0.4, 1.0)
       for z in (CZ0 + 0.5, mid_z, PZ - 0.5)]
probe(tc, "aria fra linguetta e piano", gap + [(v, u, z) for (u, v, z) in gap], False)

print("clip: tasca del pannello")


def dp(s, off, z):
    """Punto a distanza `s` dall'angolo lungo la diagonale locale (u = v) e
    `off` in perpendicolare. Asola, svaso e cava della guida corrono tutti
    lungo quella diagonale: campionarli in (u, v) a occhio porta solo a
    prendere il vuoto dell'asola e a leggere fallimenti che non ci sono."""
    h = 0.70710678
    return (s * h - off * h, s * h + off * h, z)


# lo spazio del pannello e` libero fino al dente...
probe(tc, "sede del pannello", [(u, v, panel_z) for u in (3.0, 8.0, 15.0, 25.0)
                                for v in (1.0, 5.0, 15.0, 25.0)], False)
# ...il piano d'appoggio sotto c'e' (fuori dall'asola, che corre in diagonale)...
probe(tc, "piano d'appoggio", [dp(s, off, PZ - 0.8) for s in (6.0, 14.0, 22.0, 29.0)
                               for off in (-9.0, -5.0, 5.0, 9.0)], True)
# ...e il dente scavalca il pannello (e` cio` che lo trattiene in Z). Il punto
# va preso sotto la rampa a 45 gradi, non sopra.
lip_us = [BLK + LIP_START + 2.0, BLK + LIP_START + 6.0, BLK + TL - 1.0]
probe(tc, "dente sopra il pannello", [(u, LIP_OVER - 0.4, LIP_Z0 + 0.3) for u in lip_us]
      + [(LIP_OVER - 0.4, u, LIP_Z0 + 0.3) for u in lip_us], True)
# la rampa d'invito: sopra il dente, verso l'interno, non c'e` materiale
probe(tc, "rampa d'invito", [(u, LIP_OVER - 0.3, TZ1 - 0.3) for u in lip_us]
      + [(LIP_OVER - 0.3, u, TZ1 - 0.3) for u in lip_us], False)
# fermo laterale rigido all'angolo (montante), non affidato alle linguette
probe(tc, "montante d'angolo", [(-CLR - 1.5, -CLR - 1.5, z) for z in (12.0, mid_z, PZ + 1, TZ1 - 0.5)]
      + [(-CLR - 2.8, -CLR - 0.2, CZ0 + 0.5)], True)

print("clip: guida e asola")
S = g["LOCAL_S"]
RH, RW = g["RIB_H"], g["RIB_W"]
ADJ, CB = g["SLOT_ADJ"], g["CBORE_W"]
# la cava della guida e` vuota su tutta la corsa, e la nervatura ci entra
probe(tc, "cava della guida", [dp(s, off, CZ0 + RH / 2.0)
                               for s in (2.0, 10.0, S, 26.0, 30.0)
                               for off in (-RW / 2.0 + 0.2, 0.0, RW / 2.0 - 0.2)], False)
# fianco della cava: appena fuori dalla larghezza della nervatura c'e` materiale
probe(tc, "fianco della guida", [dp(s, off, CZ0 + RH / 2.0) for s in (10.0, S, 26.0)
                                 for off in (-RW / 2.0 - 1.5, RW / 2.0 + 1.5)], True)
# asola passante lungo tutta la corsa di registrazione
probe(tc, "asola di registrazione", [dp(S + d, 0.0, z) for d in (-ADJ + 0.5, 0.0, ADJ - 0.5)
                                     for z in (CZ0 + RH + 0.5, (CZ0 + PZ) / 2.0, PZ - 0.5)], False)
# web fra il cielo della cava e il fondo dello svaso, ai fianchi dell'asola:
# e` il materiale su cui tira la vite della clip
probe(tc, "web attorno all'asola", [dp(S + d, off, (CZ0 + RH + g["CBORE_Z"]) / 2.0)
                                    for d in (-ADJ + 2.0, 0.0, ADJ - 2.0)
                                    for off in (-CB / 2.0 + 0.4, CB / 2.0 - 0.4)], True)
# lo svaso c'e' (la testa bombata ci sparisce dentro, sotto il pannello)
probe(tc, "svaso della testa", [dp(S + d, off, g["CBORE_Z"] + 0.5)
                                for d in (-ADJ + 1.0, 0.0, ADJ - 1.0)
                                for off in (-CB / 2.0 + 0.4, 0.0, CB / 2.0 - 0.4)], False)

# --------------------------------------------------------------------- telaio
print("telaio")
tf, bmf = tree(frame)
LUG_XY, ARM_Z0, ARM_Z1 = g["LUG_XY"], g["ARM_Z0"], g["ARM_Z1"]
PZ0, PZ1, FOOT_H = g["PLATE_Z0"], g["PLATE_Z1"], g["FOOT_H"]
LUG_R, SCREW_D, PILOT_D = g["LUG_R"], g["SCREW_D"], g["PILOT_D"]
# i sei piedini ci sono e sono forati
probe(tf, "piedini", [(lx + dx, ly + dy, FOOT_H / 2.0) for (lx, ly) in LUG_XY
                      for (dx, dy) in ((LUG_R - 0.6, 0), (-LUG_R + 0.6, 0),
                                       (0, LUG_R - 0.6), (0, -LUG_R + 0.6))], True)
probe(tf, "passanti M3", [(lx + d, ly, z) for (lx, ly) in LUG_XY
                          for d in (0.0, SCREW_D / 2.0 - 0.3)
                          for z in (0.3, FOOT_H + 0.5, PZ1 - 0.3)], False)
# il piano non tocca il coperchio fra un piedino e l'altro: sotto PLATE_Z0 e
# fuori dai piedini dev'essere tutto vuoto (a parte i bracci, che partono da 2)
probe(tf, "aria sotto il piano", [(x, y, FOOT_H - 0.5) for x in (-26.0, 26.0)
                                  for y in (-31.6, 0.0, 31.6)]
      + [(0.0, y, FOOT_H - 0.5) for y in (-20.0, 20.0)], False)
# travi e traverso: il telaio e` UN pezzo, il traverso e` cio` che lega i due lati
probe(tf, "travi longitudinali", [(x, sy * 31.6, (PZ0 + PZ1) / 2.0)
                                  for x in (-56.0, -26.0, 26.0, 56.0) for sy in (-1, 1)], True)
probe(tf, "traverso centrale", [(0.0, y, (PZ0 + PZ1) / 2.0)
                                for y in (-28.0, -15.0, 0.0, 15.0, 28.0)], True)
# bracci: pieni per tutto lo sbalzo, su tutta l'altezza
for sx, sy in g["CORNERS"]:
    (ax, ay), (ex, ey) = g["arm_axis"](sx, sy)
    pts = [(ax + (ex - ax) * k, ay + (ey - ay) * k, z)
           for k in (0.15, 0.35, 0.55, 0.75, 0.95)
           for z in (ARM_Z0 + 0.5, (ARM_Z0 + ARM_Z1) / 2.0, ARM_Z1 - 0.5)]
    probe(tf, f"braccio {sx:+d}{sy:+d}", pts, True)
# piastrino, nervatura e foro pilota
RIB_L, RIB_H, RIB_W = g["RIB_L"], g["RIB_H"], g["RIB_W"]
for sx, sy in g["CORNERS"]:
    _, (ex, ey) = g["arm_axis"](sx, sy)
    gx, gy = sx * g["GX"], sy * g["GY"]
    probe(tf, f"nervatura {sx:+d}{sy:+d}",
          [(ex + gx * d, ey + gy * d, ARM_Z1 + RIB_H / 2.0)
           for d in (-RIB_L / 2.0 + 1.0, -4.0, 4.0, RIB_L / 2.0 - 1.0)], True)
    probe(tf, f"foro pilota {sx:+d}{sy:+d}",
          [(ex, ey, z) for z in (ARM_Z0 + 0.3, (ARM_Z0 + ARM_Z1) / 2.0, ARM_Z1 + RIB_H - 0.3)], False)

# ------------------------------------------------------- montaggio delle clip
# Le quattro clip devono essere LO STESSO PEZZO, ruotato di 0/90/180/270. Vale
# perche` la clip e` simmetrica rispetto alla propria bisettrice e la guida e`
# a 45 gradi esatti. Qui si monta davvero: si trasforma la clip nei quattro
# angoli e si controlla che la nervatura del telaio entri nella cava e che il
# foro pilota caschi nell'asola.
print("montaggio delle clip sul telaio")
import mathutils

ANG = {(-1, -1): 0.0, (1, -1): 90.0, (1, 1): 180.0, (-1, 1): 270.0}
for (sx, sy), deg in ANG.items():
    _, (ex, ey) = g["arm_axis"](sx, sy)
    cx, cy = sx * g["PANEL_HX"], sy * g["PANEL_HY"]
    M = (mathutils.Matrix.Translation((cx, cy, 0.0))
         @ mathutils.Matrix.Rotation(math.radians(deg), 4, 'Z'))
    ob = clip.copy()
    ob.data = clip.data.copy()
    ob.matrix_world = M
    bpy.context.collection.objects.link(ob)
    ob.data.transform(M)
    ob.matrix_world = mathutils.Matrix.Identity(4)
    tcc, _ = tree(ob)
    # la nervatura sta nella cava (= fuori dal solido della clip)
    rib_pts = [(ex + g["GX"] * sx * d, ey + g["GY"] * sy * d, ARM_Z1 + RIB_H / 2.0)
               for d in (-RIB_L / 2.0 + 1.0, -4.0, 0.0, 4.0, RIB_L / 2.0 - 1.0)]
    probe(tcc, f"nervatura nella cava, angolo {sx:+d}{sy:+d}", rib_pts, False)
    # ...ma i fianchi della cava ci sono, se no non fa da antirotazione
    side = [(ex + g["GX"] * sx * d - g["GY"] * sy * o, ey + g["GY"] * sy * d + g["GX"] * sx * o,
             ARM_Z1 + RIB_H / 2.0)
            for d in (-4.0, 4.0) for o in (-RIB_W / 2.0 - 1.5, RIB_W / 2.0 + 1.5)]
    probe(tcc, f"fianchi della cava, angolo {sx:+d}{sy:+d}", side, True)
    # l'asse del foro pilota casca nell'asola su tutta la corsa
    adj = g["SLOT_ADJ"]
    slot = [(ex + g["GX"] * sx * d, ey + g["GY"] * sy * d, z)
            for d in (-adj + 0.5, 0.0, adj - 0.5) for z in (ARM_Z1 + RIB_H + 0.5, 14.0)]
    probe(tcc, f"asola sul foro pilota, angolo {sx:+d}{sy:+d}", slot, False)
    bpy.data.objects.remove(ob, do_unlink=True)

# ------------------------------------------------- telaio contro il coperchio
lid_path = os.path.join(HERE, "case_lid.stl")
if os.path.exists(lid_path):
    print("telaio contro il coperchio (case_lid.stl)")
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=lid_path)
    lid = [o for o in bpy.data.objects if o not in before][0]
    tl, bml = tree(lid)
    LID_TOP = max(v.co.z for v in lid.data.vertices)
    # ogni piedino deve cadere INTERAMENTE sul lug: e` l'unico punto in cui il
    # coperchio e` sostenuto dalla vite. Fuori dal lug il coperchio e` una
    # piastra da 3.2 e il piedino la inarcherebbe.
    pts = [(lx + dx, ly + dy, LID_TOP - 0.4) for (lx, ly) in LUG_XY
           for (dx, dy) in ((LUG_R - 0.2, 0), (-LUG_R + 0.2, 0),
                            (0, LUG_R - 0.2), (0, -LUG_R + 0.2),
                            (LUG_R * 0.7, LUG_R * 0.7), (-LUG_R * 0.7, -LUG_R * 0.7))]
    probe(tl, "piedini dentro il profilo del lug", pts, True)
    # e niente del telaio deve scendere sotto il piano d'appoggio
    zmin = min(v.co.z for v in frame.data.vertices)
    ok = abs(zmin) < 1e-6
    print(f"  [{'ok ' if ok else 'FAIL'}] quota minima del telaio {zmin:.3f} "
          f"(dev'essere 0: sotto c'e` il coperchio)")
    if not ok:
        fails.append("quota minima telaio")
else:
    print("telaio contro il coperchio: case_lid.stl assente, salto")

print()
print("VERIFICA FALLITA:", ", ".join(fails)) if fails else print("verifica: tutto ok")
