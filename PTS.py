import tkinter as tk
import random
import math

root = tk.Tk()
root.title("Симулятор Автобуса")
root.geometry("820x460+100+100")

BASE_W, BASE_H = 820, 380
canvas = tk.Canvas(root, width=BASE_W, height=BASE_H, bg="#6ab04c", highlightthickness=0, takefocus=True)
canvas.pack(fill=tk.BOTH, expand=True)

panel = tk.Frame(root, bg="#1e272e")
panel.pack(fill=tk.X, side=tk.BOTTOM)

label = tk.Label(panel, text="", font=("Sans", 11, "bold"), bg="#1e272e", fg="white", pady=6)
label.pack(side=tk.LEFT, padx=10)

speed, dist, money, people, board_timer = 0.0, 0.0, 100, 0, 0
doors, btn_gas, btn_brake, was_moving = False, False, False, False
keys = set()
alert_text = ""
alert_timer = 0
speed_fine_timer = 0

dresses = ["#e84118", "#9c88ff", "#fbc531", "#00a8ff", "#4cd137"]
hairs = ["#2f3640", "#e1b12c", "#8c7ae6", "#c23616", "#574b90"]

buildings = [{"x": i * 160, "w": random.randint(90, 130), "h": random.randint(65, 105),
              "c": random.choice(["#d1ccc0", "#aaa69d", "#84817a", "#ccae62", "#706fd3"])} for i in range(10)]
trees = [{"x": i * 240 + 40} for i in range(8)]

def make_stop(x):
    plist = [{"x": x - 45 + i * 18, "y": 148, "d": dresses[i % 5], "h": hairs[i % 5], "go": False, "step": 0.0}
             for i in range(random.randint(3, 6))]
    return {"x": x, "plist": plist, "exited": False, "served": False}

stops = [make_stop(1500), make_stop(4500)]
car_colors = ["#e84118", "#0097e6", "#fbc531", "#8c7ae6", "#44bd32", "#f5f6fa"]
cars = [
    {"x": 950, "y": 178, "v": 5.5, "c": "#0097e6", "dir": 1},
    {"x": 1450, "y": 178, "v": 7.2, "c": "#8c7ae6", "dir": 1},
    {"x": 1950, "y": 178, "v": 6.4, "c": "#44bd32", "dir": 1},
    {"x": 1100, "y": 248, "v": -5.5, "c": "#e84118", "dir": -1},
    {"x": 1750, "y": 248, "v": -6.2, "c": "#fbc531", "dir": -1}
]

def toggle_doors():
    global doors
    if speed < 0.35:
        doors = not doors

def key_down(e):
    keys.add(e.keycode)
    keys.add(e.keysym.lower())
    if e.keycode == 65 or e.keysym.lower() == "space":
        toggle_doors()

def key_up(e):
    keys.discard(e.keycode)
    keys.discard(e.keysym.lower())

for w in (root, canvas):
    w.bind("<KeyPress>", key_down)
    w.bind("<KeyRelease>", key_up)

root.bind("<FocusOut>", lambda e: keys.clear())
canvas.bind("<Button-1>", lambda e: canvas.focus_force())

def set_gas(v):
    global btn_gas
    btn_gas = v

def set_brake(v):
    global btn_brake
    btn_brake = v

tk.Button(panel, text="ДВЕРИ", font=("Sans", 10, "bold"), bg="#27ae60", fg="white", command=toggle_doors).pack(side=tk.RIGHT, padx=5, pady=4)
b_gas = tk.Button(panel, text="ГАЗ (W)", font=("Sans", 10, "bold"), bg="#2980b9", fg="white")
b_gas.pack(side=tk.RIGHT, padx=5, pady=4)
b_gas.bind("<ButtonPress-1>", lambda e: set_gas(True))
b_gas.bind("<ButtonRelease-1>", lambda e: set_gas(False))
b_brake = tk.Button(panel, text="ТОРМОЗ (S)", font=("Sans", 10, "bold"), bg="#c0392b", fg="white")
b_brake.pack(side=tk.RIGHT, padx=5, pady=4)
b_brake.bind("<ButtonPress-1>", lambda e: set_brake(True))
b_brake.bind("<ButtonRelease-1>", lambda e: set_brake(False))

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
    canvas.create_rectangle(0, 165, BASE_W, 315, fill="#2f3640", outline="")
    canvas.create_rectangle(0, 315, BASE_W, 321, fill="#dcdde1", outline="")
    canvas.create_rectangle(0, 321, BASE_W, BASE_H, fill="#6ab04c", outline="")
    for x in range(-(int(dist) % 80), BASE_W + 80, 80):
        canvas.create_rectangle(x, 237, x + 40, 243, fill="white", outline="")

    bus_door_x = dist + 115
    for s in stops:
        sx = s["x"] - dist + 100
        if -250 < sx < 1050:
            done = len(s["plist"]) == 0
            in_z = abs(bus_door_x - (s["x"] + 20)) < 250 and not done
            canvas.create_rectangle(sx - 130, 165, sx + 130, 183, fill="#7f8fa6" if done else "#fbc531", outline="#4cd137" if in_z else "", width=3)
            canvas.create_rectangle(sx - 50, 112, sx + 45, 156, fill="#487eb0", outline="#192a56", width=2)
            canvas.create_rectangle(sx - 56, 106, sx + 51, 113, fill="#192a56", outline="")
            canvas.create_rectangle(sx + 55, 98, sx + 59, 158, fill="white", outline="")
            canvas.create_rectangle(sx + 48, 85, sx + 66, 103, fill="#0097e6", outline="#4cd137" if in_z else "white", width=2)
            canvas.create_text(sx + 57, 94, text="А", fill="white", font=("Sans", 9, "bold"))

    for c in cars:
        cx, cy = c["x"] - dist + 100, c["y"]
        if -120 < cx < 950:
            canvas.create_rectangle(cx, cy + 8, cx + 80, cy + 32, fill=c["c"], outline="black", width=2)
            canvas.create_rectangle(cx + 15, cy, cx + 65, cy + 12, fill=c["c"], outline="black", width=2)
            canvas.create_oval(cx + 10, cy + 25, cx + 24, cy + 39, fill="black")
            canvas.create_oval(cx + 56, cy + 25, cx + 70, cy + 39, fill="black")

    bx, by = 100, 170
    canvas.create_rectangle(bx, by, bx + 135, by + 48, fill="#ff9f1a", outline="black", width=2)
    for i in range(3):
        w_col = "#fff200" if people > i * 3 else "#dff9fb"
        canvas.create_rectangle(bx + 10 + i * 30, by + 8, bx + 32 + i * 30, by + 24, fill=w_col, outline="black")
    canvas.create_rectangle(bx + 105, by + 8, bx + 126, by + 44, fill="#4cd137" if doors else "#2f3640", outline="black")
    canvas.create_oval(bx + 18, by + 38, bx + 38, by + 58, fill="black")
    canvas.create_oval(bx + 96, by + 38, bx + 116, by + 58, fill="black")

    for s in stops:
        sx = s["x"] - dist + 100
        if -250 < sx < 1050:
            for p in s["plist"]:
                px, py = p["x"] - dist + 100, p["y"]
                ls = math.sin(p["step"]) * 3 if p["step"] > 0 else 0
                canvas.create_line(px - 3, py, px - 3 - ls, py + 8, fill="#ffbe76", width=2)
                canvas.create_line(px + 3, py, px + 3 + ls, py + 8, fill="#ffbe76", width=2)
                canvas.create_polygon(px - 5, py - 12, px + 5, py - 12, px + 8, py, px - 8, py, fill=p["d"], outline="black")
                canvas.create_oval(px - 6, py - 23, px + 6, py - 11, fill=p["h"], outline="")
                canvas.create_oval(px - 4, py - 21, px + 4, py - 12, fill="#ffbe76", outline="black")

    cw, ch = canvas.winfo_width(), canvas.winfo_height()
    if cw > 10 and ch > 10:
        canvas.scale("all", 0, 0, cw / BASE_W, ch / BASE_H)

def loop():
    global speed, dist, money, people, board_timer, alert_text, alert_timer, speed_fine_timer, doors, was_moving
    if alert_timer > 0:
        alert_timer -= 1
    if speed_fine_timer > 0:
        speed_fine_timer -= 1

    gas = btn_gas or any(k in keys for k in (25, 111, "w", "up", "cyrillic_tse"))
    brake = btn_brake or any(k in keys for k in (39, 116, "s", "down", "cyrillic_yeru"))

    if gas:
        doors = False
        speed = min(10.0, speed + 0.08)
        if speed > 0.5:
            was_moving = True
    elif brake:
        speed = max(0.0, speed - 0.35)
    else:
        speed = max(0.0, speed - 0.04)

    if speed >= 9.0 and speed_fine_timer == 0:
        money = max(0, money - 10)
        alert_text = " | Штраф 90+ (-10р)"
        alert_timer = 110
        speed_fine_timer = 150

    dist += speed

    if stops[-1]["x"] - dist < 1200:
        stops.append(make_stop(stops[-1]["x"] + random.randint(2500, 4000)))
    if len(stops) > 3 and next(iter(stops))["x"] - dist < -400:
        stops.pop(0)

    bus_door_x = dist + 115
    near_stop = False

    for s in stops:
        if abs(bus_door_x - (s["x"] + 20)) < 250 and len(s["plist"]) > 0:
            near_stop = True
            if speed < 0.15 and not gas :
                doors = True
                s["served"] = True
                if not s["exited"]:
                    people -= people // 2
                    s["exited"] = True

            if doors:
                board_timer += 1
                if board_timer >= 15:
                    board_timer = 0
                    for p in s["plist"]:
                        if not p["go"]:
                            p["go"] = True
                            break
                for p in s["plist"][:]:
                    if p["go"]:
                        dx, dy = bus_door_x - p["x"], 192 - p["y"]
                        d = (dx**2 + dy**2)**0.5
                        if d < 7:
                            s["plist"].remove(p)
                            people += 1
                            money += 35
                        else:
                            p["x"] += (dx / d) * 3.0
                            p["y"] += (dy / d) * 3.0
                            p["step"] += 0.4


    same_lane = [c for c in cars if c["dir"] == 1]
    for c in cars:
        if c["dir"] == 1:
            ahead = [o["x"] - c["x"] for o in same_lane if 0 < o["x"] - c["x"] < 140]
            c["x"] += min(c["v"], 4.8) if ahead else c["v"]
        else:
            c["x"] += c["v"]
        cx = c["x"] - dist + 100
        if cx < -200 or cx > 1400:
            active = [o["x"] for o in cars if o["dir"] == c["dir"] and o is not c and -200 <= (o["x"] - dist + 100) <= 1400]
            c["x"] = max(active + [dist + 920]) + random.randint(350, 600)
            c["c"] = random.choice(car_colors)
            if c["dir"] == 1:
                c["v"] = random.uniform(4.8, 9.0)
        cx = c["x"] - dist + 100
        if c["dir"] == 1 and 100 < cx + 80 and 235 > cx:
            speed = 0.0; money = max(0, money - 25); c["x"] += 160; alert_text = " | ДТП (-25р)"; alert_timer = 90
    draw_all()
    msg = alert_text if alert_timer > 0 else (" | Посадка..." if (near_stop and doors) else "")
    label.config(text=f"Деньги: {money}р | Пассажиры: {people} | {int(speed*10)} км/ч{msg}")
    root.after(16, loop)

canvas.focus_force()
loop()
root.mainloop()
