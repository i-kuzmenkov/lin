import math

def parse_tilt(obj):
    if isinstance(obj, str) and obj.endswith(":inv"): obj = obj[:-4]
    if not isinstance(obj, str):
        return obj, 0
    s_part, _, _ = obj.partition("*")
    base, _, ang_s = s_part.partition("@")
    return base, int(ang_s) if ang_s.isdigit() else 0

def parse_scale(obj):
    if isinstance(obj, str) and obj.endswith(":inv"): obj = obj[:-4]
    if not isinstance(obj, str) or "*" not in obj:
        return 1.0
    _, _, sc_s = obj.rpartition("*")
    try:
        return float(sc_s)
    except Exception:
        return 1.0

def rot_pts(pts, cx, cy, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    res = []
    for x, y in pts:
        res.extend([cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c])
    return res

def draw_tilted(canvas, sx, sy, grid, base, ang, highlight=False, sc=1.0):
    g = grid * sc
    ox, oy = sx - (g - grid) / 2, sy - (g - grid) / 2
    cx, cy = sx + grid / 2, sy + grid / 2
    if base == "spike":
        pts = rot_pts([(ox + g / 2, oy + 4 * sc), (ox + g - 3 * sc, oy + g), (ox + 3 * sc, oy + g)], cx, cy, ang)
        canvas.create_polygon(pts, fill="#ff4757", outline="#00ffcc" if highlight else "white", width=1.5)
        return True
    pts = rot_pts([(ox, oy), (ox + g, oy), (ox + g, oy + g), (ox, oy + g)], cx, cy, ang)
    canvas.create_polygon(pts, fill="#1c2331" if base == "ghost_block" else "#2d3436", outline="#00ffcc" if highlight else "#74b9ff", width=2)
    return True
