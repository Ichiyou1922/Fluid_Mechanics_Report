#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Case C geometry generator -- Autodesk Inventor 2025 COM API (Windows).

CLAUDE-original "r^2-weighted volumetric cascade tower":
  - Lift (axial thrust Fz) is the ONLY objective; everything else ignored.
  - Thrust per unit area ~ r^2 (U = omega*r) -> blades only in the OUTER annulus.
  - r^2 weighting has no z-term -> axial height is "free real estate" -> stack
    many decks over the full allowed height.
  - Strong camber + near-stall stagger for high C_L at low Re (~500).

Structure: K decks stacked along +Z, each a circular cascade of M strongly
cambered, inverse-tapered (tip-loaded) blades spanning the annulus
[R_in, R_tip] radially. Thin central spindle for visual reference.

NOTE: this does NOT use the parametric template scripts/propeller_gen.py
(Case C must be designed from scratch).

Run (Inventor must be installable/sign-in done once):
    python scripts/caseC_inventor.py
Requires: pywin32 (`pip install pywin32`).

Inventor internal length unit is centimetres; design is in millimetres and
scaled by MM = 0.1 cm/mm.
"""
import os
import json
import math
import sys

import win32com.client
from win32com.client import gencache, constants

# ----------------------------------------------------------------------------
# Design parameters (millimetres / degrees)
# ----------------------------------------------------------------------------
P = dict(
    n_blades=14,        # M: blades per deck
    n_decks=7,          # K: stacked decks along Z
    R_in=4.0,           # blade root radius (embeds into spindle for fusion)
    R_tip=49.0,         # tip radius -> D = 98 mm <= 100
    chord_root=1.2,     # thin root chord -> no root overlap; slender lifting arm
    chord_tip=16.0,     # large tip chord (tip-loaded; area concentrated outboard)
    stagger_deg=20.0,   # blade pitch from rotor plane (near-stall at low Re)
    camber=0.11,        # max camber as fraction of chord
    thickness=1.0,      # plate thickness (mm)
    deck_spacing=8.3,   # axial spacing between decks
    z_base=4.0,         # axial centre of the bottom deck
    spindle_r=6.0,      # central spindle radius (blade roots embed into it)
    height=58.0,        # spindle height (<= 60)
)

MM = 0.1  # cm per mm

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "geometry", "caseC")
ASSET_DIR = os.path.join(REPO, "assets")
STEP_ID = "{90AF7F40-0C01-11D5-8E83-0010B541CD80}"


def blade_profile(chord, zc, p):
    """Closed boundary points (u,v) in mm for one cambered, staggered plate.

    u -> tangential (global Y), v -> axial (global Z). Chord centred at u=0,
    parabolic camber, constant thickness, rotated by the stagger angle, then
    translated to axial centre zc.
    """
    m = p["camber"]
    t = p["thickness"]
    beta = math.radians(p["stagger_deg"])
    n = 16
    top, bot = [], []
    for i in range(n + 1):
        x = -chord / 2.0 + chord * i / n          # along chord, centred
        xc = 2.0 * x / chord                        # in [-1, 1]
        yc = m * chord * (1.0 - xc * xc)            # parabolic camber line
        top.append((x, yc + t / 2.0))
        bot.append((x, yc - t / 2.0))
    boundary = top + list(reversed(bot))            # LE->TE top, TE->LE bottom
    cb, sb = math.cos(beta), math.sin(beta)
    pts = []
    for (u, v) in boundary:
        ur = u * cb - v * sb
        vr = u * sb + v * cb
        pts.append((ur, vr + zc))
    return pts


def add_closed_polyline(sketch, tg, pts_mm):
    """Add a closed connected polyline through pts (mm) to a sketch."""
    p2 = [tg.CreatePoint2d(u * MM, v * MM) for (u, v) in pts_mm]
    lines = sketch.SketchLines
    first = lines.AddByTwoPoints(p2[0], p2[1])
    prev = first
    for k in range(2, len(p2)):
        prev = lines.AddByTwoPoints(prev.EndSketchPoint, p2[k])
    lines.AddByTwoPoints(prev.EndSketchPoint, first.StartSketchPoint)
    return sketch.Profiles.AddForSolid()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(ASSET_DIR, exist_ok=True)

    app = gencache.EnsureDispatch("Inventor.Application")
    app.Visible = True
    print("Inventor:", app.SoftwareVersion.DisplayName)
    tg = app.TransientGeometry

    # close any documents left open from previous runs
    while app.Documents.Count > 0:
        try:
            app.Documents.Item(1).Close(True)  # skip save
        except Exception:
            break

    doc = app.Documents.Add(
        constants.kPartDocumentObject,
        app.FileManager.GetTemplateFile(constants.kPartDocumentObject),
        True,
    )
    doc = win32com.client.CastTo(doc, "PartDocument")
    doc.UnitsOfMeasure.LengthUnits = constants.kMillimeterLengthUnits
    cd = doc.ComponentDefinition
    feats = cd.Features

    # origin geometry
    yz = next(cd.WorkPlanes.Item(i) for i in range(1, cd.WorkPlanes.Count + 1)
              if cd.WorkPlanes.Item(i).Name.upper().startswith("YZ"))
    xy = next(cd.WorkPlanes.Item(i) for i in range(1, cd.WorkPlanes.Count + 1)
              if cd.WorkPlanes.Item(i).Name.upper().startswith("XY"))
    zaxis = next(cd.WorkAxes.Item(i) for i in range(1, cd.WorkAxes.Count + 1)
                 if cd.WorkAxes.Item(i).Name.upper().startswith("Z"))

    # ---- seed blade: loft root section (x=R_in) -> tip section (x=R_tip) ----
    plane_root = cd.WorkPlanes.AddByPlaneAndOffset(yz, P["R_in"] * MM)
    plane_tip = cd.WorkPlanes.AddByPlaneAndOffset(yz, P["R_tip"] * MM)
    sk_root = cd.Sketches.Add(plane_root)
    sk_tip = cd.Sketches.Add(plane_tip)
    prof_root = add_closed_polyline(sk_root, tg, blade_profile(P["chord_root"], P["z_base"], P))
    prof_tip = add_closed_polyline(sk_tip, tg, blade_profile(P["chord_tip"], P["z_base"], P))

    sections = app.TransientObjects.CreateObjectCollection()
    sections.Add(prof_root)
    sections.Add(prof_tip)
    loft_def = feats.LoftFeatures.CreateLoftDefinition(sections, constants.kNewBodyOperation)
    blade = feats.LoftFeatures.Add(loft_def)
    print("seed blade created")

    # ---- circular pattern: M blades around Z ----
    col = app.TransientObjects.CreateObjectCollection()
    col.Add(blade)
    circ = feats.CircularPatternFeatures.Add(
        col, zaxis, True, P["n_blades"], "360 deg", True)
    print("circular pattern: %d blades -> bodies=%d"
          % (P["n_blades"], cd.SurfaceBodies.Count))

    # ---- rectangular pattern: K decks along Z ----
    col2 = app.TransientObjects.CreateObjectCollection()
    col2.Add(blade)
    col2.Add(circ)
    rect = feats.RectangularPatternFeatures.Add(
        col2, zaxis, True, P["n_decks"], "%g mm" % P["deck_spacing"])
    print("rectangular pattern: %d decks -> bodies=%d"
          % (P["n_decks"], cd.SurfaceBodies.Count))

    # ---- central spindle (full height) ----
    sk_sp = cd.Sketches.Add(xy)
    sk_sp.SketchCircles.AddByCenterRadius(tg.CreatePoint2d(0, 0), P["spindle_r"] * MM)
    prof_sp = sk_sp.Profiles.AddForSolid()
    edef = feats.ExtrudeFeatures.CreateExtrudeDefinition(prof_sp, constants.kNewBodyOperation)
    edef.SetDistanceExtent(P["height"] * MM, constants.kPositiveExtentDirection)
    spindle_feat = feats.ExtrudeFeatures.Add(edef)
    print("spindle created")

    # ---- fuse blades into the spindle (one connected solid) ----
    # Every blade root (r=R_in=3) embeds into the spindle (r=6), so the spindle
    # body intersects all blade lumps -> a single Join yields one solid.
    def maxabsx(b):
        rb = b.RangeBox
        return max(abs(rb.MinPoint.X), abs(rb.MaxPoint.X)) / MM

    bodies = [cd.SurfaceBodies.Item(i) for i in range(1, cd.SurfaceBodies.Count + 1)]
    spindle_body = min(bodies, key=lambda b: abs(maxabsx(b) - P["spindle_r"]))
    blade_body = max(bodies, key=maxabsx)
    tools = app.TransientObjects.CreateObjectCollection()
    tools.Add(blade_body)
    feats.CombineFeatures.Add(spindle_body, tools, constants.kJoinOperation, False)
    print("combined bodies -> %d body" % cd.SurfaceBodies.Count)

    # ---- overall bounding box from all solid bodies ----
    INF = float("inf")
    lo = [INF, INF, INF]
    hi = [-INF, -INF, -INF]
    nb = cd.SurfaceBodies.Count
    for i in range(1, nb + 1):
        rb = cd.SurfaceBodies.Item(i).RangeBox
        for ax, mn, mx in ((0, rb.MinPoint.X, rb.MaxPoint.X),
                            (1, rb.MinPoint.Y, rb.MaxPoint.Y),
                            (2, rb.MinPoint.Z, rb.MaxPoint.Z)):
            lo[ax] = min(lo[ax], mn / MM)
            hi[ax] = max(hi[ax], mx / MM)
    dx, dy, dz = (hi[k] - lo[k] for k in range(3))
    diameter = max(dx, dy)
    print("bodies: %d  bbox(mm): dx=%.2f dy=%.2f dz=%.2f  D=%.2f  z[%.2f,%.2f]"
          % (nb, dx, dy, dz, diameter, lo[2], hi[2]))

    ok_d = diameter <= 100.0 + 1e-6
    ok_h = dz <= 60.0 + 1e-6
    print("CONSTRAINTS: D<=100 %s (%.2f) | H<=60 %s (%.2f)"
          % ("OK" if ok_d else "FAIL", diameter, "OK" if ok_h else "FAIL", dz))

    # ---- exports ----
    ipt_path = os.path.join(OUT_DIR, "caseC.ipt")
    doc.SaveAs(ipt_path, False)
    print("saved IPT:", ipt_path)

    step_path = os.path.join(OUT_DIR, "caseC.step")
    export_step(app, doc, step_path)
    print("saved STEP:", step_path)

    info = dict(
        bbox_dx_mm=round(dx, 2), bbox_dy_mm=round(dy, 2), bbox_dz_mm=round(dz, 2),
        diameter_mm=round(diameter, 2), axial_extent_mm=round(dz, 2),
        n_blades=P["n_blades"], n_decks=P["n_decks"],
        n_bodies=nb, fits_D100=ok_d, fits_H60=ok_h, params=P,
    )
    with open(os.path.join(OUT_DIR, "caseC_info.json"), "w") as f:
        json.dump(info, f, indent=2)
    print("saved caseC_info.json")

    # ---- screenshots ----
    try:
        capture_views(app)
    except Exception as e:  # noqa
        print("screenshot warning:", e)

    print("DONE")


def export_step(app, doc, path):
    if os.path.exists(path):
        os.remove(path)
    step = app.ApplicationAddIns.ItemById(STEP_ID)
    step = win32com.client.CastTo(step, "TranslatorAddIn")
    ctx = app.TransientObjects.CreateTranslationContext()
    ctx.Type = constants.kFileBrowseIOMechanism
    opts = app.TransientObjects.CreateNameValueMap()
    medium = app.TransientObjects.CreateDataMedium()
    step.HasSaveCopyAsOptions(doc, ctx, opts)  # populate defaults (AP214)
    medium.FileName = path
    step.SaveCopyAs(doc, ctx, opts, medium)


def capture_views(app):
    """Save iso / top(down +Z axis) / side(elevation) bitmaps via explicit camera."""
    tg = app.TransientGeometry
    cam = app.ActiveView.Camera
    zc = P["height"] * MM / 2.0
    target = tg.CreatePoint(0, 0, zc)
    D = 30.0  # cm; Fit() rescales, only direction matters
    views = {
        # name: (eye, up)
        "top": (tg.CreatePoint(0, 0, zc + D), tg.CreateUnitVector(0, 1, 0)),
        "side": (tg.CreatePoint(D, 0, zc), tg.CreateUnitVector(0, 0, 1)),
        "iso": (tg.CreatePoint(D, -D, zc + D), tg.CreateUnitVector(0, 0, 1)),
    }
    for name, (eye, up) in views.items():
        cam.Target = target
        cam.Eye = eye
        cam.UpVector = up
        cam.Fit()
        cam.Apply()
        app.ActiveView.Update()
        out = os.path.join(ASSET_DIR, "caseC_%s.png" % name)
        app.ActiveView.SaveAsBitmap(out, 1400, 1050)
        print("screenshot:", out)


if __name__ == "__main__":
    main()
