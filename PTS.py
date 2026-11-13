import tkinter as tk, random, math, json, os

root = tk.Tk()
root.title("Симулятор Автобуса")
root.geometry("820x460+100+100")
root.bind("<F11>", lambda e: root.attributes("-fullscreen", not root.attributes("-fullscreen")))

BASE_W, BASE_H = 820, 380
canvas = tk.Canvas(root, width=BASE_W, height=BASE_H, bg="#6ab04c", highlightthickness=0, takefocus=True)
panel = tk.Frame(root, bg="#1e272e")
panel.pack(fill=tk.X, side=tk.BOTTOM)
panel.pack(fill=tk.X, side=tk.BOTTOM); canvas.pack(fill=tk.BOTH, expand=True)
label = tk.Label(panel, text=f"Скорость: 0 км/ч | Деньги: 100р | Пассажиры: 0", font=("Sans", 11, "bold"), bg="#1e272e", fg="white", pady=6)
label.pack(side=tk.LEFT, padx=10)

game_state = "menu"
bus_color = "#ff9f1a"
accel_bonus = 0.0
ticket_price = 35
cost_color, cost_engine, cost_ticket = 150, 250, 400

SAVE_FILE = "/home/iakov/gith/lin/save.json"

def load_progress():
    global money, bus_color, accel_bonus, ticket_price, cost_color, cost_engine, cost_ticket
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                money = data.get("money", 100)
                bus_color = data.get("bus_color", "#ff9f1a")
                accel_bonus = data.get("accel_bonus", 0.0)
                ticket_price = data.get("ticket_price", 35)
                cost_color = data.get("cost_color", 150)
                cost_engine = data.get("cost_engine", 250)
                cost_ticket = data.get("cost_ticket", 400)
        except Exception:
            pass

def save_progress():
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump({"money": money, "bus_color": bus_color, "accel_bonus": accel_bonus, "ticket_price": ticket_price, "cost_color": cost_color, "cost_engine": cost_engine, "cost_ticket": cost_ticket}, f)
    except Exception:
        pass

load_progress()

speed, dist, people, board_timer = 0.0, 0.0, 0, 0
doors, btn_gas, btn_brake = False, False, False
keys, alert_text, alert_timer, speed_fine_timer, stop_counter = set(), "", 0, 0, 2
dresses = ["#e84118", "#9c88ff", "#fbc531", "#00a8ff", "#4cd137"]
hairs = ["#2f3640", "#e1b12c", "#8c7ae6", "#c23616", "#574b90"]
car_colors = ["#e84118", "#0097e6", "#fbc531", "#8c7ae6", "#44bd32", "#f5f6fa"]
buildings = [{"x": i * 160, "w": random.randint(90, 130), "h": random.randint(65, 105), "c": random.choice(["#d1ccc0", "#aaa69d", "#84817a", "#ccae62", "#706fd3"])} for i in range(18)]
sidewalk_peds = [{"x": i * 300 + 150, "y": 148.0 if i % 2 == 0 else 338.0, "dir": 1 if i % 3 == 0 else -1, "v": random.uniform(0.8, 1.3), "d": dresses[i % 5], "h": hairs[i % 5], "step": 0.0, "cross": 0, "cd": 0} for i in range(14)]
trees = [{"x": i * 240 + 40} for i in range(15)]

def make_stop(x):
    return {"x": x, "plist": [{"x": x - 45 + i * 18, "y": 335, "d": dresses[i % 5], "h": hairs[i % 5], "go": False, "step": 0.0} for i in range(random.randint(3, 6))], "exited": False}

def make_crosswalk(x, has_light=False):
    peds = [{"dx": -12 + i * 14, "py": 335.0 if i % 2 == 0 else 145.0, "dir": -1 if i % 2 == 0 else 1, "v": random.uniform(0.9, 1.4), "step": 0.0, "d": random.choice(dresses), "h": random.choice(hairs), "hit": False} for i in range(random.randint(2, 3))]
    return {"x": x, "peds": peds, "py": 335.0, "dir": -1, "step": 0.0, "d": random.choice(dresses), "h": random.choice(hairs), "fined": False, "hit": False, "light": has_light, "timer": random.randint(0, 500)}

stops, crosswalks, cars, exiting_plist = [], [], [], []
def reset_game():
    global speed, dist, money, people, board_timer, doors, alert_text, alert_timer, speed_fine_timer, stop_counter, stops, crosswalks, cars
    speed, dist, money, people, board_timer, doors, alert_text, alert_timer, speed_fine_timer, stop_counter = 0.0, 0.0, 100, 0, 0, False, "", 0, 0, 2
    stops = [make_stop(1200), make_stop(4200)]
    crosswalks = [make_crosswalk(2050, False)]
    cars = [{"x": 650 + i * 480, "y": 248, "v": random.uniform(4.8, 7.8), "c": car_colors[i % 6], "dir": 1} for i in range(4)] + [{"x": 800 + i * 520, "y": 175, "v": random.uniform(-6.8, -4.5), "c": car_colors[(i + 2) % 6], "dir": -1} for i in range(4)]

reset_game()

menu_frame = tk.Frame(canvas, bg="#1e272e", bd=3, relief=tk.RIDGE, padx=30, pady=25)
tk.Label(menu_frame, text="СИМУЛЯТОР АВТОБУСА", font=("Sans", 20, "bold"), bg="#1e272e", fg="#fbc531").pack(pady=(0, 10))
tk.Label(menu_frame, text="W / Стрелка вверх — Газ | S / Стрелка вниз — Тормоз\nПробел — Двери | Esc — Пауза | F11 — На весь экран", font=("Sans", 10), bg="#1e272e", fg="#dcdde1").pack(pady=(0, 20))

pause_frame = tk.Frame(canvas, bg="#1e272e", bd=3, relief=tk.RIDGE, padx=30, pady=25)
tk.Label(pause_frame, text="ПАУЗА", font=("Sans", 20, "bold"), bg="#1e272e", fg="#00a8ff").pack(pady=(0, 15))

def start_game(restart=False):
    global game_state
    if restart:
        reset_game()
    game_state = "play"
    menu_frame.place_forget()
    pause_frame.place_forget()
    if "shop_frame" in globals(): shop_frame.place_forget()
    btn_top_pause.place(relx=0.985, rely=0.025, anchor=tk.NE)
    root.focus_force()
    canvas.focus_force()

def resume_game():
    global game_state
    game_state = "play"
    pause_frame.place_forget()
    root.focus_force()
    canvas.focus_force()

def go_to_menu():
    global game_state
    save_progress()
    game_state = "menu"
    pause_frame.place_forget()
    if "shop_frame" in globals(): shop_frame.place_forget()
    btn_top_pause.place_forget()
    menu_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    menu_frame.lift()

def toggle_pause(e=None):
    if game_state == "play":
        globals().update(game_state="pause")
        keys.clear()
        pause_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    elif game_state == "pause":
        resume_game()

btn_top_pause = tk.Button(canvas, text="ПАУЗА", font=("Sans", 10, "bold"), bg="#1e272e", fg="white", bd=2, relief=tk.RIDGE, padx=10, pady=3, command=toggle_pause)
tk.Button(menu_frame, text="ИГРАТЬ", font=("Sans", 13, "bold"), bg="#27ae60", fg="white", width=18, pady=6, command=start_game).pack(pady=5)
tk.Button(menu_frame, text="МАГАЗИН", font=("Sans", 12, "bold"), bg="#e67e22", fg="white", width=18, pady=5, command=lambda: open_shop()).pack(pady=5)
tk.Button(menu_frame, text="ВЫХОД", font=("Sans", 11, "bold"), bg="#c0392b", fg="white", width=18, pady=4, command=root.destroy).pack(pady=5)
tk.Button(pause_frame, text="ПРОДОЛЖИТЬ", font=("Sans", 12, "bold"), bg="#27ae60", fg="white", width=18, pady=5, command=resume_game).pack(pady=5)
tk.Button(pause_frame, text="ЗАНОВО", font=("Sans", 12, "bold"), bg="#2980b9", fg="white", width=18, pady=5, command=lambda: start_game(True)).pack(pady=5)
tk.Button(pause_frame, text="В ГЛАВНОЕ МЕНЮ", font=("Sans", 11, "bold"), bg="#7f8fa6", fg="white", width=18, pady=4, command=go_to_menu).pack(pady=5)
menu_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)


shop_frame = tk.Frame(canvas, bg="#1e272e", bd=3, relief=tk.RIDGE, padx=25, pady=20)
tk.Label(shop_frame, text="МАГАЗИН УЛУЧШЕНИЙ", font=("Sans", 18, "bold"), bg="#1e272e", fg="#fbc531").pack(pady=(0, 8))
shop_bal = tk.Label(shop_frame, text=f"Ваш баланс: {money}р", font=("Sans", 12, "bold"), bg="#1e272e", fg="#4cd137")
shop_bal.pack(pady=(0, 12))
shop_msg = tk.Label(shop_frame, text="Выберите улучшение для автобуса", font=("Sans", 10), bg="#1e272e", fg="#dcdde1")
shop_msg.pack(pady=(0, 10))

def update_shop_btns():
    shop_bal.config(text=f"Ваш баланс: {money}р")
    btn_c.config(text=f"Новая покраска ({cost_color}р)")
    btn_e.config(text=f"Турбо-двигатель ({cost_engine}р)")
    btn_t.config(text=f"Билеты +{ticket_price + 15}р ({cost_ticket}р)")

def open_shop():
    menu_frame.place_forget()
    update_shop_btns()
    shop_msg.config(text="Выберите улучшение для автобуса", fg="#dcdde1")
    shop_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    shop_frame.lift()

def close_shop():
    shop_frame.place_forget()
    menu_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    menu_frame.lift()

def buy_color():
    global money, bus_color, cost_color
    if money >= cost_color:
        money -= cost_color
        cost_color += 50
        colors = ["#00a8ff", "#e84118", "#4cd137", "#9c88ff", "#fbc531", "#ff9f1a"]
        bus_color = colors[(colors.index(bus_color) + 1) % len(colors)] if bus_color in colors else "#00a8ff"
        save_progress()
        update_shop_btns()
        shop_msg.config(text="Куплен новый цвет! Цена выросла.", fg="#4cd137")
    else:
        shop_msg.config(text=f"Недостаточно денег (нужно {cost_color}р)!", fg="#ff3838")

def buy_engine():
    global money, accel_bonus, cost_engine
    if money >= cost_engine:
        money -= cost_engine
        cost_engine += 150
        accel_bonus += 0.02
        save_progress()
        update_shop_btns()
        shop_msg.config(text="Двигатель улучшен! Цена выросла.", fg="#4cd137")
    else:
        shop_msg.config(text=f"Недостаточно денег (нужно {cost_engine}р)!", fg="#ff3838")

def buy_ticket():
    global money, ticket_price, cost_ticket
    if money >= cost_ticket:
        money -= cost_ticket
        cost_ticket += 250
        ticket_price += 15
        save_progress()
        update_shop_btns()
        shop_msg.config(text=f"Тариф теперь {ticket_price}р! Цена выросла.", fg="#4cd137")
    else:
        shop_msg.config(text=f"Недостаточно денег (нужно {cost_ticket}р)!", fg="#ff3838")

btn_c = tk.Button(shop_frame, text=f"Новая покраска ({cost_color}р)", font=("Sans", 11, "bold"), bg="#0097e6", fg="white", width=28, pady=4, command=buy_color)
btn_c.pack(pady=4)
btn_e = tk.Button(shop_frame, text=f"Турбо-двигатель ({cost_engine}р)", font=("Sans", 11, "bold"), bg="#e67e22", fg="white", width=28, pady=4, command=buy_engine)
btn_e.pack(pady=4)
btn_t = tk.Button(shop_frame, text=f"Билеты +{ticket_price + 15}р ({cost_ticket}р)", font=("Sans", 11, "bold"), bg="#8c7ae6", fg="white", width=28, pady=4, command=buy_ticket)
btn_t.pack(pady=4)
tk.Button(shop_frame, text="НАЗАД В МЕНЮ", font=("Sans", 11, "bold"), bg="#7f8fa6", fg="white", width=28, pady=5, command=close_shop).pack(pady=(12, 0))

def toggle_doors():
    global doors
    if game_state == "play" and speed < 0.35: doors = not doors

def key_down(e):
    if e.keysym == "Escape": toggle_pause(); return
    if game_state == "play":
        keys.add(e.keycode); keys.add(e.keysym.lower())
        if e.keycode == 65 or e.keysym.lower() == "space": toggle_doors()

def key_up(e): keys.discard(e.keycode); keys.discard(e.keysym.lower())
root.bind_all("<KeyPress>", key_down); root.bind_all("<KeyRelease>", key_up)

tk.Button(panel, text="ДВЕРИ", font=("Sans", 10, "bold"), bg="#27ae60", fg="white", command=toggle_doors).pack(side=tk.RIGHT, padx=5, pady=4)
b_gas = tk.Button(panel, text="ГАЗ (W)", font=("Sans", 10, "bold"), bg="#2980b9", fg="white"); b_gas.pack(side=tk.RIGHT, padx=5, pady=4)
b_gas.bind("<ButtonPress-1>", lambda e: globals().update(btn_gas=True)); b_gas.bind("<ButtonRelease-1>", lambda e: globals().update(btn_gas=False))
b_brake = tk.Button(panel, text="ТОРМОЗ (S)", font=("Sans", 10, "bold"), bg="#c0392b", fg="white"); b_brake.pack(side=tk.RIGHT, padx=5, pady=4)
b_brake.bind("<ButtonPress-1>", lambda e: globals().update(btn_brake=True)); b_brake.bind("<ButtonRelease-1>", lambda e: globals().update(btn_brake=False))
def draw_person(px, py, dc, hc, step):
    ls = math.sin(step) * 3 if step > 0 else 0
    canvas.create_line(px - 3, py, px - 3 - ls, py + 8, fill="#ffbe76", width=2)
    canvas.create_line(px + 3, py, px + 3 + ls, py + 8, fill="#ffbe76", width=2)
    canvas.create_polygon(px - 5, py - 12, px + 5, py - 12, px + 8, py, px - 8, py, fill=dc, outline="black")
    canvas.create_oval(px - 6, py - 23, px + 6, py - 11, fill=hc, outline="")
    canvas.create_oval(px - 4, py - 21, px + 4, py - 12, fill="#ffbe76", outline="black")

def draw_all():
    canvas.delete("all")
    rw, rh = max(1, canvas.winfo_width()), max(1, canvas.winfo_height())
    cw = max(820, int(BASE_H * (rw / rh)))
    canvas.create_rectangle(0, 0, cw, 135, fill="#74b9ff", outline="")
    canvas.create_rectangle(0, 85, cw, 135, fill="#81ecec", outline="")
    canvas.create_oval(700, 14, 768, 82, fill="#ffeaa7", outline="")
    canvas.create_oval(710, 24, 758, 72, fill="#fdcb6e", outline="")
    for i in range(7):
        clx = (i * 420 - dist * 0.12) % (cw + 300) - 150
        cly = 24 + (i % 3) * 18
        canvas.create_oval(clx, cly, clx + 65, cly + 26, fill="white", outline="")
        canvas.create_oval(clx + 20, cly - 10, clx + 85, cly + 24, fill="white", outline="")
        canvas.create_oval(clx + 48, cly + 2, clx + 105, cly + 26, fill="white", outline="")
    for i in range(16):
        hx = (i * 190 - dist * 0.25) % (cw + 300) - 150
        hh = 45 + (i % 4) * 18
        canvas.create_rectangle(hx, 135 - hh, hx + 110, 135, fill="#a4b0be", outline="#747d8c")
    canvas.create_rectangle(0, 135, cw, 380, fill="#55efc4", outline="")
    canvas.create_rectangle(0, 135, cw, 162, fill="#dfe4ea", outline="#a4b0be")
    canvas.create_rectangle(0, 162, cw, 315, fill="#2f3542", outline="")
    canvas.create_rectangle(0, 315, cw, 380, fill="#ced6e0", outline="#a4b0be")
    for i in range(int(cw // 90) + 3):
        lx = i * 90 - (dist % 90)
        canvas.create_rectangle(lx, 236, lx + 48, 241, fill="#f1f2f6", outline="")
    for b_obj in buildings:
        bx_pos = (b_obj["x"] - dist * 0.65) % 2880 - 200
        if -180 < bx_pos < cw + 180:
            by_top = 135 - b_obj["h"]
            canvas.create_rectangle(bx_pos, by_top, bx_pos + b_obj["w"], 135, fill=b_obj["c"], outline="#2f3542", width=2)
            canvas.create_polygon(bx_pos - 6, by_top, bx_pos + b_obj["w"] // 2, by_top - 18, bx_pos + b_obj["w"] + 6, by_top, fill="#57606f", outline="#2f3542", width=2)
            for wy in range(by_top + 12, 118, 22):
                for wx in range(int(bx_pos) + 14, int(bx_pos + b_obj["w"]) - 18, 24):
                    canvas.create_rectangle(wx, wy, wx + 12, wy + 14, fill="#ffeaa7", outline="#2f3542")
    for t_obj in trees:
        tx_pos = (t_obj["x"] - dist) % 3600 - 150
        if -100 < tx_pos < cw + 100:
            canvas.create_oval(tx_pos - 22, 132, tx_pos + 22, 146, fill="#00b894", outline="")
            canvas.create_rectangle(tx_pos - 5, 102, tx_pos + 5, 140, fill="#6F4E37", outline="#3d2b1f")
            canvas.create_oval(tx_pos - 26, 68, tx_pos + 26, 112, fill="#009432", outline="#006266", width=2)
            canvas.create_oval(tx_pos - 18, 56, tx_pos + 18, 92, fill="#2ed573", outline="")
    for cw_obj in crosswalks:
        cx = cw_obj["x"] - dist + 100
        if -150 < cx < 2500:
            for zy in range(172, 310, 22): canvas.create_rectangle(cx - 28, zy, cx + 28, zy + 11, fill="#f5f6fa", outline="")
            if cw_obj["light"]:
                t_val = cw_obj["timer"] % 500
                canvas.create_rectangle(cx + 28, 246, cx + 46, 294, fill="#1e272e", outline="white")
                canvas.create_oval(cx + 32, 250, cx + 42, 260, fill="#ff3838" if t_val < 220 else "#4b4b4b")
                canvas.create_oval(cx + 32, 265, cx + 42, 275, fill="#fff200" if 220 <= t_val < 270 else "#4b4b4b")
                canvas.create_oval(cx + 32, 280, cx + 42, 290, fill="#32ff7e" if t_val >= 270 else "#4b4b4b")
    for s in stops:
        sx = s["x"] - dist + 100
        if -250 < sx < 2500:
            canvas.create_rectangle(sx - 130, 297, sx + 130, 315, fill="#fbc531", outline="")
            canvas.create_rectangle(sx - 50, 322, sx + 45, 366, fill="#487eb0", outline="#192a56", width=2)
            canvas.create_rectangle(sx - 56, 316, sx + 51, 323, fill="#192a56", outline="")
            canvas.create_rectangle(sx + 55, 305, sx + 59, 365, fill="white", outline="")
            canvas.create_rectangle(sx + 48, 292, sx + 66, 310, fill="#0097e6", outline="white", width=2)
            canvas.create_text(sx + 57, 301, text="А", fill="white", font=("Sans", 9, "bold"))
    for c in cars:
        cx, cy = c["x"] - dist + 100, c["y"]
        if -150 < cx < 2500:
            canvas.create_rectangle(cx, cy + 8, cx + 82, cy + 32, fill=c["c"], outline="black", width=2)
            canvas.create_polygon(cx + 14, cy + 8, cx + 24, cy - 2, cx + 58, cy - 2, cx + 68, cy + 8, fill=c["c"], outline="black", width=2)
            fx = cx + 77 if c["dir"] == 1 else cx; canvas.create_rectangle(fx, cy + 12, fx + 5, cy + 19, fill="#fff200", outline="")
            for wx in (cx + 12, cx + 56): canvas.create_oval(wx, cy + 25, wx + 15, cy + 40, fill="#1e272e", outline="black")
    bx, by = 100, 242
    canvas.create_rectangle(bx, by, bx + 135, by + 48, fill=bus_color, outline="black", width=2)
    for i in range(3): canvas.create_rectangle(bx + 10 + i * 30, by + 8, bx + 32 + i * 30, by + 24, fill="#fff200" if people > i * 3 else "#dff9fb", outline="black")
    canvas.create_rectangle(bx + 105, by + 8, bx + 126, by + 44, fill="#4cd137" if doors else "#2f3640", outline="black")
    canvas.create_oval(bx + 18, by + 38, bx + 38, by + 58, fill="black"); canvas.create_oval(bx + 96, by + 38, bx + 116, by + 58, fill="black")
    for ep in exiting_plist:
        if ep["delay"] == 0: draw_person(ep["x"] - dist + 100, ep["y"], ep["d"], ep["h"], ep["step"])
    for s in stops:
        for p in s["plist"]: draw_person(p["x"] - dist + 100, p["y"], p["d"], p["h"], p["step"])
    for cw_obj in crosswalks:
        for ped in []:
            if not ped["hit"]: draw_person(cw_obj["x"] - dist + 100 + ped.get("dx", 0), ped["py"], ped["d"], ped["h"], ped["step"])
    for sp in sidewalk_peds:
        spx = sp["x"] - dist + 100
        if -100 < spx < 2500: draw_person(spx, sp.get("y", 148.0), sp["d"], sp["h"], sp["step"])
    rw, rh = max(1, canvas.winfo_width()), max(1, canvas.winfo_height())
    if rw > 10 and rh > 10: canvas.scale("all", 0, 0, rh / BASE_H, rh / BASE_H)
def loop():
    global speed, dist, money, people, board_timer, alert_text, alert_timer, speed_fine_timer, doors, stop_counter
    if game_state != "play":
        draw_all(); root.after(16, loop); return
    if alert_timer > 0: alert_timer -= 1
    if speed_fine_timer > 0: speed_fine_timer -= 1
    gas = btn_gas or bool(keys & {25, 111, "w", "up", "cyrillic_tse", "ц"})
    brake = btn_brake or bool(keys & {39, 116, "s", "down", "cyrillic_yeru", "ы"})
    if gas: doors = False; speed = min(10.0, speed + 0.08 + accel_bonus)
    elif brake: speed = max(0.0, speed - 0.35)
    else: speed = max(0.0, speed - 0.04)
    if speed >= 9.0 and speed_fine_timer == 0: money = max(0, money - 10); alert_text = " | Штраф 90+ (-10р)"; alert_timer = 110; speed_fine_timer = 150
    dist += speed
    if stops[-1]["x"] - dist < 4500:
        nx = stops[-1]["x"] + random.randint(2800, 4200); stops.append(make_stop(nx)); stop_counter += 1
        if stop_counter % 4 == 0: crosswalks.append(make_crosswalk(nx + 450, True))
        elif stop_counter % 2 == 0: crosswalks.append(make_crosswalk(nx + 450, False))
    for sp in sidewalk_peds:
        if sp.get("cd", 0) > 0:
            sp["cd"] -= 1
        if sp.get("cross", 0) == 0:
            sp["x"] += sp["dir"] * sp["v"]
            sp["step"] += 0.25
            if sp["x"] < dist - 400:
                sp["x"] = dist + 2400 + random.randint(50, 300)
            elif sp["x"] > dist + 2600:
                sp["x"] = dist - 200
            if sp.get("cd", 0) == 0:
                for cw in crosswalks:
                    if abs(sp["x"] - cw["x"]) < 18:
                        sp["x"] = cw["x"] + random.randint(-12, 12)
                        sp["cross"] = 1 if sp["y"] < 200 else -1
                        sp["cw"] = cw
                        break
        else:
            cw = sp["cw"]
            is_red = cw["light"] and (cw["timer"] % 500 < 270)
            on_road = 154 < sp["y"] < 330
            if (not cw["light"]) or is_red or on_road:
                sp["y"] += sp["cross"] * 1.3
                sp["step"] += 0.3
                if sp["cross"] == 1 and sp["y"] >= 338.0:
                    sp["y"] = 338.0
                    sp["cross"] = 0
                    sp["cd"] = 220
                elif sp["cross"] == -1 and sp["y"] <= 148.0:
                    sp["y"] = 148.0
                    sp["cross"] = 0
                    sp["cd"] = 220
            else:
                sp["step"] = 0.0
            if on_road and 235 < sp["y"] < 300 and 105 < (sp["x"] - dist + 100) < 230 and speed > 0.3 and sp.get("cd", 0) == 0:
                sp["cd"] = 150
                money = max(0, money - 10)
                alert_text = " | Пешеход (-10р)"
                alert_timer = 130
    for cw_obj in crosswalks:
        cw_obj["timer"] += 1; cx = cw_obj["x"] - dist + 100
        is_red = cw_obj["light"] and (cw_obj["timer"] % 500 < 270)
        is_green = cw_obj["light"] and (cw_obj["timer"] % 500 >= 270)
        if is_red and 80 < cx < 235 and speed > 0.5 and not cw_obj["fined"]:
            money = max(0, money - 20); alert_text = " | Красный (-20р)"; alert_timer = 130; cw_obj["fined"] = True
        for ped in []:
            on_road = 152 < ped["py"] < 328
            if (not cw_obj["light"]) or is_red or on_road:
                spd = ped.get("v", 1.1) * (1.4 if (is_green and on_road) else 1.0)
                ped["py"] += ped["dir"] * spd; ped["step"] += 0.25
                if ped["py"] >= 335: ped["py"] = 335.0; ped["dir"] = -1
                elif ped["py"] <= 145: ped["py"] = 145.0; ped["dir"] = 1
            else:
                ped["step"] = 0.0
            if on_road and not ped["hit"] and 235 < ped["py"] < 300 and 105 < cx + ped.get("dx", 0) < 230 and speed > 0.3:
                ped["hit"] = True; money = max(0, money - 10); alert_text = " | Пешеход (-10р)"; alert_timer = 130
    near_stop = False
    for s in stops:
        sx = s["x"] - dist + 100
        if sx - 135 < 215 < sx + 135 and len(s["plist"]) > 0:
            near_stop = True
            if speed < 0.15 and not gas:
                doors = True
                if not s["exited"]:
                    cnt = people // 2; people -= cnt; s["exited"] = True
                    for i in range(cnt): exiting_plist.append({"x": dist + 115, "y": 285.0, "tx": s["x"] - 30 + i * 16, "ty": 338.0, "d": random.choice(dresses), "h": random.choice(hairs), "step": 0.0, "delay": i * 12})
            if doors:
                board_timer += 1
                if board_timer >= 15:
                    board_timer = 0
                    for pl in s["plist"]:
                        if not pl["go"]: pl["go"] = True; break
                for pl in s["plist"][:]:
                    if pl["go"]:
                        px = pl["x"] - dist + 100; dx, dy = 215 - px, 285 - pl["y"]; d = (dx**2 + dy**2)**0.5
                        if d < 8: s["plist"].remove(pl); people += 1; money += ticket_price
                        else: pl["x"] += (dx / d) * 3.0; pl["y"] += (dy / d) * 3.0; pl["step"] += 0.4
    for ep in exiting_plist[:]:
        if ep.get("done"): continue
        if ep["delay"] > 0: ep["delay"] -= 1; continue
        if not ep.get("on_path"):
            dx, dy = ep["tx"] - ep["x"], 338.0 - ep["y"]; d = (dx**2 + dy**2)**0.5
            if d < 6: ep["on_path"] = True; ep["goal_x"] = min([cw["x"] - 25 for cw in crosswalks if cw["x"] > ep["x"]] + [ep["x"] + 280])
            else: ep["x"] += (dx / d) * 2.2; ep["y"] += (dy / d) * 2.2; ep["step"] += 0.4
        else:
            if ep["x"] < ep["goal_x"]: ep["x"] += 1.3; ep["step"] += 0.3
            else: ep["step"] = 0.0; ep["done"] = True
    for c in cars:
        if "cur_v" not in c: c["cur_v"] = c["v"]
        tv = c["v"]
        if c["dir"] == 1:
            if any(o is not c and o["dir"] == 1 and 0 < o["x"] - (c["x"] + 82) < 120 for o in cars): tv = 0.0
            if 0 < dist - (c["x"] + 82) < 120: tv = 0.0
            if any(sp.get("cross", 0) != 0 and 150 < sp.get("y", 148) < 335 and 0 < (sp["x"] - 35) - (c["x"] + 82) < 135 for sp in sidewalk_peds): tv = 0.0
            if any(sp.get("cross", 0) != 0 and 150 < sp.get("y", 148) < 335 and 0 < c["x"] - (sp["x"] + 35) < 135 for sp in sidewalk_peds): tv = 0.0
            if any(cw["light"] and (cw["timer"] % 500 < 270) and 0 < (cw["x"] - 35) - (c["x"] + 82) < 130 for cw in crosswalks): tv = 0.0
        else:
            if any(o is not c and o["dir"] == -1 and 0 < c["x"] - (o["x"] + 82) < 120 for o in cars): tv = 0.0
            if any(cw["light"] and (cw["timer"] % 500 < 270) and 0 < c["x"] - (cw["x"] + 35) < 130 for cw in crosswalks): tv = 0.0
        c["cur_v"] += (tv - c["cur_v"]) * 0.15; c["x"] += c["cur_v"]; cx = c["x"] - dist + 100
        if cx < -300 or cx > 2600:
            same = [o["x"] for o in cars if o["dir"] == c["dir"] and o is not c]
            c["x"] = max(same + [dist + 2200]) + random.randint(150, 420); c["c"] = random.choice(car_colors)
            c["v"] = random.uniform(4.8, 8.8) if c["dir"] == 1 else random.uniform(-7.0, -4.5); c["cur_v"] = c["v"]
        if c["dir"] == 1 and 100 < cx + 82 and 235 > cx: speed = 0.0; money = max(0, money - 25); c["x"] += 170; alert_text = " | ДТП (-25р)"; alert_timer = 90
    draw_all()
    msg = alert_text if alert_timer > 0 else (" | Посадка..." if (near_stop and doors) else "")
    label.config(text=f"Скорость: {int(speed*10)} км/ч | Деньги: {money}р | Пассажиры: {people}{msg}")
    root.after(16, loop)
canvas.focus_force()
loop()
root.protocol("WM_DELETE_WINDOW", lambda: (save_progress(), root.destroy()))
root.mainloop()
