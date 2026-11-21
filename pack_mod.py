import json, os, tkinter as tk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_FILE = os.path.join(BASE_DIR, "active_pack.json")

BUILTIN_PACKS = {
    "default": {
        "title": "Классический (Стандарт)",
        "desc": "Оригинальный стиль Cube Dash",
        "bg": "#161626",
    },
    "neon_glow": {
        "title": "Неон (Кибер-ночь)",
        "desc": "Яркие неоновые контуры, светящиеся шипы и кибер-кубик",
        "bg": "#0b0719",
    },
    "retro_8bit": {
        "title": "Ретро 8-Бит (Аркада)",
        "desc": "Кирпичные блоки, пиксельные шипы и аркадный кубик",
        "bg": "#1b1429",
    },
    "matrix_hacker": {
        "title": "Матрица (Кибер-код)",
        "desc": "Зелёные микросхемы, лазерные шипы и цифровой мир",
        "bg": "#051408",
    },
    "candy_land": {
        "title": "Сладкий мир (Карамель)",
        "desc": "Вафельные блоки с глазурью и леденцовые шипы",
        "bg": "#2e1226",
    },
}

def init_packs(app):
    app.active_pack = "default"
    if os.path.exists(CFG_FILE):
        try:
            pk = json.load(open(CFG_FILE, "r", encoding="utf-8")).get("pack", "default")
            if pk in BUILTIN_PACKS:
                app.active_pack = pk
        except Exception:
            pass
    app.pack_imgs = {}

def draw_pack_obj(app, sx, sy, obj):
    pk = getattr(app, "active_pack", "default")
    if pk == "default":
        return False
    c = app.canvas
    g = 40
    if pk == "neon_glow":
        if obj == "block":
            c.create_rectangle(sx, sy, sx+g, sy+g, fill="#120929", outline="#00f3ff", width=2)
            c.create_rectangle(sx+5, sy+5, sx+g-5, sy+g-5, outline="#ff00ff", width=1.5)
            c.create_line(sx+8, sy+8, sx+g-8, sy+g-8, fill="#00f3ff", width=1)
            c.create_line(sx+g-8, sy+8, sx+8, sy+g-8, fill="#00f3ff", width=1)
            return True
        elif obj == "spike":
            c.create_polygon(sx+g/2, sy+4, sx+g-3, sy+g, sx+3, sy+g, fill="#240029", outline="#ff00ff", width=2.5)
            c.create_polygon(sx+g/2, sy+12, sx+g-10, sy+g-3, sx+10, sy+g-3, fill="#ff007f", outline="")
            return True
        elif obj == "player":
            c.create_rectangle(sx, sy, sx+g, sy+g, fill="#0d0221", outline="#00f3ff", width=3)
            c.create_rectangle(sx+5, sy+5, sx+g-5, sy+g-5, outline="#ff00ff", width=1.5)
            c.create_rectangle(sx+18, sy+11, sx+35, sy+18, fill="#00f3ff", outline="")
            return True
    if obj == "block":
        if pk == "retro_8bit":
            c.create_rectangle(sx, sy, sx+g, sy+g, fill="#b33939", outline="#ff793f", width=2)
            c.create_line(sx, sy+20, sx+g, sy+20, fill="#2c2c54", width=2)
            c.create_line(sx+20, sy, sx+20, sy+20, fill="#2c2c54", width=2)
            c.create_line(sx+10, sy+20, sx+10, sy+g, fill="#2c2c54", width=2)
            return True
        elif pk == "matrix_hacker":
            c.create_rectangle(sx, sy, sx+g, sy+g, fill="#081c0c", outline="#00ff41", width=2)
            c.create_rectangle(sx+8, sy+8, sx+g-8, sy+g-8, outline="#008f11", width=1)
            c.create_text(sx+g/2, sy+g/2, text="01", fill="#00ff41", font=("Monospace", 10, "bold"))
            return True
        elif pk == "candy_land":
            c.create_rectangle(sx, sy, sx+g, sy+g, fill="#ffb8b8", outline="#ff4d4d", width=2)
            c.create_rectangle(sx+2, sy+2, sx+g-2, sy+12, fill="#ff6b81", outline="")
            return True
    elif obj == "spike":
        if pk == "retro_8bit":
            c.create_polygon(sx+g/2, sy+4, sx+g-3, sy+g, sx+3, sy+g, fill="#ff5252", outline="#ffda79", width=2)
            return True
        elif pk == "matrix_hacker":
            c.create_polygon(sx+g/2, sy+4, sx+g-3, sy+g, sx+3, sy+g, fill="#003b00", outline="#00ff41", width=2)
            return True
        elif pk == "candy_land":
            c.create_polygon(sx+g/2, sy+4, sx+g-3, sy+g, sx+3, sy+g, fill="#ff9ff3", outline="#ffffff", width=2)
            return True
    elif obj == "player":
        if pk == "retro_8bit":
            c.create_rectangle(sx, sy, sx+g, sy+g, fill="#ffda79", outline="#cc8e35", width=3)
            c.create_rectangle(sx+20, sy+10, sx+27, sy+17, fill="#2c2c54", outline="")
            c.create_rectangle(sx+30, sy+10, sx+37, sy+17, fill="#2c2c54", outline="")
            return True
        elif pk == "matrix_hacker":
            c.create_rectangle(sx, sy, sx+g, sy+g, fill="#000000", outline="#00ff41", width=3)
            c.create_rectangle(sx+18, sy+11, sx+38, sy+17, fill="#00ff41", outline="")
            return True
        elif pk == "candy_land":
            c.create_rectangle(sx, sy, sx+g, sy+g, fill="#ff6b81", outline="#ffffff", width=3)
            c.create_oval(sx+21, sy+10, sx+28, sy+17, fill="#ffffff", outline="")
            c.create_oval(sx+30, sy+10, sx+37, sy+17, fill="#ffffff", outline="")
            return True
    return False

def open_packs_ui(app):
    app.clear_container()
    f = tk.Frame(app.main_container, bg="#161626")
    f.pack(fill=tk.BOTH, expand=True)
    tk.Label(f, text="ВСТРОЕННЫЕ РЕСУРСПАКИ", font=("Sans", 22, "bold"), bg="#161626", fg="#00ffcc").pack(pady=(25, 6))
    tk.Label(f, text="Выбери графический стиль игры — текстуры применяются мгновенно", font=("Sans", 10), bg="#161626", fg="#a0a0c0").pack(pady=(0, 15))

    lst = tk.Frame(f, bg="#161626")
    lst.pack(pady=8, fill=tk.X, padx=160)
    for pk, info in BUILTIN_PACKS.items():
        row = tk.Frame(lst, bg="#2b2b40", padx=14, pady=10)
        row.pack(fill=tk.X, pady=5)
        left = tk.Frame(row, bg="#2b2b40")
        left.pack(side=tk.LEFT)
        tk.Label(left, text=info["title"], font=("Sans", 12, "bold"), bg="#2b2b40", fg="white", anchor="w").pack(anchor="w")
        tk.Label(left, text=info["desc"], font=("Sans", 9), bg="#2b2b40", fg="#b2bec3", anchor="w").pack(anchor="w")
        if pk == app.active_pack:
            tk.Label(row, text="ВКЛЮЧЕНО", font=("Sans", 9, "bold"), bg="#00b894", fg="#12121a", padx=12, pady=5).pack(side=tk.RIGHT)
        else:
            tk.Button(row, text="Выбрать", font=("Sans", 9, "bold"), bg="#0984e3", fg="white", relief=tk.FLAT, padx=14, pady=5, command=lambda x=pk: select_pack(app, x)).pack(side=tk.RIGHT)

    tk.Button(f, text="Назад в меню", font=("Sans", 11, "bold"), bg="#d63031", fg="white", relief=tk.FLAT, padx=18, pady=8, command=app.show_menu).pack(pady=22)

def select_pack(app, pk):
    app.active_pack = pk
    app.bg_color = BUILTIN_PACKS[pk]["bg"]
    json.dump({"pack": pk}, open(CFG_FILE, "w", encoding="utf-8"))
    open_packs_ui(app)
