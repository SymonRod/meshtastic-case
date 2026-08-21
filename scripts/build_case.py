"""Meshtastic case: 21700 cell + Seeed XIAO nRF52840 / Wio-SX1262 stack + N bulkhead.

Parametric. Edit the constants below and re-run to regenerate base + lid in models/.
All dimensions in millimetres. Z+ is up; the box prints open-side-up, the lid flat.

Revisione "guarnizione": cava continua per O-ring in corda di silicone Ø3 sul
bordo della base, viti M3 portate FUORI dalla linea di tenuta su sei lug
esterni, nessun supporto interno per la scheda, nessuna costola sul coperchio.
"""
import math
import os

import bmesh
import bpy

# ---------------------------------------------------------------- parameters

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
MODEL_DIR = os.path.join(PROJECT_DIR, "models")

CELL_D, CELL_L = 21.0, 70.0          # 21700 cell
CELL_CLR = 0.6                        # diametral clearance around the cell

# XIAO nRF52840 + Wio-SX1262, ruotato di 90 gradi attorno a Z: il lato lungo
# (21 mm) corre lungo Y. Nessun supporto stampato: la scheda si fissa con
# biadesivo. Le quote restano qui solo per verificare gli spazi liberi.
BOARD_X, BOARD_Y, BOARD_Z = 17.8, 21.0, 13.0
BOARD_CX = -14.0                      # verso -X, vicino al connettore N

# Pareti a 6.4 mm: e` la larghezza minima per ospitare la cava dell'O-ring
# (1.2 + 4.0 + 1.2). Il pavimento resta sottile.
WALL, FLOOR, LID_T = 6.4, 2.4, 3.2
LIP_H, LIP_CLR = 3.0, 0.35            # lid spigot depth / fit clearance
LIP_W = 3.0                           # spessore del labbro: e` una cornice, non un tappo

INNER_X, INNER_Y, INNER_Z = 105.0, 46.0, 26.5
INNER_R = 6.0                         # raccordo degli spigoli verticali interni

# ---- O-ring: corda di silicone Ø3 mm, giunta a colla nel solco.
# Solco 4.0 x 2.0: schiacciamento 1.0 mm (33%), riempimento 88%. Il coperchio
# va in battuta sulle due spalle da 1.2 mm, che fanno da fine corsa.
# Era 3.8 x 2.2 (27%, 85%): a norma sulla carta, ma senza margine per la
# planarita` di un coperchio stampato lungo 118 mm - alla prova della doccia
# passava acqua. Allargando il solco insieme all'approfondimento il
# riempimento resta sotto il 90%: l'O-ring ha ancora dove spanciare e non
# fa da distanziale impedendo la battuta. GROOVE_MID resta 3.2, quindi
# raggi d'angolo e mezzeria non si muovono.
ORING_D = 3.0
GROOVE_W, GROOVE_D = 4.0, 2.0
GROOVE_LAND = 1.2                     # spalla fra solco e faccia interna

# ---- viti M3: SEI lug esterni, tutti oltre il bordo esterno del solco.
# La tenuta deve stare fra la vite e l'interno, altrimenti l'acqua che entra
# nel foro del coperchio arriva in cavita' passando sopra al boss.
LUG_R, LUG_CY = 4.6, 31.6
LUG_CX = (-52.0, 0.0, 52.0)
LUG_FILLET = 3.0                      # raccordo concavo fra lug e parete
INSERT_D, INSERT_DEPTH = 4.0, 6.0     # M3 heat-set insert: hole dia and depth
SCREW_D = 3.4                         # M3 clearance in the lid (button-head, sits proud)

# Connettore N bulkhead (filetto 5/8"-24 = 15.88 mm), non SMA.
CONN_D = 16.4                         # foro passante nella parete -X
CONN_SEAT_D = 22.0                    # anello+guarnizione: superficie piana richiesta sulla sede
CONN_BODY_L = 20.0                    # sporgenza rigida verso l'interno (corpo + coda di cavo rigida)
# Con la parete a 6.4 il filetto non uscirebbe abbastanza per il dado. Lo
# scasso che riporta lo spessore utile a 2.4 mm sta DENTRO: la faccia esterna
# resta piana e a filo, cosi` il dado ci appoggia sopra e la chiave lo prende.
CONN_RELIEF_D, CONN_RELIEF_DEPTH = 23.0, 4.0

# Nessuna asola USB: con la scheda ruotata la porta guarda +/-X, dove non c'e`
# parete raggiungibile. La ricarica passera` dalla PCB solare; per riflashare si
# apre il coperchio.

# ---- sella della cella: TRE bande, non un blocco pieno da 70 mm.
# L'altezza NON e` un parametro libero: e` derivata (CRADLE_H = CELL_CZ), cioe`
# il labbro della culla sta esattamente all'equatore della cella. E` l'unica
# quota per cui la bocca vale quanto lo scavo (Ø CELL_D + CELL_CLR) e quindi
# qualunque cella che entra nella culla ci scende dall'alto senza forzare.
# Piu` in basso la bocca si stringe e la cella appoggia sui due spigoli del
# labbro invece che sull'arco: e` quello che faceva la sella da 7 mm, che su una
# cella da 21 lasciava una bocca di 20.06 (0.47 di interferenza per lato).
CRADLE_MARGIN = 1.6                   # materiale oltre la tangente della cella
CRADLE_BAND_W = 12.0                  # larghezza (X) di ogni banda
CRADLE_BAND_DX = 29.0                 # |x| delle due bande esterne dal centro cella
# Gli smussi delle bande vanno tenuti PICCOLI. Al labbro il fianco della culla
# e` spesso solo CRADLE_LIP_T (~1.6 mm): uno smusso d'angolo confrontabile con
# quello spessore non arrotonda l'angolo, lo riduce a un cuneo che va a zero e
# che la stampante non riesce a fare. Vedi il controllo CRADLE_LIP_MIN sotto.
# NIENTE smusso d'invito sul labbro della culla: c'era (0.4 x 45, tagliato in
# YZ lungo la banda) e negli angoli incontrava lo smusso d'angolo lasciando una
# faccetta triangolare che si assottigliava fino a zero. Il labbro resta uno
# spigolo netto: la bocca vale gia` quanto lo scavo, l'invito non serviva.
CRADLE_CHAMF = 0.3                    # smusso verticale sugli angoli delle bande
# Gola di sfogo sul fondo della culla: toglie la lametta di materiale che il
# cilindro di scavo lascerebbe sopra il pavimento (0.3 mm al centro, meno di un
# layer). Larga 8 mm, cosi` sparisce tutta la zona in cui il film e` sotto ~1 mm.
CRADLE_RELIEF_W = 8.0

# Alette di fissaggio al dorso del pannello solare. Complanari al pavimento:
# stampano appoggiate al piatto, nessuno sbalzo. Sporgono dalle pareti +/-Y.
EAR_X = 38.0                          # |x| dei due assi di alette
EAR_L, EAR_W, EAR_T = 14.0, 11.0, 4.0  # lunghezza (X), sporgenza (Y), spessore (Z)
EAR_HOLE_D = 4.5                      # passante M4
EAR_HOLE_OUT = 6.5                    # centro foro, misurato dalla faccia esterna
EAR_CHAMF = 3.0                       # smusso a 45 gradi sui due spigoli esterni
# Nervature a 45 gradi contro la parete: DUE per aletta, affiancate al foro.
# Una sola nervatura centrata sull'asse passava sopra il foro e lo ritappava.
EAR_GUSSET_T, EAR_GUSSET_H = 2.6, 8.0
EAR_GUSSET_OFF = 5.3                  # |x| dell'asse nervatura rispetto all'aletta

# Passacavo del pannello solare: foro nudo Ø5 nella parete +X (opposta
# all'antenna), da sigillare a silicone. Spostato in +Y per lasciare liberi i
# 13 mm davanti al polo + della cella.
GLAND_D = 5.0
GLAND_CY, GLAND_CZ = 9.0, 15.0

# derived ------------------------------------------------------------------
CELL_R = (CELL_D + CELL_CLR) / 2.0
OUT_X, OUT_Y = INNER_X + 2 * WALL, INNER_Y + 2 * WALL
HX, HY = INNER_X / 2.0, INNER_Y / 2.0
RIM_Z = FLOOR + INNER_Z                             # bordo su cui appoggia il coperchio

CELL_CY = -HY + 0.5 + CELL_R          # cell axis, hugging the -Y wall
# L'asse NON va portato a CELL_R esatti: il cilindro di scavo diventerebbe
# tangente al pavimento e la linea di tangenza e` uno spigolo a quattro facce
# (non-manifold) lungo tutta la cella. Si tiene lo stacco e si toglie invece il
# film sottile con la gola di sfogo qui sotto.
CELL_CZ = CELL_R + 0.3
# La cella e` spostata verso +X per lasciare CONN_BODY_L di camera libera davanti
# al connettore N. La sella (CELL_L + 4) parte esattamente dove finisce il corpo.
CELL_CX = -HX + CONN_BODY_L + (CELL_L + 4) / 2.0

# Asse del connettore: il piu` basso possibile mantenendo 1 mm di margine fra la
# sede piana da 22 mm e il pavimento.
CONN_CZ = FLOOR + CONN_SEAT_D / 2.0 + 1.0

CRADLE_H = CELL_CZ                                  # labbro all'equatore: vedi sopra
CRADLE_HW = CELL_R + CRADLE_MARGIN                  # semilarghezza della sella
CRADLE_Y_MAX = CELL_CY + CRADLE_HW                  # bordo +Y della sella
CRADLE_TOP = FLOOR + CRADLE_H                       # quota del labbro della culla
# Semicorda dello scavo al labbro: e` la semi-bocca della culla. Deve restare
# >= CELL_D / 2, altrimenti la cella non scende e appoggia sugli spigoli.
CRADLE_HALF_MOUTH = math.sqrt(max(CELL_R ** 2 - (FLOOR + CELL_CZ - CRADLE_TOP) ** 2, 0.0))
CRADLE_LIP_T = CRADLE_HW - CRADLE_HALF_MOUTH        # spessore del fianco al labbro
# Materiale che resta in piano sul labbro nel punto peggiore, cioe` nell'angolo
# smussato della banda. Sotto ~0.8 mm la stampante non ci fa piu` un perimetro:
# e` il cuneo da evitare.
CRADLE_LIP_MIN = CRADLE_LIP_T - CRADLE_CHAMF
CRADLE_BAND_X = [CELL_CX + dx for dx in (-CRADLE_BAND_DX, 0.0, CRADLE_BAND_DX)]
# Altezza della gola: quota a cui il cilindro passa sopra il bordo della gola,
# piu` 0.4 di sfondo. Lo sfondo serve: se il box si fermasse esattamente sul
# cilindro, i due spigoli superiori gli sarebbero tangenti e tornerebbe il
# problema di prima, solo su uno spigolo invece che su una linea.
CRADLE_RELIEF_H = (CELL_CZ - math.sqrt(CELL_R ** 2 - (CRADLE_RELIEF_W / 2.0) ** 2)) + 0.4

# La scheda occupa la striscia libera fra la sella e la parete +Y.
BOARD_CY = (CRADLE_Y_MAX + HY) / 2.0
BOARD_Y_GAP = (HY - CRADLE_Y_MAX - BOARD_Y) / 2.0   # aria per lato in Y

# Mezzeria del solco e raggi: tutti i raccordi condividono i centri d'angolo
# della cavita` (+/-(HX - INNER_R), +/-(HY - INNER_R)), cosi` la spalla interna
# resta larga GROOVE_LAND anche in curva.
GROOVE_MID = GROOVE_LAND + GROOVE_W / 2.0
GROOVE_R = INNER_R + GROOVE_MID
GROOVE_Z0 = RIM_Z - GROOVE_D

OUT_HY = OUT_Y / 2.0                                # faccia esterna delle pareti +/-Y
EAR_HOLE_Y = OUT_HY + EAR_HOLE_OUT                  # semi-interasse dei fori
EAR_XY = [(sx * EAR_X, sy) for sx in (-1, 1) for sy in (-1, 1)]
LUG_XY = [(lx, sy * LUG_CY) for lx in LUG_CX for sy in (-1, 1)]

# Raccordo lug/parete: il cerchio di raccordo e` tangente alla faccia esterna
# della parete (centro a LUG_FILLET da essa) e al cilindro del lug (centri a
# distanza LUG_R + LUG_FILLET). Da qui l'offset in X dei due centri, che e`
# anche la meta` dello sviluppo del raccordo lungo la parete.
LUG_FIL_DY = LUG_CY - OUT_HY                        # sporgenza del centro lug
LUG_FIL_M = math.sqrt((LUG_R + LUG_FILLET) ** 2 - (LUG_FILLET - LUG_FIL_DY) ** 2)
# Quota (misurata dalla faccia esterna) del punto di tangenza raccordo/lug: e`
# il punto piu` esterno del raccordo, e quindi dove va chiuso il blocco.
LUG_FIL_TOP = LUG_FIL_DY + LUG_R * (LUG_FILLET - LUG_FIL_DY) / (LUG_R + LUG_FILLET)

# ---------------------------------------------------------------- helpers


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def box(name, size, center):
    """Axis-aligned box given (sx, sy, sz) and its centre."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return ob


def cyl(name, radius, depth, center, axis="Z", verts=64):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth,
                                        location=center, vertices=verts)
    ob = bpy.context.active_object
    ob.name = name
    if axis == "X":
        ob.rotation_euler = (0, math.radians(90), 0)
    elif axis == "Y":
        ob.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    return ob


def _mesh_object(name, verts, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    # il solver booleano EXACT vuole normali coerenti verso l'esterno
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return ob


def prism_yz(name, tri, x0, x1):
    """Prisma triangolare esteso lungo X. `tri` = tre vertici (y, z)."""
    verts = [(x, y, z) for x in (x0, x1) for (y, z) in tri]
    faces = [(0, 1, 2), (5, 4, 3),
             (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    return _mesh_object(name, verts, faces)


def rounded_rect(hx, hy, r, seg=10):
    """Poligono (x, y) di un rettangolo a spigoli raccordati, senso antiorario.
    I centri d'angolo sono sempre (+/-(hx - r), +/-(hy - r))."""
    cx, cy = hx - r, hy - r
    pts = []
    for (sx, sy, a0) in ((1, 1, 0.0), (-1, 1, 90.0), (-1, -1, 180.0), (1, -1, 270.0)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90.0 * k / seg)
            pts.append((sx * cx + r * math.cos(a), sy * cy + r * math.sin(a)))
    return pts


def prism(name, poly, z0, z1):
    """Estrusione solida di un poligono convesso fra z0 e z1."""
    n = len(poly)
    verts = [(x, y, z0) for (x, y) in poly] + [(x, y, z1) for (x, y) in poly]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return _mesh_object(name, verts, faces)


def ring_prism(name, outer, inner, z0, z1):
    """Anello a sezione rettangolare fra due poligoni con lo stesso numero di
    vertici (usato per la cava dell'O-ring e per il labbro del coperchio)."""
    n = len(outer)
    verts = ([(x, y, z) for z in (z0, z1) for (x, y) in outer] +
             [(x, y, z) for z in (z0, z1) for (x, y) in inner])
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))                          # fianco esterno
        faces.append((2 * n + i, 2 * n + j, 3 * n + j, 3 * n + i))  # fianco interno
        faces.append((i, j, 2 * n + j, 2 * n + i))                  # fondo
        faces.append((n + i, n + j, 3 * n + j, 3 * n + i))          # cielo
    return _mesh_object(name, verts, faces)


def lug_fillets(name, z0, z1):
    """Raccordi concavi che fondono i lug nelle pareti +/-Y.

    Per ogni lug: il blocco che riempie l'angolo fra parete e cilindro, meno i
    due cilindri di raggio LUG_FILLET tangenti a entrambe le superfici. Quel
    che resta e` esattamente il triangolo curvilineo del raccordo, piu` la
    porzione gia` occupata dal lug (innocua, e` un'unione). Il tutto viene
    intersecato con l'ingombro in X del corpo: il raccordo dei lug d'angolo
    finirebbe 0.7 mm oltre la parete +/-X, dove non ha piu` niente da
    raccordare; li` il taglio e` alto 0.07 mm, quindi invisibile.
    """
    zc, zh = (z0 + z1) / 2.0, z1 - z0
    parts = []
    for i, (lx, ly) in enumerate(LUG_XY):
        sy = math.copysign(1.0, ly)
        # 0.6 mm di penetrazione nella parete: evita facce complanari. Fuori,
        # il blocco si ferma al punto di tangenza: oltre non c'e` raccordo, e
        # la lama fra i due cilindri manda in schegge il solver.
        blk = box(f"{name}{i}", (2 * LUG_FIL_M, LUG_FIL_TOP + 0.6, zh),
                  (lx, sy * (OUT_HY + (LUG_FIL_TOP - 0.6) / 2.0), zc))
        cut(blk, [cyl(f"{name}{i}_{s:+d}", LUG_FILLET, zh + 2,
                      (lx + s * LUG_FIL_M, sy * (OUT_HY + LUG_FILLET), zc))
                  for s in (-1, 1)])
        parts.append(blk)
    tool = parts[0]
    fuse(tool, parts[1:])
    boolean(tool, box(f"{name}_clip", (OUT_X, OUT_Y + 4 * LUG_FILLET, zh + 4),
                      (0, 0, zc)), "INTERSECT")
    return tool


def weld(ob, dist=1e-4):
    """Salda i vertici sdoppiati che le booleane lasciano dove tre superfici si
    incontrano (sul coperchio: il foro della vite sulla cucitura del raccordo).
    La tolleranza deve restare minima: a 1e-3 fonde anche i vertici veri del
    raccordo lungo la tangenza col lug, e apre dei buchi."""
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


# ---------------------------------------------------------------- base


def build_base():
    base = box("Case_Base", (OUT_X, OUT_Y, RIM_Z), (0, 0, RIM_Z / 2.0))

    # ---- lug esterni per le M3, colonne piene da terra al bordo: stanno tutti
    # oltre il bordo esterno della cava, quindi la vite e` fuori tenuta.
    fuse(base, [cyl(f"lug_{i}", LUG_R, RIM_Z, (lx, ly, RIM_Z / 2.0))
                for i, (lx, ly) in enumerate(LUG_XY)])

    # raccordo concavo lug/parete: il lug non nasce da uno spigolo netto, la
    # parete gli si piega dentro. Il materiale aggiunto sta tutto fuori dalla
    # faccia esterna, quindi non tocca ne` la cava ne` la cavita`. Va fuso
    # prima delle forature: il blocco da cui e` ricavato copre anche l'asse
    # del lug, e se arrivasse dopo ritapperebbe il foro dell'inserto.
    fuse(base, [lug_fillets("lugfil", 0.0, RIM_Z)])

    # ---- alette di fissaggio + nervature a 45 gradi.
    # Complanari al pavimento (z da 0 a EAR_T): appoggiano sul piatto, quindi
    # non introducono sbalzi. Penetrano 0.6 mm nella parete per evitare facce
    # complanari nell'unione booleana.
    # Gli spigoli esterni sono smussati a 45 gradi (EAR_CHAMF): niente angoli
    # vivi che si impigliano nelle fascette e nessuna punta fragile in stampa.
    # Le nervature sono due, affiancate al foro invece che a cavallo del suo
    # asse: fra la loro faccia interna e il foro restano 1.75 mm, quindi la
    # testa della M4 (e una rondella Ø9) appoggia in piano sul dorso.
    ears = []
    for sx, sy in EAR_XY:
        x0, x1 = sx - EAR_L / 2.0, sx + EAR_L / 2.0
        y_in, y_tip = sy * (OUT_HY - 0.6), sy * (OUT_HY + EAR_W)
        y_ch = y_tip - sy * EAR_CHAMF
        ears.append(prism(f"ear_{sx:+.0f}_{sy:+.0f}",
                          [(x0, y_in), (x1, y_in), (x1, y_ch),
                           (x1 - EAR_CHAMF, y_tip), (x0 + EAR_CHAMF, y_tip),
                           (x0, y_ch)],
                          0.0, EAR_T))
        y_out = sy * (OUT_HY + EAR_GUSSET_H)
        for sg in (-1, 1):
            gx = sx + sg * EAR_GUSSET_OFF
            ears.append(prism_yz(f"gus_{sx:+.0f}_{sy:+.0f}_{sg:+d}",
                                 [(y_in, EAR_T), (y_in, EAR_T + EAR_GUSSET_H),
                                  (y_out, EAR_T)],
                                 gx - EAR_GUSSET_T / 2.0, gx + EAR_GUSSET_T / 2.0))
    fuse(base, ears)

    # ---- cavita`, spigoli verticali raccordati: e` il raccordo che permette
    # alla cava di curvare su un raggio decente senza assottigliare la spalla.
    cut(base, [prism("cav", rounded_rect(HX, HY, INNER_R), FLOOR, RIM_Z + 1)])

    # ---- sella della batteria: TRE bande svuotate dal cilindro della cella.
    # Gli angoli in pianta sono smussati a 45 gradi nel profilo estruso, quindi
    # sono tagli verticali: non costano nulla in stampa.
    bands = []
    for i, bx in enumerate(CRADLE_BAND_X):
        hw, c = CRADLE_BAND_W / 2.0, CRADLE_CHAMF
        y0, y1 = CELL_CY - CRADLE_HW, CELL_CY + CRADLE_HW
        # Solo il lato +Y viene smussato: il lato -Y e` annegato nella parete.
        bands.append(prism(f"band{i}",
                           [(bx - hw, y0), (bx + hw, y0),
                            (bx + hw, y1 - c), (bx + hw - c, y1),
                            (bx - hw + c, y1), (bx - hw, y1 - c)],
                           FLOOR, CRADLE_TOP))
    fuse(base, bands)

    tools = [cyl("cell", CELL_R, CELL_L + 4,
                 (CELL_CX, CELL_CY, FLOOR + CELL_CZ), axis="X"),
             box("cradlerelief", (CELL_L + 4, CRADLE_RELIEF_W, CRADLE_RELIEF_H),
                 (CELL_CX, CELL_CY, FLOOR + CRADLE_RELIEF_H / 2.0))]

    # Nessun invito sul labbro della culla: vedi la nota su CRADLE_CHAMF.

    # Nessun supporto per la scheda: si fissa con biadesivo sul pavimento.

    for sx, sy in EAR_XY:
        tools.append(cyl(f"earh_{sx:+.0f}_{sy:+.0f}", EAR_HOLE_D / 2.0, EAR_T + 2,
                         (sx, sy * EAR_HOLE_Y, EAR_T / 2.0)))

    # ---- passacavo del pannello solare, parete +X, spostato verso +Y
    tools.append(cyl("gland", GLAND_D / 2.0, WALL * 3,
                     (HX + WALL / 2.0, GLAND_CY, GLAND_CZ), axis="X"))

    # ---- heat-set insert holes, drilled down from the rim
    for i, (lx, ly) in enumerate(LUG_XY):
        tools.append(cyl(f"ins{i}", INSERT_D / 2.0, INSERT_DEPTH + 2,
                         (lx, ly, RIM_Z - INSERT_DEPTH / 2.0 + 1)))

    # ---- N bulkhead nella parete -X, centrato in Y. Lo scasso che assottiglia
    # la parete e` sul lato INTERNO: la faccia esterna resta piana, il dado ci
    # va sopra a filo ed e` raggiungibile con la chiave. Il cilindro sfonda per
    # CONN_RELIEF_DEPTH anche verso la cavita`, che li` e` gia` vuota: serve solo
    # a non lasciare facce complanari sul piano x = -HX.
    tools.append(cyl("conn", CONN_D / 2.0, WALL * 3,
                     (-HX - WALL / 2.0, 0, CONN_CZ), axis="X"))
    tools.append(cyl("connrelief", CONN_RELIEF_D / 2.0, CONN_RELIEF_DEPTH * 2,
                     (-HX, 0, CONN_CZ), axis="X"))

    # ---- cava dell'O-ring: anello continuo, nessuna interruzione
    tools.append(ring_prism("groove",
                            rounded_rect(HX + GROOVE_MID + GROOVE_W / 2.0,
                                         HY + GROOVE_MID + GROOVE_W / 2.0,
                                         GROOVE_R + GROOVE_W / 2.0),
                            rounded_rect(HX + GROOVE_MID - GROOVE_W / 2.0,
                                         HY + GROOVE_MID - GROOVE_W / 2.0,
                                         GROOVE_R - GROOVE_W / 2.0),
                            GROOVE_Z0, RIM_Z + 1))

    cut(base, tools)
    return base


# ---------------------------------------------------------------- lid


def build_lid():
    lid = box("Case_Lid", (OUT_X, OUT_Y, LID_T), (0, 0, RIM_Z + LID_T / 2.0))

    # orecchie del coperchio in corrispondenza dei lug
    fuse(lid, [cyl(f"ltab{i}", LUG_R, LID_T, (lx, ly, RIM_Z + LID_T / 2.0))
               for i, (lx, ly) in enumerate(LUG_XY)])

    # stesso raccordo della base: i due profili devono coincidere, altrimenti
    # il coperchio lascia uno scalino sopra il piede dei lug
    fuse(lid, [lug_fillets("lidfil", RIM_Z, RIM_Z + LID_T)])

    # Labbro perimetrale: cornice continua che entra nella cavita` e centra il
    # coperchio. Non tocca la tenuta, che e` piu` esterna. Non e` un tappo pieno:
    # un blocco riempirebbe tutta la sezione da RIM_Z - LIP_H in su.
    lid = fuse(lid, [ring_prism(
        "lip",
        rounded_rect(HX - LIP_CLR, HY - LIP_CLR, INNER_R - LIP_CLR),
        rounded_rect(HX - LIP_CLR - LIP_W, HY - LIP_CLR - LIP_W,
                     INNER_R - LIP_CLR - LIP_W),
        RIM_Z - LIP_H, RIM_Z)])

    # Nessuna costola ferma-cella: la cella la tiene il biadesivo, la costola
    # faceva inarcare il coperchio e apriva la tenuta.

    # Solo il passante della vite attraversa la piastra. Niente svasatura: si
    # usano M3 a testa bombata che appoggiano sulla corona da r=1.7 a r=3.
    cut(lid, [cyl(f"scr{i}", SCREW_D / 2.0, LID_T * 4,
                  (lx, ly, RIM_Z + LID_T / 2.0))
              for i, (lx, ly) in enumerate(LUG_XY)])

    return lid


# ---------------------------------------------------------------- run

clear_scene()
base = weld(build_base())
lid = weld(build_lid())

os.makedirs(MODEL_DIR, exist_ok=True)
for ob, fname in ((base, "case_base.stl"), (lid, "case_lid.stl")):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    if "stl_export" in dir(bpy.ops.wm):          # Blender >= 4.2
        bpy.ops.wm.stl_export(filepath=os.path.join(MODEL_DIR, fname),
                              export_selected_objects=True, apply_modifiers=True)
    else:                                        # Blender 4.0/4.1
        bpy.ops.export_mesh.stl(filepath=os.path.join(MODEL_DIR, fname),
                                use_selection=True)

# ---------------------------------------------------------------- report

GROOVE_LEN = (2 * (2 * (HX + GROOVE_MID) - 2 * GROOVE_R) +
              2 * (2 * (HY + GROOVE_MID) - 2 * GROOVE_R) + 2 * math.pi * GROOVE_R)
CELL_TOP = FLOOR + CELL_CZ - (CELL_R - CELL_D / 2.0) + CELL_D / 2.0
CELL_AXIS_Z = CELL_TOP - CELL_D / 2.0               # asse della cella reale, appoggiata
# Il labbro del coperchio non passa sopra il colmo della cella: e` una cornice
# larga LIP_W addossata alla parete -Y, dove il cilindro e` gia` sceso. Il
# franco che conta e` quello, non colmo-contro-labbro.
LIP_Y_IN = -(HY - LIP_CLR - LIP_W)                  # bordo interno del labbro, lato -Y
CELL_UNDER_LIP = (CELL_AXIS_Z +
                  math.sqrt(max((CELL_D / 2.0) ** 2 - (LIP_Y_IN - CELL_CY) ** 2, 0.0))
                  if abs(LIP_Y_IN - CELL_CY) < CELL_D / 2.0 else FLOOR)
CRADLE_BAND_TXT = ", ".join(f"{x:.1f}" for x in CRADLE_BAND_X)

print(f"outer footprint: {OUT_X:.1f} x {OUT_Y:.1f} x {RIM_Z + LID_T:.1f} mm  "
      f"(con lug {2 * (LUG_CY + LUG_R):.1f} in Y, con alette {OUT_Y + 2 * EAR_W:.1f})")
print(f"O-ring: corda {ORING_D} in cava {GROOVE_W} x {GROOVE_D} "
      f"(schiacciamento {ORING_D - GROOVE_D:.1f} mm = "
      f"{100 * (ORING_D - GROOVE_D) / ORING_D:.0f}%, riempimento "
      f"{100 * math.pi * (ORING_D / 2) ** 2 / (GROOVE_W * GROOVE_D):.0f}%)")
print(f"  mezzeria a {GROOVE_MID:.1f} dalla faccia interna, raggio d'angolo "
      f"{GROOVE_R:.1f}, sviluppo ~{GROOVE_LEN:.0f} mm; spalle "
      f"{GROOVE_LAND:.1f} interna / {WALL - GROOVE_LAND - GROOVE_W:.1f} esterna")
print(f"  z del solco: {GROOVE_Z0:.1f}..{RIM_Z:.1f}")
print(f"viti: {len(LUG_XY)} M3 a (x={LUG_CX}, y=+/-{LUG_CY}), inserto Ø{INSERT_D}x{INSERT_DEPTH}; "
      f"materiale fra foro e cava {LUG_CY - SCREW_D / 2.0 - (HY + GROOVE_MID + GROOVE_W / 2.0):.1f} mm; "
      f"vite consigliata M3x{LID_T + INSERT_DEPTH:.0f}")
print(f"  raccordo lug/parete R{LUG_FILLET}: sviluppo +/-{LUG_FIL_M:.2f} mm attorno "
      f"a ogni lug (lug d'angolo tagliato a filo, {LUG_FIL_M - (OUT_X / 2 - max(LUG_CX)):.2f} mm)")
print(f"cell bay: r={CELL_R:.2f} axis x={CELL_CX:.2f} y={CELL_CY:.2f} z={FLOOR + CELL_CZ:.2f}, "
      f"colmo {CELL_TOP:.2f} -> {RIM_Z - CELL_TOP:.2f} mm sotto il coperchio piano; "
      f"sotto il labbro la cella arriva a {CELL_UNDER_LIP:.2f} "
      f"({RIM_Z - LIP_H - CELL_UNDER_LIP:.2f} mm liberi)")
print(f"  sella: {len(CRADLE_BAND_X)} bande da {CRADLE_BAND_W} a x={CRADLE_BAND_TXT}, "
      f"h={CRADLE_H:.1f} (labbro z={CRADLE_TOP:.1f}, all'equatore), "
      f"bocca {2 * CRADLE_HALF_MOUTH:.2f} mm "
      f"su cella Ø{CELL_D} -> {2 * CRADLE_HALF_MOUTH - CELL_D:+.2f} mm; "
      f"fianco al labbro {CRADLE_LIP_T:.2f} mm (spigolo netto, niente invito), "
      f"smusso d'angolo {CRADLE_CHAMF}x45 -> piano minimo sul labbro "
      f"{CRADLE_LIP_MIN:.2f} mm{'  ** SOTTILE **' if CRADLE_LIP_MIN < 0.8 else ''}")
print(f"conn N: foro d={CONN_D} z={CONN_CZ:.2f}, scasso INTERNO Ø{CONN_RELIEF_D}x{CONN_RELIEF_DEPTH} "
      f"-> parete utile {WALL - CONN_RELIEF_DEPTH:.1f} mm; faccia esterna piana a x="
      f"{-OUT_X / 2:.1f}, il dado appoggia fuori")
print(f"  scasso arriva a z={CONN_CZ + CONN_RELIEF_D / 2:.1f} vs fondo cava {GROOVE_Z0:.1f} "
      f"({GROOVE_Z0 - (CONN_CZ + CONN_RELIEF_D / 2):.1f} mm di materiale sotto la cava)")
print(f"  sede piana Ø{CONN_SEAT_D} sul fondo dello scasso (x={-HX - CONN_RELIEF_DEPTH:.1f}), "
      f"arriva a z={CONN_CZ + CONN_SEAT_D / 2:.1f}; labbro del coperchio a z={RIM_Z - LIP_H:.1f}")
print(f"  camera libera x da {-HX:.1f} a {CELL_CX - (CELL_L + 4) / 2.0:.1f} ({CONN_BODY_L:.0f} mm), "
      f"il corpo parte {CONN_RELIEF_DEPTH:.0f} mm piu` indietro -> "
      f"{CONN_RELIEF_DEPTH:.0f} mm di margine in piu`")
print(f"board (ruotata 90, senza supporti): {BOARD_X} x {BOARD_Y} @ x={BOARD_CX:.1f} "
      f"y={BOARD_CY:.2f}, striscia libera fra sella e parete +Y "
      f"{HY - CRADLE_Y_MAX:.1f} mm ({BOARD_Y_GAP:.2f}/lato)")
print(f"alette: 4x M4 passante {EAR_HOLE_D}, interasse "
      f"{2 * EAR_X:.1f} x {2 * EAR_HOLE_Y:.1f} mm, spigoli esterni smussati "
      f"{EAR_CHAMF}x45")
print(f"  2 nervature per aletta a x=+/-{EAR_GUSSET_OFF} (sp. {EAR_GUSSET_T}): "
      f"libero attorno al foro {EAR_GUSSET_OFF - EAR_GUSSET_T / 2.0 - EAR_HOLE_D / 2.0:.2f} mm "
      f"per lato; nervatura lunga {EAR_GUSSET_H:.0f} vs bordo aletta a "
      f"{EAR_W:.0f}, smusso a {EAR_W - EAR_CHAMF:.0f}")
print(f"passacavo Ø{GLAND_D} nella parete +X a y={GLAND_CY} z={GLAND_CZ}; "
      f"cella finisce a x={CELL_CX + (CELL_L + 4) / 2.0:.1f} "
      f"({HX - (CELL_CX + (CELL_L + 4) / 2.0):.1f} mm liberi per il polo +), "
      f"bordo +Y della cella y={CELL_CY + CELL_R:.1f}")
print("exported:", sorted(f for f in os.listdir(MODEL_DIR) if f.endswith(".stl")))
