"""Sezione della clip attraverso la linguetta: come il pannello ci si aggancia.

    blender --background --factory-startup --python render_clip_section.py

Taglia la clip su un piano perpendicolare al bordo del pannello, all'altezza
del dente, e la guarda di profilo. Due stati affiancati: pannello che scende
(a sinistra) e pannello agganciato (a destra). Produce mount_clip_section.png.
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

clip = g["clip"]
bpy.data.objects.remove(g["frame"], do_unlink=True)

PT, PZ = g["PANEL_T"], g["PANEL_Z"]
CUT_U = g["CLIP_BLK"] + g["LIP_START"] + 6.0     # dove tagliare, in pieno dente
SLICE = 8.0                                       # spessore della fetta di sezione
SEP = 44.0                                        # distanza fra i due stati
RAISE = 7.0                                       # quanto e` alzato il pannello a sinistra


COL_CLIP, COL_PANEL = (0.95, 0.72, 0.15, 1.0), (0.10, 0.14, 0.34, 1.0)


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


# taglio: via tutto cio` che sta oltre CUT_U lungo il bordo
# si tiene una fetta sottile: cosi` si vede la linguetta e il piano, e non
# finisce nell'inquadratura la linguetta dell'altro bordo, che sta dietro
boolean(clip, cube("knife_hi", (200, 200, 200), (CUT_U + 100, 0, 0)))
boolean(clip, cube("knife_lo", (200, 200, 200), (CUT_U - SLICE - 100, 0, 0)))

for i, (dv, dz) in enumerate(((0.0, RAISE), (SEP, 0.0))):
    c = clip.copy()
    c.data = clip.data.copy()
    bpy.context.collection.objects.link(c)
    c.location = (0.0, dv, 0.0)
    c.color = COL_CLIP
    # sezione di pannello: parte dal bordo (v = 0) e va verso l'interno
    p = cube(f"panel{i}", (SLICE, 26.0, PT), (CUT_U - SLICE / 2.0, dv + 13.0, PZ + dz + PT / 2.0))
    p.color = COL_PANEL
bpy.data.objects.remove(clip, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.render.image_settings.compression = 100
sh = scene.display.shading
sh.light, sh.color_type = "STUDIO", "OBJECT"
sh.show_cavity, sh.cavity_type, sh.show_shadows = True, "BOTH", False
scene.world.color = (0.93, 0.93, 0.94)

bpy.ops.object.camera_add()
cam = bpy.context.active_object
cam.data.type = "ORTHO"
cam.data.ortho_scale = 74.0
scene.camera = cam
# sguardo lungo -u (cioe` lungo il bordo del pannello): in orizzontale si vede
# v (dentro/fuori dal pannello), in verticale z
d = mathutils.Vector((1.0, -0.04, 0.05)).normalized()
cam.location = mathutils.Vector((CUT_U, SEP / 2.0 + 5.0, 15.0)) + d * 400.0
cam.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

scene.render.filepath = os.path.join(HERE, "mount_clip_section.png")
bpy.ops.render.render(write_still=True)
print("render: mount_clip_section.png")
