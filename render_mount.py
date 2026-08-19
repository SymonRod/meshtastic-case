"""Render di controllo della montatura: assieme e dettaglio di una clip.

    blender --background --factory-startup --python render_mount.py

Produce mount_assembly.png (scatola + telaio + quattro clip, vista isometrica)
e mount_clip.png (una clip con l'angolo del pannello inserito, in sezione di
vista). Serve a guardare, non a misurare: le quote le controlla verify_mount.py.
"""
import contextlib
import io
import math
import os

import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "build_mount.py")).read()
g = {"__name__": "__main__", "__file__": os.path.join(HERE, "build_mount.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, "build_mount.py", "exec"), g)

frame, clip = g["frame"], g["clip"]
LID_TOP = 32.1                                   # faccia del coperchio, in coordinate scatola
PANEL_W, PANEL_H, PANEL_T = g["PANEL_W"], g["PANEL_H"], g["PANEL_T"]
PANEL_Z, ANG = g["PANEL_Z"], {(-1, -1): 0.0, (1, -1): 90.0, (1, 1): 180.0, (-1, 1): 270.0}


def mat(name, rgba):
    m = bpy.data.materials.new(name)
    m.use_nodes = False
    m.diffuse_color = rgba
    return m


COL = {"case": mat("case", (0.22, 0.24, 0.28, 1.0)),
       "mount": mat("mount", (0.85, 0.45, 0.12, 1.0)),
       "clip": mat("clip", (0.95, 0.72, 0.15, 1.0)),
       "panel": mat("panel", (0.10, 0.14, 0.34, 1.0))}


def paint(ob, key):
    ob.data.materials.clear()
    ob.data.materials.append(COL[key])
    return ob


def import_stl(name):
    path = os.path.join(HERE, name)
    if not os.path.exists(path):
        return None
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=path)
    return [o for o in bpy.data.objects if o not in before][0]


for n in ("case_base.stl", "case_lid.stl"):
    ob = import_stl(n)
    if ob:
        paint(ob, "case")

frame.location.z = LID_TOP
paint(frame, "mount")

clips = []
for (sx, sy), deg in ANG.items():
    ob = clip.copy()
    ob.data = clip.data.copy()
    bpy.context.collection.objects.link(ob)
    ob.matrix_world = (mathutils.Matrix.Translation((sx * PANEL_W / 2.0, sy * PANEL_H / 2.0, LID_TOP))
                       @ mathutils.Matrix.Rotation(math.radians(deg), 4, 'Z'))
    clips.append(paint(ob, "clip"))
bpy.data.objects.remove(clip, do_unlink=True)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, LID_TOP + PANEL_Z + PANEL_T / 2.0))
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
    scene.render.filepath = os.path.join(HERE, fname)
    bpy.ops.render.render(write_still=True)
    for ob in hide:
        ob.hide_render = False
    print("render:", fname)


shoot((0, 0, LID_TOP + 8), 250.0, (0.75, -0.95, 0.75), "mount_assembly.png", hide=(panel,))
shoot((0, 0, LID_TOP + 10), 250.0, (0.75, -0.95, 0.75), "mount_assembly_panel.png")
shoot((PANEL_W / 2.0 - 12, PANEL_H / 2.0 - 12, LID_TOP + PANEL_Z), 70.0,
      (0.9, -0.7, 0.55), "mount_clip.png")
