"""Rialzo per aggiornare la cava O-ring del case gia` stampato.

Il case precedente ha una cava 3.8 x 2.2 mm; quello attuale usa 4.0 x 2.0 mm.
Una fascia piena larga quanto la vecchia cava recupererebbe i 0.2 mm di
compressione, ma toglierebbe troppo volume all'O-ring (riempimento 93%).

Lo script produce due binari centrali continui:

* standard, 0.2 x 1.8 mm: compressione 33%;
* alta compressione, 0.3 x 1.2 mm: compressione 37%;
* lascia due tasche laterali nelle quali il silicone puo` deformarsi;
* lascia 8.0 mm^2 di sezione libera, esattamente come la nuova cava 4 x 2.

Stampa una sola variante, piatta, senza supporti e senza scalarla in Z.

    blender --background --factory-startup --python scripts/build_oring_shim.py
"""
import math
import os
import re

import bmesh
import bpy


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
MODEL_DIR = os.path.join(PROJECT_DIR, "models")

# Cava della base gia` stampata. Le quote della cava attuale e del percorso
# vengono invece lette da build_case.py, per non duplicare la fonte di verita`.
OLD_GROOVE_W, OLD_GROOVE_D = 3.8, 2.2


def case_constants(*names):
    """Legge le costanti numeriche semplici da build_case.py senza eseguirlo."""
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


(INNER_X, INNER_Y, INNER_R, ORING_D, NEW_GROOVE_W, NEW_GROOVE_D,
 NEW_GROOVE_LAND) = case_constants(
    "INNER_X", "INNER_Y", "INNER_R", "ORING_D", "GROOVE_W", "GROOVE_D",
    "GROOVE_LAND")
GROOVE_MID = NEW_GROOVE_LAND + NEW_GROOVE_W / 2.0

# Entrambe conservano il volume libero della cava nuova. Aumentando l'altezza
# si riduce la larghezza, evitando che l'O-ring incomprimibile faccia da
# distanziale e impedisca al coperchio di andare in battuta.
TARGET_FREE_AREA = NEW_GROOVE_W * NEW_GROOVE_D
VARIANTS = (
    ("oring_groove_shim.stl", OLD_GROOVE_D - NEW_GROOVE_D, "standard"),
    ("oring_groove_shim_high_compression.stl", 0.30, "alta compressione"),
)

SEG = 10  # uguale a rounded_rect() di build_case.py: stessi archi poligonali


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def rounded_rect(hx, hy, radius, seg=SEG):
    """Poligono raccordato antiorario, compatibile con build_case.py."""
    cx, cy = hx - radius, hy - radius
    points = []
    for sx, sy, a0 in ((1, 1, 0.0), (-1, 1, 90.0),
                       (-1, -1, 180.0), (1, -1, 270.0)):
        # L'estremo a 90° e` il primo punto del quarto successivo: non viene
        # duplicato, cosi` l'STL non contiene facce degeneri sugli angoli.
        for k in range(seg):
            angle = math.radians(a0 + 90.0 * k / seg)
            points.append((sx * cx + radius * math.cos(angle),
                           sy * cy + radius * math.sin(angle)))
    return points


def ring_prism(name, outer, inner, z0, z1):
    """Anello chiuso a sezione rettangolare."""
    count = len(outer)
    verts = ([(x, y, z) for z in (z0, z1) for x, y in outer]
             + [(x, y, z) for z in (z0, z1) for x, y in inner])
    faces = []
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, count + j, count + i))
        faces.append((2 * count + i, 2 * count + j,
                      3 * count + j, 3 * count + i))
        faces.append((i, j, 2 * count + j, 2 * count + i))
        faces.append((count + i, count + j,
                      3 * count + j, 3 * count + i))

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


hx, hy = INNER_X / 2.0, INNER_Y / 2.0
path_r = INNER_R + GROOVE_MID
path_len = (2 * (2 * (hx + GROOVE_MID) - 2 * path_r)
            + 2 * (2 * (hy + GROOVE_MID) - 2 * path_r)
            + 2 * math.pi * path_r)
oring_area = math.pi * (ORING_D / 2.0) ** 2


def build_variant(filename, shim_h, label):
    """Costruisce una variante conservando TARGET_FREE_AREA nella cava."""
    if shim_h <= 0:
        raise SystemExit(f"{label}: il rialzo non ha altezza positiva")
    shim_w = ((OLD_GROOVE_W * OLD_GROOVE_D) - TARGET_FREE_AREA) / shim_h
    if shim_w <= 0:
        raise SystemExit(f"{label}: il rialzo non ha larghezza positiva")
    if shim_w >= OLD_GROOVE_W:
        raise SystemExit(f"{label}: il rialzo non lascia tasche laterali")

    free_area = OLD_GROOVE_W * OLD_GROOVE_D - shim_w * shim_h
    if not math.isclose(free_area, TARGET_FREE_AREA, abs_tol=1e-9):
        raise SystemExit(f"{label}: errore nel calcolo del volume libero")

    half_w = shim_w / 2.0
    clear_scene()
    shim = ring_prism(
        f"O-ring groove shim - {label}",
        rounded_rect(hx + GROOVE_MID + half_w,
                     hy + GROOVE_MID + half_w,
                     path_r + half_w),
        rounded_rect(hx + GROOVE_MID - half_w,
                     hy + GROOVE_MID - half_w,
                     path_r - half_w),
        0.0, shim_h)

    bpy.ops.object.select_all(action="DESELECT")
    shim.select_set(True)
    bpy.context.view_layer.objects.active = shim
    os.makedirs(MODEL_DIR, exist_ok=True)
    out_path = os.path.join(MODEL_DIR, filename)
    if "stl_export" in dir(bpy.ops.wm):          # Blender >= 4.2
        bpy.ops.wm.stl_export(filepath=out_path,
                              export_selected_objects=True,
                              apply_modifiers=True)
    else:                                         # Blender 4.0/4.1
        bpy.ops.export_mesh.stl(filepath=out_path, use_selection=True)

    effective_depth = OLD_GROOVE_D - shim_h
    squeeze = ORING_D - effective_depth
    print(f"Creato: {out_path}")
    print(f"  {label}: {shim_w:.2f} x {shim_h:.2f} mm, sviluppo ~{path_len:.0f} mm")
    print(f"  compressione: {squeeze:.2f} mm = {100 * squeeze / ORING_D:.1f}%; "
          f"riempimento: {100 * oring_area / free_area:.1f}%")


for variant in VARIANTS:
    build_variant(*variant)
