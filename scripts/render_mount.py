"""Render di controllo della montatura: assieme e dettaglio di un angolo.

    blender --background --factory-startup --python scripts/render_mount.py

Produce mount_assembly.png (scatola + montatura, vista isometrica),
mount_assembly_panel.png (con il pannello agganciato) e mount_corner.png
(dettaglio di una testa d'angolo). Serve a guardare, non a misurare: le quote
le controlla verify_mount.py.
"""
import contextlib
import io
import os

import bpy
import mathutils

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
MODEL_DIR = os.path.join(PROJECT_DIR, "models")
RENDER_DIR = os.path.join(PROJECT_DIR, "renders")
src = open(os.path.join(SCRIPT_DIR, "build_mount.py")).read()
g = {"__name__": "__main__", "__file__": os.path.join(SCRIPT_DIR, "build_mount.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, "build_mount.py", "exec"), g)

mount = g["mount"]
LID_TOP = 32.1                                   # faccia del coperchio, in coordinate scatola
PANEL_W, PANEL_H, PANEL_T = g["PANEL_W"], g["PANEL_H"], g["PANEL_T"]
RISE_H = g["RISE_H"]


def mat(name, rgba):
    m = bpy.data.materials.new(name)
    m.use_nodes = False
    m.diffuse_color = rgba
    return m


COL = {"case": mat("case", (0.22, 0.24, 0.28, 1.0)),
       "mount": mat("mount", (0.85, 0.45, 0.12, 1.0)),
       "panel": mat("panel", (0.10, 0.14, 0.34, 1.0))}


def paint(ob, key):
    ob.data.materials.clear()
    ob.data.materials.append(COL[key])
    return ob


def import_stl(name):
    path = os.path.join(MODEL_DIR, name)
    if not os.path.exists(path):
        return None
    before = set(bpy.data.objects)
    if "stl_import" in dir(bpy.ops.wm):
        bpy.ops.wm.stl_import(filepath=path)
    else:
        bpy.ops.import_mesh.stl(filepath=path)
    return [o for o in bpy.data.objects if o not in before][0]


for n in ("case_base.stl", "case_lid.stl"):
    ob = import_stl(n)
    if ob:
        paint(ob, "case")

mount.location.z = LID_TOP
paint(mount, "mount")

bpy.ops.mesh.primitive_cube_add(size=1,
                                location=(0, 0, LID_TOP + RISE_H + PANEL_T / 2.0))
panel = bpy.context.active_object
panel.name = "Panel"
panel.scale = (PANEL_W, PANEL_H, PANEL_T)
bpy.ops.object.transform_apply(scale=True)
paint(panel, "panel")

# ------------------------------------------------------------------- scena
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
# i PNG versionati sono passati anche da `magick <f> -colors 256 -depth 8 <f>`:
# il render Workbench e` a tinte piatte, la palette indicizzata lo porta da
# ~1.2 MB a ~100 kB senza differenze visibili.
scene.render.resolution_x, scene.render.resolution_y = 1280, 880
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.compression = 100
sh = scene.display.shading
sh.light = "STUDIO"
sh.color_type = "MATERIAL"
sh.show_cavity = True
sh.cavity_type = "BOTH"
sh.show_shadows = True
scene.world.color = (0.92, 0.92, 0.93)

bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.data.type = "ORTHO"
scene.camera = cam


def shoot(target, ortho, direction, fname, hide=()):
    for ob in hide:
        ob.hide_render = True
    d = mathutils.Vector(direction).normalized()
    cam.location = mathutils.Vector(target) + d * 600.0
    cam.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    cam.data.ortho_scale = ortho
    os.makedirs(RENDER_DIR, exist_ok=True)
    scene.render.filepath = os.path.join(RENDER_DIR, fname)
    bpy.ops.render.render(write_still=True)
    for ob in hide:
        ob.hide_render = False
    print("render:", fname)


shoot((0, 0, LID_TOP + 6), 250.0, (0.75, -0.95, 0.75), "mount_assembly.png", hide=(panel,))
shoot((0, 0, LID_TOP + 8), 250.0, (0.75, -0.95, 0.75), "mount_assembly_panel.png")
shoot((PANEL_W / 2.0 - 16, PANEL_H / 2.0 - 16, LID_TOP + RISE_H), 70.0,
      (0.9, -0.7, 0.55), "mount_corner.png", hide=(panel,))
