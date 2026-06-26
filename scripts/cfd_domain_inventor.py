#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the CFD flow domain for each case in Autodesk Inventor and export a
single multi-body STEP ready for Autodesk CFD import.

Per case it produces 3 NESTED solid bodies (no boolean union):
  1. propeller   (imported from geometry/<case>/<case>.step)
  2. rotating cylinder  r=56 mm, axial = prop_centre +/- 35 mm  -> "Rotating Region"
  3. outer box   +/-180 mm (X,Y), Z = prop_centre +/- 300 mm    -> static fluid

Autodesk CFD treats the nesting as: propeller = solid, cylinder-minus-propeller
= rotating air, box-minus-cylinder = static air. Identical domain for A/B/C
except the axial position, which follows each propeller's centre (fair compare).

    python scripts/cfd_domain_inventor.py            # caseA caseB caseC
    python scripts/cfd_domain_inventor.py caseC

Writes geometry/<case>/<case>_cfd.step. See scripts/cfd_setup.md.
"""
import os
import sys
import win32com.client
from win32com.client import gencache, constants

MM = 0.1
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP_ID = "{90AF7F40-0C01-11D5-8E83-0010B541CD80}"

CYL_R = 56.0       # rotating cylinder radius (mm), common to all cases
CYL_HALF = 35.0    # rotating cylinder half-height about prop centre
BOX_XY = 180.0     # outer box half-width in X,Y
BOX_HALFZ = 300.0  # outer box half-height about prop centre


def origin_plane(cd, prefix):
    for i in range(1, cd.WorkPlanes.Count + 1):
        if cd.WorkPlanes.Item(i).Name.upper().startswith(prefix):
            return cd.WorkPlanes.Item(i)
    raise RuntimeError("no %s plane" % prefix)


def prop_center_z(cd):
    lo = min(cd.SurfaceBodies.Item(i).RangeBox.MinPoint.Z
             for i in range(1, cd.SurfaceBodies.Count + 1))
    hi = max(cd.SurfaceBodies.Item(i).RangeBox.MaxPoint.Z
             for i in range(1, cd.SurfaceBodies.Count + 1))
    return (lo + hi) / 2.0 / MM  # mm


def export_step(app, doc, path):
    if os.path.exists(path):
        os.remove(path)
    step = win32com.client.CastTo(app.ApplicationAddIns.ItemById(STEP_ID), "TranslatorAddIn")
    ctx = app.TransientObjects.CreateTranslationContext()
    ctx.Type = constants.kFileBrowseIOMechanism
    opts = app.TransientObjects.CreateNameValueMap()
    medium = app.TransientObjects.CreateDataMedium()
    step.HasSaveCopyAsOptions(doc, ctx, opts)
    medium.FileName = path
    step.SaveCopyAs(doc, ctx, opts, medium)


def build(app, case):
    tg = app.TransientGeometry
    step_in = os.path.join(REPO, "geometry", case, case + ".step")
    if not os.path.exists(step_in):
        print("MISSING:", step_in)
        return
    doc = win32com.client.CastTo(app.Documents.Open(step_in, False), "PartDocument")
    doc.UnitsOfMeasure.LengthUnits = constants.kMillimeterLengthUnits
    cd = doc.ComponentDefinition
    feats = cd.Features
    xy = origin_plane(cd, "XY")
    zc = prop_center_z(cd)
    nprop = cd.SurfaceBodies.Count
    print("%s: prop centre z=%.1f mm, prop bodies=%d" % (case, zc, nprop))

    # rotating cylinder (separate body, encloses propeller)
    pc = cd.WorkPlanes.AddByPlaneAndOffset(xy, (zc - CYL_HALF) * MM)
    sc = cd.Sketches.Add(pc)
    sc.SketchCircles.AddByCenterRadius(tg.CreatePoint2d(0, 0), CYL_R * MM)
    ec = feats.ExtrudeFeatures.CreateExtrudeDefinition(
        sc.Profiles.AddForSolid(), constants.kNewBodyOperation)
    ec.SetDistanceExtent(2 * CYL_HALF * MM, constants.kPositiveExtentDirection)
    feats.ExtrudeFeatures.Add(ec)

    # outer box (separate body, encloses cylinder)
    pb = cd.WorkPlanes.AddByPlaneAndOffset(xy, (zc - BOX_HALFZ) * MM)
    sb = cd.Sketches.Add(pb)
    sb.SketchLines.AddAsTwoPointRectangle(
        tg.CreatePoint2d(-BOX_XY * MM, -BOX_XY * MM),
        tg.CreatePoint2d(BOX_XY * MM, BOX_XY * MM))
    eb = feats.ExtrudeFeatures.CreateExtrudeDefinition(
        sb.Profiles.AddForSolid(), constants.kNewBodyOperation)
    eb.SetDistanceExtent(2 * BOX_HALFZ * MM, constants.kPositiveExtentDirection)
    feats.ExtrudeFeatures.Add(eb)

    nb = cd.SurfaceBodies.Count
    print("  bodies now=%d (prop + cylinder + box)" % nb)
    out = os.path.join(REPO, "geometry", case, case + "_cfd.step")
    export_step(app, doc, out)
    print("  saved:", out)
    doc.Close(True)


def main(cases):
    app = gencache.EnsureDispatch("Inventor.Application")
    app.Visible = True
    app.SilentOperation = True
    for case in cases:
        build(app, case)
    app.SilentOperation = False
    print("DONE")


if __name__ == "__main__":
    main(sys.argv[1:] or ["caseA", "caseB", "caseC"])
