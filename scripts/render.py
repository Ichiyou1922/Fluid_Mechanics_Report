#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render an STL propeller to PNG screenshots (no GUI, matplotlib only).

Usage:  python3 scripts/render.py <case>          # geometry/<case>/<case>.stl
Outputs: assets/<case>_iso.png, _top.png, _side.png
"""
import os
import struct
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_stl(path):
    """Return (Ntri,3,3) float array of triangle vertices; handles bin & ascii."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:5].lower() == b"solid" and b"facet" in data[:512].lower():
        # ASCII
        verts = []
        for line in data.decode("ascii", "ignore").splitlines():
            s = line.strip().split()
            if len(s) == 4 and s[0] == "vertex":
                verts.append([float(s[1]), float(s[2]), float(s[3])])
        v = np.array(verts).reshape(-1, 3, 3)
        return v
    # binary
    n = struct.unpack("<I", data[80:84])[0]
    tris = np.zeros((n, 3, 3))
    off = 84
    for i in range(n):
        vals = struct.unpack("<12f", data[off:off + 48])
        tris[i] = np.array(vals[3:12]).reshape(3, 3)
        off += 50
    return tris


def shade(tris, light=(0.3, 0.4, 0.85), base=(0.30, 0.55, 0.85)):
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0] = 1
    n = n / ln
    L = np.array(light) / np.linalg.norm(light)
    inten = np.clip(np.abs(n @ L), 0.25, 1.0)
    base = np.array(base)
    return inten[:, None] * base[None, :]


def set_equal(ax, tris):
    pts = tris.reshape(-1, 3)
    mins, maxs = pts.min(0), pts.max(0)
    c = (mins + maxs) / 2
    r = (maxs - mins).max() / 2 * 1.05
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    try:
        ax.set_box_aspect((1, 1, 1))
    except Exception:
        pass


def render(tris, view, out, title):
    colors = shade(tris)
    fig = plt.figure(figsize=(6, 6), dpi=130)
    ax = fig.add_subplot(111, projection="3d")
    coll = Poly3DCollection(tris, facecolors=colors, edgecolors="none")
    ax.add_collection3d(coll)
    set_equal(ax, tris)
    ax.view_init(elev=view[0], azim=view[1])
    ax.set_axis_off()
    ax.set_title(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  wrote", out)


def main(case):
    stl = os.path.join(ROOT, "geometry", case, case + ".stl")
    tris = load_stl(stl)
    print("%s: %d triangles" % (case, len(tris)))
    adir = os.path.join(ROOT, "assets")
    os.makedirs(adir, exist_ok=True)
    render(tris, (28, -55), os.path.join(adir, case + "_iso.png"),
           "%s  (isometric)" % case)
    render(tris, (90, -90), os.path.join(adir, case + "_top.png"),
           "%s  (top / rotor plane)" % case)
    render(tris, (2, -90), os.path.join(adir, case + "_side.png"),
           "%s  (side)" % case)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: render.py <case>")
        sys.exit(1)
    main(sys.argv[1])
