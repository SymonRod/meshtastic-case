"""Sezione di una testa d'angolo attraverso la linguetta: come si aggancia.

    blender --background --factory-startup --python render_corner_section.py

Taglia una fetta perpendicolare al bordo del pannello, in pieno dente, e la
guarda di profilo. Due stati affiancati: pannello che scende (a sinistra) e
pannello agganciato (a destra). Produce mount_corner_section.png.
"""
import contextlib
import io
import os

import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "build_mount.py")).read()
g = {"__name__": "__main__", "__file__": os.path.join(HERE, "build_mount.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, "build_mount.py", "exec"), g)

mount = g["mount"]
PT, BASE_T = g["PANEL_T"], g["BASE_T"]
HX, HY = g["PANEL_HX"], g["PANEL_HY"]

# Si seziona l'angolo (+1, +1): li` u cresce verso -X e v verso -Y, quindi la
# fetta e` una lastra normale a X e la vista guarda lungo X.
CUT_U = g["CORNER_L"] + g["LIP_START"] + 6.0     # dove tagliare, in pieno dente
SLICE = 8.0                                      # spessore della fetta
DEPTH = 24.0                                     # quanto si mostra verso l'interno
SEP = 44.0                                       # distanza fra i due stati
RAISE = 7.0                                      # quanto e` alzato il pannello

COL_MOUNT, COL_PANEL = (0.95, 0.72, 0.15, 1.0), (0.10, 0.14, 0.34, 1.0)


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


# la fetta: x fra i due coltelli, e via tutto cio` che sta oltre DEPTH
# dall'angolo, cosi` non finisce in inquadratura il resto della montatura
x0 = HX - CUT_U
boolean(mount, cube("knife_lo", (400, 400, 400), (x0 - 200, 0, 0)))
boolean(mount, cube("knife_hi", (400, 400, 400), (x0 + SLICE + 200, 0, 0)))
boolean(mount, cube("knife_in", (400, 400, 400), (0, HY - DEPTH - 200, 0)))

for i, (dy, dz) in enumerate(((-SEP, RAISE), (0.0, 0.0))):
    c = mount.copy()
    c.data = mount.data.copy()
    bpy.context.collection.objects.link(c)
    c.location = (0.0, dy, 0.0)
    c.color = COL_MOUNT
    # sezione di pannello: dal bordo (y = HY) verso l'interno
    p = cube(f"panel{i}", (SLICE, 26.0, PT),
             (x0 + SLICE / 2.0, HY - 13.0 + dy, BASE_T + dz + PT / 2.0))
    p.color = COL_PANEL
bpy.data.objects.remove(mount, do_unlink=True)

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
# sguardo lungo il bordo del pannello: in orizzontale si vede dentro/fuori dal
# pannello, in verticale z
d = mathutils.Vector((1.0, 0.04, 0.05)).normalized()
cam.location = mathutils.Vector((x0, HY - SEP / 2.0 - 8.0, 8.0)) + d * 400.0
cam.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

scene.render.filepath = os.path.join(HERE, "mount_corner_section.png")
bpy.ops.render.render(write_still=True)
print("render: mount_corner_section.png")
