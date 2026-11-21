import tkinter as tk

def init_practice(app):
    app.paused = False
    app.practice_mode = False
    app.checkpoints = []
    app.cp_timer = 0
    app.pause_overlay = None

def toggle_pause(app):
    if app.won:
        app.checkpoints.clear()
        app.show_menu()
        return
    if app.screen_state != "play":
        if app.screen_state == "edit":
            app.show_menu()
        return
    if app.paused:
        resume_game(app)
    else:
        app.paused = True
        show_pause_menu(app)

def resume_game(app):
    app.paused = False
    if app.pause_overlay:
        app.pause_overlay.destroy()
        app.pause_overlay = None

def toggle_practice(app):
    app.practice_mode = not app.practice_mode
    app.checkpoints.clear()
    app.cp_timer = 0
    resume_game(app)
    app.reset_player()

def show_pause_menu(app):
    if app.pause_overlay:
        app.pause_overlay.destroy()
    ov = tk.Frame(app.main_container, bg="#12121a", bd=3, relief=tk.RIDGE)
    ov.place(relx=0.5, rely=0.5, anchor="center", width=360, height=270)
    app.pause_overlay = ov
    tk.Label(ov, text="ПАУЗА", font=("Sans", 22, "bold"), bg="#12121a", fg="#00ffcc").pack(pady=(18, 12))
    tk.Button(ov, text="Продолжить (Esc)", font=("Sans", 11, "bold"), bg="#00b894", fg="#12121a", relief=tk.FLAT, width=24, pady=6, command=lambda: resume_game(app)).pack(pady=5)
    p_txt = "Практика: ВКЛ (Выключить)" if app.practice_mode else "Включить режим практики"
    p_col = "#2ed573" if app.practice_mode else "#f39c12"
    tk.Button(ov, text=p_txt, font=("Sans", 11, "bold"), bg=p_col, fg="#12121a", relief=tk.FLAT, width=24, pady=6, command=lambda: toggle_practice(app)).pack(pady=5)
    tk.Button(ov, text="В главное меню", font=("Sans", 11, "bold"), bg="#d63031", fg="white", relief=tk.FLAT, width=24, pady=6, command=lambda: (resume_game(app), app.show_menu())).pack(pady=5)

def save_checkpoint(app):
    if not app.practice_mode or app.player["dead"]:
        return
    p = app.player
    app.checkpoints.append({"x": p["x"], "y": p["y"], "vy": 0.0, "mode": p["mode"], "grav": p.get("grav", 1), "spd": p.get("speed_mult", 1.0), "bg": getattr(app, "bg_color", "#161626")})

def delete_checkpoint(app):
    if app.practice_mode and app.checkpoints:
        app.checkpoints.pop()

def respawn_checkpoint(app):
    cp = app.checkpoints[-1]
    app.player.update({"x": cp["x"], "y": cp["y"], "vy": 0.0, "grounded": False, "dead": False, "mode": cp["mode"], "grav": cp["grav"], "speed_mult": cp.get("spd", 1.0)})
    app.bg_color = cp["bg"]
    app.dead_timer = 0
    app.used_orbs.clear()

def update_checkpoints(app, dt):
    if not app.practice_mode or app.player["dead"] or app.won:
        return
    app.cp_timer += dt
    if app.cp_timer >= 400:
        app.cp_timer = 0
        save_checkpoint(app)

def draw_checkpoints(app, cx, cy):
    if not app.practice_mode:
        return
    for cp in app.checkpoints:
        sx, sy = cp["x"] - cx + 20, cp["y"] - cy + 20
        app.canvas.create_polygon(sx, sy-12, sx+10, sy, sx, sy+12, sx-10, sy, fill="#2ed573", outline="white", width=2)
    app.canvas.create_text(20, 46, text=f"ПРАКТИКА (Z - чекпоинт, X - удалить) | Точек: {len(app.checkpoints)}", fill="#2ed573", font=("Sans", 10, "bold"), anchor="w")
