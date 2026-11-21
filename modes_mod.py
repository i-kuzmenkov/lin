EXTRA_PORTALS = {
    "portal_ball": {"mode": "ball", "label": "ШАР", "fill": "#4d1a00", "out": "#ff793f"},
    "portal_ufo":  {"mode": "ufo",  "label": "НЛО", "fill": "#3d1a4d", "out": "#cd84f1"},
    "portal_wave": {"mode": "wave", "label": "ВОЛНА", "fill": "#003d3d", "out": "#18dcff"},
}

def init_modes(app):
    app.attempt_num = 1
    app.goal_x = 1000.0

def calc_goal_x(app, grid):
    goals = [gx * grid for (gx, _), obj in app.level.items() if obj == "goal"]
    app.goal_x = float(max(goals)) if goals else 1000.0

def step_extra_physics(app, action_pressed, jump_just, speed, jump_force, gravity):
    m = app.player["mode"]
    g = app.player.get("grav", 1)
    if m == "ball":
        if jump_just and app.player["grounded"]:
            app.player["grav"] = -g
            app.player["grounded"] = False
            app.player["vy"] = 4.0 * app.player["grav"]
        app.player["vy"] += gravity * app.player.get("grav", 1)
        return True
    elif m == "ufo":
        if jump_just:
            app.player["vy"] = jump_force * 0.78 * g
            app.player["grounded"] = False
        app.player["vy"] += gravity * 0.85 * g
        return True
    elif m == "wave":
        spd = speed * app.player.get("speed_mult", 1.0) * getattr(app, "hard_mult", 1.0)
        app.player["vy"] = (-spd if action_pressed else spd) * g
        return True
    return False

def draw_extra_portal(canvas, sx, sy, grid, obj):
    info = EXTRA_PORTALS[obj]
    canvas.create_oval(sx + 6, sy + 2, sx + grid - 6, sy + grid - 2, fill=info["fill"], outline=info["out"], width=3)
    canvas.create_text(sx + grid / 2, sy + grid / 2, text=info["label"], fill=info["out"], font=("Sans", 7, "bold"))

def draw_extra_player(canvas, px, py, grid, mode, vy, tick):
    if mode == "ball":
        canvas.create_oval(px + 2, py + 2, px + grid - 2, py + grid - 2, fill="#ff793f", outline="white", width=2)
        ang = (tick % 12) * 30
        canvas.create_arc(px + 6, py + 6, px + grid - 6, py + grid - 6, start=ang, extent=120, fill="#2d3436", outline="")
        return True
    elif mode == "ufo":
        canvas.create_arc(px + 8, py + 4, px + grid - 8, py + 28, start=0, extent=180, fill="#7ed6df", outline="white", width=2)
        canvas.create_oval(px + 2, py + 16, px + grid - 2, py + 32, fill="#cd84f1", outline="white", width=2)
        return True
    elif mode == "wave":
        dy = -8 if vy < 0 else 8
        canvas.create_polygon(px + 4, py + 10, px + grid - 2, py + grid / 2 + dy, px + 4, py + grid - 10, fill="#18dcff", outline="white", width=2)
        return True
    return False

def draw_hud(app, w):
    if app.screen_state != "play":
        return
    goals = [gx * 40 for (gx, _), obj in app.level.items() if obj == "goal"]
    end_x = float(max(goals)) if goals else float(max([gx * 40 for (gx, _) in app.level] + [1000]))
    start_x = 80.0
    if getattr(app, "won", False):
        pct = 100
    else:
        pct = int(max(0, min(99, ((app.player["x"] - start_x) / max(40.0, end_x - start_x)) * 100)))
    bx1, bx2 = w // 2 - 120, w // 2 + 120
    app.canvas.create_rectangle(bx1, 12, bx2, 24, fill="#12121a", outline="#00ffcc", width=1.5)
    if pct > 0:
        app.canvas.create_rectangle(bx1 + 2, 14, bx1 + 2 + int((bx2 - bx1 - 4) * pct / 100), 22, fill="#00ffcc", outline="")
    app.canvas.create_text(bx2 + 10, 18, text=f"{pct}%", fill="#00ffcc", font=("Sans", 9, "bold"), anchor="w")
    app.canvas.create_text(w - 20, 22, text=f"Попытка #{getattr(app, 'attempt_num', 1)}", fill="white", font=("Sans", 10, "bold"), anchor="e")
