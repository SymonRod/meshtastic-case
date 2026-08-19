"""Montatura per pannello solare, appesa alle 6 viti M3 del coperchio.

UN PEZZO SOLO da stampare:

  panel_mount.stl  x1  anello rettangolare sulle sei viti + quattro bracci
                       diagonali + quattro teste d'angolo con le linguette a
                       scatto che trattengono il pannello.

La scatola non viene toccata: nessun foro nuovo, nessun inserto nuovo. Le
uniche viti sono le sei M3 del coperchio, che diventano M3x12 (le teste
stanno annegate nello svaso, cosi` il pannello ci appoggia sopra).

Il pannello e` di misura FISSA (PANEL_W x PANEL_H qui sotto). Cambiando
pannello si ricompila e si ristampa: e` quello che ha permesso di buttare via
asole, guide di registrazione, piastrini e viti autofilettanti.

Sistema di riferimento: X e Y come in build_case.py (origine al centro della
scatola), ma **z = 0 e` la faccia superiore del coperchio**, cioe` z = 32.1 in
coordinate scatola. z = 0 e` anche il piano di stampa: tutto il pezzo e` una
estrusione verticale che parte da li`.

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
CASE_HX = 58.9                        # meta` lunghezza esterna della scatola

# ------------------------------------------------------------------ pannello
PANEL_W, PANEL_H = 170.0, 170.0       # ingombro del pannello (X, Y)
PANEL_T = 2.4                         # spessore del laminato in vetroresina
PANEL_FIT = 0.3                       # aria in Z fra dorso e dente
PANEL_CLR = 0.4                       # aria in pianta fra bordo e montanti

# ------------------------------------------------------------------- corpo
# Due sole quote in Z: la lastra e` sottile, e sale a RISE_H solo dove serve
# (bossi delle viti, bracci, teste d'angolo).
PLATE_T = 3.5                         # spessore della lastra dell'anello
RISE_H = 8.0                          # quota della faccia d'appoggio del
                                      # pannello sopra il coperchio
BOSS_R = LUG_R                        # raggio dei bossi attorno alle viti
SPINE_W = 6.0                         # larghezza (Y) delle travi
END_X = 62.0                          # asse delle traverse d'estremita`
END_W = 5.0                           # larghezza (X) delle traverse
ARM_W = 7.0                           # larghezza dei bracci diagonali
CBORE_D = 6.4                         # svaso per la testa bombata M3
SCREW_HEAD_H = 2.2                    # altezza della testa bombata M3

# ------------------------------------------------------------ testa d'angolo
CORNER_W = 3.0                        # spessore dei montanti d'angolo
CORNER_L = 12.0                       # lunghezza dei montanti lungo il bordo
PAD_W = 7.0                           # larghezza dei rami del piano d'appoggio
PAD_S = 21.0                          # lunghezza dei rami
GAP = 1.2                             # aria fra linguetta e resto del pezzo
TONGUE_T = 2.4                        # spessore della linguetta elastica
TONGUE_L = 24.0                       # sbalzo libero della linguetta
TONGUE_ROOT = 4.0                     # quanto la radice entra nella testa
LIP_OVER = 1.5                        # quanto il dente scavalca il pannello
LIP_H = 1.5                           # altezza del dente
LIP_START = 10.0                      # da dove parte il dente lungo lo sbalzo
RAMP_LEAD = 0.3                       # quanto dente resta pieno sotto la rampa

# ------------------------------------------------------------------- derivate
LUG_XY = [(lx, sy * LUG_CY) for lx in LUG_CX for sy in (-1, 1)]
CORNERS = [(sx, sy) for sx in (-1, 1) for sy in (-1, 1)]

PANEL_HX, PANEL_HY = PANEL_W / 2.0, PANEL_H / 2.0
PANEL_BACK = RISE_H + PANEL_T                       # dorso del pannello
LIP_Z0 = PANEL_BACK + PANEL_FIT                     # sotto del dente
LIP_Z1 = LIP_Z0 + LIP_H                             # cima del pezzo
PAD_IN = GAP - PANEL_CLR                            # quanto il piano entra
                                                    # sotto il bordo pannello
# Lo svaso scende dalla cima del bosso fino alla lastra: sotto la testa resta
# esattamente PLATE_T, comunque si muovano RISE_H e PLATE_T.
CBORE_DEPTH = RISE_H - PLATE_T
SCREW_STACK = PLATE_T + LID_T                       # materiale sotto la testa
SCREW_L = 12.0                                      # M3x12
SCREW_BITE = SCREW_L - SCREW_STACK                  # impegno nell'inserto
HEAD_GAP = RISE_H - (PLATE_T + SCREW_HEAD_H)        # aria testa vite/pannello

HEAD_IN = 10.0                        # dove il braccio incontra l'angolo

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

    Tutto il pezzo e` unione di prismi convessi estrusi in Z e appoggiati al
    piano di stampa: nessun sottosquadro, nessun supporto. L'unica eccezione
    e` il dente delle linguette, che sporge di 1.5 mm ed e` autoportante."""
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
    coperchio) siano ancora quelle. Se qualcuno tocca i lug, la montatura non
    ci va piu` sopra: meglio fermarsi qui che scoprirlo in stampa."""
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


# ------------------------------------------------------------- testa d'angolo
# Frame locale dell'angolo: origine sull'ANGOLO DEL PANNELLO, u lungo un bordo
# e v lungo l'altro, entrambi verso l'interno del pannello. Il pannello occupa
# u >= 0, v >= 0. z e` quello globale (0 = faccia del coperchio = piano di
# stampa). I quattro angoli sono lo stesso disegno con (sx, sy) diversi.


def mapper(sx, sy):
    def L(u, v):
        return (sx * (PANEL_HX - u), sy * (PANEL_HY - v))
    return L


def corner_parts(sx, sy):
    """Testa d'angolo: piano d'appoggio, montanti rigidi, due linguette."""
    L = mapper(sx, sy)
    cw, cl, clr = CORNER_W, CORNER_L, PANEL_CLR
    t_in, t_out = -clr, -clr - TONGUE_T          # facce della linguetta
    u0 = cl - TONGUE_ROOT                        # radice, dentro la testa
    u1 = cl + TONGUE_L                           # punta della linguetta
    parts = []

    # blocco d'angolo: quadrato pieno che porta i montanti e le radici delle
    # linguette. Arriva solo a CORNER_L in u e v: oltre, la fascia esterna al
    # bordo del pannello e` riservata alle linguette.
    parts.append(prism(f"blk_{sx:+d}{sy:+d}",
                       [L(-cw, -cw), L(cl, -cw), L(cl, cl), L(-cw, cl)],
                       0.0, RISE_H))

    for swap in (False, True):
        def P(u, v, _s=swap):
            return L(v, u) if _s else L(u, v)
        tag = f"{'v' if swap else 'u'}_{sx:+d}{sy:+d}"

        # piano d'appoggio: un ramo per bordo, non un piastrone pieno. Si ferma
        # a PAD_IN dal bordo del pannello: fra lui e la linguetta restano GAP
        # mm d'aria. Se si toccassero, l'unione li salderebbe e la linguetta
        # non flette piu`.
        parts.append(prism(f"pad_{tag}",
                           [P(PAD_IN, PAD_IN), P(PAD_S, PAD_IN),
                            P(PAD_S, PAD_W), P(PAD_IN, PAD_W)],
                           0.0, RISE_H))
        # montante: fermo laterale rigido in pianta, separato dalle linguette.
        parts.append(prism(f"post_{tag}",
                           [P(-cw, -cw), P(cl, -cw), P(cl, t_in), P(-cw, t_in)],
                           0.0, LIP_Z1))
        # linguetta elastica: lamella verticale alta tutto il pezzo, quindi
        # appoggiata al piano di stampa. Flette IN PIANTA, non in Z.
        parts.append(prism(f"tongue_{tag}",
                           [P(u0, t_out), P(u1, t_out), P(u1, t_in), P(u0, t_in)],
                           0.0, LIP_Z1))
        # dente: scavalca il pannello di LIP_OVER
        parts.append(prism(f"lip_{tag}",
                           [P(cl + LIP_START, t_in), P(u1, t_in),
                            P(u1, LIP_OVER), P(cl + LIP_START, LIP_OVER)],
                           LIP_Z0, LIP_Z1))
        # Niente aletta di sgancio: sporgeva oltre lo spigolo del pannello ed
        # era l'unica cosa che usciva dal profilo. Non serve: la linguetta sta
        # tutta fuori dal bordo del pannello, quindi la si preme direttamente
        # sul fianco per sganciare.
    return parts


def corner_ramps(sx, sy):
    """Invito a 45 gradi sul dente: la rampa che apre le linguette quando si
    preme il pannello. Prisma triangolare lungo il bordo."""
    L = mapper(sx, sy)
    tools = []
    # La rampa e` la retta v + z = k a 45 gradi. RAMP_LEAD la sposta di quel
    # tanto che basta perche` NON passi per gli spigoli del dente: passandoci
    # esattamente (com'era) il taglio e` tangente a due spigoli e il solver
    # EXACT lascia la faccia inclinata sdoppiata. In cima al dente restano
    # RAMP_LEAD mm di sporgenza invece di zero.
    k = LIP_OVER + LIP_Z0 + RAMP_LEAD
    zlo, zhi = LIP_Z0 - 1.0, LIP_Z1 + 1.0
    tri = [(k - zlo, zlo), (k - zlo, zhi), (k - zhi, zhi)]
    a0 = CORNER_L + LIP_START - 0.5
    a1 = CORNER_L + TONGUE_L + 0.5
    for swap in (False, True):
        verts = []
        for a in (a0, a1):
            for (b, z) in tri:
                x, y = L(b, a) if swap else L(a, b)
                verts.append((x, y, z))
        faces = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
        tools.append(_mesh_object(f"ramp_{swap}_{sx:+d}{sy:+d}", verts, faces))
    return tools


# --------------------------------------------------------------------- pezzo


def build_mount():
    parts = []

    # anello rettangolare: due travi longitudinali sulle sei viti + due
    # traverse d'estremita`. Le traverse passano OLTRE la scatola in X
    # (END_X - END_W/2 > CASE_HX), quindi del coperchio il pezzo tocca solo la
    # striscia sopra i lug e sopra le pareti: mai la campata centrale.
    # L'anello e` chiuso: nessuna cerniera possibile (tre viti in fila da sole
    # non bloccherebbero la rotazione attorno alla loro linea).
    ring_hx = END_X + END_W / 2.0
    for sy in (-1, 1):
        parts.append(box("spine", (2 * ring_hx, SPINE_W, PLATE_T),
                         (0.0, sy * LUG_CY, PLATE_T / 2.0)))
    for sx in (-1, 1):
        parts.append(box("end", (END_W, 2 * LUG_CY + SPINE_W, PLATE_T),
                         (sx * END_X, 0.0, PLATE_T / 2.0)))

    # bossi sulle sei viti: sono l'unico punto in cui la lastra sale a RISE_H.
    # Servono a due cose insieme: ospitare lo svaso (sotto la testa restano
    # PLATE_T di materiale) e portare la sezione alta fin sopra la vite, cosi`
    # il momento dei bracci finisce nella vite e non nella lastra sottile.
    for i, (lx, ly) in enumerate(LUG_XY):
        parts.append(cyl(f"boss{i}", BOSS_R, RISE_H, (lx, ly, RISE_H / 2.0)))

    # bracci diagonali: dal lug d'angolo alla testa d'angolo.
    for sx, sy in CORNERS:
        ax, ay = sx * LUG_CX[-1], sy * LUG_CY
        ex, ey = sx * (PANEL_HX - HEAD_IN), sy * (PANEL_HY - HEAD_IN)
        dx, dy = ex - ax, ey - ay
        dl = math.hypot(dx, dy)
        ux, uy = dx / dl, dy / dl
        cx, cy = ax - 3.0 * ux, ay - 3.0 * uy   # 3 mm dentro la trave
        parts.append(prism(f"arm_{sx:+d}{sy:+d}",
                           rect((cx + ex) / 2.0, (cy + ey) / 2.0, ux, uy,
                                dl + 3.0, ARM_W),
                           0.0, RISE_H))
        parts += corner_parts(sx, sy)

    mount = parts[0]
    fuse(mount, parts[1:])

    # forature: sei passanti M3 con svaso per la testa bombata. La testa resta
    # annegata, cosi` il pannello appoggia sulla faccia del corpo.
    # I tre cilindri concentrici (bosso 64, svaso 56, foro 48) hanno numero di
    # lati DIVERSO apposta: con lo stesso numero i vertici cadono sulle stesse
    # generatrici radiali e il solver EXACT lascia un triangolo sciolto sul
    # bordo del foro. Non uniformarli.
    tools = []
    for i, (lx, ly) in enumerate(LUG_XY):
        tools.append(cyl(f"sh{i}", SCREW_D / 2.0, RISE_H + 4.0,
                         (lx, ly, RISE_H / 2.0), verts=48))
        tools.append(cyl(f"cb{i}", CBORE_D / 2.0, CBORE_DEPTH + 2.0,
                         (lx, ly, PLATE_T + (CBORE_DEPTH + 2.0) / 2.0), verts=56))
    for sx, sy in CORNERS:
        tools += corner_ramps(sx, sy)
    cut(mount, tools)
    mount.name = "Panel_Mount"
    return mount


# ------------------------------------------------------------------- export


clear_scene()
check_case_interface()

mount = weld(build_mount())

os.makedirs(OUT_DIR, exist_ok=True)
bpy.ops.object.select_all(action="DESELECT")
mount.select_set(True)
bpy.context.view_layer.objects.active = mount
bpy.ops.wm.stl_export(filepath=os.path.join(OUT_DIR, "panel_mount.stl"),
                      export_selected_objects=True, apply_modifiers=True)

# -------------------------------------------------------------------- report

E_PETG = 1800.0                       # modulo a flessione, MPa (ordine di grandezza)
RHO_PETG = 1.27e-3                    # g/mm3
strain = 1.5 * LIP_OVER * TONGUE_T / TONGUE_L ** 2
inertia = LIP_Z1 * TONGUE_T ** 3 / 12.0
force = 3.0 * E_PETG * inertia * LIP_OVER / TONGUE_L ** 3


def bbox(ob):
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)), (min(zs), max(zs))


def volume(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    v = bm.calc_volume(signed=True)
    bm.free()
    return abs(v)


bb, zr = bbox(mount)
vol = volume(mount)
arm_len = math.hypot(PANEL_HX - HEAD_IN - LUG_CX[-1], PANEL_HY - HEAD_IN - LUG_CY)

print()
print(f"pannello {PANEL_W:.0f} x {PANEL_H:.0f} x {PANEL_T} mm, dorso a "
      f"z={PANEL_BACK:.1f} sopra il coperchio "
      f"(z={PANEL_BACK + 32.1:.1f} dal pavimento della scatola)")
print(f"UN PEZZO: {bb[0]:.1f} x {bb[1]:.1f} x {bb[2]:.1f} mm, z da {zr[0]:.1f} a {zr[1]:.1f}")
print(f"  volume {vol / 1000.0:.1f} cm3 -> ~{vol * RHO_PETG:.0f} g pieno "
      f"(~{vol * RHO_PETG * 0.55:.0f} g a riempimento 30%)")
print(f"  anello sulle sei M3 a x={LUG_CX} y=+/-{LUG_CY}; traverse a x=+/-{END_X} "
      f"(la scatola finisce a {CASE_HX})")
print(f"  lastra {PLATE_T} mm, sale a {RISE_H} solo sui bossi delle viti, sui "
      f"bracci e sulle teste d'angolo")
print(f"  svaso {CBORE_D} x {CBORE_DEPTH} -> {PLATE_T} + coperchio {LID_T} sotto "
      f"la testa -> vite M3x{SCREW_L:.0f} (impegno {SCREW_BITE:.1f} mm su "
      f"inserto {INSERT_DEPTH})")
print(f"  testa vite annegata: {HEAD_GAP:.1f} mm d'aria fino al pannello"
      f"{'  ** TOCCA **' if HEAD_GAP < 0.5 else ''}")
print(f"  bracci {ARM_W} x {RISE_H} mm, sbalzo {arm_len:.1f} mm dal lug d'angolo")
# vento: ~12 N per angolo su un pannello 170 x 170 a 100 km/h, normale al piano
arm_w = ARM_W * RISE_H ** 2 / 6.0                      # modulo di resistenza
arm_i = ARM_W * RISE_H ** 3 / 12.0
arm_sigma = 12.0 * arm_len / arm_w
arm_defl = 12.0 * arm_len ** 3 / (3.0 * E_PETG * arm_i)
print(f"    vento ~12 N per angolo -> {arm_sigma:.0f} MPa e {arm_defl:.1f} mm di "
      f"freccia (PETG cede ~50 MPa){'  ** ALTO **' if arm_sigma > 20 else ''}")
print(f"  8 linguette (2 per angolo): {TONGUE_L} x {TONGUE_T} mm alte {LIP_Z1:.1f}, "
      f"dente {LIP_OVER} mm")
print(f"  deformazione allo scatto {100 * strain:.2f}% (limite pratico PETG ~3%)"
      f"{'  ** ALTA **' if strain > 0.03 else ''}")
print(f"  forza di scatto ~{force:.0f} N per linguetta, ~{2 * force:.0f} N per angolo")
print("  tutto estruso da z=0: nessun supporto, nessun piedino, nessuna vite in piu`")
print("exported: panel_mount.stl")
