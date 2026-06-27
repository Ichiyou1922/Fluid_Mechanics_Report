# -*- coding: utf-8 -*-
"""
Run THIS inside Autodesk CFD's Script Editor (not external Python).
It creates a study from caseA_cfd.step and prints the real API values needed
to finalize scripts/cfd_run.py (turbulence enum, Motion creation, material
names, part identification, WallResults usage). Paste the whole output back.

The external Python 3.13 can `import CFD.Setup` but `DesignStudy.Create()`
segfaults outside the app, so this must run in-app.
"""
import os

try:
    import CFD.Setup as Setup
    import CFD.Results as Results
except Exception:
    # fallback if the app exposes them unqualified
    import Setup           # type: ignore
    import Results         # type: ignore

REPO = r"c:\Users\mogi2\src\Fluid_Mechanics_Report"
STEP = os.path.join(REPO, "geometry", "caseA", "caseA_cfd.step")


def show(label, obj):
    pub = [m for m in dir(obj) if not m.startswith("_")]
    print("--- %s ---" % label)
    print(pub)


print("=== 0. module-level names (look for Motion factory / enums) ===")
print("Setup names:", [n for n in dir(Setup) if not n.startswith("_")])
print("Results names:", [n for n in dir(Results) if not n.startswith("_")])

print("\n=== 1. create study from", STEP, "===")
print("exists:", os.path.exists(STEP))
ds = Setup.DesignStudy.Create()
ds.createFrom(STEP)
scn = ds.getActiveScenario()
print("active scenario:", scn)
show("Scenario methods/props", scn)

print("\n=== 2. parts (name / id / volume) ===")
pl = Setup.PartList()
scn.parts(pl)
try:
    n = len(pl)
except Exception:
    n = pl.count() if hasattr(pl, "count") else 0
print("part count:", n)
for i in range(n):
    p = pl[i]
    try:
        print("  part[%d] name=%r id=%s volume=%s" % (i, p.name(), p.id(), p.volume()))
    except Exception as e:
        print("  part[%d] err:" % i, e)

print("\n=== 3. turbulence / iterations defaults ===")
for attr in ("turbulence", "turbulenceIntensity", "iterations", "innerIterations"):
    try:
        print("  scn.%s =" % attr, getattr(scn, attr))
    except Exception as e:
        print("  scn.%s err:" % attr, e)

print("\n=== 4. materials: try getMaterial('Air') and list helpers ===")
try:
    air = scn.getMaterial("Air")
    print("  getMaterial('Air') ->", air)
except Exception as e:
    print("  getMaterial('Air') err:", e)
print("  Material:", [m for m in dir(Setup.Material) if not m.startswith("_")])
print("  Motion:", [m for m in dir(Setup.Motion) if not m.startswith("_")])
print("  BoundaryCondition:", [m for m in dir(Setup.BoundaryCondition) if not m.startswith("_")])

print("\n=== 5. results / WallResults ===")
try:
    res = scn.results()
    print("  scn.results() ->", res)
    show("Results methods", res)
except Exception as e:
    print("  scn.results() err:", e)
print("  WallResults:", [m for m in dir(Results.WallResults) if not m.startswith("_")])

print("\n=== DONE: paste everything above back ===")
