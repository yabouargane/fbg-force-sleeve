"""Generate the 3D model, the STL files and the technical drawings of the v0/v2 sleeve.

CONCEPT ONLY. Not printed, not tested on an instrument. Every dimension is a default to
confirm against the real instrument and the real fiber (marked [TO CONFIRM] in the docs).

Requires: numpy, matplotlib, trimesh, manifold3d  (see hardware/requirements-hardware.txt)
Usage (from the repository root):
    python hardware/generate_sleeve.py
Outputs in hardware/: sleeve_v0.stl, test_assembly_v0.stl,
and in docs/: plan_technique_sleeve.png, assembly_3d.png
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

matplotlib.rcParams.update({"figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb", "text.color": "#0b0b0b"})
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from matplotlib.patches import Circle, PathPatch, Rectangle  # noqa: E402
from matplotlib.path import Path  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "docs")


@dataclass(frozen=True)
class Params:
    # All lengths in mm. Defaults are placeholders to confirm.
    shaft_d: float = 5.0  # instrument shaft diameter [TO CONFIRM]; 5 and 10 mm are the common manual sizes
    clearance: float = 0.2  # diametral clearance between shaft and sleeve
    wall: float = 2.0  # sleeve wall thickness
    length: float = 30.0  # sleeve length along the shaft
    slit_w: float = 1.0  # clip slit width
    fiber_d: float = 0.25  # coated fiber diameter [TO CONFIRM against the fiber bought]
    groove_w: float = 0.6  # groove width for strained fibers
    groove_d: float = 0.5  # groove depth from the sleeve bore
    ref_groove_w: float = 0.9  # open groove for the reference fiber in its loose capillary
    ref_groove_d: float = 0.8  # depth of that groove from the sleeve bore
    capillary_d: float = 0.6  # loose polyimide capillary around the reference fiber [TO CONFIRM]
    window_len: float = 4.0  # adhesive access window, length along the shaft
    window_w: float = 1.5  # adhesive access window, width
    window_dz: float = 7.0  # windows are centered at length/2 +/- window_dz
    sim_port_id: float = 5.5  # bushing that simulates the port in the bench test, between the tip load and the sleeve (not modelled) [TO DEFINE]
    tab_len: float = 4.0  # tab protrusion beyond the outer surface
    tab_t: float = 3.0  # tab thickness each side of the slit
    tab_z: float = 14.0  # tab length along z
    screw_hole_d: float = 2.2  # clearance hole for an M2 screw
    strained_deg: tuple = (60.0, 180.0, 300.0)  # angles measured from the slit direction (+x)
    ref_deg: float = 120.0
    shaft_len: float = 80.0
    fiber_extra: float = 15.0  # fiber length beyond each end of the sleeve
    sections: int = 96


def rz(angle_deg):
    return trimesh.transformations.rotation_matrix(np.deg2rad(angle_deg), [0, 0, 1])


def cyl(r, h, z0=0.0, sections=96):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=sections)
    m.apply_translation([0, 0, z0 + h / 2])
    return m


def box(ex, ey, ez, cx, cy, cz):
    m = trimesh.creation.box(extents=[ex, ey, ez])
    m.apply_translation([cx, cy, cz])
    return m


def diff(a, b_list):
    return trimesh.boolean.difference([a] + list(b_list), engine="manifold")


def union(parts):
    return trimesh.boolean.union(list(parts), engine="manifold")


def build_sleeve(p: Params) -> trimesh.Trimesh:
    R_in = (p.shaft_d + p.clearance) / 2
    R_out = R_in + p.wall
    L = p.length
    body = diff(cyl(R_out, L, sections=p.sections), [cyl(R_in, L + 2, -1, p.sections)])

    # clamp tabs on both sides of the slit, along +x
    zc = L / 2
    x0 = R_in + 0.6
    x1 = R_out + p.tab_len
    tabs = []
    for sign in (+1, -1):
        y_mid = sign * (p.slit_w / 2 + p.tab_t / 2)
        tabs.append(box(x1 - x0, p.tab_t, p.tab_z, (x0 + x1) / 2, y_mid, zc))
    body = union([body] + tabs)

    cuts = []
    # slit
    cuts.append(box(R_out + p.tab_len + 2, p.slit_w, L + 2, (R_out + p.tab_len + 2) / 2, 0, L / 2))
    # open grooves for strained fibers (fiber is bonded to the shaft through the groove)
    for a in p.strained_deg:
        g = box(p.groove_d + 0.2, p.groove_w, L + 2, 0, 0, L / 2)
        g.apply_translation([R_in - 0.2 + (p.groove_d + 0.2) / 2, 0, 0])
        g.apply_transform(rz(a))
        cuts.append(g)
    # open groove for the reference fiber: it lies in a loose capillary on the shaft, strain-free,
    # and stays in thermal contact with the shaft (thermal grease)
    rg = box(p.ref_groove_d + 0.2, p.ref_groove_w, L + 2, 0, 0, L / 2)
    rg.apply_translation([R_in - 0.2 + (p.ref_groove_d + 0.2) / 2, 0, 0])
    rg.apply_transform(rz(p.ref_deg))
    cuts.append(rg)
    # adhesive access windows: radial slots through the wall above each strained groove
    x_start, x_end = R_in - 0.2, R_out + 0.5
    for a in p.strained_deg:
        for dz in (-p.window_dz, p.window_dz):
            w = box(x_end - x_start, p.window_w, p.window_len, (x_start + x_end) / 2, 0, L / 2 + dz)
            w.apply_transform(rz(a))
            cuts.append(w)
    # M2 clamp hole through both tabs, along y
    h = trimesh.creation.cylinder(radius=p.screw_hole_d / 2, height=2 * (p.slit_w / 2 + p.tab_t) + 2, sections=48)
    h.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    h.apply_translation([R_out + p.tab_len / 2 + 0.3, 0, zc])
    cuts.append(h)
    return diff(body, cuts)


def build_shaft(p: Params) -> trimesh.Trimesh:
    return cyl(p.shaft_d / 2, p.shaft_len, p.length / 2 - p.shaft_len / 2, p.sections)


def build_fibers(p: Params):
    R_in = (p.shaft_d + p.clearance) / 2
    Ls = p.length + 2 * p.fiber_extra
    z0 = -p.fiber_extra
    strained, ref = [], None
    for a in p.strained_deg:
        f = cyl(p.fiber_d / 2, Ls, z0, 24)
        f.apply_translation([p.shaft_d / 2 + p.fiber_d / 2, 0, 0])  # touching the shaft
        f.apply_transform(rz(a))
        strained.append(f)
    ref = cyl(p.fiber_d / 2, Ls, z0, 24)
    ref.apply_translation([p.shaft_d / 2 + p.capillary_d / 2, 0, 0])  # fiber in the capillary, on the shaft
    ref.apply_transform(rz(p.ref_deg))
    cap = cyl(p.capillary_d / 2, Ls, z0, 24)
    cap.apply_translation([p.shaft_d / 2 + p.capillary_d / 2, 0, 0])
    cap.apply_transform(rz(p.ref_deg))
    return strained, ref, cap


def checks(p, sleeve, shaft, strained, ref, cap):
    out = {}
    out["sleeve_watertight"] = bool(sleeve.is_watertight)
    out["sleeve_volume_mm3"] = round(float(sleeve.volume), 1)
    out["sleeve_bounds_mm"] = [[round(float(v), 2) for v in row] for row in sleeve.bounds]
    out["sleeve_bodies"] = int(len(sleeve.split(only_watertight=False)))
    # fibers must not overlap the sleeve or the shaft (except the strained fibers touching the shaft)
    overlaps = {}
    for i, f in enumerate(strained):
        inter = trimesh.boolean.intersection([f, sleeve], engine="manifold")
        overlaps[f"strained_{i + 1}_vs_sleeve_mm3"] = round(float(inter.volume), 6) if len(inter.vertices) else 0.0
    inter = trimesh.boolean.intersection([cap, sleeve], engine="manifold")
    overlaps["reference_capillary_vs_sleeve_mm3"] = round(float(inter.volume), 6) if len(inter.vertices) else 0.0
    inter = trimesh.boolean.intersection([sleeve, shaft], engine="manifold")
    overlaps["sleeve_vs_shaft_mm3"] = round(float(inter.volume), 6) if len(inter.vertices) else 0.0
    out["overlaps"] = overlaps
    R_in = (p.shaft_d + p.clearance) / 2
    out["min_wall_under_strained_grooves_mm"] = round(p.wall - p.groove_d, 3)
    out["min_wall_under_reference_groove_mm"] = round(p.wall - p.ref_groove_d, 3)
    out["adhesive_window_count"] = len(p.strained_deg) * 2
    out["bond_point_spacing_mm"] = round(2 * p.window_dz, 1)
    out["body_outer_diameter_mm"] = round(2 * (R_in + p.wall), 2)
    out["max_width_with_tabs_mm"] = round(float(sleeve.bounds[1][0] - sleeve.bounds[0][0]), 2)  # tabs make it wider than common 10-12 mm ports
    out["inner_diameter_mm"] = round(2 * R_in, 3)
    out["outer_diameter_mm"] = round(2 * (R_in + p.wall), 3)
    return out


# ------------------------- drawings -------------------------

def dim_h(ax, x0, x1, y, text, off=0.25, fs=8):
    ax.annotate("", xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle="<->", lw=0.8, color="k"))
    ax.text((x0 + x1) / 2, y + off, text, ha="center", va="bottom", fontsize=fs)


def dim_v(ax, x, y0, y1, text, off=0.3, fs=8):
    ax.annotate("", xy=(x, y0), xytext=(x, y1), arrowprops=dict(arrowstyle="<->", lw=0.8, color="k"))
    ax.text(x + off, (y0 + y1) / 2, text, ha="left", va="center", fontsize=fs, rotation=90)


def rings_at_z(mesh, z):
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    rings = [np.asarray(d)[:, :2] for d in sec.discrete]
    return rings


def signed_area(r):
    x, y = r[:, 0], r[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def draw_section(ax, mesh, z, title, p, label_angles=True):
    rings = rings_at_z(mesh, z)
    areas = [abs(signed_area(r)) for r in rings]
    outer = int(np.argmax(areas))
    verts, codes = [], []
    for i, r in enumerate(rings):
        want_ccw = i == outer
        r = r if (signed_area(r) > 0) == want_ccw else r[::-1]
        verts.extend(r.tolist() + [r[0].tolist()])
        codes.extend([Path.MOVETO] + [Path.LINETO] * (len(r) - 1) + [Path.CLOSEPOLY])
    ax.add_patch(PathPatch(Path(verts, codes), facecolor="#d9d9d9", edgecolor="k", lw=0.8))
    R_in = (p.shaft_d + p.clearance) / 2
    R_out = R_in + p.wall
    ax.add_patch(Circle((0, 0), p.shaft_d / 2, fill=False, ls="--", lw=0.6, ec="#555555"))  # shaft
    # fibers
    for a in p.strained_deg:
        c = (p.shaft_d / 2 + p.fiber_d / 2) * np.array([np.cos(np.deg2rad(a)), np.sin(np.deg2rad(a))])
        ax.add_patch(Circle(c, p.fiber_d / 2, fc="#2a78d6", ec="none"))
    c = (p.shaft_d / 2 + p.capillary_d / 2) * np.array([np.cos(np.deg2rad(p.ref_deg)), np.sin(np.deg2rad(p.ref_deg))])
    ax.add_patch(Circle(c, p.capillary_d / 2, fill=False, ec="#eb6834", lw=0.9))  # loose capillary
    ax.add_patch(Circle(c, p.fiber_d / 2, fc="#eb6834", ec="none"))  # reference fiber
    if label_angles:
        for a, lab in [(a, f"S{i + 1}") for i, a in enumerate(p.strained_deg)] + [(p.ref_deg, "R")]:
            r = R_out + 1.3
            ax.text(r * np.cos(np.deg2rad(a)), r * np.sin(np.deg2rad(a)), lab, ha="center", va="center", fontsize=8,
                    color="#2a78d6" if lab != "R" else "#eb6834", fontweight="bold")
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=9)
    ax.set_xlim(-R_out - 3, R_out + p.tab_len + 3)
    ax.set_ylim(-R_out - 3, R_out + 3)
    ax.axis("off")
    return R_in, R_out


def draw_plan(p, sleeve, path):
    R_in = (p.shaft_d + p.clearance) / 2
    R_out = R_in + p.wall
    L = p.length
    fig = plt.figure(figsize=(14, 9.5))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.1, 1.1, 1.1])

    # Section A-A
    ax = fig.add_subplot(gs[0, 0])
    zA = p.length / 2 - p.window_dz - 1.0  # inside the adhesive windows, before the tabs start
    draw_section(ax, sleeve, zA, f"Section A-A (z = {zA:.0f} mm, through the adhesive windows)", p)
    dim_h(ax, -R_in, R_in, -R_out - 1.6, f"Ø{2 * R_in:.1f} (bore)")
    dim_h(ax, -R_out, R_out, -R_out - 2.6, f"Ø{2 * R_out:.1f} (outer)")
    ax.text(0, R_out + 2.2, f"wall {p.wall:.1f}   slit {p.slit_w:.1f}", ha="center", fontsize=8)

    # Section B-B through the screw hole
    ax = fig.add_subplot(gs[0, 1])
    draw_section(ax, sleeve, L / 2, f"Section B-B (z = {L / 2:.0f} mm, through tabs and screw hole)", p, label_angles=False)
    tab_x1 = R_out + p.tab_len
    dim_h(ax, R_out, tab_x1, -R_out - 1.6, f"tab {p.tab_len:.0f}")
    dim_v(ax, tab_x1 + 0.8, p.slit_w / 2, p.slit_w / 2 + p.tab_t, f"{p.tab_t:.0f}", off=0.2)

    # Front view (looking along y)
    ax = fig.add_subplot(gs[0, 2])
    ax.add_patch(Rectangle((-R_out, 0), 2 * R_out, L, fc="#d9d9d9", ec="k", lw=0.8))
    ax.add_patch(Rectangle((R_out, L / 2 - p.tab_z / 2), p.tab_len, p.tab_z, fc="#bdbdbd", ec="k", lw=0.8))
    ax.add_patch(Circle((R_out + p.tab_len / 2 + 0.3, L / 2), p.screw_hole_d / 2, fc="white", ec="k", lw=0.8))
    ax.add_patch(Rectangle((-p.shaft_d / 2, -8), p.shaft_d, L + 16, fill=False, ls="--", lw=0.6, ec="#555555"))
    ax.set_aspect("equal")
    ax.set_title("Front view (looking along y), shaft dashed", fontsize=9)
    dim_v(ax, -R_out - 2.2, 0, L, f"{L:.0f}", off=-1.2)
    dim_h(ax, -R_out, R_out, L + 3.0, f"Ø{2 * R_out:.1f}")
    dim_v(ax, R_out + p.tab_len + 1.6, L / 2 - p.tab_z / 2, L / 2 + p.tab_z / 2, f"{p.tab_z:.0f}", off=0.2)
    ax.text(R_out + p.tab_len / 2, L / 2 - p.tab_z / 2 - 1.6, f"M2 hole Ø{p.screw_hole_d}", ha="center", fontsize=7)
    ax.set_xlim(-R_out - 5, R_out + p.tab_len + 5)
    ax.set_ylim(-10, L + 8)
    ax.axis("off")

    # 3D view of the sleeve
    ax = fig.add_subplot(gs[1, 0], projection="3d")
    shade_mesh(ax, sleeve, "#c8c8c8")
    set_equal3d(ax, sleeve)
    ax.view_init(elev=24, azim=-58)
    ax.set_title("Sleeve, 3D view", fontsize=9)
    ax.set_axis_off()

    # table of dimensions
    ax = fig.add_subplot(gs[1, 1:])
    ax.axis("off")
    rows = [
        ["Instrument shaft diameter", f"{p.shaft_d:.1f} mm", "[TO CONFIRM]"],
        ["Bore diameter (shaft + clearance)", f"{2 * R_in:.1f} mm", f"clearance {p.clearance:.1f} mm"],
        ["Outer diameter", f"{2 * R_out:.1f} mm", f"wall {p.wall:.1f} mm"],
        ["Length", f"{L:.0f} mm", ""],
        ["Slit width", f"{p.slit_w:.1f} mm", "clip opening"],
        ["Strained fibers S1-S3", f"at {', '.join(f'{a:.0f}' for a in p.strained_deg)}°", f"open groove {p.groove_w}×{p.groove_d} mm"],
        ["Reference fiber R", f"at {p.ref_deg:.0f}°", f"groove {p.ref_groove_w}×{p.ref_groove_d}; capillary Ø{p.capillary_d}; grease"],
        ["Adhesive windows", f"{len(p.strained_deg) * 2} slots {p.window_len:.0f}×{p.window_w} mm", f"z = {p.length / 2 - p.window_dz:.0f} and {p.length / 2 + p.window_dz:.0f}; bonds {2 * p.window_dz:.0f} mm apart"],
        ["Fiber (coated)", f"Ø{p.fiber_d} mm", "[TO CONFIRM]"],
        ["Port simulated by a bushing", f"inner Ø {p.sim_port_id:.1f} mm [TO DEFINE]", "between tip load and sleeve; sleeve stays outside"],
        ["Clamp tabs", f"{p.tab_len:.0f}×{p.tab_t:.0f}×{p.tab_z:.0f} mm", f"M2 hole Ø{p.screw_hole_d}"],
        ["Angles", "from the slit direction (+x)", "S1-S3 120° apart"],
    ]
    tb = ax.table(cellText=rows, colLabels=["Item", "Value", "Note"], loc="center", cellLoc="left", colWidths=[0.33, 0.27, 0.40])
    tb.auto_set_font_size(False)
    tb.set_fontsize(8.5)
    tb.scale(1, 1.35)
    ax.set_title("Dimensions, millimetres. CONCEPT: not printed, not tested.", fontsize=9)
    fig.suptitle("FBG force sleeve v0/v2: technical plan (concept)", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(path, dpi=160)
    plt.close(fig)


def shade_mesh(ax, mesh, color, alpha=1.0):
    tri = mesh.triangles
    normals = mesh.face_normals
    light = np.array([0.4, -0.5, 0.8])
    light = light / np.linalg.norm(light)
    shade = np.clip(normals @ light, 0, 1) * 0.6 + 0.4
    base = np.array(matplotlib.colors.to_rgb(color))
    cols = np.clip(shade[:, None] * base[None, :], 0, 1)
    pc = Poly3DCollection(tri, facecolors=np.c_[cols, np.full(len(cols), alpha)], edgecolors="none")
    ax.add_collection3d(pc)


def set_equal3d(ax, mesh, margin=1.0):
    """True proportions, with the box fitted to the mesh bounds."""
    mn, mx = mesh.bounds
    mn = mn - margin
    mx = mx + margin
    ax.set_xlim(mn[0], mx[0])
    ax.set_ylim(mn[1], mx[1])
    ax.set_zlim(mn[2], mx[2])
    ax.set_box_aspect(tuple(np.maximum(mx - mn, 1e-6)))


TITLES = {
    "en": ("Test assembly v0/v2: shaft, sleeve (transparent), fibers", "Close view. Blue: strained fibers S1-S3. Orange: reference fiber R in its loose capillary", "CONCEPT, not printed, not tested"),
    "fr": ("Assemblage d'essai : tige, manchon (transparent), fibres", "Vue rapprochée. Bleu : fibres collées S1 à S3. Orange : fibre de référence R dans son tube libre", "CONCEPT, non imprimé, non testé"),
}


def draw_assembly(p, sleeve, shaft, strained, ref, cap, path, lang="en"):
    t1, t2, t3 = TITLES[lang]
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    shade_mesh(ax, shaft, "#9aa5b1")
    shade_mesh(ax, sleeve, "#d9d9d9", alpha=0.55)
    for f in strained:
        shade_mesh(ax, f, "#2a78d6")
    shade_mesh(ax, cap, "#f2a98a", alpha=0.7)
    shade_mesh(ax, ref, "#eb6834")
    allm = trimesh.util.concatenate([shaft, sleeve])
    set_equal3d(ax, allm)
    ax.view_init(elev=18, azim=-62)
    ax.set_title(t1, fontsize=9)
    ax.set_axis_off()

    ax = fig.add_subplot(1, 2, 2, projection="3d")
    shade_mesh(ax, shaft, "#9aa5b1", alpha=0.25)
    shade_mesh(ax, sleeve, "#d9d9d9", alpha=0.35)
    for f in strained:
        shade_mesh(ax, f, "#2a78d6")
    shade_mesh(ax, cap, "#f2a98a", alpha=0.7)
    shade_mesh(ax, ref, "#eb6834")
    set_equal3d(ax, sleeve, margin=4.0)
    ax.view_init(elev=28, azim=-30)
    ax.set_title(t2, fontsize=9)
    ax.set_axis_off()
    fig.suptitle(t3, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    p = Params()
    sleeve = build_sleeve(p)
    shaft = build_shaft(p)
    strained, ref, cap = build_fibers(p)
    report = checks(p, sleeve, shaft, strained, ref, cap)
    report["parameters"] = asdict(p)

    sleeve.export(os.path.join(HERE, "sleeve_v0.stl"))
    assembly = trimesh.util.concatenate([sleeve, shaft] + strained + [cap, ref])
    assembly.export(os.path.join(HERE, "test_assembly_v0.stl"))
    with open(os.path.join(HERE, "sleeve_model_check.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    os.makedirs(DOCS, exist_ok=True)
    draw_plan(p, sleeve, os.path.join(DOCS, "plan_technique_sleeve.png"))
    draw_assembly(p, sleeve, shaft, strained, ref, cap, os.path.join(DOCS, "assembly_3d.png"))
    draw_assembly(p, sleeve, shaft, strained, ref, cap, os.path.join(DOCS, "assembly_3d_fr.png"), lang="fr")
    print(json.dumps({k: v for k, v in report.items() if k != "parameters"}, indent=2))


if __name__ == "__main__":
    main()
