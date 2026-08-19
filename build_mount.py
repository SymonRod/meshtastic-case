"""Montatura per pannello solare ~170x170, appesa alle 6 viti M3 del coperchio.

Parametrico. Due pezzi da stampare:

  panel_frame.stl  x1  telaio a H: si infila fra le teste delle viti e il
                       coperchio usando TUTTE E SEI le M3, e porta quattro
                       bracci verso gli angoli del pannello.
  panel_clip.stl   x4  clip d'angolo a scatto, identiche, registrabili lungo
                       la diagonale: cambiando pannello si spostano invece di
                       ristampare il telaio.

La scatola non viene toccata: nessun foro nuovo, nessun inserto nuovo. Le
uniche viti in piu` sono quattro M3x10 autofilettanti per bloccare le clip.

Sistema di riferimento: X e Y come in build_case.py (origine al centro della
scatola), ma **z = 0 e` la faccia superiore del coperchio**, cioe` z = 32.1 in
coordinate scatola. Gli STL vengono esportati con z = 0 sul piano di stampa.

    blender --background --factory-startup --python build_mount.py
"""
import math
import os
import re

import bmesh
import bpy

OUT_DIR = os.path.dirname(os.path.abspath(__file__)) or "/home/rod/meshtastic-case"

# ------------------------------------------------- interfaccia con la scatola
# Devono coincidere con build_case.py: sono le quote delle viti del coperchio.
# Il controllo qui sotto rilegge il sorgente e si ferma se qualcuno le cambia.
LUG_CX = (-52.0, 0.0, 52.0)
LUG_CY = 31.6
LUG_R = 4.6
SCREW_D = 3.4
LID_T = 3.2
INSERT_DEPTH = 6.0

# ------------------------------------------------------------------ pannello
PANEL_W, PANEL_H = 170.0, 170.0       # ingombro del pannello (X, Y)
PANEL_T = 2.4                         # spessore del laminato in vetroresina
PANEL_FIT = 0.3                       # aria in Z fra dorso e labbro della clip
PANEL_CLR = 0.4                       # aria in pianta fra bordo e pareti della clip

# --------------------------------------------------------------------- telaio
FOOT_H = 3.5                          # piedini che appoggiano sui sei lug
PLATE_T = 4.0                         # spessore del piano del telaio
SPINE_W = 2 * LUG_R                   # larghezza (Y) delle due travi longitudinali
CROSS_W = 12.0                        # larghezza (X) del traverso centrale
# Il traverso serve a rendere il telaio UN pezzo solo: le tre viti di un lato
# sono allineate e da sole non bloccano la rotazione attorno a quella linea.
# Con tutte e sei le viti il vincolo e` completo.

ARM_W = 9.0                           # larghezza dei bracci
ARM_Z0, ARM_Z1 = 2.0, 9.0             # i bracci sono piu` alti del piano: il
                                      # carico del vento li flette in Z, e in Z
                                      # la sezione conta al quadrato.
CLIP_INSET = 20.0                     # distanza dall'angolo del pannello, in
                                      # diagonale, del centro di registrazione
PAD_L, PAD_W = 26.0, 12.0             # piastrino di testa del braccio
RIB_L, RIB_W, RIB_H = 20.0, 3.0, 1.6  # guida antirotazione sul piastrino
PILOT_D = 2.9                         # foro passante per M3x10 autofilettante

# ----------------------------------------------------------------- clip
PANEL_Z = 16.0                        # dorso del pannello sopra il coperchio
CLIP_Z0 = ARM_Z1                      # la clip appoggia sul piastrino
CLIP_BLK = 10.0                       # lato del blocco rigido d'angolo
CLIP_PLATE = 30.0                     # lato del piano d'appoggio del pannello
CLIP_CHAMF_S = 44.0                   # smusso del piano: taglia oltre u+v
CLIP_WALL = 3.0                       # spessore delle pareti d'angolo
TONGUE_T = 2.4                        # spessore della linguetta elastica
TONGUE_L = 20.0                       # sbalzo libero della linguetta
LIP_OVER = 1.5                        # quanto il dente scavalca il pannello
LIP_H = 1.5                           # altezza del dente
LIP_START = 10.0                      # da dove parte il dente lungo la linguetta
TAB_L, TAB_W = 4.0, 4.0               # aletta per aprire la linguetta a mano
SLOT_ADJ = 12.0                       # corsa di registrazione (per lato)
CBORE_W = 6.4                         # svaso per la testa bombata M3
CBORE_Z = 13.0                        # fondo dello svaso

# ------------------------------------------------------------------- derivate
LUG_XY = [(lx, sy * LUG_CY) for lx in LUG_CX for sy in (-1, 1)]
CORNERS = [(sx, sy) for sx in (-1, 1) for sy in (-1, 1)]

PANEL_HX, PANEL_HY = PANEL_W / 2.0, PANEL_H / 2.0
# La registrazione corre a 45 GRADI ESATTI, non lungo la diagonale del
# pannello. E` cio` che rende le quattro clip lo stesso pezzo: la clip e`
# simmetrica rispetto alla propria bisettrice, quindi le quattro posizioni si
# ottengono ruotandola di 0/90/180/270 gradi -- ma solo se la guida e`
# anch'essa a 45 gradi. Con la guida lungo la diagonale di un pannello
# rettangolare le due clip di un lato andrebbero specchiate, cioe`
# stampate in due versioni. Su pannello rettangolare la corsa allarga W e H
# della stessa quantita`, che e` esattamente quel che serve.
GX = GY = math.sqrt(0.5)

PLATE_Z0, PLATE_Z1 = FOOT_H, FOOT_H + PLATE_T
FOOT_STACK = FOOT_H + PLATE_T                       # materiale sotto la testa vite
SCREW_L = LID_T + FOOT_STACK + (INSERT_DEPTH - 0.7) # lunghezza vite consigliata

PANEL_FRONT = PANEL_Z + PANEL_T
LIP_Z0 = PANEL_FRONT + PANEL_FIT
TONGUE_Z1 = LIP_Z0 + LIP_H
CLIP_H = TONGUE_Z1 - CLIP_Z0

# centro di registrazione: rientrato di CLIP_INSET dall'angolo del pannello,
# a 45 gradi. LOCAL_S e` la stessa quota vista dalla clip.
MOUNT_X = PANEL_HX - CLIP_INSET * GX
MOUNT_Y = PANEL_HY - CLIP_INSET * GY
LOCAL_S = CLIP_INSET                                # ascissa diagonale dall'angolo

# ---------------------------------------------------------------- helpers
# Copiati da build_case.py di proposito: build_case.py resta intoccato e
# autosufficiente, questo file pure.


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def box(name, size, center):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return ob


def cyl(name, radius, depth, center, verts=64):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        location=center, vertices=verts)
    ob = bpy.context.active_object
    ob.name = name
    return ob


def _mesh_object(name, verts, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return ob


def prism(name, poly, z0, z1):
    """Estrusione solida di un poligono CONVESSO fra z0 e z1.

    Tutti i pezzi sono unioni di prismi convessi: cosi` ogni faccia e` piana,
    il solver EXACT non ha ngon concavi da triangolare e -- cosa che qui conta
    di piu` -- non c'e` un solo sottosquadro in stampa."""
    n = len(poly)
    verts = [(x, y, z0) for (x, y) in poly] + [(x, y, z1) for (x, y) in poly]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return _mesh_object(name, verts, faces)


def rect(cx, cy, ux, uy, length, width):
    """Rettangolo di centro (cx, cy), lungo `length` nella direzione (ux, uy)."""
    px, py = -uy, ux
    hl, hw = length / 2.0, width / 2.0
    return [(cx + sl * hl * ux + sw * hw * px, cy + sl * hl * uy + sw * hw * py)
            for (sl, sw) in ((1, 1), (-1, 1), (-1, -1), (1, -1))]


def weld(ob, dist=1e-4):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return ob


def boolean(target, tool, op="DIFFERENCE"):
    mod = target.modifiers.new(name="bool", type="BOOLEAN")
    mod.operation = op
    mod.object = tool
    mod.solver = "EXACT"
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(tool, do_unlink=True)
    return target


def cut(target, tools):
    for t in tools:
        boolean(target, t, "DIFFERENCE")
    return target


def fuse(target, tools):
    for t in tools:
        boolean(target, t, "UNION")
    return target


def check_case_interface():
    """Rilegge build_case.py e verifica che le quote dell'interfaccia (viti del
    coperchio) siano ancora quelle. Se qualcuno tocca i lug, il telaio non ci
    va piu` sopra: meglio fermarsi qui che scoprirlo in stampa."""
    src_path = os.path.join(OUT_DIR, "build_case.py")
    if not os.path.exists(src_path):
        print("!! build_case.py non trovato: interfaccia non verificata")
        return
    # le costanti nel sorgente stanno spesso su assegnazioni multiple
    # ("LUG_R, LUG_CY = 4.6, 31.6"): si legge la riga e si prende il valore
    # nella posizione del nome.
    found = {}
    for line in open(src_path):
        m = re.match(r"^([A-Z_][A-Z0-9_, ]*)=\s*([^#]+)", line)
        if not m:
            continue
        names = [n.strip() for n in m.group(1).split(",") if n.strip()]
        vals = [float(v) for v in re.findall(r"-?\d+\.?\d*", m.group(2))]
        if len(names) > 1 and len(vals) == len(names):
            found.update(zip(names, vals))
        elif len(names) == 1:
            found[names[0]] = vals

    expect = {"LUG_CY": LUG_CY, "LUG_R": LUG_R, "SCREW_D": SCREW_D,
              "INSERT_DEPTH": INSERT_DEPTH, "LID_T": LID_T}
    for name, want in expect.items():
        if name not in found:
            raise SystemExit(f"interfaccia: {name} non trovato in build_case.py")
        got = found[name]
        if got != want and got != [want]:
            raise SystemExit(f"interfaccia: build_case.py ha {name} = {got}, "
                             f"build_mount.py si aspetta {want}")
    if tuple(found.get("LUG_CX", [])) != LUG_CX:
        raise SystemExit(f"interfaccia: LUG_CX = {found.get('LUG_CX')}, atteso {list(LUG_CX)}")
    print("interfaccia con build_case.py: ok")


# ------------------------------------------------------------------- telaio


def arm_axis(sx, sy):
    """Radice (sul lug d'angolo) e testa (centro di registrazione) del braccio."""
    ax, ay = sx * LUG_CX[-1], sy * LUG_CY
    ex, ey = sx * MOUNT_X, sy * MOUNT_Y
    return (ax, ay), (ex, ey)


def build_frame():
    parts = []

    # piano a H: due travi sui lug + traverso centrale. Il traverso passa
    # sopra il coperchio a PLATE_Z0 di distanza, non lo tocca.
    for sy in (-1, 1):
        parts.append(box("spine", (2 * (LUG_CX[-1] + LUG_R), SPINE_W, PLATE_T),
                         (0.0, sy * LUG_CY, (PLATE_Z0 + PLATE_Z1) / 2.0)))
    parts.append(box("cross", (CROSS_W, 2 * (LUG_CY + LUG_R), PLATE_T),
                     (0.0, 0.0, (PLATE_Z0 + PLATE_Z1) / 2.0)))

    # piedini: appoggiano SOLO sui sei lug del coperchio, che sono gli unici
    # punti in cui il coperchio e` spesso e sostenuto dalla vite.
    for i, (lx, ly) in enumerate(LUG_XY):
        parts.append(cyl(f"foot{i}", LUG_R, FOOT_H, (lx, ly, FOOT_H / 2.0)))

    for sx, sy in CORNERS:
        (ax, ay), (ex, ey) = arm_axis(sx, sy)
        dx, dy = ex - ax, ey - ay
        dl = math.hypot(dx, dy)
        ux, uy = dx / dl, dy / dl
        # il braccio parte 3 mm dietro il lug per sovrapporsi alla trave
        cx, cy = ax - 3.0 * ux, ay - 3.0 * uy
        parts.append(prism(f"arm_{sx:+d}{sy:+d}",
                           rect((cx + ex) / 2.0, (cy + ey) / 2.0, ux, uy,
                                dl + 3.0, ARM_W),
                           ARM_Z0, ARM_Z1))
        # piastrino e guida, orientati lungo la DIAGONALE (che e` la direzione
        # di registrazione della clip), non lungo il braccio.
        parts.append(prism(f"pad_{sx:+d}{sy:+d}",
                           rect(ex, ey, sx * GX, sy * GY, PAD_L, PAD_W),
                           ARM_Z0, ARM_Z1))
        parts.append(prism(f"rib_{sx:+d}{sy:+d}",
                           rect(ex, ey, sx * GX, sy * GY, RIB_L, RIB_W),
                           ARM_Z1, ARM_Z1 + RIB_H))

    frame = parts[0]
    fuse(frame, parts[1:])

    # forature: sei passanti M3 + quattro fori pilota per le clip
    tools = [cyl(f"sh{i}", SCREW_D / 2.0, PLATE_Z1 + 4.0, (lx, ly, PLATE_Z1 / 2.0))
             for i, (lx, ly) in enumerate(LUG_XY)]
    for sx, sy in CORNERS:
        _, (ex, ey) = arm_axis(sx, sy)
        tools.append(cyl(f"pil_{sx:+d}{sy:+d}", PILOT_D / 2.0, ARM_Z1 + RIB_H + 4.0,
                         (ex, ey, (ARM_Z0 + ARM_Z1 + RIB_H) / 2.0)))
    cut(frame, tools)
    frame.name = "Panel_Frame"
    return frame


# --------------------------------------------------------------------- clip
# Frame locale della clip: origine sull'angolo del pannello, u lungo un bordo
# e v lungo l'altro, entrambi verso l'interno del pannello. Il pannello occupa
# u >= 0, v >= 0. z e` quello globale (0 = faccia del coperchio).


def build_clip():
    w_in = -PANEL_CLR                      # faccia interna delle pareti
    w_out = w_in - CLIP_WALL               # faccia esterna
    t_in = -PANEL_CLR                      # faccia interna della linguetta
    t_out = t_in - TONGUE_T
    blk = CLIP_BLK
    tongue_u1 = blk + TONGUE_L             # punta della linguetta
    plate_in = PANEL_CLR + 1.0             # il piano si ferma 1 mm prima della
                                           # linguetta: se la toccasse, l'unione
                                           # la incollerebbe e non flette piu`.
    parts = []

    # blocco rigido d'angolo (piano d'appoggio + radice delle linguette)
    parts.append(prism("blk", [(w_out, w_out), (blk, w_out), (blk, blk), (w_out, blk)],
                       CLIP_Z0, PANEL_Z))
    # montante d'angolo: fermo laterale rigido, non affidato alle linguette
    parts.append(prism("post", [(w_out, w_out), (w_in, w_out), (w_in, w_in), (w_out, w_in)],
                       CLIP_Z0, TONGUE_Z1))
    # piano d'appoggio del pannello, con l'angolo lontano smussato
    parts.append(prism("plate",
                       [(plate_in, plate_in), (CLIP_PLATE, plate_in),
                        (CLIP_PLATE, CLIP_CHAMF_S - CLIP_PLATE),
                        (CLIP_CHAMF_S - CLIP_PLATE, CLIP_PLATE),
                        (plate_in, CLIP_PLATE)],
                       CLIP_Z0, PANEL_Z))

    # due linguette elastiche, una per bordo: la clip e` simmetrica rispetto
    # alla diagonale, quindi le quattro clip sono lo stesso pezzo ruotato.
    for swap in (False, True):
        def P(u, v, _s=swap):
            return (v, u) if _s else (u, v)
        tag = "v" if swap else "u"
        parts.append(prism(f"tongue_{tag}",
                           [P(blk - 4.0, t_out), P(tongue_u1, t_out),
                            P(tongue_u1, t_in), P(blk - 4.0, t_in)],
                           CLIP_Z0, TONGUE_Z1))
        # dente: scavalca il pannello di LIP_OVER
        parts.append(prism(f"lip_{tag}",
                           [P(blk + LIP_START, t_in), P(tongue_u1, t_in),
                            P(tongue_u1, LIP_OVER), P(blk + LIP_START, LIP_OVER)],
                           LIP_Z0, TONGUE_Z1))
        # aletta per aprire la linguetta con l'unghia
        parts.append(prism(f"tab_{tag}",
                           [P(tongue_u1 - TAB_L, t_out - TAB_W), P(tongue_u1, t_out - TAB_W),
                            P(tongue_u1, t_out), P(tongue_u1 - TAB_L, t_out)],
                           CLIP_Z0, TONGUE_Z1))

    clip = parts[0]
    fuse(clip, parts[1:])

    tools = []
    # invito a 45 gradi sul dente: e` la rampa che apre la linguetta quando si
    # preme il pannello. Prisma triangolare lungo il bordo.
    for swap in (False, True):
        tri = [(LIP_OVER + 0.2, LIP_Z0 - 0.2), (LIP_OVER + 0.2, TONGUE_Z1 + 0.2),
               (LIP_OVER - (TONGUE_Z1 - LIP_Z0) - 0.2, TONGUE_Z1 + 0.2)]
        u0, u1 = blk + LIP_START - 0.5, tongue_u1 + 0.5
        if swap:
            verts = [(v, u, z) for u in (u0, u1) for (v, z) in tri]
        else:
            verts = [(u, v, z) for u in (u0, u1) for (v, z) in tri]
        faces = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
        tools.append(_mesh_object(f"ramp_{swap}", verts, faces))

    # guida antirotazione (cava che riceve la nervatura del piastrino) e asola
    # di registrazione, entrambe lungo la diagonale locale u = v.
    dl = CLIP_PLATE * 3.0
    tools.append(prism("groove", rect(0.0, 0.0, 0.7071, 0.7071, dl, RIB_W + 0.3),
                       CLIP_Z0 - 1.0, CLIP_Z0 + RIB_H + 0.2))
    su, sv = LOCAL_S * 0.7071, LOCAL_S * 0.7071
    tools.append(prism("slot", rect(su, sv, 0.7071, 0.7071, SCREW_D + 2 * SLOT_ADJ, SCREW_D),
                       CLIP_Z0 - 1.0, PANEL_Z + 1.0))
    tools.append(prism("cbore", rect(su, sv, 0.7071, 0.7071, CBORE_W + 2 * SLOT_ADJ, CBORE_W),
                       CBORE_Z, PANEL_Z + 1.0))

    cut(clip, tools)
    clip.name = "Panel_Clip"
    return clip


# ------------------------------------------------------------------- export


clear_scene()
check_case_interface()

frame = weld(build_frame())
clip = weld(build_clip())

# in stampa: telaio con i piedini sul piatto, clip con il piano sul piatto
for ob, dz in ((frame, 0.0), (clip, -CLIP_Z0)):
    ob.location.z = dz
bpy.context.view_layer.update()

os.makedirs(OUT_DIR, exist_ok=True)
for ob, fname in ((frame, "panel_frame.stl"), (clip, "panel_clip.stl")):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.wm.stl_export(filepath=os.path.join(OUT_DIR, fname),
                          export_selected_objects=True, apply_modifiers=True)
for ob in (frame, clip):
    ob.location.z = 0.0
bpy.context.view_layer.update()

# -------------------------------------------------------------------- report

E_PETG = 1800.0                       # modulo a flessione, MPa (ordine di grandezza)
TONGUE_HZ = TONGUE_Z1 - CLIP_Z0
strain = 1.5 * LIP_OVER * TONGUE_T / TONGUE_L ** 2
inertia = TONGUE_HZ * TONGUE_T ** 3 / 12.0
force = 3.0 * E_PETG * inertia * LIP_OVER / TONGUE_L ** 3
adj = 2 * SLOT_ADJ * GX               # variazione di PANEL_W a corsa piena


def bbox(ob):
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)), (min(zs), max(zs))


fb, fz = bbox(frame)
cb, cz = bbox(clip)
(rx, ry), (tx, ty) = arm_axis(1, 1)

print()
print(f"pannello {PANEL_W:.0f} x {PANEL_H:.0f} x {PANEL_T} mm, dorso a z={PANEL_Z} "
      f"sopra il coperchio (z={PANEL_Z + 32.1:.1f} dal pavimento della scatola)")
print(f"telaio: {fb[0]:.1f} x {fb[1]:.1f} x {fb[2]:.1f} mm, sei M3 a x={LUG_CX} y=+/-{LUG_CY}")
print(f"  piedini {FOOT_H} + piano {PLATE_T} = {FOOT_STACK:.1f} mm sotto la testa; "
      f"con coperchio {LID_T} e inserto profondo {INSERT_DEPTH} -> vite M3x{SCREW_L:.0f} "
      f"(impegno {SCREW_L - LID_T - FOOT_STACK:.1f} mm)")
print(f"  bracci {ARM_W} x {ARM_Z1 - ARM_Z0} mm, sbalzo {math.hypot(tx - rx, ty - ry):.1f} mm dal lug")
print("  telaio a H: 6 viti non allineate -> nessuna cerniera (tre viti in fila "
      "non bloccherebbero la rotazione attorno alla loro linea)")
print(f"clip x4 identiche: {cb[0]:.1f} x {cb[1]:.1f} x {cb[2]:.1f} mm, "
      f"tasca {PANEL_T + PANEL_FIT:.1f} mm su pannello {PANEL_T}")
print(f"  linguette 2 per clip: {TONGUE_L} x {TONGUE_T} mm, dente {LIP_OVER} mm")
print(f"  deformazione allo scatto {100 * strain:.2f}% (limite pratico PETG ~3%)"
      f"{'  ** ALTA **' if strain > 0.03 else ''}")
print(f"  forza di scatto ~{force:.0f} N per linguetta, ~{2 * force:.0f} N per angolo")
print(f"  registrazione +/-{SLOT_ADJ} mm in diagonale -> pannelli da "
      f"{PANEL_W - adj:.0f} a {PANEL_W + adj:.0f} mm di lato")
print(f"  vite clip: M3x10 autofilettante nel foro Ø{PILOT_D} passante del piastrino, "
      f"testa bombata nello svaso (cielo a z={CBORE_Z}, {PANEL_Z - CBORE_Z:.1f} mm sotto il pannello)")
print("exported:", sorted(f for f in os.listdir(OUT_DIR) if f.startswith("panel_")))
