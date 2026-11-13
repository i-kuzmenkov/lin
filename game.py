"""Симулятор автобуса — улучшенная версия.

Управление: W/стрелка вверх — газ, S/стрелка вниз — тормоз,
Пробел — открыть или закрыть двери на остановке.
Сначала пассажиры выходят, затем новые пассажиры заходят.
Также доступны кнопки на экране. Используется только tkinter из Python.
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
import sys
import random
import math

# Окно и игровое поле.
root = tk.Tk()

# В старых версиях Tk под Linux шрифт без кириллицы может показывать
# вместо русских букв последовательности вида \u041f\u0440.
# Выбираем реально установленный шрифт с кириллическими символами.
installed_fonts = set(tkfont.families(root))
if sys.platform.startswith("win"):
    font_candidates = ("Segoe UI", "DejaVu Sans", "Noto Sans", "Liberation Sans", "Arial")
else:
    font_candidates = ("DejaVu Sans", "Noto Sans", "Liberation Sans", "FreeSans", "Arial")
UI_FONT = next((name for name in font_candidates if name in installed_fonts), "TkDefaultFont")
root.title("Симулятор автобуса — маршрут")
root.geometry("900x610+100+100")
root.minsize(820, 570)

BASE_W, BASE_H = 820, 440
canvas = tk.Canvas(root, width=BASE_W, height=BASE_H, bg="#6ab04c", highlightthickness=0, takefocus=True)
canvas.pack(fill=tk.BOTH, expand=True)

# Понятная панель: показатели, сообщение о происходящем и управление.
panel = tk.Frame(root, bg="#1e272e", padx=12, pady=7)
panel.pack(fill=tk.X, side=tk.BOTTOM)

stats = tk.Frame(panel, bg="#1e272e")
stats.pack(fill=tk.X)

def stat_label():
    lbl = tk.Label(stats, text="", font=(UI_FONT, 11, "bold"), bg="#1e272e", fg="white", anchor="w")
    lbl.pack(side=tk.LEFT, padx=(0, 18))
    return lbl

speed_label = stat_label()
passengers_label = stat_label()
money_label = stat_label()
next_stop_label = stat_label()

status_line = tk.Frame(panel, bg="#253541", padx=9, pady=6)
status_line.pack(fill=tk.X, pady=(7, 6))
status_label = tk.Label(status_line, text="", font=(UI_FONT, 11), bg="#253541", fg="#ffffff", anchor="w")
status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
progress = ttk.Progressbar(status_line, orient="horizontal", length=130, mode="determinate", maximum=100)

controls = tk.Frame(panel, bg="#1e272e")
controls.pack(fill=tk.X)
tk.Label(controls, text="Управление: W / ↑ — газ    S / ↓ — тормоз    Пробел — двери",
         font=(UI_FONT, 10), bg="#1e272e", fg="#c8d6e5").pack(side=tk.LEFT)

speed = 0.0
# dist — пройденное игровое расстояние, не реальные метры.
dist = 0.0
money = 100
people = 0
board_timer = 0
doors = False
btn_gas = False
btn_brake = False
keys = set()
alert_text = ""
alert_timer = 0
speed_fine_timer = 0
crash_timer = 0
STOP_RADIUS = 85
next_stop_number = 1

# Декорации и пассажиры из исходной игры.
dresses = ["#e84118", "#9c88ff", "#fbc531", "#00a8ff", "#4cd137"]
hairs = ["#2f3640", "#e1b12c", "#8c7ae6", "#c23616", "#574b90"]
buildings = [{"x": i * 160, "w": random.randint(90, 130), "h": random.randint(65, 105),
              "c": random.choice(["#d1ccc0", "#aaa69d", "#84817a", "#ccae62", "#706fd3"])}
             for i in range(10)]
trees = [{"x": i * 240 + 40} for i in range(8)]


def make_stop(x):
    global next_stop_number
    number = next_stop_number
    next_stop_number += 1
    count = random.randint(3, 6)
    plist = [{"x": x - 45 + i * 18, "y": 375, "d": dresses[i % 5],
              "h": hairs[i % 5], "go": False, "step": 0.0} for i in range(count)]
    return {"x": x, "number": number, "plist": plist, "total": count,
            "boarded": 0, "exited": False, "exited_count": 0,
            "exit_total": 0, "exit_queue": [], "walking_away": [], "served": False}


stops = [make_stop(1500), make_stop(4500)]
car_colors = ["#e84118", "#0097e6", "#fbc531", "#8c7ae6", "#44bd32", "#f5f6fa"]
cars = [
    {"x": 950, "y": 248, "v": 5.5, "c": "#0097e6", "dir": 1},
    {"x": 1450, "y": 248, "v": 7.2, "c": "#8c7ae6", "dir": 1},
    {"x": 1950, "y": 248, "v": 6.4, "c": "#44bd32", "dir": 1},
    {"x": 1100, "y": 178, "v": -5.5, "c": "#e84118", "dir": -1},
    {"x": 1750, "y": 178, "v": -6.2, "c": "#fbc531", "dir": -1},
]


def door_position():
    return dist + 115


def current_stop():
    """Остановка, около которой находится дверь автобуса."""
    nearby = [s for s in stops if abs(door_position() - (s["x"] + 20)) <= STOP_RADIUS]
    return min(nearby, key=lambda s: abs(door_position() - (s["x"] + 20))) if nearby else None


def toggle_doors():
    global doors, people, board_timer, alert_text, alert_timer
    if speed >= 0.15:
        return
    stop = current_stop()
    if doors:
        # Не закрываем двери, пока кто-то ещё выходит.
        if stop is not None and stop["exit_queue"]:
            alert_text, alert_timer = "Подождите: пассажиры ещё выходят!", 110
            return
        doors = False
        return
    if stop is None:
        alert_text, alert_timer = "Откройте двери у остановки", 110
        return
    doors = True
    board_timer = 0
    stop["served"] = True
    if not stop["exited"]:
        # Пассажиры выходят по одному, а не исчезают мгновенно.
        # На первой остановке автобус пуст, а на следующих выходит
        # примерно половина приехавших пассажиров.
        leaving = (people + 1) // 2
        stop["exit_total"] = leaving
        stop["exit_queue"] = [
            {"x": door_position(), "y": 290.0,
             "target_x": stop["x"] + 95 + i * 13, "target_y": 375.0,
             "d": random.choice(dresses), "h": random.choice(hairs),
             "step": 0.0}
            for i in range(leaving)
        ]
        stop["exited"] = True


def key_down(event):
    key = event.keysym.lower()
    if key in ("space", "a", "cyrillic_ef") and key not in keys:
        toggle_doors()
    keys.add(key)


def key_up(event):
    keys.discard(event.keysym.lower())


# Один обработчик клавиатуры, чтобы Пробел не открывал и тут же не закрывал двери.
root.bind_all("<KeyPress>", key_down)
root.bind_all("<KeyRelease>", key_up)
root.bind("<FocusOut>", lambda event: keys.clear())
canvas.bind("<Button-1>", lambda event: canvas.focus_set())


def set_gas(value):
    global btn_gas
    btn_gas = value


def set_brake(value):
    global btn_brake
    btn_brake = value


door_button = tk.Button(controls, text="ОТКРЫТЬ ДВЕРИ", font=(UI_FONT, 10, "bold"),
                        bg="#27ae60", fg="white", command=toggle_doors, width=17)
door_button.pack(side=tk.RIGHT, padx=(6, 0))

b_brake = tk.Button(controls, text="ТОРМОЗ (S)", font=(UI_FONT, 10, "bold"),
                    bg="#c0392b", fg="white", width=12)
b_brake.pack(side=tk.RIGHT, padx=4)
b_brake.bind("<ButtonPress-1>", lambda event: set_brake(True))
b_brake.bind("<ButtonRelease-1>", lambda event: set_brake(False))

b_gas = tk.Button(controls, text="ГАЗ (W)", font=(UI_FONT, 10, "bold"),
                  bg="#2980b9", fg="white", width=11)
b_gas.pack(side=tk.RIGHT, padx=4)
b_gas.bind("<ButtonPress-1>", lambda event: set_gas(True))
b_gas.bind("<ButtonRelease-1>", lambda event: set_gas(False))


def draw_all():
    canvas.delete("all")
    canvas.create_rectangle(0, 0, BASE_W, 135, fill="#7ed6df", outline="")
    canvas.create_oval(710, 18, 765, 73, fill="#f9ca24", outline="#f6e58d", width=3)
    for i in range(4):
        cl_x = (i * 250 - dist * 0.1) % 980 - 80
        canvas.create_oval(cl_x, 22, cl_x + 75, 50, fill="white", outline="")
    for i in range(5):
        hx = (i * 260 - dist * 0.2) % 1200 - 150
        canvas.create_oval(hx, 75, hx + 320, 175, fill="#badc58", outline="")
    for b in buildings:
        bx_p = (b["x"] - dist * 0.4) % 1600 - 150
        by_t = 135 - b["h"]
        canvas.create_rectangle(bx_p, by_t, bx_p + b["w"], 135, fill=b["c"], outline="#2f3640")
    canvas.create_rectangle(0, 135, BASE_W, 165, fill="#95afc0", outline="")
    canvas.create_rectangle(0, 160, BASE_W, 165, fill="#dcdde1", outline="")
    for t in trees:
        tx = (t["x"] - dist * 0.75) % 1800 - 80
        canvas.create_line(tx + 75, 85, tx + 75, 158, fill="#2f3640", width=3)
        canvas.create_oval(tx + 68, 80, tx + 82, 88, fill="#f9ca24", outline="black")
        canvas.create_rectangle(tx - 5, 110, tx + 5, 158, fill="#6D4C41", outline="")
        canvas.create_oval(tx - 24, 78, tx + 24, 120, fill="#218c74", outline="")
    # Правостороннее движение: автобус и попутные машины — по нижней полосе.
    canvas.create_rectangle(0, 165, BASE_W, 315, fill="#2f3640", outline="")
    canvas.create_rectangle(0, 315, BASE_W, 400, fill="#95afc0", outline="")
    canvas.create_rectangle(0, 315, BASE_W, 321, fill="#dcdde1", outline="")
    canvas.create_rectangle(0, 400, BASE_W, BASE_H, fill="#6ab04c", outline="")
    for x in range(-(int(dist) % 80), BASE_W + 80, 80):
        canvas.create_rectangle(x, 237, x + 40, 243, fill="white", outline="")

    for s in stops:
        sx = s["x"] - dist + 100
        if -250 < sx < 1050:
            done = s["boarded"] == s["total"]
            in_zone = current_stop() is s
            canvas.create_rectangle(sx - 130, 315, sx + 130, 336,
                                    fill="#7f8fa6" if done else "#fbc531",
                                    outline="#4cd137" if in_zone else "", width=3)
            canvas.create_rectangle(sx - 50, 343, sx + 45, 395,
                                    fill="#487eb0", outline="#192a56", width=2)
            canvas.create_rectangle(sx - 56, 337, sx + 51, 344, fill="#192a56", outline="")
            canvas.create_rectangle(sx + 55, 345, sx + 59, 395, fill="white", outline="")
            canvas.create_rectangle(sx + 48, 326, sx + 66, 346,
                                    fill="#0097e6", outline="#4cd137" if in_zone else "white", width=2)
            canvas.create_text(sx + 57, 336, text="А", fill="white", font=(UI_FONT, 9, "bold"))
            canvas.create_text(sx - 4, 356, text=f"№{s['number']}", fill="white", font=(UI_FONT, 9, "bold"))

    for c in cars:
        cx, cy = c["x"] - dist + 100, c["y"]
        if -120 < cx < 950:
            canvas.create_rectangle(cx, cy + 8, cx + 80, cy + 32, fill=c["c"], outline="black", width=2)
            canvas.create_rectangle(cx + 15, cy, cx + 65, cy + 12, fill=c["c"], outline="black", width=2)
            canvas.create_oval(cx + 10, cy + 25, cx + 24, cy + 39, fill="black")
            canvas.create_oval(cx + 56, cy + 25, cx + 70, cy + 39, fill="black")
            lamp_x = cx + 77 if c["dir"] == 1 else cx - 2
            canvas.create_rectangle(lamp_x, cy + 16, lamp_x + 5, cy + 23, fill="#fff200", outline="")

    bx, by = 100, 248
    canvas.create_rectangle(bx, by, bx + 135, by + 48, fill="#ff9f1a", outline="black", width=2)
    for i in range(3):
        w_col = "#fff200" if people > i * 3 else "#dff9fb"
        canvas.create_rectangle(bx + 10 + i * 30, by + 8, bx + 32 + i * 30, by + 24,
                                fill=w_col, outline="black")
    canvas.create_rectangle(bx + 105, by + 8, bx + 126, by + 44,
                            fill="#4cd137" if doors else "#2f3640", outline="black")
    canvas.create_oval(bx + 18, by + 38, bx + 38, by + 58, fill="black")
    canvas.create_oval(bx + 96, by + 38, bx + 116, by + 58, fill="black")
    canvas.create_rectangle(bx + 131, by + 17, bx + 135, by + 25, fill="#fff200", outline="")
    # Рисуем и ожидающих, и выходящих из передней двери автобуса пассажиров.
    for s in stops:
        sx = s["x"] - dist + 100
        if -250 < sx < 1050:
            visible_people = list(s["plist"]) + s["walking_away"]
            if s["exit_queue"]:
                visible_people.append(s["exit_queue"][0])
            for p in visible_people:
                px, py = p["x"] - dist + 100, p["y"]
                ls = math.sin(p["step"]) * 3 if p["step"] > 0 else 0
                canvas.create_line(px - 3, py, px - 3 - ls, py + 8, fill="#ffbe76", width=2)
                canvas.create_line(px + 3, py, px + 3 + ls, py + 8, fill="#ffbe76", width=2)
                canvas.create_polygon(px - 5, py - 12, px + 5, py - 12, px + 8, py,
                                      px - 8, py, fill=p["d"], outline="black")
                canvas.create_oval(px - 6, py - 23, px + 6, py - 11, fill=p["h"], outline="")
                canvas.create_oval(px - 4, py - 21, px + 4, py - 12, fill="#ffbe76", outline="black")

    cw, ch = canvas.winfo_width(), canvas.winfo_height()
    if cw > 10 and ch > 10:
        canvas.scale("all", 0, 0, cw / BASE_W, ch / BASE_H)


def update_hud():
    speed_label.config(text=f"СКОРОСТЬ  {int(speed * 10)} км/ч")
    passengers_label.config(text=f"В АВТОБУСЕ  {people}")
    money_label.config(text=f"ДЕНЬГИ  {money} руб.")
    door_button.config(text="ЗАКРЫТЬ ДВЕРИ" if doors else "ОТКРЫТЬ ДВЕРИ",
                       bg="#e67e22" if doors else "#27ae60")

    s = current_stop()
    if s is not None:
        next_stop_label.config(text=f"ОСТАНОВКА №{s['number']}")
        if doors:
            if s["exit_queue"]:
                message = (f"ВЫСАДКА: вышли {s['exited_count']} из {s['exit_total']}. "
                           "Затем начнётся посадка.")
            elif s["boarded"] == s["total"]:
                message = (f"Вышли {s['exited_count']}, вошли {s['boarded']}. "
                           "Остановка обслужена — закройте двери.")
            else:
                message = (f"ПОСАДКА: вошли {s['boarded']} из {s['total']}, "
                           f"осталось {len(s['plist'])}. Вышли: {s['exited_count']}.")
        elif speed >= 0.15:
            message = "Остановка рядом. Остановитесь (S), затем откройте двери (Пробел)."
        elif s["boarded"] == s["total"]:
            message = (f"Остановка обслужена: вышли {s['exited_count']}, "
                       f"вошли {s['boarded']}. Можно ехать к следующей.")
        elif s["served"]:
            message = f"Посадка прервана: осталось {len(s['plist'])}. Откройте двери."
        else:
            message = f"Остановка №{s['number']}: ждут {s['total']} человек. Откройте двери (Пробел)."
        if s["exit_queue"]:
            progress.configure(value=100 * s["exited_count"] / s["exit_total"])
        else:
            progress.configure(value=100 * s["boarded"] / s["total"])
        if not progress.winfo_manager():
            progress.pack(side=tk.RIGHT, padx=(10, 0))
    else:
        next_up = next((stop for stop in stops if stop["x"] + 20 > door_position() and
                        stop["boarded"] < stop["total"]), None)
        if next_up:
            left = max(0, round(next_up["x"] + 20 - door_position()))
            next_stop_label.config(text=f"ДО №{next_up['number']}  {left} м")
        else:
            next_stop_label.config(text="МАРШРУТ")
        message = "Едьте к жёлтой остановке. Остановитесь рядом с ней и откройте двери."
        if progress.winfo_manager():
            progress.pack_forget()

    if doors and speed < 0.15 and s is None:
        message = "Закройте двери, чтобы продолжить движение."
    if alert_timer > 0:
        message += "    |    " + alert_text
    status_label.config(text=message)


def loop():
    global speed, dist, money, people, board_timer, alert_text, alert_timer, speed_fine_timer, crash_timer
    if alert_timer > 0:
        alert_timer -= 1
    if speed_fine_timer > 0:
        speed_fine_timer -= 1
    if crash_timer > 0:
        crash_timer -= 1

    gas = btn_gas or bool(keys & {"w", "up", "cyrillic_tse"})
    brake = btn_brake or bool(keys & {"s", "down", "cyrillic_yeru"})

    # С открытыми дверями автобус не трогается.
    if doors:
        speed = 0.0
    elif brake:
        speed = max(0.0, speed - 0.35)
    elif gas:
        speed = min(10.0, speed + 0.08)
    else:
        speed = max(0.0, speed - 0.04)

    if speed >= 9.0 and speed_fine_timer == 0:
        money = max(0, money - 10)
        alert_text, alert_timer = "Превышение скорости: штраф 10 руб.", 140
        speed_fine_timer = 150

    dist += speed
    if stops[-1]["x"] - dist < 1200:
        stops.append(make_stop(stops[-1]["x"] + random.randint(2500, 4000)))
    if len(stops) > 3 and stops[0]["x"] - dist < -400:
        stops.pop(0)

    # Высадка: один пассажир выходит из передней двери и идёт к тротуару.
    # Пока кто-то выходит, новых пассажиров не запускаем в автобус.
    s = current_stop()
    if s is not None and doors and speed < 0.15:
        if s["exit_queue"]:
            leaving_person = s["exit_queue"][0]
            dx = leaving_person["target_x"] - leaving_person["x"]
            dy = leaving_person["target_y"] - leaving_person["y"]
            d = math.hypot(dx, dy)
            if d <= 4.5:
                s["exit_queue"].pop(0)
                leaving_person["x"] = leaving_person["target_x"]
                leaving_person["y"] = leaving_person["target_y"]
                s["walking_away"].append(leaving_person)
                s["exited_count"] += 1
                people -= 1
                board_timer = 0
            else:
                leaving_person["x"] += dx / d * min(d, 4.5)
                leaving_person["y"] += dy / d * min(d, 4.5)
                leaving_person["step"] += 0.5
        elif s["plist"]:
            # Посадка начинается только ПОСЛЕ высадки и идёт по одному.
            moving = next((p for p in s["plist"] if p["go"]), None)
            if moving is None:
                board_timer += 1
                if board_timer >= 12:
                    board_timer = 0
                    moving = s["plist"][0]
                    moving["go"] = True
            if moving is not None:
                dx, dy = door_position() - moving["x"], 288 - moving["y"]
                d = math.hypot(dx, dy)
                if d <= 5.0:
                    s["plist"].remove(moving)
                    s["boarded"] += 1
                    people += 1
                    money += 35
                else:
                    moving["x"] += dx / d * min(d, 4.5)
                    moving["y"] += dy / d * min(d, 4.5)
                    moving["step"] += 0.5

    # Высадившиеся пассажиры ещё некоторое время видны на тротуаре:
    # они идут от остановки, а не исчезают сразу после выхода.
    for stop in stops:
        for pedestrian in stop["walking_away"][:]:
            pedestrian["x"] += 1.2
            pedestrian["y"] += 0.6
            pedestrian["step"] += 0.4
            if pedestrian["y"] > BASE_H + 20:
                stop["walking_away"].remove(pedestrian)

    # Попутные машины в нижнем ряду, встречные — в верхнем.
    same_lane = [c for c in cars if c["dir"] == 1]
    for c in cars:
        if c["dir"] == 1:
            ahead = [o["x"] - c["x"] for o in same_lane if 0 < o["x"] - c["x"] < 140]
            c["x"] += min(c["v"], 4.8) if ahead else c["v"]
        else:
            c["x"] += c["v"]
        cx = c["x"] - dist + 100
        if cx < -200 or cx > 1400:
            active = [o["x"] for o in cars if o["dir"] == c["dir"] and o is not c and
                      -200 <= (o["x"] - dist + 100) <= 1400]
            c["x"] = max(active + [dist + 920]) + random.randint(350, 600)
            c["c"] = random.choice(car_colors)
            if c["dir"] == 1:
                c["v"] = random.uniform(4.8, 9.0)
        cx = c["x"] - dist + 100
        if c["dir"] == 1 and 100 < cx + 80 and cx < 235 and crash_timer == 0:
            speed = 0.0
            money = max(0, money - 25)
            c["x"] = max(c["x"] + 170, dist + 280)
            alert_text, alert_timer = "ДТП: штраф 25 руб.", 120
            crash_timer = 110

    draw_all()
    update_hud()
    root.after(16, loop)


canvas.focus_set()
loop()
root.mainloop()
