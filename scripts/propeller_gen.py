#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parametric drone-propeller generator for FreeCAD (headless).

Run with the snap FreeCAD interpreter, e.g.:

    freecad.cmd -c "exec(open('scripts/propeller_gen.py').read())" -- <config.json>

or via the wrapper:  scripts/run_freecad.sh scripts/propeller_gen.py <config.json>

Coordinate system (matches the OpenFOAM case):
  * Z  = rotation / thrust axis (propeller spins about +Z, thrust along +Z)
  * X,Y = rotor plane
Units inside FreeCAD are millimetres; STEP/STL are exported in mm.
The whole propeller is designed to fit inside a cylinder D=100 mm x H=60 mm
(radius 50 mm, axial half-extent +/-30 mm) -- the assignment's hard constraint.

The blade is a lofted stack of NACA-4-digit airfoil sections.  Each radial
station r has its own chord, twist (pitch angle measured from the rotor plane),
and camber.  Blades are then circularly patterned about Z and fused to a hub.
"""

import os
import sys
import json
import math

import FreeCAD as App
import Part


# --------------------------------------------------------------------------- #
# Airfoil
# --------------------------------------------------------------------------- #
def naca4(m, p, t, n=60):
    """Return a closed list of (xc, yc) airfoil points, chord normalised 0..1.

    m  max camber (fraction of chord),  p  position of max camber (0..1),
    t  max thickness (fraction of chord),  n  points per surface.
    Loop goes TE -> (upper) -> LE -> (lower) -> TE, consistent for lofting.
    """
    # cosine spacing clusters points at LE/TE for a clean section
    beta = [math.pi * i / (n - 1) for i in range(n)]
    xs = [0.5 * (1.0 - math.cos(b)) for b in beta]

    def camber(x):
        if p <= 0.0 or m <= 0.0:
            return 0.0, 0.0
        if x < p:
            yc = m / (p * p) * (2 * p * x - x * x)
            dy = 2 * m / (p * p) * (p - x)
        else:
            yc = m / ((1 - p) ** 2) * ((1 - 2 * p) + 2 * p * x - x * x)
            dy = 2 * m / ((1 - p) ** 2) * (p - x)
        return yc, dy

    def thick(x):
        return (t / 0.2) * (0.2969 * math.sqrt(max(x, 0.0))
                            - 0.1260 * x - 0.3516 * x * x
                            + 0.2843 * x ** 3 - 0.1015 * x ** 4)

    upper, lower = [], []
    for x in xs:
        yc, dy = camber(x)
        yt = thick(x)
        th = math.atan(dy)
        upper.append((x - yt * math.sin(th), yc + yt * math.cos(th)))
        lower.append((x + yt * math.sin(th), yc - yt * math.cos(th)))
    # TE -> upper to LE -> lower back to TE (drop duplicate LE point)
    pts = list(reversed(upper)) + lower[1:]
    return pts


# --------------------------------------------------------------------------- #
# Section placement
# --------------------------------------------------------------------------- #
def section_wire(r, chord, twist_deg, m, p, t, le_offset=0.25):
    """Build a FreeCAD wire for one airfoil section at radius r (mm).

    The 2D airfoil (chordwise s, normal h) is placed so the chord lies in the
    rotor plane before twist, then rotated by `twist_deg` about the radial
    (here +X) axis so positive twist pitches the trailing edge downward and the
    section pushes air toward +Z.  le_offset positions the pitch axis along the
    chord (0=LE, 0.25=quarter-chord).
    """
    beta = math.radians(twist_deg)
    cb, sb = math.cos(beta), math.sin(beta)
    af = naca4(m, p, t)
    verts = []
    for (xc, yc) in af:
        s = (xc - le_offset) * chord      # chordwise position (centred at pitch axis)
        h = yc * chord                    # section-normal position
        # twist about radial axis: maps (s,h) -> (Y,Z)
        y = s * cb - h * sb
        z = s * sb + h * cb
        verts.append(App.Vector(r, y, z))
    verts.append(verts[0])
    return Part.makePolygon(verts)


def blade_shape(params):
    """Loft the radial stack of sections into a single blade solid."""
    r_hub = params["hub_radius"]
    r_tip = params["tip_radius"]
    n_sec = params.get("n_sections", 12)
    root_embed = params.get("root_embed", 3.0)   # extend root inside hub (mm)

    radii = [r_hub - root_embed + (r_tip - (r_hub - root_embed)) * i / (n_sec - 1)
             for i in range(n_sec)]
    wires = []
    for r in radii:
        x = max((r - (r_hub - root_embed)) / (r_tip - (r_hub - root_embed)), 0.0)
        chord = _interp(params["chord"], x)
        twist = _interp(params["twist"], x)
        m = _interp(params["camber"], x)
        p = params.get("camber_pos", 0.4)
        t = _interp(params["thickness"], x)
        wires.append(section_wire(r, chord, twist, m, p, t,
                                   params.get("le_offset", 0.25)))
    loft = Part.makeLoft(wires, True, params.get("ruled", True))
    return loft


def _interp(table, x):
    """Linear interpolation over a list of [frac, value] control points (0..1)."""
    if isinstance(table, (int, float)):
        return float(table)
    pts = sorted(table, key=lambda kv: kv[0])
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for (x0, v0), (x1, v1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            f = (x - x0) / (x1 - x0)
            return v0 + f * (v1 - v0)
    return pts[-1][1]


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #
def build_propeller(params):
    blade = blade_shape(params)

    n_blades = params["n_blades"]
    blades = []
    for k in range(n_blades):
        ang = 360.0 * k / n_blades
        b = blade.copy()
        b.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), ang)
        blades.append(b)

    hub_r = params["hub_radius"]
    hub_h = params["hub_height"]
    hub = Part.makeCylinder(hub_r, hub_h, App.Vector(0, 0, -hub_h / 2.0),
                            App.Vector(0, 0, 1))

    # single multi-fuse is far faster than chaining pairwise .fuse() calls
    solid = hub.multiFuse(blades)
    solid = solid.removeSplitter()   # merge coplanar faces from the fusion
    return solid


def report(solid, params):
    bb = solid.BoundBox
    info = {
        "volume_mm3": round(solid.Volume, 1),
        "bbox_dx_mm": round(bb.XLength, 2),
        "bbox_dy_mm": round(bb.YLength, 2),
        "bbox_dz_mm": round(bb.ZLength, 2),
        "diameter_mm": round(2 * max(abs(bb.XMin), bb.XMax,
                                     abs(bb.YMin), bb.YMax), 2),
        "axial_extent_mm": round(bb.ZLength, 2),
        "n_blades": params["n_blades"],
        "watertight_solid": bool(solid.isValid() and solid.Solids),
    }
    return info


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv):
    if not argv:
        print("usage: propeller_gen.py <config.json>")
        return 1
    cfg_path = argv[0]
    with open(cfg_path) as f:
        params = json.load(f)

    name = params["name"]
    out_dir = os.path.join(os.path.dirname(os.path.abspath(cfg_path)),
                           "..", "geometry", name)
    out_dir = os.path.normpath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    solid = build_propeller(params)

    step = os.path.join(out_dir, name + ".step")
    stl = os.path.join(out_dir, name + ".stl")
    solid.exportStep(step)
    solid.exportStl(stl)  # default linear/angular deflection; refine below

    # finer STL tessellation for CFD surface meshing
    mesh = solid.tessellate(0.1)  # 0.1 mm chordal deflection
    import Mesh
    m = Mesh.Mesh()
    for facet in mesh[1]:
        v = mesh[0]
        m.addFacet(v[facet[0]].x, v[facet[0]].y, v[facet[0]].z,
                   v[facet[1]].x, v[facet[1]].y, v[facet[1]].z,
                   v[facet[2]].x, v[facet[2]].y, v[facet[2]].z)
    m.write(stl)

    info = report(solid, params)
    with open(os.path.join(out_dir, name + "_info.json"), "w") as f:
        json.dump(info, f, indent=2)

    print("=== %s ===" % name)
    for k, v in info.items():
        print("  %-18s %s" % (k, v))
    print("  STEP ->", step)
    print("  STL  ->", stl)

    # hard-constraint check
    ok = info["diameter_mm"] <= 100.0 + 1e-6 and info["axial_extent_mm"] <= 60.0 + 1e-6
    print("  CONSTRAINT (D<=100, H<=60):", "OK" if ok else "VIOLATED")
    return 0 if ok else 2


# Launched via snap `freecad.cmd -c "exec(...)"`, so prefer the env var the
# wrapper sets; fall back to any .json found on argv / after a "--".
if __name__ == "__main__" or True:
    _argv = sys.argv
    if "--" in _argv:
        _argv = _argv[_argv.index("--") + 1:]
    else:
        _argv = [a for a in _argv[1:] if a.endswith(".json")]
    if not _argv and os.environ.get("PROP_CONFIG"):
        _argv = [os.environ["PROP_CONFIG"]]
    sys.exit(main(_argv))
