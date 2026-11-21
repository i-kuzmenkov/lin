import random, tkinter as tk

def init_respect(app):
    app.respect_timer = 0
    app.spike_scale = 0
    app.hard_mult = 1.0
    app.angry_bees = []
    app.pe_mode = getattr(app, "pe_mode", True)
    app._resp_box = None

def reset_respect(app):
    app.respect_timer = 0
    app.spike_scale = 0
    app.hard_mult = 1.0
    app.angry_bees.clear()
    if getattr(app, "_resp_box", None):
        app._resp_box.destroy()
        app._resp_box = None

def spawn_bees(app, count=3):
    px, py = app.player["x"], app.player["y"]
    for i in range(count):
        app.angry_bees.append({
            "x": px - 140 - i * 35,
            "y": py + random.randint(-60, 60),
            "spd": 6.8 + random.uniform(0.1, 0.5)
        })

def _answer(app, yes):
    if getattr(app, "_resp_box", None):
        app._resp_box.destroy()
        app._resp_box = None
    app.paused = False
    app.mouse_down = False
    app.keys.clear()
    if yes:
        if hasattr(app, "shop_data"):
            app.shop_data["coins"] += 1
            try:
                import shop_mod
                shop_mod.save_shop(app.shop_data)
            except Exception:
                pass
    else:
        app.spike_scale = min(14, app.spike_scale + 4)
        app.hard_mult = round(app.hard_mult + 0.15, 2)
        spawn_bees(app, 3)

def update_respect(app, dt):
    if not getattr(app, "pe_mode", False) or app.screen_state != "play" or app.won or app.player["dead"] or getattr(app, "paused", False):
        return
    px, py = app.player["x"], app.player["y"]
    for b in app.angry_bees:
        b["x"] += b["spd"] * getattr(app, "hard_mult", 1.0)
        b["y"] += (py - b["y"]) * 0.06
        if abs(b["x"] - px) < 28 and abs(b["y"] - py) < 28:
            app.player["dead"] = True
            return
    app.respect_timer += dt
    if app.respect_timer >= 5000:
        app.respect_timer = 0
        app.paused = True
        app.mouse_down = False
        app.keys.clear()
        box = tk.Frame(app.main_container, bg="#12121a", bd=3, relief=tk.RIDGE)
        box.place(relx=0.5, rely=0.5, anchor="center", width=360, height=190)
        app._resp_box = box
        tk.Label(box, text="Уважаешь ли ты пчёл? 🐝", font=("Sans", 16, "bold"), bg="#12121a", fg="#ffd32a").pack(pady=(25, 20))
        row = tk.Frame(box, bg="#12121a")
        row.pack()
        tk.Button(row, text="ДА", font=("Sans", 12, "bold"), bg="#00b894", fg="#12121a", width=10, pady=5, command=lambda: _answer(app, True)).pack(side=tk.LEFT, padx=10)
        tk.Button(row, text="НЕТ", font=("Sans", 12, "bold"), bg="#ff4757", fg="white", width=10, pady=5, command=lambda: _answer(app, False)).pack(side=tk.LEFT, padx=10)

def draw_angry_bees(app, cx, cy, tick):
    if app.screen_state != "play":
        return
    for b in getattr(app, "angry_bees", []):
        bx, by = b["x"] - cx, b["y"] - cy
        wy = 2 if (tick // 3) % 2 == 0 else 7
        app.canvas.create_oval(bx+10, by+wy, bx+24, by+wy+12, fill="#ffcccc", outline="#ff4757")
        app.canvas.create_oval(bx+2, by+8, bx+34, by+30, fill="#ffa502", outline="#1e272e", width=2)
        app.canvas.create_line(bx+12, by+9, bx+12, by+29, fill="#1e272e", width=3)
        app.canvas.create_line(bx+20, by+9, bx+20, by+29, fill="#1e272e", width=3)
        app.canvas.create_oval(bx+25, by+13, bx+31, by+19, fill="#ff4757", outline="")
        app.canvas.create_polygon(bx+34, by+19, bx+42, by+16, bx+42, by+22, fill="#1e272e")
