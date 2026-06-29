# -*- coding: utf-8 -*-
"""Post-process an Autodesk CFD motion CSV (the file with `Hydraulic ForceZ`).

Computes the thrust |Fz|, torque Mz and thrust coefficient C_T by averaging
over the final revolution, and draws a Hydraulic ForceZ-vs-time history.

    python scripts/cfd_post.py caseA results/caseA-motion.csv

- Force/torque are converted dyne -> N (x1e-5) and dyne-cm -> N*m (x1e-7).
- Averaging window = last 1 revolution (0.6 s at 100 rpm) of the record.
- Always writes results/<case>-fz-history.csv (Excel-plottable). If matplotlib
  is available, also writes assets/<case>_cfd_fz_history.png.
"""
import csv
import os
import sys

RHO = 1.225          # kg/m^3
N = 100.0 / 60.0     # rev/s (100 rpm)
REV = 0.6            # s per revolution
D = {"caseA": 0.096, "caseB": 0.0908, "caseC": 0.099}   # swept diameter [m]


def col(fieldnames, sub):
    for c in fieldnames:
        if sub.lower() in c.lower():
            return c
    raise KeyError(sub)


def load(path):
    t, fz, mz = [], [], []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        r = csv.DictReader(f)
        tc = col(r.fieldnames, "Time")
        fc = col(r.fieldnames, "Hydraulic ForceZ")
        mc = col(r.fieldnames, "Hydraulic TorqueZ")
        for row in r:
            try:
                t.append(float(row[tc]))
                fz.append(float(row[fc]))
                mz.append(float(row[mc]))
            except (TypeError, ValueError):
                pass
    return t, fz, mz


def main():
    if len(sys.argv) < 3:
        print("usage: python scripts/cfd_post.py <case> <motion.csv>")
        return
    case, path = sys.argv[1], sys.argv[2]
    d = D.get(case, 0.096)
    t, fz, mz = load(path)
    if not t:
        print("no data parsed from", path)
        return

    T = max(t)
    t0 = T - REV
    sel = [(ti, fzi, mzi) for ti, fzi, mzi in zip(t, fz, mz) if ti >= t0 - 1e-9]
    fz_avg = sum(x[1] for x in sel) / len(sel)
    mz_avg = sum(x[2] for x in sel) / len(sel)
    fz_n = abs(fz_avg) * 1e-5
    mz_nm = mz_avg * 1e-7
    rn2d4 = RHO * N * N * d ** 4
    ct = fz_n / rn2d4

    print("case=%s  D=%.4f m  rev-avg window=%.3f..%.3f s (%d pts of %d)"
          % (case, d, t0, T, len(sel), len(t)))
    print("  mean Hydraulic ForceZ  = %+9.4f dyne -> |Fz| = %.4e N = %.3f uN"
          % (fz_avg, fz_n, fz_n * 1e6))
    print("  mean Hydraulic TorqueZ = %+9.4f dyne-cm -> Mz = %.4e N*m"
          % (mz_avg, mz_nm))
    print("  rho*n^2*D^4 = %.4e N ;  C_T = %.4e" % (rn2d4, ct))
    print("  range of Fz over record: %.3f .. %.3f dyne (start..end %.3f -> %.3f)"
          % (min(fz), max(fz), fz[0], fz[-1]))

    hist = os.path.join("results", case + "-fz-history.csv")
    with open(hist, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Time_s", "HydraulicForceZ_dyne", "Fz_uN"])
        for ti, fzi in zip(t, fz):
            w.writerow(["%.4f" % ti, "%.6g" % fzi, "%.6g" % (fzi * 1e-5 * 1e6)])
    print("  wrote", hist)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  matplotlib not found -> PNG skipped; plot results/%s-fz-history.csv in Excel"
              % case)
        return

    fz_un = [x * 1e-5 * 1e6 for x in fz]
    plt.figure(figsize=(7.2, 4.0))
    plt.plot(t, fz_un, lw=1.0, color="#1f4fd8")
    plt.axvspan(t0, T, color="orange", alpha=0.15,
                label="averaging (last rev, %.1f-%.1f s)" % (t0, T))
    plt.axhline(fz_n * 1e6, color="red", ls="--", lw=1.0,
                label="mean |Fz| = %.2f uN" % (fz_n * 1e6))
    plt.xlabel("Time [s]")
    plt.ylabel(r"Thrust $F_z$ [$\mu$N]")
    plt.title("%s  Autodesk CFD (transient, laminar, compressible)" % case)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    out = os.path.join("assets", case + "_cfd_fz_history.png")
    plt.savefig(out, dpi=130)
    print("  wrote", out)


if __name__ == "__main__":
    main()
