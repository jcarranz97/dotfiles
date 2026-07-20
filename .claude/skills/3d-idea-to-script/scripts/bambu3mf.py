"""Bambu-flavoured 3MF writer for build123d solids.

Copy this file next to your model script and `from bambu3mf import Part, write_3mf`.
It is deliberately standalone so a generated project has no import gymnastics.

Why this exists rather than build123d's own `Mesher`:

  * Bambu Studio ignores the standard 3MF `<basematerials>` colour tags. It
    picks filament from `Metadata/model_settings.config`, a sidecar holding an
    extruder index per part. Without that file a model is grey no matter how
    correct its colour tags are.
  * `Mesher.add_shape()` explodes a `Compound` into its children, and a
    build123d `Part` *is* a Compound -- so a colour set on the Part is silently
    dropped, and every solid lands as its own top-level object.
  * Loose top-level objects make Bambu Studio pop up "Multi-part object
    detected". One object whose `<components>` are the parts does not.

So: every part becomes one mesh, all meshes hang off a single assembly object,
and the sidecar assigns filament. Colour tags are still written for viewers and
slicers that do read them.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from xml.sax.saxutils import escape

PLATE_CENTRE = (128.0, 128.0)  # middle of a 256 mm Bambu bed (A1 / P1 / X1)

MESH_TOLERANCE = 0.02          # mm of chord error allowed off the true surface
MESH_ANGULAR_TOLERANCE = 0.15


@dataclass
class Part:
    """One printable piece of the model.

    shape:    a build123d solid/Part. Disjoint lumps are fine -- they are
              merged into a single mesh so the part stays one part.
    label:    shown in the slicer's object tree.
    extruder: filament slot, 1-based. This is what actually colours it.
    color:    anything build123d's Color accepts (CSS name or #rrggbb), or
              None. Only used by viewers that read 3MF colour tags.
    """
    shape: object
    label: str
    extruder: int = 1
    color: object = None


def _num(value):
    """Plain decimal. Scientific notation trips up some 3MF readers."""
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def _rgba_hex(color):
    from build123d import Color
    if color is None:
        return "#FFFFFFFF"
    rgba = color if isinstance(color, Color) else Color(color)
    r, g, b, a = (round(c * 255) for c in tuple(rgba))
    return f"#{r:02X}{g:02X}{b:02X}{a:02X}"


def _mesh_part(shape):
    """Tessellate every solid of a part into one merged vertex/triangle soup.

    Merging is the point: a part made of five disjoint lumps would otherwise
    become five objects in the slicer. One mesh holding five shells is valid
    3MF and arrives as a single part.
    """
    verts, tris = [], []
    for solid in shape.solids():
        v, t = solid.tessellate(MESH_TOLERANCE, MESH_ANGULAR_TOLERANCE)
        base = len(verts)
        verts.extend(v)
        tris.extend((a + base, b + base, c + base) for a, b, c in t)
    if not tris:
        raise ValueError("part tessellated to nothing -- is the shape empty?")
    return verts, tris


def _model_xml(meshes, parts, offset, title):
    asm_id = len(meshes) + 2
    mat_id = asm_id + 1
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model unit="millimeter" xml:lang="en-US"'
        ' xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"'
        ' xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">',
        '<metadata name="Application">build123d</metadata>',
        '<metadata name="BambuStudio:3mfVersion">1</metadata>',
        f'<metadata name="Title">{escape(title)}</metadata>',
        '<resources>',
        f'<basematerials id="{mat_id}">',
    ]
    for part in parts:
        out.append(f'<base name="{escape(part.label)}"'
                   f' displaycolor="{_rgba_hex(part.color)}"/>')
    out.append('</basematerials>')

    for i, (verts, tris) in enumerate(meshes, start=1):
        out.append(f'<object id="{i}" type="model" pid="{mat_id}" pindex="{i - 1}">')
        out.append('<mesh><vertices>')
        out += [f'<vertex x="{_num(v.X)}" y="{_num(v.Y)}" z="{_num(v.Z)}"/>'
                for v in verts]
        out.append('</vertices><triangles>')
        out += [f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris]
        out.append('</triangles></mesh></object>')

    out.append(f'<object id="{asm_id}" type="model"><components>')
    out += [f'<component objectid="{i}"/>' for i in range(1, len(meshes) + 1)]
    out.append('</components></object></resources>')
    out.append(
        f'<build><item objectid="{asm_id}" transform="1 0 0 0 1 0 0 0 1 '
        f'{_num(offset[0])} {_num(offset[1])} 0" printable="1"/></build>'
    )
    out.append('</model>')
    return "\n".join(out)


def _settings_xml(parts, asm_id, title):
    """Bambu's sidecar. This, not the colour tags, is what picks filament."""
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<config>',
           f'<object id="{asm_id}">',
           f'<metadata key="name" value="{escape(title)}"/>',
           f'<metadata key="extruder" value="{parts[0].extruder}"/>']
    for i, part in enumerate(parts, start=1):
        out += [
            f'<part id="{i}" subtype="normal_part">',
            f'<metadata key="name" value="{escape(part.label)}"/>',
            '<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>',
            f'<metadata key="extruder" value="{part.extruder}"/>',
            '</part>',
        ]
    out += ['</object>', '</config>']
    return "\n".join(out)


CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
    '<Default Extension="rels"'
    ' ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
    '<Default Extension="model"'
    ' ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
    '</Types>'
)

RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
    '<Relationship Target="/3D/3dmodel.model" Id="rel-1"'
    ' Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
    '</Relationships>'
)


def write_3mf(path, parts, title, plate_centre=PLATE_CENTRE):
    """Write `parts` to a Bambu-ready 3MF, centred on the plate.

    Parts keep their absolute coordinates relative to one another; only the
    whole assembly is translated, so pieces that touch stay touching.
    """
    parts = [p for p in parts if p is not None]
    if not parts:
        raise ValueError("nothing to write -- parts list is empty")

    meshes = [_mesh_part(p.shape) for p in parts]

    every = [v for verts, _ in meshes for v in verts]
    lo_x, hi_x = min(v.X for v in every), max(v.X for v in every)
    lo_y, hi_y = min(v.Y for v in every), max(v.Y for v in every)
    offset = (plate_centre[0] - (lo_x + hi_x) / 2,
              plate_centre[1] - (lo_y + hi_y) / 2)

    asm_id = len(meshes) + 2
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        zf.writestr("_rels/.rels", RELS)
        zf.writestr("3D/3dmodel.model", _model_xml(meshes, parts, offset, title))
        zf.writestr("Metadata/model_settings.config",
                    _settings_xml(parts, asm_id, title))
