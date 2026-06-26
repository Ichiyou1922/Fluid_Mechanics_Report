#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render iso / top(down +Z axis) / side(elevation) screenshots of a case STEP
in Autodesk Inventor, for visual consistency with Case C.

    python scripts/render_inventor.py caseA caseB

Writes assets/<case>_{iso,top,side}.png. Z is the rotation axis (all cases).
"""
import os
import sys
import win32com.client
from win32com.client import gencache, constants

MM = 0.1
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(REPO, "assets")


def body_bbox_center_z(doc):
    """Return axial centre (cm) of all solid bodies; fallback 0."""
    try:
        cd = doc.ComponentDefinition
        lo = hi = None
        for i in range(1, cd.SurfaceBodies.Count + 1):
            rb = cd.SurfaceBodies.Item(i).RangeBox
            zlo, zhi = rb.MinPoint.Z, rb.MaxPoint.Z
            lo = zlo if lo is None else min(lo, zlo)
            hi = zhi if hi is None else max(hi, zhi)
        if lo is not None:
            return (lo + hi) / 2.0
    except Exception:
        pass
    return 0.0


def capture(app, case, zc):
    tg = app.TransientGeometry
    cam = app.ActiveView.Camera
    target = tg.CreatePoint(0, 0, zc)
    D = 30.0
    views = {
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
        out = os.path.join(ASSET_DIR, "%s_%s.png" % (case, name))
        app.ActiveView.SaveAsBitmap(out, 1400, 1050)
        print("  screenshot:", out)


def main(cases):
    app = gencache.EnsureDispatch("Inventor.Application")
    app.Visible = True
    app.SilentOperation = True  # suppress STEP import dialogs
    for case in cases:
        step = os.path.join(REPO, "geometry", case, case + ".step")
        if not os.path.exists(step):
            print("MISSING:", step)
            continue
        print(case, "<-", step)
        doc = app.Documents.Open(step, True)
        zc = body_bbox_center_z(doc)
        capture(app, case, zc)
        doc.Close(True)
    app.SilentOperation = False
    print("DONE")


if __name__ == "__main__":
    main(sys.argv[1:] or ["caseA", "caseB"])
