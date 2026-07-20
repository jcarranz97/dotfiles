"""Render a 3MF to a PNG so you can actually look at what you built.

    python preview.py out/model.3mf shot.png              # top-down
    python preview.py out/model.3mf iso.png --elev 32 --azim -128

Parts are coloured from the 3MF's own colour tags, so a two-colour model reads
as two colours and you can confirm the split landed where you meant it to.

Reads the 3MF directly (stdlib XML + zipfile) rather than going through
trimesh, which needs lxml for 3MF and is easy to not have installed. Only
matplotlib and numpy are required.

Two rendering details worth keeping, both learned the hard way:

  * Every triangle goes into ONE Poly3DCollection. Matplotlib sorts by depth
    within a collection but not between collections, so drawing each part
    separately makes the near part vanish behind the far one.
  * A 1 mm emboss on a flat floor is invisible in a flat-shaded top-down view
    because both surfaces face the same way. --tint-z paints faces at a given
    height so shallow relief shows up.

Matplotlib sorts whole triangles, so a concave model at an oblique angle shows
some triangles punching through surfaces that should hide them. Straight-down
(--elev 90, the default) is the reliable view for judging a shape; use oblique
shots to sanity-check proportion, not to hunt for defects.
"""

from __future__ import annotations

import argparse
import zipfile
from xml.etree import ElementTree

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

CORE = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
FALLBACK = [(0.93, 0.93, 0.95), (0.16, 0.33, 0.85), (0.95, 0.45, 0.15),
            (0.20, 0.70, 0.35), (0.85, 0.20, 0.45)]


def load_parts(path):
    """[(vertices Nx3, triangles Mx3, rgb)] for each mesh object in the file."""
    with zipfile.ZipFile(path) as zf:
        model = ElementTree.fromstring(zf.read("3D/3dmodel.model"))

    colors = [_hex_rgb(b.get("displaycolor"))
              for b in model.iter(f"{CORE}base")]

    parts = []
    for i, obj in enumerate(model.iter(f"{CORE}object")):
        mesh = obj.find(f"{CORE}mesh")
        if mesh is None:
            continue
        verts = np.array([[float(v.get("x")), float(v.get("y")), float(v.get("z"))]
                          for v in mesh.iter(f"{CORE}vertex")])
        tris = np.array([[int(t.get("v1")), int(t.get("v2")), int(t.get("v3"))]
                         for t in mesh.iter(f"{CORE}triangle")])
        idx = obj.get("pindex")
        rgb = (colors[int(idx)] if idx is not None and int(idx) < len(colors)
               else FALLBACK[i % len(FALLBACK)])
        parts.append((verts, tris, np.array(rgb)))
    return parts


def _hex_rgb(text):
    if not text:
        return FALLBACK[0]
    text = text.lstrip("#")
    return tuple(int(text[i:i + 2], 16) / 255 for i in (0, 2, 4))


def render(path, out, elev, azim, tint_z, tint_band):
    parts = load_parts(path)
    if not parts:
        raise SystemExit(f"{path} holds no meshes")

    light = np.array([0.25, -0.4, 0.88])
    tris, cols = [], []
    for verts, faces, rgb in parts:
        corners = verts[faces]
        normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
        lengths = np.linalg.norm(normals, axis=1, keepdims=True)
        normals = normals / np.where(lengths == 0, 1, lengths)

        shade = np.clip(normals @ light, 0.32, 1.0)
        face_rgb = np.clip(rgb * shade[:, None] * 1.05, 0, 1)

        if tint_z is not None:
            mid_z = corners[:, :, 2].mean(axis=1)
            lit = (normals[:, 2] > 0.7) & (np.abs(mid_z - tint_z) < tint_band)
            face_rgb[lit] = np.clip(np.array([0.95, 0.35, 0.45]) * shade[lit, None], 0, 1)

        tris.append(corners)
        cols.append(face_rgb)

    tris = np.concatenate(tris)
    cols = np.concatenate(cols)

    fig = plt.figure(figsize=(10, 7.5))
    ax = fig.add_subplot(111, projection="3d")
    # one collection, so matplotlib depth-sorts every triangle together
    ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, linewidths=0))

    pts = tris.reshape(-1, 3)
    centre = pts.mean(axis=0)
    reach = (pts.max(axis=0) - pts.min(axis=0)).max() / 2
    for axis, mid in zip("xyz", centre):
        getattr(ax, f"set_{axis}lim")(mid - reach, mid + reach)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(out, dpi=95)
    print(f"{out}  ({len(parts)} part(s), {len(tris)} triangles)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model")
    ap.add_argument("out")
    ap.add_argument("--elev", type=float, default=90, help="90 = straight down")
    ap.add_argument("--azim", type=float, default=-90)
    ap.add_argument("--tint-z", type=float, default=None,
                    help="Paint upward faces at this Z so shallow relief is visible.")
    ap.add_argument("--tint-band", type=float, default=0.25)
    args = ap.parse_args()
    render(args.model, args.out, args.elev, args.azim, args.tint_z, args.tint_band)
