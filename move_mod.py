from tkinter import simpledialog

MOVE_DIRS = {
    "move_up":    {"dx": 0,  "dy": -1, "label": "ДВ▲", "col": "#ff6b81"},
    "move_down":  {"dx": 0,  "dy": 1,  "label": "ДВ▼", "col": "#1e90ff"},
    "move_left":  {"dx": -1, "dy": 0,  "label": "ДВ◄", "col": "#ffa502"},
    "move_right": {"dx": 1,  "dy": 0,  "label": "ДВ►", "col": "#2ed573"},
}

def parse_move(obj):
    if not isinstance(obj, str):
        return None, 3
    base, sep, dist = obj.partition(":")
    if base in MOVE_DIRS:
        return base, int(dist) if sep and dist.isdigit() else 3
    return None, 3

def ask_distance(app, tool):
    app.mouse_down = False
    val = simpledialog.askinteger(
        "Настройка триггера",
        "На сколько блоков двигать привязанный объект?",
        initialvalue=3, minvalue=1, maxvalue=40, parent=app.root
    )
    return f"{tool}:{val if val else 3}"

def init_move(app):
    app.active_moves = []
    app.triggered_moves = set()
    app.move_links = {}
    app.link_source = None

def reset_moves(app):
    app.active_moves.clear()
    app.triggered_moves.clear()
    if hasattr(app, "_backup_links"):
        app.move_links = {k: list(v) for k, v in app._backup_links.items()}

def handle_link_click(app, gx, gy):
    base, _ = parse_move(app.level.get((gx, gy)))
    if base:
        app.link_source = (gx, gy)
    elif app.link_source and (gx, gy) in app.level:
        links = app.move_links.setdefault(app.link_source, [])
        if (gx, gy) in links:
            links.remove((gx, gy))
        else:
            links.append((gx, gy))

def draw_links(app, cx, cy, grid):
    if app.screen_state != "edit":
        return
    if app.link_source and app.link_source in app.level:
        sx, sy = app.link_source[0] * grid - cx, app.link_source[1] * grid - cy
        app.canvas.create_rectangle(sx - 3, sy - 3, sx + grid + 3, sy + grid + 3, outline="#00ffcc", width=2)
    for src, targets in list(app.move_links.items()):
        if src not in app.level:
            continue
        x1, y1 = src[0] * grid + grid / 2 - cx, src[1] * grid + grid / 2 - cy
        for tgt in targets:
            if tgt in app.level:
                x2, y2 = tgt[0] * grid + grid / 2 - cx, tgt[1] * grid + grid / 2 - cy
                app.canvas.create_line(x1, y1, x2, y2, fill="#00ffcc", dash=(3, 5), width=1.5)
                app.canvas.create_oval(x2-4, y2-4, x2+4, y2+4, fill="#00ffcc", outline="")

def check_triggers(app, grid):
    if not app.triggered_moves and not app.active_moves:
        app._backup_links = {k: list(v) for k, v in app.move_links.items()}
    px = app.player["x"]
    for (gx, gy), obj in list(app.level.items()):
        base, dist = parse_move(obj)
        if base and (gx, gy) not in app.triggered_moves:
            if abs(px - gx * grid) <= 10:
                app.triggered_moves.add((gx, gy))
                d = MOVE_DIRS[base]
                linked = app.move_links.get((gx, gy), [])
                targets = [t for t in linked if t in app.level]
                for (ox, oy) in targets:
                    app.active_moves.append({
                        "from": (ox, oy),
                        "to": (ox + d["dx"] * dist, oy + d["dy"] * dist),
                        "type": app.level[(ox, oy)],
                        "prog": 0.0
                    })

def update_moves(app):
    if not app.active_moves:
        return
    still = []
    for m in app.active_moves:
        if m["prog"] == 0.0:
            app.level.pop(m["from"], None)
        m["prog"] = min(1.0, m["prog"] + 0.05)
        if m["prog"] >= 1.0:
            app.level[m["to"]] = m["type"]
            move_link_coord(app, m["from"], m["to"])
        else:
            still.append(m)
    app.active_moves = still

def draw_moving(app, cx, cy, grid):
    for m in app.active_moves:
        fx, fy = m["from"]; tx, ty = m["to"]; p = m["prog"]
        app.draw_object((fx + (tx - fx) * p) * grid - cx, (fy + (ty - fy) * p) * grid - cy, m["type"])

def draw_trigger(canvas, sx, sy, h, grid, obj):
    base, dist = parse_move(obj)
    d = MOVE_DIRS[base]
    canvas.create_line(sx + grid/2, 0, sx + grid/2, h, fill=d["col"], dash=(4, 4), width=2)
    canvas.create_rectangle(sx + 4, sy + 4, sx + grid - 4, sy + grid - 4, fill="#12121a", outline=d["col"], width=3)
    canvas.create_text(sx + grid/2, sy + grid/2, text=f"{d['label']}{dist}", fill=d["col"], font=("Sans", 7, "bold"))

def move_link_coord(app, old_pos, new_pos):
    links = getattr(app, "move_links", {})
    if old_pos in links:
        links[new_pos] = links.pop(old_pos)
    for src, targets in links.items():
        links[src] = [new_pos if t == old_pos else t for t in targets]

def export_links(app, shift_y):
    res = {}
    for (sx, sy), targets in getattr(app, "move_links", {}).items():
        if (sx, sy) in app.level and targets:
            valid = [[tx, ty + shift_y] for (tx, ty) in targets if (tx, ty) in app.level]
            if valid:
                res[f"{sx},{sy + shift_y}"] = valid
    return res

def import_links(app, raw_links, shift_y):
    app.move_links = {}
    app.link_source = None
    if not isinstance(raw_links, dict):
        return
    for sk, targets in raw_links.items():
        try:
            sx, sy = map(int, sk.split(","))
            app.move_links[(sx, sy + shift_y)] = [(int(tx), int(ty) + shift_y) for tx, ty in targets]
        except Exception:
            pass
