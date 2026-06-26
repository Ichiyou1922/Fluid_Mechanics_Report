#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse an OpenFOAM forces.dat and report thrust (Fz) and torque (Mz).

Usage: python3 scripts/thrust.py cases/<case>
Reads cases/<case>/postProcessing/forces/0/forces.dat (latest line).
Force line format: time ((pres_x pres_y pres_z)(visc_x visc_y visc_z)) ((m..)(m..))
"""
import os
import re
import sys


def parse(path):
    nums = []
    with open(path) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            vals = [float(x) for x in re.findall(r"[-+0-9.eE]+", line)]
            nums.append(vals)
    return nums


def main(case_dir):
    fp = os.path.join(case_dir, "postProcessing", "forces", "0", "forces.dat")
    if not os.path.exists(fp):
        # find any forces.dat
        for root, _, files in os.walk(os.path.join(case_dir, "postProcessing")):
            if "forces.dat" in files:
                fp = os.path.join(root, "forces.dat")
                break
    rows = parse(fp)
    last = rows[-1]
    t = last[0]
    # layout: t, p(3), v(3), mp(3), mv(3)  -> 13 numbers
    px, py, pz = last[1], last[2], last[3]
    vx, vy, vz = last[4], last[5], last[6]
    mpx, mpy, mpz = last[7], last[8], last[9]
    mvx, mvy, mvz = last[10], last[11], last[12]
    Fz = pz + vz           # thrust (axial)
    Mz = mpz + mvz         # torque about axis
    # convergence: last 5 Fz
    hist = [(r[0], r[3] + r[6]) for r in rows[-5:]]

    print("case:", case_dir)
    print("  iterations run : %g" % t)
    print("  Fx,Fy,Fz [N]   : %.4e  %.4e  %.4e" % (px+vx, py+vy, Fz))
    print("  Thrust |Fz| [N]: %.4e   (mgf-equiv: %.3f g)" % (abs(Fz), abs(Fz)/9.81*1000))
    print("  Torque Mz [N.m]: %.4e" % Mz)
    print("  pressure/viscous Fz: %.4e / %.4e" % (pz, vz))
    print("  Fz convergence (last 5):")
    for tt, fz in hist:
        print("    t=%-7g Fz=%.4e" % (tt, fz))
    return abs(Fz), Mz


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
