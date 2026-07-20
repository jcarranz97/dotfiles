"""One-line summary of what this generates.

Describe the shape in a sentence or two, say which parameter is the primary
one, and note what is solved rather than given.

Always writes a 3MF. Pass --stl or --fcstd to also get those.
"""

import shutil
import subprocess
import tempfile
import zipfile  # noqa: F401  (drop if unused)
from pathlib import Path

import click
from build123d import (
    Axis,
    Circle,
    Color,
    Pos,
    export_step,
    export_stl,
    extrude,
    fillet,
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bambu3mf import MESH_ANGULAR_TOLERANCE, MESH_TOLERANCE, Part, write_3mf

console = Console()


# --------------------------------------------------------------------------
# geometry
#
# Keep these as plain functions of numbers -- no click objects, no globals.
# They stay testable from a REPL and reusable when the shape gets reused.
# --------------------------------------------------------------------------
def build_body(radius, height, wall):
    """The main solid. Build solid first, cut features afterwards."""
    body = extrude(Circle(radius), amount=height)
    return body - Pos(0, 0, wall) * extrude(Circle(radius - wall), amount=height)


def build_motif(size, emboss):
    """A decorative part, drawn at unit scale then scaled once.

    Returning it separately (rather than fused) is what lets it print in its
    own colour -- 3MF pins colour per part.
    """
    raise NotImplementedError


# --------------------------------------------------------------------------
# export helpers
# --------------------------------------------------------------------------
def parse_color(text, what):
    """A CSS3 name or #rrggbb, turned into a build123d Color."""
    try:
        return Color(text)
    except ValueError as exc:
        raise click.ClickException(f"{what}: {exc}") from exc


def find_freecadcmd():
    """The argv prefix that runs freecadcmd, or None if FreeCAD is missing."""
    for name in ("freecadcmd", "FreeCADCmd"):
        found = shutil.which(name)
        if found:
            return [found]

    flatpak = shutil.which("flatpak")
    if flatpak:
        listed = subprocess.run([flatpak, "list", "--app", "--columns=application"],
                                capture_output=True, text=True)
        if "org.freecad.FreeCAD" in listed.stdout:
            return [flatpak, "run", "--command=freecadcmd", "--filesystem=home",
                    "org.freecad.FreeCAD"]
    return None


def export_fcstd(shape, fcstd_path, label):
    """Round-trip through STEP so FreeCAD sees real faces and edges.

    The driver script has to live under $HOME: the FreeCAD flatpak's sandbox
    cannot read /tmp, which is where a temp file would otherwise land.
    """
    launcher = find_freecadcmd()
    if launcher is None:
        raise click.ClickException(
            "FreeCAD not found. Install it (`flatpak install flathub "
            "org.freecad.FreeCAD`) or drop --fcstd."
        )

    fcstd_path = fcstd_path.resolve()
    workdir = Path(tempfile.mkdtemp(prefix=".build-", dir=fcstd_path.parent))
    try:
        step_path = workdir / "shape.step"
        export_step(shape, str(step_path))

        driver = workdir / "to_fcstd.py"
        driver.write_text(
            "import FreeCAD, Part\n"
            f"doc = FreeCAD.newDocument({label!r})\n"
            f"obj = doc.addObject('Part::Feature', {label!r})\n"
            "shape = Part.Shape()\n"
            f"shape.read({str(step_path)!r})\n"
            "obj.Shape = shape\n"
            "doc.recompute()\n"
            f"doc.saveAs({str(fcstd_path)!r})\n"
        )
        run = subprocess.run([*launcher, str(driver)], capture_output=True, text=True)
        if not fcstd_path.exists():
            detail = (run.stderr or run.stdout or "").strip()
            raise click.ClickException(f"FreeCAD could not write the document.\n{detail}")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------
@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--radius", "-r", required=True, type=float,
              help="The one number you must give (mm).")
@click.option("--wall", "-w", default=3.0, show_default=True,
              help="Wall thickness (mm).")
@click.option("--motif-size", default=None, type=float, show_default="fitted",
              help="Motif size (mm). 0 leaves it off.")
@click.option("--motif-emboss", default=1.0, show_default=True,
              help="How far the motif stands proud (mm).")
@click.option("--motif-color", default="blue", show_default=True,
              help="Motif colour for viewers that read 3MF colours.")
@click.option("--body-color", default="white", show_default=True,
              help="Body colour for viewers that read 3MF colours.")
@click.option("--motif-extruder", default=2, show_default=True,
              help="Which filament slot prints the motif in Bambu Studio.")
@click.option("--body-extruder", default=1, show_default=True,
              help="Which filament slot prints the body in Bambu Studio.")
@click.option("--stl", is_flag=True, help="Also write an .stl alongside the 3MF.")
@click.option("--fcstd", is_flag=True, help="Also write a .FCStd to edit in FreeCAD.")
@click.option("--name", "-n", default="model", show_default=True,
              help="Output file stem.")
@click.option("--outdir", "-o", type=click.Path(file_okay=False, path_type=Path),
              default=Path("out"), show_default=True, help="Where to write the files.")
def main(radius, wall, motif_size, motif_emboss, motif_color, body_color,
         motif_extruder, body_extruder, stl, fcstd, name, outdir):
    """One-line description shown in --help."""
    # 1. validate, with messages that say what to do about it
    if radius <= 0 or wall <= 0:
        raise click.ClickException("radius and wall must be positive.")
    if wall >= radius:
        raise click.ClickException(
            f"--wall {wall:g} does not fit inside a {radius:g} mm radius."
        )

    motif_rgba = parse_color(motif_color, "--motif-color")
    body_rgba = parse_color(body_color, "--body-color")

    # 2. derive: solve anything the model promises to be exact about
    height = 42.0  # replace with a real solve

    # 3. show the resolved numbers before spending time building
    specs = Table.grid(padding=(0, 2))
    specs.add_column(style="cyan", justify="right")
    specs.add_column(style="white")
    specs.add_row("outside", f"{2 * radius:g} mm wide x {height:.1f} mm tall")
    specs.add_row("wall", f"{wall:g} mm")
    console.print(Panel(specs, title="[bold]model[/]", border_style="cyan", expand=False))

    # 4. build: body and decoration stay separate so each can take a colour
    with console.status("[cyan]shaping..."):
        body = build_body(radius, height, wall)
        motif = None
        if motif_size:
            motif = Pos(0, 0, wall) * build_motif(motif_size, motif_emboss)
        # one fused solid for the formats that cannot hold colours
        whole = body if motif is None else body + motif

    # 5. export
    outdir.mkdir(parents=True, exist_ok=True)
    mf_path = outdir / f"{name}.3mf"

    parts = [Part(body, f"{name}-body", body_extruder, body_rgba)]
    if motif is not None:
        parts.append(Part(motif, f"{name}-motif", motif_extruder, motif_rgba))

    with console.status("[cyan]exporting 3MF..."):
        write_3mf(mf_path, parts, name)

    out = Table.grid(padding=(0, 2))
    out.add_column(style="green")
    out.add_column(style="dim")
    out.add_row(str(mf_path), "slice and print")

    if stl:
        stl_path = outdir / f"{name}.stl"
        export_stl(whole, str(stl_path), tolerance=MESH_TOLERANCE,
                   angular_tolerance=MESH_ANGULAR_TOLERANCE)
        out.add_row(str(stl_path), "same mesh, older format")

    if fcstd:
        fcstd_path = outdir / f"{name}.FCStd"
        export_fcstd(whole, fcstd_path, name)
        out.add_row(str(fcstd_path), "open in FreeCAD to edit")

    console.print(out)

    # 6. report what was measured, not what was asked for
    console.print(f"[dim]plastic ~{whole.volume / 1000:.1f} cm3[/]")


if __name__ == "__main__":
    main()
