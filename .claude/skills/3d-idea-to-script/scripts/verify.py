"""Validate a generated 3MF: structure a slicer needs, and mesh integrity.

    python verify.py out/model.3mf

Checks the two things that actually go wrong. Structure: does Bambu see one
object with parts (quiet load, colours assigned) or a pile of loose objects
(the "Multi-part object detected" prompt, everything grey). Mesh: is each part
closed and consistently wound, because a slicer will happily produce garbage
from a mesh with holes without telling you.

Deliberately dependency-free -- no trimesh, no lxml -- so it runs in the same
venv as the model script without extra installs.
"""

from __future__ import annotations

import sys
import zipfile
from collections import defaultdict
from xml.etree import ElementTree

CORE = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
WELD = 1e-4  # mm; tessellation leaves seam vertices that are equal but distinct


def _read(path):
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        model = ElementTree.fromstring(zf.read("3D/3dmodel.model"))
        settings = None
        if "Metadata/model_settings.config" in names:
            settings = ElementTree.fromstring(zf.read("Metadata/model_settings.config"))
    return names, model, settings


def _meshes(model):
    """{object id: (welded vertices, triangles)} for every object with a mesh."""
    out = {}
    for obj in model.iter(f"{CORE}object"):
        mesh = obj.find(f"{CORE}mesh")
        if mesh is None:
            continue
        raw = [(float(v.get("x")), float(v.get("y")), float(v.get("z")))
               for v in mesh.iter(f"{CORE}vertex")]

        index, verts = {}, []
        remap = []
        for p in raw:
            key = tuple(round(c / WELD) for c in p)
            if key not in index:
                index[key] = len(verts)
                verts.append(p)
            remap.append(index[key])

        tris = [(remap[int(t.get("v1"))], remap[int(t.get("v2"))], remap[int(t.get("v3"))])
                for t in mesh.iter(f"{CORE}triangle")]
        out[obj.get("id")] = (verts, tris)
    return out


def _volume(verts, tris):
    """Signed volume in mm3. Positive means outward-facing normals."""
    total = 0.0
    for a, b, c in tris:
        ax, ay, az = verts[a]
        bx, by, bz = verts[b]
        cx, cy, cz = verts[c]
        total += (ax * (by * cz - bz * cy)
                  - ay * (bx * cz - bz * cx)
                  + az * (bx * cy - by * cx))
    return total / 6.0


def _shells(verts, tris):
    """How many disconnected lumps the mesh holds (union-find over vertices)."""
    parent = list(range(len(verts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for tri in tris:
        roots = [find(v) for v in tri]
        for r in roots[1:]:
            parent[r] = roots[0]
    return len({find(v) for tri in tris for v in tri})


def _manifold(tris):
    """Every edge used exactly twice, once in each direction."""
    directed = defaultdict(int)
    for a, b, c in tris:
        for e in ((a, b), (b, c), (c, a)):
            directed[e] += 1

    undirected = defaultdict(int)
    for (a, b), n in directed.items():
        undirected[(min(a, b), max(a, b))] += n

    bad_count = [e for e, n in undirected.items() if n != 2]
    bad_wind = [e for e, n in directed.items() if n != 1]
    return bad_count, bad_wind


def main(path):
    names, model, settings = _read(path)
    problems, notes = [], []

    for required in ("[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model"):
        if required not in names:
            problems.append(f"archive is missing {required}")

    if model.get("unit") != "millimeter":
        problems.append(f"unit is {model.get('unit')!r}, expected 'millimeter'")

    meshes = _meshes(model)
    assemblies = {obj.get("id"): [c.get("objectid") for c in obj.iter(f"{CORE}component")]
                  for obj in model.iter(f"{CORE}object")
                  if obj.find(f"{CORE}components") is not None}
    items = [i.get("objectid") for i in model.iter(f"{CORE}item")]

    print(f"{path}\n  mesh objects : {len(meshes)}")
    print(f"  assemblies   : {len(assemblies)}")
    print(f"  build items  : {len(items)}")

    # --- structure: one object with parts, not a pile of loose objects -----
    if len(items) != 1:
        problems.append(
            f"{len(items)} build items. Bambu will treat these as separate objects "
            f"and ask 'Multi-part object detected'. Emit one assembly instead."
        )
    elif items[0] not in assemblies:
        problems.append(
            f"the build item points at object {items[0]}, which has no <components>. "
            f"Meshes must hang off one assembly object."
        )
    else:
        asm = items[0]
        if sorted(assemblies[asm]) != sorted(meshes):
            problems.append(f"assembly {asm} references {assemblies[asm]} "
                            f"but the mesh objects are {sorted(meshes)}")

    # --- the sidecar: this is what actually assigns filament ---------------
    if settings is None:
        problems.append(
            "no Metadata/model_settings.config. Bambu ignores 3MF colour tags and "
            "reads filament from this file -- without it the model loads grey."
        )
    else:
        for obj in settings.iter("object"):
            parts = obj.findall("part")
            if items and obj.get("id") != items[0]:
                problems.append(f"sidecar describes object {obj.get('id')} but the "
                                f"build item is {items[0]}")
            if sorted(p.get("id") for p in parts) != sorted(meshes):
                problems.append(f"sidecar parts {[p.get('id') for p in parts]} do not "
                                f"match mesh objects {sorted(meshes)}")
            for part in parts:
                meta = {m.get("key"): m.get("value") for m in part.findall("metadata")}
                if "extruder" not in meta:
                    problems.append(f"part {part.get('id')} has no extruder -- it will "
                                    f"not get its own colour")
                else:
                    notes.append(f"part {part.get('id')} "
                                 f"{meta.get('name', '?'):<24} extruder {meta['extruder']}")

    # --- mesh integrity ----------------------------------------------------
    print()
    total = 0.0
    for oid, (verts, tris) in sorted(meshes.items(), key=lambda kv: int(kv[0])):
        vol = _volume(verts, tris)
        total += vol
        bad_count, bad_wind = _manifold(tris)
        shells = _shells(verts, tris)
        ok = not bad_count and not bad_wind and vol > 0
        lo = [min(p[i] for p in verts) for i in range(3)]
        hi = [max(p[i] for p in verts) for i in range(3)]

        # bounds are worth reading, not skimming: a part reaching somewhere you
        # did not expect is the cheapest way to catch a stale file or a shape
        # built from the wrong parameters
        print(f"  object {oid}: {len(tris):6d} tris  {vol / 1000:9.3f} cm3  "
              f"{shells} shell(s)  {'watertight' if ok else 'BROKEN'}")
        print(f"             x {lo[0]:8.2f}..{hi[0]:<8.2f} y {lo[1]:8.2f}..{hi[1]:<8.2f} "
              f"z {lo[2]:8.2f}..{hi[2]:.2f}")

        if bad_count:
            problems.append(f"object {oid}: {len(bad_count)} edges not shared by exactly "
                            f"two triangles -- the mesh has holes or overlaps")
        if bad_wind:
            problems.append(f"object {oid}: {len(bad_wind)} edges wound inconsistently -- "
                            f"normals disagree between neighbouring triangles")
        if vol <= 0:
            problems.append(f"object {oid}: volume is {vol:.1f} mm3 -- normals point inward")

    print(f"\n  total volume : {total / 1000:.3f} cm3")
    if notes:
        print()
        for note in notes:
            print(f"  {note}")

    if problems:
        print(f"\nFAILED ({len(problems)}):")
        for p in problems:
            print(f"  - {p}")
        return 1

    print("\nOK: one object with parts, every part extruder-assigned, all meshes closed.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
