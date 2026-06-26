# -*- coding: utf-8 -*-
"""
Autodesk CFD 2027 automation scaffold for Case A / B / C (identical settings).

HOW TO RUN  (this CANNOT run from a normal Python interpreter):
  The Autodesk CFD API is SWIG bindings (CFD.Setup / CFD.Results) built for
  CFD's *embedded Python 3.13* and needs a live CFD session. Run this from
  **Autodesk CFD -> Script Editor (CFDScriptEditor)**, not from system Python.

WHAT IT DOES (per case, all settings identical except geometry + rotating-region
axial centre — see scripts/cfd_setup.md):
  createFrom(<case>_cfd.step) -> Air to the cylinder+box fluid volumes, solid to
  the propeller -> rotating Motion 100 rpm about +Z on the cylinder -> 0 Pa on the
  outer box faces -> mesh (fine on blades) -> steady solve (SST k-w, then laminar)
  -> WallResults force Z (= thrust) and torque Z on the propeller walls.

The method names below are taken from the real SWIG wrappers
(C:\\Program Files\\Autodesk\\CFD 2027\\Python\\CFD\\Setup.py / Results.py).
Lines marked  # CONFIRM  use an identifier/enum that must be checked live in the
Script Editor (e.g. `print(dir(scn))`, `help(...)`), because they can't be
verified outside the app. Do NOT assume they are correct as written.
"""
import os
import CFD.Setup as Setup
import CFD.Results as Results

REPO = r"c:\Users\mogi2\src\Fluid_Mechanics_Report"

# axial centre of each propeller (mm) -> rotating-region / torque axis point.
CASES = {
    "caseA": dict(zc_mm=0.0),
    "caseB": dict(zc_mm=0.0),
    "caseC": dict(zc_mm=29.0),
}

RPM = 100.0
TURB_SST = 1      # CONFIRM: turbulence enum for SST k-omega (scn.turbulence = ?)
TURB_LAMINAR = 0  # CONFIRM: turbulence enum for laminar
ITERATIONS = 500  # steady iterations; raise until |Fz| monitor is flat


def classify_parts(scn):
    """Return (prop, cylinder, box) parts by volume: smallest=prop, largest=box."""
    pl = Setup.PartList()
    scn.parts(pl)
    parts = [pl[i] for i in range(len(pl))]            # CONFIRM: list iteration
    parts.sort(key=lambda p: p.volume())
    prop, cyl, box = parts[0], parts[1], parts[2]
    print("  parts by volume: prop=%s cyl=%s box=%s"
          % (prop.name(), cyl.name(), box.name()))
    return prop, cyl, box


def run_case(case, zc_mm, turbulence):
    step = os.path.join(REPO, "geometry", case, case + "_cfd.step")
    print("=== %s <- %s ===" % (case, step))

    ds = Setup.DesignStudy.Create()
    ds.createFrom(step)                                # import geometry + void fill
    scn = ds.getActiveScenario()

    prop, cyl, box = classify_parts(scn)

    # --- materials -----------------------------------------------------------
    air = scn.getMaterial("Air")                       # CONFIRM: library name "Air"
    cyl.applyMaterial(air)
    box.applyMaterial(air)
    # propeller: leave as the default solid, or assign an Aluminum/solid material:
    # prop.applyMaterial(scn.getMaterial("Aluminum"))  # CONFIRM material name

    # --- rotating region (100 rpm about +Z through the prop centre) ----------
    # CONFIRM: how a rotating Motion is constructed in this version. Likely a
    # Material/Motion of a "rotating" type applied to the cylinder volume, e.g.
    #   mot = Setup.Material.Create(scn, <ROTATING_TYPE>, "rotor")  # CONFIRM type
    # then set the axis/centre/speed and apply to the cylinder:
    #   mot.setAxisOfRotation(0, 0, 1)
    #   mot.setCenterOfRotation(0.0, 0.0, zc_mm/1000.0)   # metres (CONFIRM units)
    #   mot.setSpeed(RPM, "rpm")                          # CONFIRM speed setter
    #   scn.applyMotion(mot)  (or cyl.applyMaterial(mot))
    # See Setup.Motion methods: setAxisOfRotation / setCenterOfRotation / ...

    # --- boundary condition: 0 Pa (gauge) on the outer box faces -------------
    # CONFIRM: build a pressure BC and the outer-face entity ids. Outer faces are
    # the 6 faces of the box part; select them, then:
    #   bc = ... pressure BC, value 0 Pa ...
    #   scn.applyBoundaryCondition(bc, outer_face_ids, <ENTITY_TYPE_SURFACE>)

    # --- mesh: automatic + fine on the blades (>=3 elements across ~1 mm) -----
    scn.automaticSize()
    # mesh enhancement / local refinement on the propeller surface here:
    #   me = scn.mesh().meshEnahancement(); ...            # CONFIRM controls
    scn.mesh()

    # --- steady solve --------------------------------------------------------
    scn.turbulence = turbulence                        # CONFIRM enum (see top)
    scn.iterations = ITERATIONS
    scn.run()
    scn.wait()

    # --- extract thrust (Fz) and torque (Mz) on the propeller walls ----------
    res = scn.results()
    wr = Results.WallResults(res)                       # CONFIRM constructor
    wr.deselectAll()
    wr.select(prop)                                     # CONFIRM: select prop walls
    wr.setTorqueAxisDirection(0, 0, 1)
    wr.setTorqueAxisPoint(0.0, 0.0, zc_mm / 1000.0)     # metres (CONFIRM units)
    wr.calculate()
    f = wr.force()                                      # force vector
    fz = f[2]                                           # CONFIRM indexing (Vector)
    mz = wr.torque()
    print("  RESULT %s: Fz=%g N  Mz=%g N*m" % (case, fz, mz))
    wr.writeToFile(os.path.join(REPO, "geometry", case, case + "_wall.txt"))
    ds.save()
    return fz, mz


def main():
    print("== SST k-omega ==")
    for case, p in CASES.items():
        run_case(case, p["zc_mm"], TURB_SST)
    print("== Laminar (low-Re sensitivity) ==")
    for case, p in CASES.items():
        run_case(case, p["zc_mm"], TURB_LAMINAR)


if __name__ == "__main__":
    main()
