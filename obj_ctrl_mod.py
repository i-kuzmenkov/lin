import tkinter as tk
import tilt_mod

def close_panel(app):
    if getattr(app, "_ctrl_box", None):
        app._ctrl_box.destroy()
        app._ctrl_box = None

def open_obj_panel(app, gx, gy):
    if (gx, gy) not in app.level:
        return
    close_panel(app)
    app._sel_cell = (gx, gy)
    box = tk.Frame(app.main_container, bg="#12121a", bd=2, relief=tk.RIDGE)
    box.place(relx=0.5, y=46, anchor="n", width=500, height=175)
    app._ctrl_box = box

    tk.Label(box, text="УПРАВЛЕНИЕ ОБЪЕКТОМ (Поворот, Размер, Невидимость, Сдвиг)", font=("Sans", 9, "bold"), bg="#12121a", fg="#00ffcc").pack(pady=(5, 3))

    r1 = tk.Frame(box, bg="#12121a")
    r1.pack(pady=2)
    for deg, lbl in [(45, "+45°"), (90, "+90°"), (180, "+180°"), (360, "0°")]:
        tk.Button(r1, text=lbl, font=("Sans", 8, "bold"), bg="#6c5ce7", fg="white", relief=tk.FLAT, padx=8, pady=2, command=lambda d=deg: update_obj(app, deg=d)).pack(side=tk.LEFT, padx=3)

    r_sc = tk.Frame(box, bg="#12121a")
    r_sc.pack(pady=2)
    for sc, lbl in [(0.5, "0.5x"), (1.0, "1x"), (1.5, "1.5x"), (2.0, "2x")]:
        tk.Button(r_sc, text=lbl, font=("Sans", 8, "bold"), bg="#e17055", fg="white", relief=tk.FLAT, padx=7, pady=2, command=lambda s=sc: update_obj(app, sc=s)).pack(side=tk.LEFT, padx=3)
    tk.Button(r_sc, text="Невидимый (Вкл/Выкл)", font=("Sans", 8, "bold"), bg="#00b894", fg="#12121a", relief=tk.FLAT, padx=8, pady=2, command=lambda: toggle_inv(app)).pack(side=tk.LEFT, padx=6)

    r2 = tk.Frame(box, bg="#12121a")
    r2.pack(pady=3)
    for dx, dy, lbl in [(0, -1, "▲"), (0, 1, "▼"), (-1, 0, "◄"), (1, 0, "►")]:
        tk.Button(r2, text=lbl, font=("Sans", 8, "bold"), bg="#0984e3", fg="white", relief=tk.FLAT, padx=9, pady=2, command=lambda x=dx, y=dy: move_sel(app, x, y)).pack(side=tk.LEFT, padx=3)
    tk.Button(r2, text="Закрыть", font=("Sans", 8, "bold"), bg="#d63031", fg="white", relief=tk.FLAT, padx=8, pady=2, command=lambda: close_panel(app)).pack(side=tk.LEFT, padx=6)

def toggle_inv(app):
    cell = getattr(app, "_sel_cell", None)
    if cell and cell in app.level:
        v = str(app.level[cell])
        app.level[cell] = v[:-4] if v.endswith(":inv") else f"{v}:inv"

def update_obj(app, deg=None, sc=None):
    cell = getattr(app, "_sel_cell", None)
    if not cell or cell not in app.level:
        return
    raw = str(app.level[cell])
    inv = raw.endswith(":inv")
    clean = raw[:-4] if inv else raw
    base, ang = tilt_mod.parse_tilt(clean)
    cur_sc = tilt_mod.parse_scale(clean)
    if deg is not None: ang = 0 if deg == 360 else (ang + deg) % 360
    if sc is not None: cur_sc = sc
    app.level[cell] = base + (f"@{ang}" if ang > 0 else "") + (f"*{cur_sc}" if cur_sc != 1.0 else "") + (":inv" if inv else "")

def move_sel(app, dx, dy):
    cell = getattr(app, "_sel_cell", None)
    if cell and cell in app.level:
        gx, gy = cell; nx, ny = gx + dx, gy + dy
        if app.is_valid_cell(nx, ny) and (nx, ny) not in app.level:
            app.level[(nx, ny)] = app.level.pop((gx, gy)); app._sel_cell = (nx, ny)
