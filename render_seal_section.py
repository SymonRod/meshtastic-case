"""Sezione della tenuta, tagliata negli STL veri: corda libera e schiacciata.

    blender --background --factory-startup --python render_seal_section.py

Importa case_base.stl e case_lid.stl e li taglia con delle booleane: la
sezione e` quella della mesh esportata, non di un modello ricostruito da
build_case.py. E` deliberato - se un giorno gli STL nella cartella non
corrispondono piu` al sorgente, questo render lo fa vedere invece di
nasconderlo. Percio` NON esegue build_case.py e non riscrive nulla.

L'unico pezzo disegnato qui e` la corda di silicone, che negli STL non c'e':
le sue quote si leggono dal sorgente con lo stesso mini-parser che
build_mount.py usa per l'interfaccia, senza eseguirlo.

Due stati affiancati: coperchio sollevato con la corda a sezione circolare (a
sinistra) e coperchio in battuta sulle spalle con la corda schiacciata (a
destra). La sezione schiacciata e` disegnata a volume costante: un rettangolo
alto GROOVE_D con i due fianchi a semicerchio (forma a stadio), largo quanto
serve perche` l'area torni quella della corda tonda. E` il modo onesto di far
vedere il riempimento: quello che avanza sono i quattro angoli della cava, e
il gioco che resta ai fianchi e` quello vero.

Produce seal_section.png.
"""
import math
import os
import re

import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))


def case_constants(*names):
    """Legge le costanti da build_case.py senza eseguirlo (vedi
    check_case_interface in build_mount.py: stesso parser, stessa ragione)."""
    found = {}
    for line in open(os.path.join(HERE, "build_case.py")):
        m = re.match(r"^([A-Z_][A-Z0-9_, ]*)=\s*([^#]+)", line)
        if not m:
            continue
        keys = [n.strip() for n in m.group(1).split(",") if n.strip()]
        vals = [float(v) for v in re.findall(r"-?\d+\.?\d*", m.group(2))]
        if len(keys) == len(vals):
            found.update(zip(keys, vals))
    missing = [n for n in names if n not in found]
    if missing:
        raise SystemExit(f"build_case.py: costanti non trovate: {missing}")
    return [found[n] for n in names]


(ORING_D, GROOVE_W, GROOVE_D, GROOVE_LAND, INNER_Y, WALL, FLOOR,
 INNER_Z) = case_constants("ORING_D", "GROOVE_W", "GROOVE_D", "GROOVE_LAND",
                           "INNER_Y", "WALL", "FLOOR", "INNER_Z")
HY = INNER_Y / 2.0
RIM_Z = FLOOR + INNER_Z
GROOVE_Z0 = RIM_Z - GROOVE_D
GROOVE_CY = HY + GROOVE_LAND + GROOVE_W / 2.0    # mezzeria della cava, lato +Y

CUT_X = 26.0                                     # dove tagliare: parete +Y, fra i lug
SLICE = 6.0                                      # spessore della fetta
Y_IN = 15.0                                      # quanto si mostra verso l'interno
Z_LO = 19.0                                      # quanto si mostra verso il basso
SEP = 27.0                                       # distanza fra i due stati
RAISE = 4.5                                      # di quanto e` alzato il coperchio

COL_CASE = (0.88, 0.88, 0.90, 1.0)
COL_LID = (0.44, 0.54, 0.72, 1.0)
COL_RING = (0.86, 0.22, 0.18, 1.0)
COL_TEXT = (0.10, 0.10, 0.12, 1.0)

SQUEEZE = ORING_D - GROOVE_D                     # schiacciamento, mm
# larghezza della sezione a stadio che conserva l'area della corda tonda
AREA = math.pi * (ORING_D / 2.0) ** 2
FLAT_W = (AREA - math.pi * (GROOVE_D / 2.0) ** 2) / GROOVE_D + GROOVE_D
SIDE_GAP = (GROOVE_W - FLAT_W) / 2.0             # aria che resta per fianco

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()


def import_stl(fname):
    before = set(bpy.data.objects)
    path = os.path.join(HERE, fname)
    if not os.path.exists(path):
        raise SystemExit(f"{fname} non trovato: rigenera con build_case.py")
    if "stl_import" in dir(bpy.ops.wm):          # Blender >= 4.2
        bpy.ops.wm.stl_import(filepath=path)
    else:                                        # Blender 4.0/4.1
        bpy.ops.import_mesh.stl(filepath=path)
    ob = (set(bpy.data.objects) - before).pop()
    ob.name = fname[:-4]
    # l'importer puo` lasciare la mesh con piu` di un utente, e in quel caso
    # modifier_apply si rifiuta di lavorare: la si stacca subito.
    ob.data = ob.data.copy()
    return ob


def boolean(target, tool, op="DIFFERENCE"):
    mod = target.modifiers.new(name="b", type="BOOLEAN")
    mod.operation, mod.object, mod.solver = op, tool, "EXACT"
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(tool, do_unlink=True)
    return target


def cube(name, size, center):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    ob = bpy.context.active_object
    ob.name, ob.scale = name, size
    bpy.ops.object.transform_apply(scale=True)
    return ob


def cyl_x(name, r, length, center):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=length, location=center,
                                        vertices=96,
                                        rotation=(0.0, math.pi / 2.0, 0.0))
    ob = bpy.context.active_object
    ob.name = name
    return ob


def slice_part(ob):
    """Riduce il pezzo alla sola fetta inquadrata: due coltelli in X, uno in Y
    e uno in Z. Il taglio e` una booleana sulla mesh importata, quindi la
    faccia di sezione e` la sezione vera dell'STL."""
    boolean(ob, cube("k_lo", (400, 400, 400), (CUT_X - 200, 0, 0)))
    boolean(ob, cube("k_hi", (400, 400, 400), (CUT_X + SLICE + 200, 0, 0)))
    boolean(ob, cube("k_in", (400, 400, 400), (0, Y_IN - 200, 0)))
    boolean(ob, cube("k_dn", (400, 400, 400), (0, 0, Z_LO - 200)))
    if not ob.data.polygons:
        raise SystemExit(f"{ob.name}: la fetta a x={CUT_X} e` vuota")
    return ob


base = slice_part(import_stl("case_base.stl"))
lid = slice_part(import_stl("case_lid.stl"))


def oring_round(name, dy):
    """Corda libera: tonda, appoggiata sul fondo della cava."""
    ob = cyl_x(name, ORING_D / 2.0, SLICE,
               (CUT_X + SLICE / 2.0, GROOVE_CY + dy, GROOVE_Z0 + ORING_D / 2.0))
    ob.color = COL_RING
    return ob


def oring_flat(name, dy):
    """Corda schiacciata: sezione a stadio, area conservata."""
    zc = (GROOVE_Z0 + RIM_Z) / 2.0
    body = cube(name, (SLICE, FLAT_W - GROOVE_D, GROOVE_D),
                (CUT_X + SLICE / 2.0, GROOVE_CY + dy, zc))
    for s in (-1, 1):
        c = cyl_x("bead", GROOVE_D / 2.0, SLICE,
                  (CUT_X + SLICE / 2.0,
                   GROOVE_CY + dy + s * (FLAT_W - GROOVE_D) / 2.0, zc))
        boolean(body, c, op="UNION")
    body.color = COL_RING
    return body


def label(text, y, z, size=1.35):
    bpy.ops.object.text_add(location=(CUT_X + SLICE + 2.0, y, z),
                            rotation=(math.pi / 2.0, 0.0, math.pi / 2.0))
    ob = bpy.context.active_object
    ob.data.body, ob.data.size, ob.data.align_x = text, size, "CENTER"
    bpy.ops.object.convert(target="MESH")
    ob.color = COL_TEXT
    return ob


for dy, lift, is_flat in ((-SEP, RAISE, False), (0.0, 0.0, True)):
    for part, col in ((base, COL_CASE), (lid, COL_LID)):
        c = part.copy()
        c.data = part.data.copy()
        bpy.context.collection.objects.link(c)
        c.location = (0.0, dy, lift if part is lid else 0.0)
        c.color = col
    (oring_flat if is_flat else oring_round)("oring", dy)

for part in (base, lid):
    bpy.data.objects.remove(part, do_unlink=True)

label("LIBERO", GROOVE_CY - SEP, Z_LO - 2.5, 2.2)
label(f"corda Ø{ORING_D:g} tonda sul fondo della cava",
      GROOVE_CY - SEP, Z_LO - 5.2)
label(f"sporge {SQUEEZE:g} mm sopra le spalle",
      GROOVE_CY - SEP, Z_LO - 7.4)
label("IN BATTUTA", GROOVE_CY, Z_LO - 2.5, 2.2)
label(f"cava {GROOVE_W:g} × {GROOVE_D:g}, schiacciamento {SQUEEZE:g} mm "
      f"({100 * SQUEEZE / ORING_D:.0f}%)", GROOVE_CY, Z_LO - 5.2)
label(f"riempimento {100 * AREA / (GROOVE_W * GROOVE_D):.0f}%, "
      f"{SIDE_GAP:.2f} mm di aria per fianco", GROOVE_CY, Z_LO - 7.4)
label("sezione di case_base.stl / case_lid.stl - la battuta fissa la "
      "compressione, non il serraggio delle viti",
      GROOVE_CY - SEP / 2.0, Z_LO - 11.0, 1.2)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x, scene.render.resolution_y = 1600, 1000
scene.render.image_settings.compression = 100
sh = scene.display.shading
sh.light, sh.color_type = "STUDIO", "OBJECT"
sh.show_cavity, sh.cavity_type, sh.show_shadows = True, "BOTH", False
sh.background_type = "WORLD"
scene.world.color = (1.0, 1.0, 1.0)

bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.data.type = "ORTHO"
cam.data.ortho_scale = 58.0
scene.camera = cam
d = mathutils.Vector((1.0, 0.03, 0.04)).normalized()
cam.location = (mathutils.Vector((CUT_X, GROOVE_CY - SEP / 2.0, RIM_Z - 7.0))
                + d * 400.0)
cam.rotation_euler = d.to_track_quat("Z", "Y").to_euler()

scene.render.filepath = os.path.join(HERE, "seal_section.png")
bpy.ops.render.render(write_still=True)
print(f"render: seal_section.png  (sezione degli STL a x={CUT_X:g}; "
      f"cava {GROOVE_W:g} x {GROOVE_D:g} letta da build_case.py, "
      f"stadio {FLAT_W:.2f} x {GROOVE_D:g}, aria {SIDE_GAP:.2f}/fianco)")
