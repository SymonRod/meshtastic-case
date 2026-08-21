"""Sezione del vecchio case con il rialzo O-ring ad alta compressione.

Usa gli STL reali del commit precedente alla modifica della cava (3.8 x 2.2)
e lo STL corrente del rialzo 1.2 x 0.3. Mostra affiancati O-ring libero e
O-ring compresso con il coperchio in battuta.

    blender --background --factory-startup --python scripts/render_shim_section.py

Produce ``seal_shim_section.png``.
"""
import math
import os
import re
import subprocess
import tempfile

import bpy
import mathutils


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
MODEL_DIR = os.path.join(PROJECT_DIR, "models")
RENDER_DIR = os.path.join(PROJECT_DIR, "renders")
OLD_CASE_REV = "3188763"  # ultimo commit con cava 3.8 x 2.2 mm
OLD_GROOVE_W, OLD_GROOVE_D = 3.8, 2.2
SHIM_W, SHIM_H = 1.2, 0.3


def case_constants(*names):
    """Legge le costanti numeriche da build_case.py senza eseguirlo."""
    found = {}
    with open(os.path.join(SCRIPT_DIR, "build_case.py"), encoding="utf-8") as src:
        for line in src:
            match = re.match(r"^([A-Z_][A-Z0-9_, ]*)=\s*([^#]+)", line)
            if not match:
                continue
            keys = [key.strip() for key in match.group(1).split(",") if key.strip()]
            values = [float(value) for value in
                      re.findall(r"-?\d+\.?\d*", match.group(2))]
            if len(keys) == len(values):
                found.update(zip(keys, values))
    missing = [name for name in names if name not in found]
    if missing:
        raise SystemExit(f"build_case.py: costanti non trovate: {missing}")
    return [found[name] for name in names]


(ORING_D, INNER_X, INNER_Y, INNER_R, WALL, FLOOR,
 INNER_Z) = case_constants("ORING_D", "INNER_X", "INNER_Y", "INNER_R",
                          "WALL", "FLOOR", "INNER_Z")
HX, HY = INNER_X / 2.0, INNER_Y / 2.0
RIM_Z = FLOOR + INNER_Z
GROOVE_MID = 3.2
GROOVE_R = INNER_R + GROOVE_MID
GROOVE_CY = HY + GROOVE_MID
OLD_GROOVE_Z0 = RIM_Z - OLD_GROOVE_D

CUT_X = 26.0
SLICE = 6.0
Y_IN = 15.0
Z_LO = 19.0
SEP = 28.0
RAISE = 4.8

COL_CASE = (0.88, 0.88, 0.90, 1.0)
COL_LID = (0.44, 0.54, 0.72, 1.0)
COL_RING = (0.86, 0.22, 0.18, 1.0)
COL_SHIM = (0.96, 0.62, 0.10, 1.0)
COL_TEXT = (0.10, 0.10, 0.12, 1.0)

SQUEEZE = ORING_D - (OLD_GROOVE_D - SHIM_H)
FREE_AREA = OLD_GROOVE_W * OLD_GROOVE_D - SHIM_W * SHIM_H
ORING_AREA = math.pi * (ORING_D / 2.0) ** 2
# Nella sezione compressa il silicone occupa la cava a gradino lasciando aria
# nei quattro angoli. Quattro quarti di cerchio hanno area pi*r^2.
AIR_R = math.sqrt((FREE_AREA - ORING_AREA) / math.pi)

if FREE_AREA <= ORING_AREA:
    raise SystemExit("Il rialzo non lascia volume sufficiente all'O-ring")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()


def old_stl(name, temp_dir):
    """Materializza dal git object database lo STL del vecchio case."""
    path = os.path.join(temp_dir, name)
    with open(path, "wb") as output:
        result = subprocess.run(
            ["git", "show", f"{OLD_CASE_REV}:{name}"], cwd=PROJECT_DIR,
            stdout=output, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise SystemExit(f"Impossibile leggere {name} da {OLD_CASE_REV}: {detail}")
    return path


def import_stl(path, name):
    before = set(bpy.data.objects)
    if "stl_import" in dir(bpy.ops.wm):          # Blender >= 4.2
        bpy.ops.wm.stl_import(filepath=path)
    else:                                        # Blender 4.0/4.1
        bpy.ops.import_mesh.stl(filepath=path)
    ob = (set(bpy.data.objects) - before).pop()
    ob.name = name
    ob.data = ob.data.copy()
    return ob


def boolean(target, tool, operation="DIFFERENCE"):
    modifier = target.modifiers.new(name="section boolean", type="BOOLEAN")
    modifier.operation = operation
    modifier.object = tool
    modifier.solver = "EXACT"
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(tool, do_unlink=True)
    return target


def cube(name, size, center):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return ob


def cyl_x(name, radius, length, center):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius, depth=length, location=center, vertices=96,
        rotation=(0.0, math.pi / 2.0, 0.0))
    ob = bpy.context.active_object
    ob.name = name
    return ob


def slice_part(ob):
    """Riduce un STL alla fetta della parete +Y inquadrata."""
    boolean(ob, cube("cut x-", (400, 400, 400), (CUT_X - 200, 0, 0)))
    boolean(ob, cube("cut x+", (400, 400, 400), (CUT_X + SLICE + 200, 0, 0)))
    boolean(ob, cube("cut y", (400, 400, 400), (0, Y_IN - 200, 0)))
    boolean(ob, cube("cut z", (400, 400, 400), (0, 0, Z_LO - 200)))
    if not ob.data.polygons:
        raise SystemExit(f"{ob.name}: sezione vuota")
    return ob


def copy_at(ob, dy, dz, color):
    clone = ob.copy()
    clone.data = ob.data.copy()
    bpy.context.collection.objects.link(clone)
    clone.location = (0.0, dy, dz)
    clone.color = color
    return clone


def round_oring(dy):
    """Corda libera appoggiata sopra il rialzo."""
    ring = cyl_x(
        "O-ring libero", ORING_D / 2.0, SLICE,
        (CUT_X + SLICE / 2.0, GROOVE_CY + dy,
         OLD_GROOVE_Z0 + SHIM_H + ORING_D / 2.0))
    ring.color = COL_RING
    return ring


def compressed_oring(dy):
    """Silicone a volume costante nella cava a gradino.

    Parte dall'intero volume libero, sottrae il rialzo centrale e quattro
    tasche d'aria uguali agli angoli. L'area rossa risultante e` esattamente
    quella della corda tonda Ø3.
    """
    body = cube(
        "O-ring compresso", (SLICE, OLD_GROOVE_W, OLD_GROOVE_D),
        (CUT_X + SLICE / 2.0, GROOVE_CY + dy,
         OLD_GROOVE_Z0 + OLD_GROOVE_D / 2.0))
    boolean(body, cube(
        "volume rialzo", (SLICE + 2.0, SHIM_W, SHIM_H),
        (CUT_X + SLICE / 2.0, GROOVE_CY + dy,
         OLD_GROOVE_Z0 + SHIM_H / 2.0)))
    for sy in (-1, 1):
        for top in (False, True):
            z = RIM_Z if top else OLD_GROOVE_Z0
            boolean(body, cyl_x(
                "tasca aria", AIR_R, SLICE + 2.0,
                (CUT_X + SLICE / 2.0,
                 GROOVE_CY + dy + sy * OLD_GROOVE_W / 2.0, z)))
    body.color = COL_RING
    return body


def label(text, y, z, size=1.3):
    bpy.ops.object.text_add(
        location=(CUT_X + SLICE + 2.0, y, z),
        rotation=(math.pi / 2.0, 0.0, math.pi / 2.0))
    ob = bpy.context.active_object
    ob.data.body = text
    ob.data.size = size
    ob.data.align_x = "CENTER"
    bpy.ops.object.convert(target="MESH")
    ob.color = COL_TEXT
    return ob


with tempfile.TemporaryDirectory(prefix="meshtastic-old-case-") as temp_dir:
    base = slice_part(import_stl(old_stl("case_base.stl", temp_dir), "Base vecchia"))
    lid = slice_part(import_stl(old_stl("case_lid.stl", temp_dir), "Coperchio vecchio"))

shim_path = os.path.join(MODEL_DIR, "oring_groove_shim_high_compression.stl")
if not os.path.exists(shim_path):
    raise SystemExit("oring_groove_shim_high_compression.stl non trovato")
shim = import_stl(shim_path, "Rialzo 0.30 mm")
shim.location.z = OLD_GROOVE_Z0
bpy.context.view_layer.objects.active = shim
bpy.ops.object.transform_apply(location=True)
shim = slice_part(shim)

for dy, lift, compressed in ((-SEP, RAISE, False), (0.0, 0.0, True)):
    copy_at(base, dy, 0.0, COL_CASE)
    copy_at(lid, dy, lift, COL_LID)
    copy_at(shim, dy, 0.0, COL_SHIM)
    (compressed_oring if compressed else round_oring)(dy)

for source in (base, lid, shim):
    bpy.data.objects.remove(source, do_unlink=True)

label("LIBERO + RIALZO", GROOVE_CY - SEP, Z_LO - 2.5, 2.1)
label(f"vecchia cava {OLD_GROOVE_W:g} × {OLD_GROOVE_D:g} mm; "
      f"rialzo {SHIM_W:g} × {SHIM_H:g} mm",
      GROOVE_CY - SEP, Z_LO - 5.2)
label(f"la corda Ø{ORING_D:g} sporge {SQUEEZE:.1f} mm dalle spalle",
      GROOVE_CY - SEP, Z_LO - 7.4)
label("IN BATTUTA", GROOVE_CY, Z_LO - 2.5, 2.1)
label(f"compressione {SQUEEZE:.1f} mm "
      f"({100 * SQUEEZE / ORING_D:.1f}%)",
      GROOVE_CY, Z_LO - 5.2)
label(f"riempimento {100 * ORING_AREA / FREE_AREA:.1f}% — "
      "volume laterale conservato", GROOVE_CY, Z_LO - 7.4)
label("sezione degli STL del vecchio case + rialzo ad alta compressione",
      GROOVE_CY - SEP / 2.0, Z_LO - 11.0, 1.2)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.compression = 100
shading = scene.display.shading
shading.light = "STUDIO"
shading.color_type = "OBJECT"
shading.show_cavity = True
shading.cavity_type = "BOTH"
shading.show_shadows = False
shading.background_type = "WORLD"
scene.world.color = (1.0, 1.0, 1.0)

bpy.ops.object.camera_add()
camera = bpy.context.active_object
camera.data.type = "ORTHO"
camera.data.ortho_scale = 59.0
scene.camera = camera
direction = mathutils.Vector((1.0, 0.03, 0.04)).normalized()
camera.location = (
    mathutils.Vector((CUT_X, GROOVE_CY - SEP / 2.0, RIM_Z - 7.0))
    + direction * 400.0)
camera.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()

os.makedirs(RENDER_DIR, exist_ok=True)
scene.render.filepath = os.path.join(RENDER_DIR, "seal_shim_section.png")
bpy.ops.render.render(write_still=True)
print(f"Render: {scene.render.filepath}")
print(f"Vecchia cava {OLD_GROOVE_W:g} x {OLD_GROOVE_D:g}; "
      f"rialzo {SHIM_W:g} x {SHIM_H:g}; "
      f"compressione {100 * SQUEEZE / ORING_D:.1f}%; "
      f"riempimento {100 * ORING_AREA / FREE_AREA:.1f}%")
