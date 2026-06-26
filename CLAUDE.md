# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

Working pipeline in place. FreeCAD geometry generation + OpenFOAM-12 MRF CFD are implemented and run; Case A and Case B geometries, screenshots, and cases exist. Final CFD is done in Autodesk CFD (Windows). `README.md` (Japanese) remains the authoritative spec.

## Environment notes (important)

- **FreeCAD is the snap build.** There is no `freecadcmd`; run headless Python via `freecad.cmd -c "exec(open('script').read())"`. The snap prints harmless mount warnings to stderr. The generator reads its config from the `PROP_CONFIG` env var (see `scripts/run_freecad.sh`).
- **Snap-launched FreeCAD processes cannot be killed by this CLI** (`kill` → permission denied). If a run hangs, ask the user to kill it. The blade fusion uses `Part.multiFuse` (one shot) — chaining pairwise `.fuse()` was pathologically slow.
- **OpenFOAM 12 (Foundation)**, sourced in the shell (`WM_PROJECT_VERSION=12`). Solver is `foamRun` with `solver incompressibleFluid` (not `simpleFoam`). MRF is configured via `constant/MRFProperties` (cellZone). `surfaceTransformPoints` uses the OF12 syntax `surfaceTransformPoints "scale=(0.001 0.001 0.001)" in out` (NOT `-scale`).
- GPU is **not** used: OpenCASCADE booleans and standard OpenFOAM solvers are CPU-only. Parallelism is MPI domain decomposition (`decomposePar` + `mpirun -np N foamRun -parallel`). 22 cores available.

## Commands

```bash
# geometry (STEP/STL) + screenshots
scripts/run_freecad.sh scripts/propeller_gen.py scripts/caseA.json   # or PROP_CONFIG=... freecad.cmd -c ...
python3 scripts/render.py caseA                                      # assets/<case>_{iso,top,side}.png

# OpenFOAM case + mesh + solve + post
python3 scripts/gen_case.py caseA --rpm 100 --nprocs 8 --level 4     # writes cases/caseA
cd cases/caseA && ./Allrun                                           # scale->blockMesh->surfaceFeatures->snappy->topoSet->decompose->foamRun
python3 scripts/thrust.py cases/caseA                                # thrust |Fz|, torque Mz from forces.dat
```

Mesh refinement `--level` (snappy surface level) is the key knob: level 3 ≈ 1.25 mm (≈140k cells, fast, under-resolves the ~1 mm-thick blades), level 4 ≈ 0.47 mm (≈1.2 M cells, slow). Thrust is small (µN scale at 100 rpm) and mesh-sensitive; the **relative** A/B/C comparison is what matters, and Autodesk CFD is the final authority.

## Case structure

- **Case A** — conventional 3-blade, near-constant pitch. Parametric template `scripts/caseA.json`.
- **Case B** — CLAUDE-original lift maximiser: 8-blade, inverted-taper (tip-loaded) high-solidity rotor. Parametric template `scripts/caseB.json`.
- **Case C** — built on Windows with the **Autodesk Fusion API + Autodesk CFD API**, designed **from scratch WITHOUT the parametric template** in this repo. This is the unconstrained from-scratch original design; do not reuse `propeller_gen.py` for it.

## Goal

Design a drone propeller in FreeCAD that **maximizes lift, and nothing else**. Every other parameter (efficiency, torque, structural soundness, manufacturability, aesthetics, physical plausibility) is explicitly out of scope and must be ignored when it competes with lift.

## Hard constraints

- Propeller must fit inside a cylinder of diameter 10 cm × height 6 cm.
- Rotation speed is fixed at 100 rpm.
- Produce **at least two propeller cases** and compare them.
- One case must be an original CLAUDE-designed shape that ignores all prior art and references — only lift matters. Unnatural or humanly-incomprehensible geometry is acceptable for this case.

## Intended pipeline

1. **Geometry (FreeCAD Python API)** — build the 3D solid programmatically and export a STEP file. Do not model by hand in the GUI; the build must be reproducible from a script.
2. **CFD (OpenFOAM)** — generate mesh, `controlDict`, velocity and other dictionaries; run the simulation.
3. **Final solver (Autodesk CFD)** — OpenFOAM is the working solver, but results are ultimately reproduced in Autodesk CFD. Keep all settings portable to Autodesk CFD, and write the Autodesk CFD setup procedure as Markdown under `reports/`.

## Reporting requirement (`reports/`)

For **each** propeller case, write a Markdown report under `reports/` covering, in order:
1. Design concept — what the case is built to compare/highlight.
2. Calculation conditions — similarity parameters (e.g. Reynolds number), boundary conditions, mesh.
3. Discussion — computed lift and other results, flow-field visualization, comparison with references.
4. Summary.
5. References.

Note: `README.md` writes this directory as both `reports/` and `repots/` (typo); use `reports/`.
