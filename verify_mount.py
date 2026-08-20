"""Verifica geometrica di panel_mount.stl.

Rigenera il pezzo eseguendo build_mount.py nella stessa sessione Blender e poi
lo sonda con test di appartenenza per ray-cast (BVHTree + conteggio
intersezioni), piu` due controlli topologici che il ray-cast non vede:

  - il pezzo e` UN SOLO solido connesso (se una linguetta si stacca dal corpo
    lo slicer stampa un coriandolo e la scatola resta senza aggancio);
  - il pezzo e` chiuso (ogni spigolo su due facce).

    blender --background --factory-startup --python verify_mount.py
"""
import os
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__)) or "/home/rod/meshtastic-case"

# esegue build_mount.py: costanti e mesh vengono da li`, non sono riscritte qui
src = open(os.path.join(HERE, "build_mount.py")).read()
G = {"__name__": "__main__", "__file__": os.path.join(HERE, "build_mount.py")}
exec(compile(src, "build_mount.py", "exec"), G)

mount = G["mount"]
PLATE_T, RISE_H = G["PLATE_T"], G["RISE_H"]
BOSS_R, SCREW_HEAD_H = G["BOSS_R"], G["SCREW_HEAD_H"]
PANEL_HX, PANEL_HY = G["PANEL_HX"], G["PANEL_HY"]
PANEL_T, PANEL_CLR, PANEL_FIT = G["PANEL_T"], G["PANEL_CLR"], G["PANEL_FIT"]
PANEL_BACK, LIP_Z0, LIP_Z1 = G["PANEL_BACK"], G["LIP_Z0"], G["LIP_Z1"]
LIP_OVER, LIP_START = G["LIP_OVER"], G["LIP_START"]
RAIL_T, RAIL_L, TONGUE_L = G["RAIL_T"], G["RAIL_L"], G["TONGUE_L"]
RAIL_IN, RAIL_OUT, RAIL_END = G["RAIL_IN"], G["RAIL_OUT"], G["RAIL_END"]
PAD_W = G["PAD_W"]
SCREW_D, CBORE_D, CBORE_DEPTH = G["SCREW_D"], G["CBORE_D"], G["CBORE_DEPTH"]
LUG_XY, LUG_CY, LUG_R = G["LUG_XY"], G["LUG_CY"], G["LUG_R"]
CORNERS, CASE_HX = G["CORNERS"], G["CASE_HX"]
END_X, END_W, SPINE_W = G["END_X"], G["END_W"], G["SPINE_W"]
mapper = G["mapper"]

bpy.context.view_layer.update()
bm = bmesh.new()
bm.from_mesh(mount.data)
bm.transform(mount.matrix_world)
bvh = BVHTree.FromBMesh(bm)

RAY = Vector((0.13, 0.29, 0.948)).normalized()   # direzione "storta" apposta:
                                                 # niente facce parallele


def inside(p):
    """Test di appartenenza: conta le intersezioni verso l'alto."""
    origin = Vector(p)
    hits = 0
    pos = origin.copy()
    for _ in range(64):
        hit = bvh.ray_cast(pos + RAY * 1e-4, RAY)
        if hit[0] is None:
            break
        hits += 1
        pos = hit[0]
    return hits % 2 == 1


FAILS = []
NCHECK = [0]


def want(state, p, what):
    NCHECK[0] += 1
    got = inside(p)
    if got != state:
        FAILS.append(f"{what}: ({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}) "
                     f"{'vuoto' if not got else 'pieno'}, atteso "
                     f"{'pieno' if state else 'vuoto'}")


def solid(p, what):
    want(True, p, what)


def empty(p, what):
    want(False, p, what)


# ------------------------------------------------------- topologia del pezzo

def shells(bmesh_obj):
    """Componenti connesse per spigoli."""
    seen = set()
    count = 0
    for f in bmesh_obj.faces:
        if f.index in seen:
            continue
        count += 1
        stack = [f]
        seen.add(f.index)
        while stack:
            cur = stack.pop()
            for e in cur.edges:
                for nb in e.link_faces:
                    if nb.index not in seen:
                        seen.add(nb.index)
                        stack.append(nb)
    return count


bm.faces.ensure_lookup_table()
n_shells = shells(bm)
open_edges = [e for e in bm.edges if len(e.link_faces) != 2]
print(f"topologia: {len(bm.verts)} vertici, {len(bm.faces)} facce, "
      f"{n_shells} guscio/i, {len(open_edges)} spigoli aperti")
if n_shells != 1:
    FAILS.append(f"il pezzo e` in {n_shells} gusci separati: non e` un pezzo solo")
if open_edges:
    FAILS.append(f"{len(open_edges)} spigoli non-manifold/aperti")

# ------------------------------------------------------------ corpo e anello

for lx, ly in LUG_XY:
    # foro vite passante
    for z in (0.5, PLATE_T - 0.5):
        empty((lx, ly, z), "foro M3")
    # svaso sopra
    empty((lx + CBORE_D / 2.0 - 0.6, ly, RISE_H - 0.5), "svaso M3")
    # sotto lo svaso c'e` ancora materiale (e` quello che la vite tira)
    solid((lx + CBORE_D / 2.0 - 0.6, ly, PLATE_T - 0.5), "cielo dello svaso")
    # materiale attorno al foro
    for dx, dy in ((SCREW_D / 2.0 + 1.0, 0.0), (0.0, SCREW_D / 2.0 + 1.0)):
        solid((lx + dx, ly + dy, 1.0), "trave attorno alla vite")

# le travi corrono da un capo all'altro sopra i lug (saltando i fori)
for x in range(-60, 61, 5):
    if min(abs(x - lx) for lx in G["LUG_CX"]) < CBORE_D / 2.0 + 0.5:
        continue
    for sy in (-1, 1):
        solid((x, sy * LUG_CY, 1.5), "trave longitudinale")

# traverse d'estremita`: chiudono l'anello e stanno FUORI dalla scatola
for sx in (-1, 1):
    for y in (-20.0, 0.0, 20.0):
        solid((sx * END_X, y, PLATE_T / 2.0), "traversa d'estremita`")
    empty((sx * (CASE_HX - 1.0), 0.0, PLATE_T / 2.0), "sopra il coperchio, in mezzeria")
    # il bordo interno della traversa non sconfina sulla scatola
    empty((sx * (END_X - END_W / 2.0 - 0.4), 0.0, PLATE_T / 2.0), "aria fra traversa e scatola")

# il pezzo non appoggia sulla campata centrale del coperchio: a z=0, dentro
# l'impronta della scatola, c'e` materiale solo nella fascia delle travi
for x in (-40.0, -20.0, 0.0, 20.0, 40.0):
    for y in (0.0, 10.0, 20.0, 25.0):
        empty((x, y, 0.2), "campata centrale del coperchio libera")
        empty((x, -y, 0.2), "campata centrale del coperchio libera")

# la lastra e` SOTTILE: fra un bosso e l'altro, sopra PLATE_T non c'e` niente.
# (i bracci partono dai lug d'angolo e se ne vanno in diagonale, quindi lungo
# la trave restano solo i bossi a salire)
for x in range(-45, 46, 5):
    if abs(x) < BOSS_R + 1.5:                   # bosso della vite centrale
        continue
    for sy in (-1, 1):
        empty((x, sy * LUG_CY, PLATE_T + 0.5), "lastra sottile fra i bossi")

# i bossi invece salgono fino a RISE_H, e la testa della vite ci sta dentro
for lx, ly in LUG_XY:
    solid((lx + BOSS_R - 1.0, ly, RISE_H - 0.5), "bosso della vite")
    empty((lx + CBORE_D / 2.0 - 0.6, ly, PLATE_T + SCREW_HEAD_H + 0.2),
          "spazio per la testa della vite")
if G["HEAD_GAP"] < 0.5:
    FAILS.append(f"la testa della vite arriva a {G['HEAD_GAP']:.1f} mm dal pannello")

# bracci diagonali continui dal lug d'angolo alla testa, e alti quanto RISE_H
for sx, sy in CORNERS:
    ax, ay = sx * 52.0, sy * LUG_CY
    ex, ey = sx * (PANEL_HX - G["HEAD_IN"]), sy * (PANEL_HY - G["HEAD_IN"])
    for t in [i / 20.0 for i in range(2, 20)]:   # t=0 e` il foro del lug,
                                                 # t=1 la faccia di testa
        px, py = ax + (ex - ax) * t, ay + (ey - ay) * t
        solid((px, py, 1.5), "braccio")
        solid((px, py, RISE_H - 0.5), "braccio alto fino al pannello")

# ------------------------------------------------------- alloggiamento pannello
# Lo spazio che occupa il pannello (z da RISE_H a PANEL_BACK, dentro il
# perimetro rientrato di PANEL_CLR) deve essere COMPLETAMENTE libero: se
# qualcosa ci sporge dentro, il pannello non ci appoggia in piano.
zmid = RISE_H + PANEL_T / 2.0
for i in range(41):
    t = -1.0 + 2.0 * i / 40.0
    for edge in range(4):
        d = PANEL_HX - 1.0
        if edge == 0:
            p = (t * d, PANEL_HY - 1.0, zmid)
        elif edge == 1:
            p = (t * d, -(PANEL_HY - 1.0), zmid)
        elif edge == 2:
            p = (PANEL_HX - 1.0, t * d, zmid)
        else:
            p = (-(PANEL_HX - 1.0), t * d, zmid)
        empty(p, "volume del pannello libero")
for x in (-60.0, 0.0, 60.0):
    for y in (-60.0, 0.0, 60.0):
        empty((x, y, zmid), "volume del pannello libero")

# appoggio: subito sotto il pannello, agli angoli e lungo le diagonali,
# ci deve essere materiale
for sx, sy in CORNERS:
    L = mapper(sx, sy)
    for u, v in ((1.0, 1.0), (RAIL_L - 1.5, 1.0),
                 (1.0, RAIL_L - 1.5), (PAD_W - 1.0, PAD_W - 1.0)):
        x, y = L(u, v)
        solid((x, y, RISE_H - 0.5), "piano d'appoggio d'angolo")
    # il braccio arriva sullo spigolo rientrante fra i due rami e ci si
    # innesta di piatto: subito dietro la faccia di testa c'e` materiale
    x, y = L(PAD_W + 1.0, PAD_W + 1.0)
    solid((x, y, RISE_H - 0.5), "innesto del braccio sul piano")

# ------------------------------------------------------------------ montanti
for sx, sy in CORNERS:
    L = mapper(sx, sy)
    for swap in (False, True):
        def P(u, v, _s=swap):
            return L(v, u) if _s else L(u, v)
        vmid = RAIL_IN - RAIL_T / 2.0
        # tratto rigido della lamella: pieno fino in cima, fuori dal pannello
        for u in (RAIL_OUT + 0.5, RAIL_L / 2.0, RAIL_L - 1.0):
            x, y = P(u, vmid)
            solid((x, y, LIP_Z1 - 0.5), "montante d'angolo")
        # ed e` fasciato dal piano d'appoggio per tutto quel tratto: e` questo
        # a fissare la radice della linguetta, ora che il blocco non c'e` piu`
        for u in (RAIL_OUT + 0.5, RAIL_L / 2.0, RAIL_L - 1.0):
            x, y = P(u, 0.5)
            solid((x, y, RISE_H - 0.5), "piano che fascia il montante")
        # il piano finisce NETTO a RAIL_L: da li` in poi la linguetta ha
        # tutti e due i fianchi liberi
        for u in (RAIL_L + 1.5, RAIL_L + TONGUE_L / 2.0):
            for v in (0.5, PAD_W / 2.0):
                x, y = P(u, v)
                empty((x, y, RISE_H - 0.5), "fianco interno della linguetta libero")
        # fra lamella e bordo del pannello: PANEL_CLR d'aria
        x, y = P(RAIL_L / 2.0, -PANEL_CLR / 2.0)
        empty((x, y, zmid), "aria fra pannello e montante")

# ----------------------------------------------------------------- linguette
for sx, sy in CORNERS:
    L = mapper(sx, sy)
    for swap in (False, True):
        def P(u, v, _s=swap):
            return L(v, u) if _s else L(u, v)
        vmid = RAIL_IN - RAIL_T / 2.0
        # corpo della linguetta, da terra fino in cima
        for u in (RAIL_L + 2.0, RAIL_L + TONGUE_L / 2.0, RAIL_END - 1.0):
            for z in (0.5, RISE_H, LIP_Z1 - 0.3):
                x, y = P(u, vmid)
                solid((x, y, z), "linguetta")
        # dente: scavalca il bordo del pannello. Si sonda appena sopra LIP_Z0,
        # dove la rampa a 45 gradi non ha ancora mangiato il profilo.
        for u in (RAIL_L + LIP_START + 1.0, RAIL_L + TONGUE_L - 1.0):
            x, y = P(u, 0.6)
            solid((x, y, LIP_Z0 + 0.3), "dente")
            # sotto il dente ci passa il pannello
            empty((x, y, zmid), "sotto il dente: passa il pannello")
        # prima di LIP_START il dente non c'e` ancora (e` la` che la linguetta
        # deve poter flettere senza toccare il pannello)
        x, y = P(RAIL_L + 2.0, 0.6)
        empty((x, y, LIP_Z0 + 0.3), "dente assente sulla radice")
        # rampa a 45 gradi: in alto, verso l'interno, il dente e` tagliato
        x, y = P(RAIL_L + TONGUE_L - 2.0, LIP_OVER - 0.2)
        empty((x, y, LIP_Z1 - 0.2), "invito a 45 gradi sul dente")
        # niente aletta di sgancio: fuori dalla linguetta non sporge nulla
        for u in (RAIL_L + TONGUE_L - 2.0, RAIL_L + TONGUE_L / 2.0):
            x, y = P(u, RAIL_OUT - 1.5)
            empty((x, y, LIP_Z1 - 1.0), "niente aletta oltre la linguetta")

# ------------------------------------------------------------------- niente
# materiale sotto il piano di stampa
for sx, sy in CORNERS:
    empty((sx * PANEL_HX, sy * PANEL_HY, -0.5), "niente sotto z=0")

print(f"{NCHECK[0]} punti campione, {len(FAILS)} falliti")
for f in FAILS[:25]:
    print("  !!", f)
bm.free()
if FAILS:
    sys.exit(1)
print("verifica montatura: OK")
