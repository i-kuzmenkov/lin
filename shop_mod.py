import json, os, tkinter as tk
from tkinter import messagebox

SHOP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shop.json")
SKINS = {
    "classic": {"name": "Классика", "price": 0, "fill": "#ffeaa7", "out": "#fdcb6e", "eye": "#2d3436"},
    "neon": {"name": "Киборг", "price": 30, "fill": "#00ffcc", "out": "#0984e3", "eye": "#12121a"},
    "fire": {"name": "Демон", "price": 60, "fill": "#ff4757", "out": "#ffa502", "eye": "#fff200"},
    "ghost": {"name": "Призрак", "price": 100, "fill": "#a55eea", "out": "#ffffff", "eye": "#ffffff"},
    "gold": {"name": "Золото", "price": 150, "fill": "#ffd32a", "out": "#ffffff", "eye": "#1e272e"},
}

def load_shop():
    if os.path.exists(SHOP_FILE):
        try: return json.load(open(SHOP_FILE, "r", encoding="utf-8"))
        except Exception: pass
    d = {"coins": 0, "unlocked": ["classic"], "selected": "classic"}
    save_shop(d)
    return d

def save_shop(d):
    json.dump(d, open(SHOP_FILE, "w", encoding="utf-8"), indent=2)

def open_shop_ui(app):
    app.clear_container()
    f = tk.Frame(app.main_container, bg="#161626")
    f.pack(fill=tk.BOTH, expand=True)
    tk.Label(f, text=f"МАГАЗИН КУБИКОВ  |  Монеты: {app.shop_data['coins']}", font=("Sans", 22, "bold"), bg="#161626", fg="#ffd32a").pack(pady=25)
    grid = tk.Frame(f, bg="#161626")
    grid.pack(pady=10)
    for sid, info in SKINS.items():
        card = tk.Frame(grid, bg="#2b2b40", padx=14, pady=12)
        card.pack(side=tk.LEFT, padx=8)
        cv = tk.Canvas(card, width=50, height=50, bg="#161626", highlightthickness=0)
        cv.pack()
        cv.create_rectangle(5, 5, 45, 45, fill=info["fill"], outline=info["out"], width=3)
        cv.create_rectangle(27, 15, 33, 21, fill=info["eye"], outline="")
        cv.create_rectangle(36, 15, 42, 21, fill=info["eye"], outline="")
        tk.Label(card, text=info["name"], font=("Sans", 11, "bold"), bg="#2b2b40", fg="white").pack(pady=6)
        if app.shop_data["selected"] == sid:
            tk.Label(card, text="ВЫБРАНО", font=("Sans", 9, "bold"), bg="#00b894", fg="#12121a", padx=8, pady=4).pack()
        elif sid in app.shop_data["unlocked"]:
            tk.Button(card, text="Выбрать", font=("Sans", 9, "bold"), bg="#0984e3", fg="white", relief=tk.FLAT, padx=10, pady=4, command=lambda x=sid: sel_skin(app, x)).pack()
        else:
            tk.Button(card, text=f"Купить ({info['price']})", font=("Sans", 9, "bold"), bg="#f39c12", fg="#12121a", relief=tk.FLAT, padx=8, pady=4, command=lambda x=sid: buy_skin(app, x)).pack()
    tk.Button(f, text="Назад в меню", font=("Sans", 11, "bold"), bg="#d63031", fg="white", relief=tk.FLAT, padx=18, pady=8, command=app.show_menu).pack(pady=25)

def sel_skin(app, sid):
    app.shop_data["selected"] = sid; save_shop(app.shop_data); open_shop_ui(app)

def buy_skin(app, sid):
    pr = SKINS[sid]["price"]
    if app.shop_data["coins"] >= pr:
        app.shop_data["coins"] -= pr; app.shop_data["unlocked"].append(sid); app.shop_data["selected"] = sid
        save_shop(app.shop_data); open_shop_ui(app)
    else:
        messagebox.showwarning("Мало монет", f"Нужно {pr} монет!")
