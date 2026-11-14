import json
import os
import tkinter as tk
from tkinter import messagebox, simpledialog

WIDTH, HEIGHT = 900, 480
GRID = 40
FLOOR_Y = HEIGHT - GRID
FPS_MS = 16

GRAVITY = 0.85
JUMP_FORCE = -13.5
SPEED = 6.5

LEVELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels.json")


def get_default_levels():
    return {
        "Стартовый уровень": {
            "8,10": "spike",
            "13,10": "block", "14,10": "block", "14,9": "spike",
            "19,10": "block", "20,10": "block", "20,9": "block",
            "21,10": "block", "21,9": "block", "21,8": "block",
            "25,10": "spike", "26,10": "spike",
            "31,10": "goal",
        }
    }


class CubeDashApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cube Dash Maker")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        self.saved_levels = self.load_levels_from_disk()
        self.current_level_name = "Новый уровень"

        self.screen_state = "menu"  # "menu", "edit", "play"
        self.tool = "move"
        self.camera_x = 0.0
        self.won = False
        self.dead_timer = 0

        self.keys = set()
        self.mouse_down = False
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
        for k, v in raw_dict.items():
            gx, gy = map(int, k.split(","))
            res[(gx, gy)] = v
        return res

    def serialize_level(self, level_dict):
        return {f"{gx},{gy}": v for (gx, gy), v in level_dict.items()}

    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # ================= ГЛАВНОЕ МЕНЮ =================
    def show_menu(self):
        self.screen_state = "menu"
        self.dragging_obj = None
        self.mouse_down = False
        self.clear_container()

        menu_frame = tk.Frame(self.main_container, bg="#161626", width=WIDTH, height=HEIGHT + 46)
        menu_frame.pack_propagate(False)
        menu_frame.pack()

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

        # Контейнер списка уровней со скроллом
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
        self.level = {(20, 10): "goal"}
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

    # ================= ЭКРАН ИГРЫ И РЕДАКТОРА =================
    def open_game_screen(self, start_mode="edit"):
        self.clear_container()
        self.screen_state = start_mode
        self.camera_x = 0.0
        self.won = False

        toolbar = tk.Frame(self.main_container, bg="#1e1e2e", pady=7, padx=8)
        toolbar.pack(fill=tk.X)

        self.tool_buttons = {}
        tools = (
            ("move", "Двигать"),
            ("block", "Блок"),
            ("spike", "Шип"),
            ("goal", "Финиш"),
            ("erase", "Ластик"),
        )

        for tid, label in tools:
            btn = tk.Button(
                toolbar,
                text=label,
                font=("Sans", 9, "bold"),
                bg="#2b2b40",
                fg="white",
                relief=tk.FLAT,
                padx=8,
                pady=4,
                command=lambda t=tid: self.set_tool(t),
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.tool_buttons[tid] = btn

        self.clear_btn = tk.Button(
            toolbar,
            text="Очистить",
            font=("Sans", 9, "bold"),
            bg="#2b2b40",
            fg="white",
            relief=tk.FLAT,
            padx=8,
            pady=4,
            command=self.clear_level,
        )
        self.clear_btn.pack(side=tk.LEFT, padx=2)

        self.publish_btn = tk.Button(
            toolbar,
            text="Выложить",
            font=("Sans", 9, "bold"),
            bg="#6c5ce7",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self.publish_level,
        )
        self.publish_btn.pack(side=tk.LEFT, padx=(8, 2))

        # Кнопка паузы / выхода в главное меню
        self.menu_btn = tk.Button(
            toolbar,
            text="Меню (Esc)",
            font=("Sans", 9, "bold"),
            bg="#d63031",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self.show_menu,
        )
        self.menu_btn.pack(side=tk.RIGHT, padx=2)

        self.play_btn = tk.Button(
            toolbar,
            text="ИГРАТЬ",
            font=("Sans", 9, "bold"),
            bg="#00b894",
            fg="#12121a",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            command=self.toggle_mode,
        )
        self.play_btn.pack(side=tk.RIGHT, padx=4)

        self.canvas = tk.Canvas(
            self.main_container,
            width=WIDTH,
            height=HEIGHT,
            bg="#161626",
            highlightthickness=0,
        )
        self.canvas.pack()

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
            self.play_btn.configure(text="ИГРАТЬ", bg="#00b894")
        else:
            self.play_btn.configure(text="РЕДАКТОР", bg="#ff7675")

    def set_tool(self, tool):
        if self.screen_state == "edit":
            self.tool = tool
            self.sync_toolbar_state()

    def clear_level(self):
        if self.screen_state == "edit":
            self.level.clear()
            self.camera_x = 0.0

    def reset_player(self):
        self.player = {
            "x": 80.0,
            "y": float(FLOOR_Y - GRID),
            "vy": 0.0,
            "grounded": True,
            "dead": False,
        }
        self.camera_x = 0.0
        self.won = False
        self.dead_timer = 0

    def toggle_mode(self):
        if self.screen_state == "edit":
            self.screen_state = "play"
            self.dragging_obj = None
            self.reset_player()
        elif self.screen_state == "play":
            self.screen_state = "edit"
            self.camera_x = 0.0
            self.won = False
        self.sync_toolbar_state()

    def bind_events(self):
        self.root.bind("<KeyPress>", self.on_key_down)
        self.root.bind("<KeyRelease>", self.on_key_up)

    def on_key_down(self, event):
        key = event.keysym.lower()
        self.keys.add(key)
        if key == "escape" and self.screen_state in ("edit", "play"):
            self.show_menu()
        elif key == "space" and self.screen_state == "play" and self.won:
            self.reset_player()

    def on_key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def screen_to_grid(self, mx, my):
        return int((mx + self.camera_x) // GRID), int(my // GRID)

    def is_valid_cell(self, gx, gy):
        max_gy = (FLOOR_Y // GRID) - 1
        if gx < 0 or gy < 0 or gy > max_gy:
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
            return

        if self.won:
            return

        if self.player["dead"]:
            self.dead_timer += FPS_MS
            if self.dead_timer >= 300:
                self.reset_player()
            return

        jump = ("space" in self.keys) or self.mouse_down
        if jump and self.player["grounded"]:
            self.player["vy"] = JUMP_FORCE
            self.player["grounded"] = False

        self.player["x"] += SPEED
        px, py = self.player["x"], self.player["y"]
        p_box = (px + 3, py + 3, px + GRID - 3, py + GRID - 3)

        for (gx, gy), obj in self.level.items():
            if obj == "block":
                b_box = (gx * GRID, gy * GRID, (gx + 1) * GRID, (gy + 1) * GRID)
                if self.rects_collide(p_box, b_box):
                    self.player["dead"] = True
                    return

        self.player["vy"] += GRAVITY
        self.player["y"] += self.player["vy"]
        self.player["grounded"] = False

        if self.player["y"] + GRID >= FLOOR_Y:
            self.player["y"] = float(FLOOR_Y - GRID)
            self.player["vy"] = 0.0
            self.player["grounded"] = True

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
                        self.player["dead"] = True
                        return
            elif obj == "spike":
                s_box = (ox + 12, oy + 14, ox + GRID - 12, oy + GRID)
                if self.rects_collide(p_box, s_box):
                    self.player["dead"] = True
                    return
            elif obj == "goal":
                g_box = (ox, oy, ox + GRID, oy + GRID)
                if self.rects_collide(p_box, g_box):
                    self.won = True
                    return

        self.camera_x = max(0.0, self.player["x"] - 180)

    def draw_object(self, sx, sy, obj, highlight=False):
        if obj == "block":
            outline = "#00ffcc" if highlight else "#74b9ff"
            self.canvas.create_rectangle(
                sx, sy, sx + GRID, sy + GRID,
                fill="#2d3436", outline=outline, width=2
            )
        elif obj == "spike":
            outline = "#00ffcc" if highlight else "white"
            self.canvas.create_polygon(
                sx + GRID / 2, sy + 4,
                sx + GRID - 3, sy + GRID,
                sx + 3, sy + GRID,
                fill="#ff4757", outline=outline, width=1.5
            )
        elif obj == "goal":
            self.canvas.create_rectangle(
                sx, sy, sx + GRID, sy + GRID,
                fill="#165b54", outline="#00ffcc", width=2
            )
            self.canvas.create_text(
                sx + GRID / 2, sy + GRID / 2,
                text="ФИНИШ", fill="#00ffcc", font=("Sans", 7, "bold")
            )

    def draw(self):
        if self.screen_state == "menu":
            return

        self.canvas.delete("all")
        cx = self.camera_x

        if self.screen_state == "edit":
            start_col = int(cx // GRID)
            end_col = start_col + (WIDTH // GRID) + 2
            for c in range(start_col, end_col):
                x = c * GRID - cx
                self.canvas.create_line(x, 0, x, FLOOR_Y, fill="#25253d")
            for r in range(1, FLOOR_Y // GRID + 1):
                y = r * GRID
                self.canvas.create_line(0, y, WIDTH, y, fill="#25253d")

            self.canvas.create_rectangle(
                80 - cx, FLOOR_Y - GRID, 80 - cx + GRID, FLOOR_Y,
                outline="#00ffcc", width=2
            )

        self.canvas.create_rectangle(0, FLOOR_Y, WIDTH, HEIGHT, fill="#0f0f1a", outline="")
        self.canvas.create_line(0, FLOOR_Y, WIDTH, FLOOR_Y, fill="#00ffcc", width=2)

        for (gx, gy), obj in self.level.items():
            sx = gx * GRID - cx
            sy = gy * GRID
            if sx + GRID < 0 or sx > WIDTH:
                continue
            self.draw_object(sx, sy, obj)

        if self.screen_state == "edit" and self.dragging_obj is not None:
            mx, my = self.drag_mouse_pos
            gx, gy = self.screen_to_grid(mx, my)
            if self.is_valid_cell(gx, gy) and (gx, gy) not in self.level:
                snap_x = gx * GRID - cx
                snap_y = gy * GRID
                self.canvas.create_rectangle(
                    snap_x, snap_y, snap_x + GRID, snap_y + GRID,
                    outline="#00ffcc", dash=(4, 4), width=2
                )
            self.draw_object(mx - GRID / 2, my - GRID / 2, self.dragging_obj, highlight=True)

        if self.screen_state == "play" and not self.player["dead"]:
            px = self.player["x"] - cx
            py = self.player["y"]
            self.canvas.create_rectangle(
                px, py, px + GRID, py + GRID,
                fill="#ffeaa7", outline="#fdcb6e", width=3
            )
            self.canvas.create_rectangle(px + 22, py + 10, px + 28, py + 16, fill="#2d3436", outline="")
            self.canvas.create_rectangle(px + 31, py + 10, px + 37, py + 16, fill="#2d3436", outline="")
            self.canvas.create_rectangle(px + 22, py + 22, px + 37, py + 26, fill="#2d3436", outline="")

            self.canvas.create_rectangle(WIDTH - 115, 10, WIDTH - 10, 40, fill="#1e1e2e", outline="#00ffcc", width=1.5)
            self.canvas.create_text(WIDTH - 62, 25, text="II ПАУЗА (Esc)", fill="white", font=("Sans", 9, "bold"))

        if self.won:
            self.canvas.create_rectangle(
                150, HEIGHT / 2 - 75, WIDTH - 150, HEIGHT / 2 + 75,
                fill="#12121a", outline="#00ffcc", width=3
            )
            self.canvas.create_text(
                WIDTH / 2, HEIGHT / 2 - 25,
                text="УРОВЕНЬ ПРОЙДЕН!",
                fill="#00ffcc", font=("Sans", 26, "bold")
            )
            self.canvas.create_text(
                WIDTH / 2, HEIGHT / 2 + 20,
                text="Пробел / ЛКМ — заново  |  Esc — в главное меню",
                fill="white", font=("Sans", 11)
            )

    def loop(self):
        self.update()
        self.draw()
        self.root.after(FPS_MS, self.loop)


root = tk.Tk()
app = CubeDashApp(root)
root.mainloop()
