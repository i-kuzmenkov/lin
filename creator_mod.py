import tkinter as tk
from tkinter import colorchooser

THEMES = [
    ("Классическая ночь", "#161626"),
    ("Пчелиный улей 🐝", "#2b210a"),
    ("Неоновый киберпанк", "#221033"),
    ("Вулканический ад", "#331015"),
]

def open_creator_dialog(app, grid, floor_y):
    app.clear_container()
    f = tk.Frame(app.main_container, bg="#161626")
    f.pack(fill=tk.BOTH, expand=True)

    tk.Label(f, text="НАСТРОЙКА НОВОГО УРОВНЯ", font=("Sans", 22, "bold"), bg="#161626", fg="#00ffcc").pack(pady=(30, 15))

    theme_var = tk.StringVar(value="#161626")
    tmpl_var = tk.StringVar(value="empty")
    mode_var = tk.StringVar(value="cube")

    box1 = tk.LabelFrame(f, text=" 1. Выбери тему (стартовый фон) ", font=("Sans", 11, "bold"), bg="#1e1e2e", fg="#ffd32a", padx=15, pady=10)
    box1.pack(pady=8)
    for name, col in THEMES:
        tk.Radiobutton(box1, text=name, variable=theme_var, value=col, font=("Sans", 10, "bold"), bg="#1e1e2e", fg="white", selectcolor="#12121a", activebackground="#1e1e2e").pack(side=tk.LEFT, padx=8)

    def pick_custom():
        c = colorchooser.askcolor(title="Выбери свой цвет фона", color=theme_var.get())
        if c and c[1]:
            theme_var.set(c[1])

    tk.Button(box1, text="Свой цвет...", font=("Sans", 9, "bold"), bg="#6c5ce7", fg="white", relief=tk.FLAT, padx=8, command=pick_custom).pack(side=tk.LEFT, padx=8)

    box2 = tk.LabelFrame(f, text=" 2. Выбери шаблон уровня ", font=("Sans", 11, "bold"), bg="#1e1e2e", fg="#00ffcc", padx=15, pady=10)
    box2.pack(pady=8)
    for t_name, t_val in [("Пустой уровень", "empty"), ("Полоса препятствий", "parkour"), ("Полёт пчёлки 🐝", "bee_fly")]:
        tk.Radiobutton(box2, text=t_name, variable=tmpl_var, value=t_val, font=("Sans", 10, "bold"), bg="#1e1e2e", fg="white", selectcolor="#12121a", activebackground="#1e1e2e").pack(side=tk.LEFT, padx=12)

    box3 = tk.LabelFrame(f, text=" 3. Кем начинаем игру? ", font=("Sans", 11, "bold"), bg="#1e1e2e", fg="#ff6b81", padx=15, pady=10)
    box3.pack(pady=8)
    for m_name, m_val in [("Кубик", "cube"), ("Пчёлка 🐝", "ship")]:
        tk.Radiobutton(box3, text=m_name, variable=mode_var, value=m_val, font=("Sans", 10, "bold"), bg="#1e1e2e", fg="white", selectcolor="#12121a", activebackground="#1e1e2e").pack(side=tk.LEFT, padx=16)

    def start_build():
        gy = (floor_y // grid) - 1
        app.current_level_name = "Новый уровень"
        app.default_bg = theme_var.get()
        app.bg_color = app.default_bg
        app.level = {(25, gy): "goal"}
        if theme_var.get() != "#161626":
            app.level[(2, gy - 2)] = f"bg:{theme_var.get()}"
        if mode_var.get() == "ship":
            app.level[(3, gy)] = "portal_ship"
        if tmpl_var.get() == "parkour":
            app.level.update({(7, gy): "pad_yellow", (11, gy - 2): "orb_yellow", (14, gy): "spike", (15, gy): "spike", (18, gy - 1): "coin"})
        elif tmpl_var.get() == "bee_fly":
            app.level[(3, gy)] = "portal_ship"
            for x in (9, 15, 21):
                app.level[(x, gy)] = "block"; app.level[(x, gy - 1)] = "block"; app.level[(x, gy - 5)] = "block"
        app.open_game_screen(start_mode="edit")

    btns = tk.Frame(f, bg="#161626")
    btns.pack(pady=22)
    tk.Button(btns, text="ОТКРЫТЬ РЕДАКТОР →", font=("Sans", 12, "bold"), bg="#00b894", fg="#12121a", relief=tk.FLAT, padx=20, pady=8, command=start_build).pack(side=tk.LEFT, padx=10)
    tk.Button(btns, text="Отмена", font=("Sans", 11, "bold"), bg="#d63031", fg="white", relief=tk.FLAT, padx=15, pady=8, command=app.show_menu).pack(side=tk.LEFT, padx=10)
