---
name: 3d-idea-to-script
description: Turn an idea, sketch, photo or reference model into a parametric Python script (build123d) that generates a printable 3MF, including correct multi-colour parts for Bambu Studio. Use this whenever the user wants to design, model, generate or modify a 3D-printable object from a description or picture, asks for an STL/3MF/STEP generator, wants a customisable or parametric version of a part, wants text or a logo embossed on a model, or wants a model split into colours for a multi-material print — even if they just say "can you make me a ..." and show a picture.
---

# From an idea to a parametric model script

The deliverable is never a one-off mesh. It is a **script** the user can rerun
with different numbers, because the second request is always "same thing but
bigger / with a different name / in two colours".

## The stack — settled, do not re-litigate

| Concern | Choice |
| --- | --- |
| Modelling | `build123d` (OpenCascade B-rep, same kernel as FreeCAD) |
| CLI | `click` |
| Terminal output | `rich` |
| Primary output | `.3mf` — carries units, part names and colour |
| Optional output | `.stl` behind `--stl`, `.FCStd` behind `--fcstd` |
| Previews | `matplotlib` (dev only; the model script never imports it) |

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python build123d click rich matplotlib
```

Keep the venv beside the script and run it as `.venv/bin/python model.py` — no
activation. build123d pulls in a large OCP wheel, so expect the install to take
a minute.

Mesh output is **3MF by default**. STL loses units and colour; there is no
reason to make it the primary artifact.

## Bundled files

Copy `scripts/bambu3mf.py` into the project and import it. It is the one piece
that must not be re-derived — a hand-rolled 3MF writer will silently load grey
in Bambu Studio, and the reasons are non-obvious.

- `assets/template.py` — skeleton with the expected shape of the script
- `scripts/bambu3mf.py` — the 3MF writer (copy into the project)
- `scripts/verify.py` — validates structure and mesh integrity of the output
- `scripts/preview.py` — renders the 3MF to a PNG so you can look at it
- `references/build123d-recipes.md` — geometry patterns and traps. **Read this
  before modelling anything organic, filleted, text-bearing, or volume-exact.**
- `references/bambu-3mf.md` — the format details, for when something loads
  wrong or a non-Bambu slicer is the target

## Workflow

**1. Pin down the shape before writing code.** Study the reference picture and
name the primitives: a cylinder, a stadium slot, a rounded triangle. Measure
proportions off the image in pixels and normalise them (see the recipes) rather
than guessing millimetres. Decide which single number is the primary parameter
— the one the user is most likely to change — and make it the required option.

**2. Decide the parts split now, not later.** Every region that could print in
a different colour must be a **separate solid**, kept separate all the way to
export. Fusing decoration into the body is a one-way door: you cannot recover
the split afterwards. Typical split: body / decoration / lettering.

**3. Build geometry as plain functions of numbers.** No click objects inside
geometry code. It keeps things testable from a REPL and reusable.

**4. Iterate in 2D before 3D.** For any motif, plot the sketch with matplotlib
and look at it. A 2D plot renders in a second; a 3MF round-trip takes far
longer and a 1 mm emboss is nearly invisible in a shaded 3D view anyway. This
is the single biggest time saver — several shape revisions today were caught in
2D in seconds each.

**5. Screenshot and actually look at it.** Render with `preview.py` and read
the image. Straight-down (`--elev 90`) is the reliable view; use `--tint-z` to
make shallow relief visible. Compare against the reference and iterate. Do not
declare a shape finished without looking at it.

**6. Verify before reporting.** Run `verify.py` on the output. Regenerate
first — a stale artifact from before the last edit reads as a real result and
will waste a long time. Check that meshed volume matches the B-rep within
~0.05%; a bigger gap means the file is not what you think.

```bash
.venv/bin/python model.py -r 40
.venv/bin/python <skill>/scripts/verify.py out/model.3mf
.venv/bin/python <skill>/scripts/preview.py out/model.3mf /tmp/shot.png
```

**7. Write a README** covering the setup command, worked examples, and the
non-obvious constraints. Future-you will not remember why the build order
matters.

## What the script should look like

Follow `assets/template.py`. The shape of it:

- Module docstring saying what it makes and what is solved rather than given
- Geometry functions taking plain numbers
- Tuning constants at module scope with a comment each, not magic numbers
  buried in expressions
- `click` options with `show_default=True`, one required primary parameter,
  everything else defaulted to something that produces a good object with no
  arguments beyond the required one
- A `rich` panel printing the resolved dimensions *before* the slow build
- Export 3MF always; `--stl` and `--fcstd` as flags
- A closing line reporting **measured** properties

Validation earns its keep. Every guard should say what went wrong, in what
units, and what to do:

```
--rim-fillet 3 would eat the whole 3 mm wall and leave a knife edge at the rim.
--paw-size 200 spills off the floor: it needs a 110.4 mm radius but only
  38.0 mm is flat. Cap it at 68.9.
```

## Traps that have already cost time

**Bambu ignores 3MF colour tags.** It assigns filament per part from
`Metadata/model_settings.config`. Standards-correct colour tags alone load
grey. Use `bambu3mf.py`; see `references/bambu-3mf.md`.

**Loose top-level objects trigger a dialog.** Several objects at different
heights make Bambu ask "Multi-part object detected", and *Arrange* scatters
them. One assembly object with `<components>` avoids it. `bambu3mf.py` does
this; `verify.py` checks it.

**One part must be one mesh even when it is in pieces.** A paw is five disjoint
lumps; emitted as five meshes it becomes five parts in the slicer.

**`build123d.Mesher` is the wrong tool for the final 3MF.** It emits one object
per solid, has nowhere to put the sidecar, and drops colour set on a `Part`
(because a `Part` is a `Compound`, which it explodes). Useful as an independent
validator via `Mesher.read()`.

**Colour is a filament slot, not an RGB value.** The model says "extruder 2";
the colour on screen is whatever filament is loaded there. Do not ship a
`project_settings.config` to force it — that is a ~570-key printer profile and
a partial one can stomp the user's settings.

**Build order changes how joins look.** Fuse appendages to the *solid*, then
cut the cavity; the cut is what produces a tangential blend. See the recipes.

**Embossing inside a cavity changes its capacity.** If the model claims to
measure a volume, compute the decoration first and deepen the cavity by exactly
what it displaces.

**OpenCascade silently substitutes a font it cannot find.** Validate the family
against `fc-list` before building text, or a typo ships the wrong lettering.

**Edge selection gets ambiguous after booleans.** Fillet while the shape is
still simple. Two concentric circles share a centre, so sorting them by
position picks arbitrarily.

**Matplotlib depth-sorts within a collection, not between collections.** Put
every triangle in one `Poly3DCollection` or near parts vanish behind far ones.

**The FreeCAD flatpak cannot read `/tmp`.** Driver scripts must be written
under `$HOME`.

## Checking in with the user

Confirm interpretation early when a picture is ambiguous — proportions,
orientation, which face carries the decoration, whether a feature is embossed
or engraved. Cheap to ask, expensive to rebuild.

Show renders as you go rather than at the end. Users correct shapes far faster
from an image than from a description, and "the notch looks like a bite" is
feedback you want in minute two, not after a print.
