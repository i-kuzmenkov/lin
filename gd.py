import json
import os
import tkinter as tk
from tkinter import messagebox, simpledialog

WIDTH, HEIGHT = 900, 480
GRID = 40
FLOOR_Y = HEIGHT - GRID
MAX_SKY_Y = -1200
FPS_MS = 16

GRAVITY = 0.85
JUMP_FORCE = -13.5
SPEED = 6.5

SHIP_THRUST = -0.75
SHIP_GRAVITY = 0.65
SHIP_MAX_VY = 7.5

LEVELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels.json")


def get_default_levels():
    return {
        "Стартовый уровень": {
            "8,10": "spike",
            "12,9": "orb_yellow",
            "14,10": "spike", "15,10": "spike",
            "18,10": "portal_ship",
            "23,10": "spike", "24,10": "spike", "25,10": "spike",
            "24,2": "block", "24,3": "block",
            "29,10": "portal_cube",
            "34,10": "spike",
            "39,10": "goal",
        }
    }


class CubeDashApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cube Dash Maker")
        self.root.configure(bg="#1e1e2e")
        self.is_fullscreen = True
        self.root.attributes("-fullscreen", True)
        self.root.update_idletasks()
        global WIDTH, HEIGHT, FLOOR_Y
        WIDTH = self.root.winfo_screenwidth()
        HEIGHT = self.root.winfo_screenheight() - 46
        FLOOR_Y = (HEIGHT // GRID) * GRID - GRID
        if FLOOR_Y < 240:
            FLOOR_Y = HEIGHT - GRID

        self.saved_levels = self.load_levels_from_disk()
        self.current_level_name = "Новый уровень"

        self.screen_state = "menu"
        self.tool = "move"
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.won = False
        self.dead_timer = 0

        self.keys = set()
        self.mouse_down = False
        self.jump_just_pressed = False
        self.used_orbs = set()

        self.dragging_obj = None
        self.drag_origin = None
        self.drag_mouse_pos = (0, 0)

        self.level = {}
        self.player = {
            "x": 80.0,
            "y": float(FLOOR_Y - GRID),
            "vy": 0.0,
            "grounded": True,
            "dead": False,
            "mode": "cube",
        }

        self.main_container = tk.Frame(self.root, bg="#161626")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.bind_events()
        self.show_menu()
        self.loop()

    def load_levels_from_disk(self):
        if os.path.exists(LEVELS_FILE):
            try:
                with open(LEVELS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and data:
                        return data
            except Exception:
                pass
        default_data = get_default_levels()
        self.save_levels_to_disk(default_data)
        return default_data

    def save_levels_to_disk(self, data=None):
        if data is None:
            data = self.saved_levels
        try:
            with open(LEVELS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", str(e))

    def deserialize_level(self, raw_dict):
        res = {}
        floor_row = (FLOOR_Y // GRID) - 1
        shift_y = floor_row - 10
        for k, v in raw_dict.items():
            gx, gy = map(int, k.split(","))
            res[(gx, gy + shift_y)] = v
        return res

    def serialize_level(self, level_dict):
        floor_row = (FLOOR_Y // GRID) - 1
        shift_y = 10 - floor_row
        return {f"{gx},{gy + shift_y}": v for (gx, gy), v in level_dict.items()}

    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def show_menu(self):
        self.screen_state = "menu"
        self.dragging_obj = None
        self.mouse_down = False
        self.clear_container()

        menu_frame = tk.Frame(self.main_container, bg="#161626", width=WIDTH, height=HEIGHT + 46)
        menu_frame.pack_propagate(False)
        menu_frame.pack()

        top_bar = tk.Frame(menu_frame, bg="#161626")
        top_bar.pack(fill=tk.X, padx=20, pady=(12, 0))
        tk.Button(
            top_bar, text="Закрыть игру", font=("Sans", 9, "bold"),
            bg="#d63031", fg="white", relief=tk.FLAT, padx=10, pady=4,
            command=self.root.destroy
        ).pack(side=tk.RIGHT)
        tk.Button(
            top_bar, text="Окно / Весь экран (F11)", font=("Sans", 9, "bold"),
            bg="#2b2b40", fg="#00ffcc", relief=tk.FLAT, padx=10, pady=4,
            command=self.toggle_fullscreen
        ).pack(side=tk.RIGHT, padx=8)

        tk.Label(
            menu_frame,
            text="CUBE DASH MAKER",
            font=("Sans", 30, "bold"),
            bg="#161626",
            fg="#00ffcc",
        ).pack(pady=(25, 5))

        tk.Label(
            menu_frame,
            text="Выбери выложенный уровень или создай свой в редакторе",
            font=("Sans", 11),
            bg="#161626",
            fg="#a0a0c0",
        ).pack(pady=(0, 15))

        tk.Button(
            menu_frame,
            text="+ СОЗДАТЬ НОВЫЙ УРОВЕНЬ",
            font=("Sans", 12, "bold"),
            bg="#00b894",
            fg="#12121a",
            activebackground="#00ffcc",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=self.create_new_level,
        ).pack(pady=(0, 20))

        list_wrapper = tk.Frame(menu_frame, bg="#1e1e2e", bd=2, relief=tk.FLAT)
        list_wrapper.pack(padx=120, fill=tk.BOTH, expand=True, pady=(0, 25))

        canvas_list = tk.Canvas(list_wrapper, bg="#1e1e2e", highlightthickness=0)
        scrollbar = tk.Scrollbar(list_wrapper, orient="vertical", command=canvas_list.yview)
        scroll_frame = tk.Frame(canvas_list, bg="#1e1e2e")

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas_list.configure(scrollregion=canvas_list.bbox("all")),
        )
        canvas_list.create_window((0, 0), window=scroll_frame, anchor="nw", width=635)
        canvas_list.configure(yscrollcommand=scrollbar.set)

        canvas_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for name in list(self.saved_levels.keys()):
            row = tk.Frame(scroll_frame, bg="#2b2b40", pady=8, padx=12)
            row.pack(fill=tk.X, pady=4, padx=4)

            tk.Label(
                row,
                text=name,
                font=("Sans", 12, "bold"),
                bg="#2b2b40",
                fg="white",
            ).pack(side=tk.LEFT)

            if name != "Стартовый уровень":
                tk.Button(
                    row,
                    text="Удалить",
                    font=("Sans", 9, "bold"),
                    bg="#d63031",
                    fg="white",
                    relief=tk.FLAT,
                    padx=8,
                    pady=3,
                    command=lambda n=name: self.delete_level(n),
                ).pack(side=tk.RIGHT, padx=(6, 0))

            tk.Button(
                row,
                text="Редактор",
                font=("Sans", 9, "bold"),
                bg="#0984e3",
                fg="white",
                relief=tk.FLAT,
                padx=10,
                pady=3,
                command=lambda n=name: self.open_level_in_editor(n),
            ).pack(side=tk.RIGHT, padx=(6, 0))

            tk.Button(
                row,
                text="ИГРАТЬ",
                font=("Sans", 9, "bold"),
                bg="#00b894",
                fg="#12121a",
                relief=tk.FLAT,
                padx=12,
                pady=3,
                command=lambda n=name: self.play_saved_level(n),
            ).pack(side=tk.RIGHT)

    def delete_level(self, name):
        if messagebox.askyesno("Удаление", f"Удалить уровень «{name}» из меню?"):
            self.saved_levels.pop(name, None)
            self.save_levels_to_disk()
            self.show_menu()

    def create_new_level(self):
        self.current_level_name = "Новый уровень"
        self.level = {(20, (FLOOR_Y // GRID) - 1): "goal"}
        self.open_game_screen(start_mode="edit")

    def open_level_in_editor(self, name):
        self.current_level_name = name
        self.level = self.deserialize_level(self.saved_levels[name])
        self.open_game_screen(start_mode="edit")

    def play_saved_level(self, name):
        self.current_level_name = name
        self.level = self.deserialize_level(self.saved_levels[name])
        self.open_game_screen(start_mode="play")

    def publish_level(self):
        if "goal" not in self.level.values():
            messagebox.showwarning("Нет финиша", "Поставь блок ФИНИШ на уровень перед публикацией!")
            return
        initial = "" if self.current_level_name == "Новый уровень" else self.current_level_name
        name = simpledialog.askstring(
            "Выложить уровень",
            "Введи название уровня для главного меню:",
            initialvalue=initial,
            parent=self.root,
        )
        if name and name.strip():
            clean_name = name.strip()
            self.current_level_name = clean_name
            self.saved_levels[clean_name] = self.serialize_level(self.level)
            self.save_levels_to_disk()
            messagebox.showinfo("Готово!", f"Уровень «{clean_name}» выложен в главное меню!")

    def open_game_screen(self, start_mode="edit"):
        self.clear_container()
        self.screen_state = start_mode
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.won = False

        toolbar = tk.Frame(self.main_container, bg="#1e1e2e", pady=7, padx=6)
        toolbar.pack(fill=tk.X)

        self.tool_buttons = {}
        tools = (
            ("move", "Двигать"),
            ("block", "Блок"),
            ("spike", "Шип"),
            ("orb_yellow", "Сфера"),
            ("pad_yellow", "Батут"),
            ("portal_ship", "Самолёт"),
            ("portal_cube", "Куб"),
            ("goal", "Финиш"),
            ("erase", "Ластик"),
        )

        for tid, label in tools:
            btn = tk.Button(
                toolbar,
                text=label,
                font=("Sans", 8, "bold"),
                bg="#2b2b40",
                fg="white",
                relief=tk.FLAT,
                padx=5,
                pady=4,
                command=lambda t=tid: self.set_tool(t),
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.tool_buttons[tid] = btn

        self.clear_btn = tk.Button(
            toolbar,
            text="Очистить",
            font=("Sans", 8, "bold"),
            bg="#2b2b40",
            fg="white",
            relief=tk.FLAT,
            padx=5,
            pady=4,
            command=self.clear_level,
        )
        self.clear_btn.pack(side=tk.LEFT, padx=2)

        self.publish_btn = tk.Button(
            toolbar,
            text="Выложить",
            font=("Sans", 8, "bold"),
            bg="#6c5ce7",
            fg="white",
            relief=tk.FLAT,
            padx=7,
            pady=4,
            command=self.publish_level,
        )
        self.publish_btn.pack(side=tk.LEFT, padx=(5, 2))

        self.menu_btn = tk.Button(
            toolbar,
            text="Меню (Esc)",
            font=("Sans", 8, "bold"),
            bg="#d63031",
            fg="white",
            relief=tk.FLAT,
            padx=7,
            pady=4,
            command=self.show_menu,
        )
        self.menu_btn.pack(side=tk.RIGHT, padx=2)

        self.play_btn = tk.Button(
            toolbar,
            text="ИГРАТЬ",
            font=("Sans", 8, "bold"),
            bg="#00b894",
            fg="#12121a",
            relief=tk.FLAT,
            padx=9,
            pady=4,
            command=self.toggle_mode,
        )
        self.play_btn.pack(side=tk.RIGHT, padx=3)

        self.canvas = tk.Canvas(
            self.main_container,
            width=WIDTH,
            height=HEIGHT,
            bg="#161626",
            highlightthickness=0,
        )
        self.canvas.pack()
        self.jump_btn = tk.Button(
            self.main_container, text="ПРЫЖОК", font=("Sans", 14, "bold"),
            bg="#1d4d4f", fg="#00ffcc", activebackground="#00ffcc", activeforeground="#12121a",
            relief=tk.RAISED, bd=3
        )
        self.jump_btn.bind("<ButtonPress-1>", lambda e: (setattr(self, "jump_just_pressed", True), setattr(self, "mouse_down", True), self.reset_player() if self.won else None))
        self.jump_btn.bind("<ButtonRelease-1>", lambda e: setattr(self, "mouse_down", False))

        self.canvas.bind("<ButtonPress-1>", self.on_left_down)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_up)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonPress-2>", self.on_middle_down)
        self.canvas.bind("<B2-Motion>", self.on_drag_move)
        self.canvas.bind("<ButtonRelease-2>", self.on_drag_release)
        self.canvas.bind("<ButtonPress-3>", self.on_right_down)
        self.canvas.bind("<B3-Motion>", self.on_right_down)

        if start_mode == "play":
            self.reset_player()
        self.sync_toolbar_state()

    def sync_toolbar_state(self):
        is_edit = self.screen_state == "edit"
        for tid, btn in self.tool_buttons.items():
            if is_edit:
                btn.configure(state=tk.NORMAL)
                if tid == self.tool:
                    btn.configure(bg="#1d4d4f", fg="#00ffcc")
                else:
                    btn.configure(bg="#2b2b40", fg="white")
            else:
                btn.configure(state=tk.DISABLED, bg="#1e1e2e", fg="#555570")

        self.clear_btn.configure(state=tk.NORMAL if is_edit else tk.DISABLED)
        self.publish_btn.configure(state=tk.NORMAL if is_edit else tk.DISABLED)

        if is_edit:
            self.jump_btn.place_forget()
            self.play_btn.configure(text="ИГРАТЬ", bg="#00b894")
        else:
            self.jump_btn.place(x=WIDTH - 165, y=HEIGHT - 45, width=150, height=75)
            self.play_btn.configure(text="РЕДАКТОР", bg="#ff7675")

    def set_tool(self, tool):
        if self.screen_state == "edit":
            self.tool = tool
            self.sync_toolbar_state()

    def clear_level(self):
        if self.screen_state == "edit":
            self.level.clear()
            self.camera_x = 0.0
            self.camera_y = 0.0

    def reset_player(self):
        self.player = {
            "x": 80.0,
            "y": float(FLOOR_Y - GRID),
            "vy": 0.0,
            "grounded": True,
            "dead": False,
            "mode": "cube",
        }
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.won = False
        self.dead_timer = 0
        self.used_orbs.clear()
        self.jump_just_pressed = False

    def toggle_mode(self):
        if self.screen_state == "edit":
            self.screen_state = "play"
            self.dragging_obj = None
            self.reset_player()
        elif self.screen_state == "play":
            self.screen_state = "edit"
            self.camera_x = 0.0
            self.camera_y = 0.0
            self.won = False
        self.sync_toolbar_state()

    def bind_events(self):
        self.root.bind("<KeyPress>", self.on_key_down)
        self.root.bind("<KeyRelease>", self.on_key_up)

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)

    def on_key_down(self, event):
        key = event.keysym.lower()
        if key == "f11":
            self.toggle_fullscreen()
            return
        if key == "space" and "space" not in self.keys:
            self.jump_just_pressed = True
        self.keys.add(key)
        if key == "escape" and self.screen_state in ("edit", "play"):
            self.show_menu()
        elif key == "space" and self.screen_state == "play" and self.won:
            self.reset_player()

    def on_key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def screen_to_grid(self, mx, my):
        return int((mx + self.camera_x) // GRID), int((my + self.camera_y) // GRID)

    def is_valid_cell(self, gx, gy):
        max_gy = (FLOOR_Y // GRID) - 1
        min_gy = MAX_SKY_Y // GRID
        if gx < 0 or gy < min_gy or gy > max_gy:
            return False
        if gx == 2 and gy == max_gy:
            return False
        return True

    def start_drag(self, mx, my):
        gx, gy = self.screen_to_grid(mx, my)
        if (gx, gy) in self.level:
            self.dragging_obj = self.level.pop((gx, gy))
            self.drag_origin = (gx, gy)
            self.drag_mouse_pos = (mx, my)

    def on_drag_move(self, event):
        if self.screen_state == "edit" and self.dragging_obj is not None:
            self.drag_mouse_pos = (event.x, event.y)

    def on_drag_release(self, event):
        if self.screen_state == "edit" and self.dragging_obj is not None:
            gx, gy = self.screen_to_grid(event.x, event.y)
            if self.is_valid_cell(gx, gy) and (gx, gy) not in self.level:
                self.level[(gx, gy)] = self.dragging_obj
            else:
                self.level[self.drag_origin] = self.dragging_obj
            self.dragging_obj = None
            self.drag_origin = None

    def on_left_down(self, event):
        if self.screen_state == "edit":
            self.mouse_down = True
        if self.screen_state == "edit":
            if self.tool == "move":
                self.start_drag(event.x, event.y)
            else:
                self.edit_cell(event.x, event.y, erase=False)
        elif self.screen_state == "play" and self.won:
            self.reset_player()

    def on_left_drag(self, event):
        if self.screen_state == "edit" and self.mouse_down:
            if self.tool == "move":
                self.on_drag_move(event)
            else:
                self.edit_cell(event.x, event.y, erase=False)

    def on_left_up(self, event):
        self.mouse_down = False
        if self.screen_state == "edit" and self.tool == "move":
            self.on_drag_release(event)

    def on_middle_down(self, event):
        if self.screen_state == "edit":
            self.start_drag(event.x, event.y)

    def on_right_down(self, event):
        if self.screen_state == "edit" and self.dragging_obj is None:
            self.edit_cell(event.x, event.y, erase=True)

    def edit_cell(self, mx, my, erase=False):
        gx, gy = self.screen_to_grid(mx, my)
        if not self.is_valid_cell(gx, gy):
            return
        if erase or self.tool == "erase":
            self.level.pop((gx, gy), None)
        else:
            self.level[(gx, gy)] = self.tool

    @staticmethod
    def rects_collide(r1, r2):
        ax1, ay1, ax2, ay2 = r1
        bx1, by1, bx2, by2 = r2
        return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1

    def update(self):
        if self.screen_state == "menu":
            return

        if self.screen_state == "edit":
            if "right" in self.keys or "d" in self.keys:
                self.camera_x += 10
            if "left" in self.keys or "a" in self.keys:
                self.camera_x = max(0.0, self.camera_x - 10)
            if "up" in self.keys or "w" in self.keys:
                self.camera_y = max(float(MAX_SKY_Y), self.camera_y - 10)
            if "down" in self.keys or "s" in self.keys:
                self.camera_y = min(0.0, self.camera_y + 10)
            return

        if self.won:
            self.jump_just_pressed = False
            return

        if self.player["dead"]:
            self.dead_timer += FPS_MS
            if self.dead_timer >= 300:
                self.reset_player()
            self.jump_just_pressed = False
            return

        action_pressed = ("space" in self.keys) or self.mouse_down

        # Проверка активации жёлтой сферы в воздухе на кубе
        if self.player["mode"] == "cube" and self.jump_just_pressed:
            px, py = self.player["x"], self.player["y"]
            orb_p_box = (px - 14, py - 14, px + GRID + 14, py + GRID + 14)
            for (gx, gy), obj in self.level.items():
                if obj == "orb_yellow" and (gx, gy) not in self.used_orbs:
                    o_box = (gx * GRID, gy * GRID, (gx + 1) * GRID, (gy + 1) * GRID)
                    if self.rects_collide(orb_p_box, o_box):
                        self.player["vy"] = JUMP_FORCE
                        self.player["grounded"] = False
                        self.used_orbs.add((gx, gy))
                        break

        if self.player["mode"] == "cube":
            if action_pressed and self.player["grounded"]:
                self.player["vy"] = JUMP_FORCE
                self.player["grounded"] = False
            self.player["vy"] += GRAVITY
        else:
            if action_pressed:
                self.player["vy"] += SHIP_THRUST
            else:
                self.player["vy"] += SHIP_GRAVITY
            self.player["vy"] = max(-SHIP_MAX_VY, min(SHIP_MAX_VY, self.player["vy"]))

        self.jump_just_pressed = False

        self.player["x"] += SPEED
        px, py = self.player["x"], self.player["y"]
        p_box = (px + 3, py + 3, px + GRID - 3, py + GRID - 3)

        for (gx, gy), obj in self.level.items():
            if obj == "block":
                b_box = (gx * GRID, gy * GRID, (gx + 1) * GRID, (gy + 1) * GRID)
                if self.rects_collide(p_box, b_box):
                    self.player["dead"] = True
                    return

        self.player["y"] += self.player["vy"]
        self.player["grounded"] = False

        if self.player["y"] + GRID >= FLOOR_Y:
            self.player["y"] = float(FLOOR_Y - GRID)
            self.player["vy"] = 0.0
            self.player["grounded"] = True

        if self.player["y"] < MAX_SKY_Y:
            self.player["y"] = float(MAX_SKY_Y)
            if self.player["vy"] < 0:
                self.player["vy"] = 0.0

        px, py = self.player["x"], self.player["y"]
        p_box = (px + 3, py, px + GRID - 3, py + GRID)

        for (gx, gy), obj in self.level.items():
            ox, oy = gx * GRID, gy * GRID
            if obj == "block":
                b_box = (ox, oy, ox + GRID, oy + GRID)
                if self.rects_collide(p_box, b_box):
                    if self.player["vy"] > 0:
                        self.player["y"] = float(oy - GRID)
                        self.player["vy"] = 0.0
                        self.player["grounded"] = True
                    elif self.player["vy"] < 0:
                        if self.player["mode"] == "ship":
                            self.player["y"] = float(oy + GRID)
                            self.player["vy"] = 0.0
                        else:
                            self.player["dead"] = True
                            return
            elif obj == "pad_yellow":
                pad_box = (ox + 4, oy + GRID - 14, ox + GRID - 4, oy + GRID)
                if self.rects_collide(p_box, pad_box):
                    self.player["vy"] = JUMP_FORCE * 1.45
                    self.player["grounded"] = False
            elif obj == "spike":
                s_box = (ox + 12, oy + 14, ox + GRID - 12, oy + GRID)
                if self.rects_collide(p_box, s_box):
                    self.player["dead"] = True
                    return
            elif obj == "portal_ship":
                p_portal = (ox + 8, oy, ox + GRID - 8, oy + GRID)
                if self.rects_collide(p_box, p_portal):
                    self.player["mode"] = "ship"
            elif obj == "portal_cube":
                p_portal = (ox + 8, oy, ox + GRID - 8, oy + GRID)
                if self.rects_collide(p_box, p_portal):
                    self.player["mode"] = "cube"
            elif obj == "goal":
                g_box = (ox, oy, ox + GRID, oy + GRID)
                if self.rects_collide(p_box, g_box):
                    self.won = True
                    return

        self.camera_x = max(0.0, self.player["x"] - 180)
        target_cy = min(0.0, max(float(MAX_SKY_Y), self.player["y"] - HEIGHT * 0.45))
        self.camera_y += (target_cy - self.camera_y) * 0.15

    def draw_object(self, sx, sy, obj, highlight=False, used=False):
        if obj == "block":
            outline = "#00ffcc" if highlight else "#74b9ff"
            self.canvas.create_rectangle(sx, sy, sx + GRID, sy + GRID, fill="#2d3436", outline=outline, width=2)
        elif obj == "pad_yellow":
            self.canvas.create_arc(sx+3, sy+GRID-22, sx+GRID-3, sy+GRID+10, start=0, extent=180, fill="#ffd32a", outline="#fff200", width=2)
        elif obj == "spike":
            outline = "#00ffcc" if highlight else "white"
            self.canvas.create_polygon(sx + GRID / 2, sy + 4, sx + GRID - 3, sy + GRID, sx + 3, sy + GRID, fill="#ff4757", outline=outline, width=1.5)
        elif obj == "orb_yellow":
            fill_c = "#635a24" if used else "#ffd32a"
            ring_c = "#00ffcc" if highlight else ("#807840" if used else "#fff200")
            self.canvas.create_oval(sx - 6, sy - 6, sx + GRID + 6, sy + GRID + 6, outline=ring_c, width=3)
            self.canvas.create_oval(sx + 1, sy + 1, sx + GRID - 1, sy + GRID - 1, fill=fill_c, outline="")
        elif obj == "portal_ship":
            self.canvas.create_oval(sx + 6, sy + 2, sx + GRID - 6, sy + GRID - 2, fill="#4a154b", outline="#ff6b81", width=3)
            self.canvas.create_text(sx + GRID / 2, sy + GRID / 2, text="САМ", fill="#ff6b81", font=("Sans", 7, "bold"))
        elif obj == "portal_cube":
            self.canvas.create_oval(sx + 6, sy + 2, sx + GRID - 6, sy + GRID - 2, fill="#0b4619", outline="#2ed573", width=3)
            self.canvas.create_text(sx + GRID / 2, sy + GRID / 2, text="КУБ", fill="#2ed573", font=("Sans", 7, "bold"))
        elif obj == "goal":
            self.canvas.create_rectangle(sx, sy, sx + GRID, sy + GRID, fill="#165b54", outline="#00ffcc", width=2)
            self.canvas.create_text(sx + GRID / 2, sy + GRID / 2, text="ФИНИШ", fill="#00ffcc", font=("Sans", 7, "bold"))

    def draw_player(self, px, py):
        if self.player["mode"] == "cube":
            self.canvas.create_rectangle(px, py, px + GRID, py + GRID, fill="#ffeaa7", outline="#fdcb6e", width=3)

            self.canvas.create_rectangle(px + 22, py + 10, px + 28, py + 16, fill="#2d3436", outline="")
            self.canvas.create_rectangle(px + 31, py + 10, px + 37, py + 16, fill="#2d3436", outline="")
            self.canvas.create_rectangle(px + 22, py + 22, px + 37, py + 26, fill="#2d3436", outline="")
        else:
            tilt = self.player["vy"] * 1.4
            self.canvas.create_polygon(px + 2, py + 22 - tilt * 0.4, px + 12, py + 36, px + 34, py + 36, px + GRID, py + 24 + tilt, px + 24, py + 18 + tilt * 0.5, fill="#ff6b81", outline="white", width=2)
            self.canvas.create_rectangle(px + 14, py + 10 + tilt * 0.3, px + 28, py + 24 + tilt * 0.3, fill="#ffeaa7", outline="#fdcb6e", width=2)

    def draw(self):
        if self.screen_state == "menu":
            return
        self.canvas.delete("all")
        cx, cy = self.camera_x, self.camera_y

        if self.screen_state == "edit":
            for c in range(int(cx // GRID), int(cx // GRID) + (WIDTH // GRID) + 2):
                self.canvas.create_line(c * GRID - cx, 0, c * GRID - cx, HEIGHT, fill="#25253d")
            for r in range(int(cy // GRID) - 1, int(cy // GRID) + (HEIGHT // GRID) + 3):
                self.canvas.create_line(0, r * GRID - cy, WIDTH, r * GRID - cy, fill="#25253d")
            self.canvas.create_rectangle(80 - cx, FLOOR_Y - GRID - cy, 80 - cx + GRID, FLOOR_Y - cy, outline="#00ffcc", width=2)

        floor_screen_y = FLOOR_Y - cy
        if floor_screen_y < HEIGHT:
            self.canvas.create_rectangle(0, floor_screen_y, WIDTH, HEIGHT, fill="#0f0f1a", outline="")
            self.canvas.create_line(0, floor_screen_y, WIDTH, floor_screen_y, fill="#00ffcc", width=2)

        for (gx, gy), obj in self.level.items():
            sx, sy = gx * GRID - cx, gy * GRID - cy
            if sx + GRID < 0 or sx > WIDTH or sy + GRID < 0 or sy > HEIGHT:
                continue
            self.draw_object(sx, sy, obj, used=((gx, gy) in self.used_orbs))

        if self.screen_state == "edit" and self.dragging_obj is not None:
            mx, my = self.drag_mouse_pos
            self.draw_object(mx - GRID / 2, my - GRID / 2, self.dragging_obj, highlight=True)

        if self.screen_state == "play" and not self.player["dead"]:
            self.draw_player(self.player["x"] - cx, self.player["y"] - cy)

        if self.won:
            self.canvas.create_rectangle(150, HEIGHT / 2 - 75, WIDTH - 150, HEIGHT / 2 + 75, fill="#12121a", outline="#00ffcc", width=3)
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 25, text="УРОВЕНЬ ПРОЙДЕН!", fill="#00ffcc", font=("Sans", 26, "bold"))
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 20, text="Пробел / ЛКМ — заново  |  Esc — в главное меню", fill="white", font=("Sans", 11))

    def loop(self):
        self.update()
        self.draw()
        self.root.after(FPS_MS, self.loop)


root = tk.Tk()
app = CubeDashApp(root)
root.mainloop()
