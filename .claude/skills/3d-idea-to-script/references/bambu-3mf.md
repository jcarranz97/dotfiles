# What Bambu Studio actually reads in a 3MF

Reference for the format `scripts/bambu3mf.py` writes. You do not need this to
use the writer — read it when something loads wrong, when you need to add
plate/printer metadata, or when a slicer other than Bambu is the target.

## The two rules

**1. Bambu ignores 3MF colour tags.** The spec's `<basematerials>` /
`displaycolor` mechanism is what a standards-compliant reader uses, and Bambu
is not one of them. It reads `Metadata/model_settings.config`, a Bambu-specific
sidecar that assigns an **extruder index** per part. A file with perfect colour
tags and no sidecar loads grey.

Because the on-screen colour comes from whichever filament sits in that slot,
the model cannot force "blue" — it can only say "slot 2". That is the portable
behaviour and the right one: the person printing chooses filaments. Do not try
to ship `Metadata/project_settings.config` to force colours; a real one is a
~570-key printer profile and a partial one risks stomping the user's printer
and filament settings.

Keep writing the standard colour tags anyway — they cost nothing and other
tools honour them.

**2. One object with components, not many loose objects.** Several top-level
objects at different heights make Bambu ask *"Multi-part object detected — should
the file be loaded as a single object with multiple parts?"*, and until you
answer, the pieces are separate objects that *Arrange* will scatter.

Structure it the way Bambu itself exports: mesh objects hold geometry, one
assembly object references them as `<components>`, and the build has exactly
one `<item>` pointing at the assembly.

```xml
<resources>
  <object id="1" type="model" pid="6" pindex="0"><mesh>…</mesh></object>
  <object id="2" type="model" pid="6" pindex="1"><mesh>…</mesh></object>
  <object id="5" type="model">
    <components>
      <component objectid="1"/>
      <component objectid="2"/>
    </components>
  </object>
</resources>
<build>
  <item objectid="5" transform="1 0 0 0 1 0 0 0 1 83 128 0" printable="1"/>
</build>
```

The sidecar mirrors it. `part id` matches `component objectid`:

```xml
<config>
  <object id="5">
    <metadata key="name" value="model"/>
    <metadata key="extruder" value="1"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="model-body"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="extruder" value="1"/>
    </part>
    <part id="2" subtype="normal_part">
      <metadata key="name" value="model-paw"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="extruder" value="2"/>
    </part>
  </object>
</config>
```

## Archive layout

The minimum that loads cleanly:

```
[Content_Types].xml              rels + model defaults
_rels/.rels                      points at /3D/3dmodel.model
3D/3dmodel.model                 geometry + assembly + build
Metadata/model_settings.config   per-part extruder assignment
```

Bambu's own exports add plate thumbnails, `project_settings.config`,
`slice_info.config` and often split geometry into `3D/Objects/*.model` via the
production extension (`p:UUID`, `requiredextensions="p"`). None of that is
needed. Keeping everything in one `3dmodel.model` avoids the production
extension entirely.

## Details that bite

**One part = one mesh, even when it is in pieces.** A paw is five disjoint
lumps. Emitted as five meshes it becomes five parts in the slicer. A single
mesh may contain several disconnected shells — merge the tessellated triangles
into one vertex/triangle list with an index offset and it arrives as one part.

**Do not use `build123d.Mesher` for this.** It emits one object per solid and
offers nowhere to attach the sidecar. It also explodes a `Compound` into its
children, and a build123d `Part` *is* a Compound — so a colour assigned to the
Part is dropped on the floor. (If you use `Mesher` anyway, set colour on each
`shape.solids()` member, not on the Part.) `Mesher.read()` is still useful as
an independent validator, since it goes through lib3mf.

**Numbers must be plain decimals.** Scientific notation like `1e-16` is valid
Python formatting and unwelcome in 3MF. Format with `f"{v:.6f}"` then strip
trailing zeros.

**Escape text going into XML.** Part labels and titles come from user input; an
`&` in a pet name produces a corrupt archive.

**Transform placement, not vertices.** Keep parts in model coordinates and put
the plate offset on the build `<item>` transform. Parts that touch stay
touching, and the model is easy to reason about. `(128, 128)` is the centre of
a 256 mm bed (A1 / P1 / X1); the A1 mini is 180 mm.

The transform is 12 numbers, column-major 3x4, translation last:
`"1 0 0 0 1 0 0 0 1 tx ty tz"`. The sidecar's `matrix` is a different format —
16 numbers, row-major 4x4 — and identity there is
`"1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"`.

## Verifying

`scripts/verify.py` checks all of the above plus mesh integrity. Cross-check
volume against the B-rep when it matters:

```python
from build123d import Mesher
shapes = Mesher().read("out/model.3mf")   # lib3mf; raises on a malformed file
```

`trimesh` also reads 3MF but needs `lxml` installed, which is why `verify.py`
and `preview.py` parse the XML themselves.

Expect meshed volume to sit within ~0.05% of the B-rep at the default
tolerances. A larger gap means the file does not contain what you think —
usually a stale artifact from before the last edit. Always regenerate before
the final check.
