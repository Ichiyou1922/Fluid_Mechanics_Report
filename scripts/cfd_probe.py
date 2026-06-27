# -*- coding: utf-8 -*-
"""
Run THIS inside Autodesk CFD's Script Editor.
Imports the caseA CFD domain via the ASM translator and prints the real API
values needed to finalize scripts/cfd_run.py. Paste the whole output back.
"""
import os
import traceback

try:
    import CFD.Setup as Setup
    import CFD.Results as Results
except Exception:
    import Setup           # type: ignore
    import Results         # type: ignore

G = r"c:\Users\mogi2\src\Fluid_Mechanics_Report\geometry\caseA"
STEP = os.path.join(G, "caseA_cfd.step")   # domain: prop + cylinder + box
print("file:", STEP, "exists:", os.path.exists(STEP))

print("\n=== 1. create study via ASM translator ===")
scn = None
ds = Setup.DesignStudy.Create()
try:
    # signature: createStudyFromAsmTranslator(fullName, studyName)
    ds.createStudyFromAsmTranslator(STEP, "caseA_probe")
    print("  createStudyFromAsmTranslator OK")
    try:
        print("  ASM error code:", ds.GetASMTranslateErrorCode())
    except Exception as e:
        print("  GetASMTranslateErrorCode err:", e)
    try:
        print("  study path:", ds.path())
    except Exception:
        pass
    scn = ds.getActiveScenario()
    print("  active scenario:", scn)
except Exception as e:
    print("  FAIL:", repr(e))
    traceback.print_exc()
    try:
        print("  ASM error code:", ds.GetASMTranslateErrorCode())
    except Exception:
        pass

if scn is not None:
    print("\n=== 2. scenario + parts ===")
    print("Scenario:", [m for m in dir(scn) if not m.startswith("_")])
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

    print("\n=== 4. materials / motion / bc factories ===")
    try:
        print("  getMaterial('Air') ->", scn.getMaterial("Air"))
    except Exception as e:
        print("  getMaterial('Air') err:", e)
    print("  Material:", [m for m in dir(Setup.Material) if not m.startswith("_")])
    print("  Motion:", [m for m in dir(Setup.Motion) if not m.startswith("_")])
    print("  BoundaryCondition:", [m for m in dir(Setup.BoundaryCondition) if not m.startswith("_")])

    print("\n=== 5. results / WallResults ===")
    try:
        res = scn.results()
        print("  scn.results() ->", res, [m for m in dir(res) if not m.startswith('_')])
    except Exception as e:
        print("  scn.results() err:", e)
    print("  WallResults:", [m for m in dir(Results.WallResults) if not m.startswith("_")])

print("\n=== DONE: paste everything above ===")
