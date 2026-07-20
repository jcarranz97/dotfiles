# build123d recipes and traps

Patterns worth reusing, and the specific mistakes that cost real iterations.

## Contents

- [Build order decides how joins look](#build-order-decides-how-joins-look)
- [Selecting edges without guessing](#selecting-edges-without-guessing)
- [Rounded organic outlines](#rounded-organic-outlines)
- [Auto-fitting a shape into a space](#auto-fitting-a-shape-into-a-space)
- [Volume that has to be exact](#volume-that-has-to-be-exact)
- [Text](#text)
- [Deriving proportions from a reference photo](#deriving-proportions-from-a-reference-photo)

## Build order decides how joins look

Fusing an appendage onto a *solid* and hollowing out afterwards produces a
tangential blend. Fusing it onto an already-hollow shell butts it against the
outside and looks stuck on.

```python
cup = extrude(Circle(outer_r), amount=total_h)      # still solid
cup += handle                                        # handle crosses the opening
cup -= Pos(0, 0, floor) * cavity                     # the cut trims it to the rim
```

The handle above is a slot whose near arc is centred on the cup's axis, so the
slab runs clear across the opening; the cavity cut is what shapes the join. If
you instead start the handle at the wall, you get a stub. When a reference
photo shows a part flowing smoothly out of another, ask what cut could have
produced that curve — usually the join is a by-product of a later operation,
not something modelled directly.

## Selecting edges without guessing

`edges().group_by(Axis.Z)[-1]` grabs the topmost band of edges. That is only
unambiguous while the geometry is simple, which is an argument for filleting
early:

```python
cup = extrude(Circle(outer_r), amount=total_h)
if rim_fillet:
    # a plain cylinder's top face has exactly one edge -- no ambiguity
    cup = fillet(cup.edges().group_by(Axis.Z)[-1], radius=rim_fillet)
```

Once the cavity is cut, that band holds two concentric circles. They share a
centre, so `sort_by(Axis.X)` cannot tell them apart and will silently pick
either one — filleting the wrong one changes an interior dimension without
looking wrong from outside. If you must select after the fact, sort on
something that actually differs, e.g. `sort_by(SortBy.LENGTH)[-1]` for the
outer circle. Prefer restructuring so the selection is unambiguous.

Guard fillets against the material they consume: `rim_fillet >= wall` grinds
the rim to a knife edge, and a bottom fillet must be smaller than the radius
it lives in.

## Rounded organic outlines

`offset(Polygon(...), amount=r)` gives a polygon with every corner rounded to
radius `r`. This is the workhorse for paw pads, blobs and lozenges. Two things
control how it reads:

**Roundness comes from the ratio.** A small polygon with a large offset reads
as a soft blob; a large polygon with a small offset reads as a box with
clipped corners. If a shape looks too boxy, shrink the polygon and raise the
offset rather than adding vertices.

**Convex sides need intermediate vertices.** A three-vertex triangle offsets
into a rounded triangle with dead-straight sides. Adding mid-edge vertices
slightly outboard makes the sides bow.

**For a notch, move a vertex — do not subtract a circle.** Subtracting a
circle from a straight edge leaves a visible bite with corners where the arc
meets the edge. Putting a reflex vertex in the outline (a point sitting
*inside* the hull, between two lobes) and offsetting gives a soft valley that
flows into the neighbouring curves:

```python
PAD_CORNERS = [
    (0.0, -0.08),    # apex
    (-0.10, -0.20),
    (-0.20, -0.36),  # left lobe
    (0.0, -0.32),    # reflex: higher than the lobes -> soft V, not a bite
    (0.20, -0.36),   # right lobe
    (0.10, -0.20),
]
pad = offset(Polygon(*PAD_CORNERS), amount=0.16)
```

Draw motifs at **unit scale** (roughly 1.0 tall) and scale once at the end.
Then a single `--motif-size` parameter controls the whole thing and the
proportions can never drift apart.

## Auto-fitting a shape into a space

To fit a motif inside a circular area, you need its true reach from the
centre. A bounding box overstates that badly for round shapes — a box corner
sits well outside a paw, which shrank the auto-fitted version by about a third
before this was fixed. Sample the real outline instead:

```python
def reach(sketch):
    """Distance from the origin to the farthest point on the outline."""
    return max(abs(wire @ (i / 120.0))
               for face in sketch.faces()
               for wire in [face.outer_wire()]
               for i in range(120))
```

`wire @ t` evaluates the wire at parameter t, so this walks the actual curve.
Then scale so `reach * scale == fill_fraction * available_radius`, and offer an
explicit override that errors out with the cap when it will not fit:

```
--paw-size 200 spills off the floor: it needs a 110.4 mm radius but only
38.0 mm is flat. Cap it at 68.9.
```

Note the usable floor of a filleted cavity is `inner_r - bottom_fillet`, not
`inner_r`.

## Volume that has to be exact

When a model claims to measure something, solve for the dimension instead of
letting the user compute it.

A fillet removes a fixed amount independent of height, so one probe corrects
for it exactly — no iteration:

```python
def solve_height(inner_r, target_mm3, bottom_fillet):
    area = math.pi * inner_r**2
    plain = target_mm3 / area
    if bottom_fillet <= 0:
        return plain
    probe = max(plain, bottom_fillet * 2 + 1.0)
    deficit = area * probe - build_cavity(inner_r, probe, bottom_fillet).volume
    return (target_mm3 + deficit) / area
```

**Anything embossed inside the cavity displaces the contents.** A paw on the
floor makes the cup measure short unless the cavity is deepened by exactly the
paw's volume. Compute the decoration first, then solve:

```python
paw_vol = paw.volume if paw is not None else 0.0
fill_h = solve_height(inner_r, target_mm3 + paw_vol, bottom_fillet)
```

Decoration *outside* the cavity (a name on the handle) displaces nothing.

Then report the measured result rather than the target, so a mistake is
visible: `brim-full 236.6 ml (1.000 cups)`.

## Text

```python
letters = Text(name, font_size=20, font="Ubuntu", font_path=None,
               font_style=FontStyle.BOLD)
```

**OpenCascade silently substitutes FreeSans for a font it cannot find.** No
exception, just different lettering — which for a customer-facing model means
shipping the wrong thing and only finding out after the print. Check the family
before building:

```python
def font_families():
    listed = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True)
    return {n.strip() for line in listed.stdout.splitlines()
            for n in line.split(",") if n.strip()}
```

`--font-path` pointing at a `.ttf` bypasses the family lookup and is the right
escape hatch, since the nice rounded faces usually are not installed.

Size text by fitting its bounding box to the available area, taking whichever
of width or height runs out first, so short and long names both work. Bold
weights matter for printing: strokes thinner than about 1.5 mm come out
fragile.

## Deriving proportions from a reference photo

Measure the picture rather than eyeballing it. Pick the overall height as 1.0,
read pixel coordinates of each feature, and convert:

```
x_unit = (x_px - centre_x_px) / height_px
y_unit = (centre_y_px - y_px) / height_px      # image Y runs down, model Y up
```

Write those into a constants table with a comment per row. It makes the shape
reviewable and adjustable without re-reading the photo:

```python
#      x       y     x_rad  y_rad  tilt
TOES = [
    (-0.190, 0.303, 0.142, 0.204, 7),    # inner left
    (0.190, 0.303, 0.142, 0.204, -7),    # inner right
]
```

Watch for features colliding once rounded — a pad that is widest at mid-height
will run into the toes that sit there, even though the numbers came straight
off the photo.
