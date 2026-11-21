import demo_level_mod
import build_mod
import obj_ctrl_mod
import tilt_mod
import modes_mod
import pack_mod
import creator_mod
import respect_mod
import bee_mod
import move_mod
import wheel_mod
import preview_mod
import speed_mod
import practice_mod
import shop_mod
import json
import os
import tkinter as tk
from tkinter import colorchooser, messagebox, simpledialog

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

        self.saved_levels = self.load_levels_from_disk(); self.shop_data = shop_mod.load_shop(); self.got_coins = set(); practice_mod.init_practice(self); move_mod.init_move(self); respect_mod.init_respect(self); pack_mod.init_packs(self); modes_mod.init_modes(self); build_mod.init_build(self); demo_level_mod.build_mega_demo(self, GRID, FLOOR_Y)
        self.current_level_name = "Новый уровень"

        self.screen_state = "menu"
        self.tool = "block"
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.won = False
        self.bg_color = "#161626"
        self.bg_palette = ["#2c1638", "#3b141c", "#11382d", "#132a4a", "#161626"]
        self.bg_idx = 0
        self.dead_timer = 0; self._tick = 0

        self.keys = set()
        self.mouse_down = False
        self.jump_just_pressed = False
        self.used_orbs = set()

        self.dragging_obj = None
        self.drag_origin = None
        self.drag_mouse_pos = (0, 0); self.hover_pos = (-100, -100)

        self.level = {}
        self.player = {
            "x": 80.0,
            "y": float(FLOOR_Y - GRID),
            "vy": 0.0,
            "grounded": True,
            "dead": False,
            "mode": "cube",
            "grav": 1, "speed_mult": 1.0,
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
        max_gy = max((int(k.split(",")[1]) for k in raw_dict), default=10)
        shift_y = (floor_row - max_gy) if max_gy > floor_row else (floor_row - 10)
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
        obj_ctrl_mod.close_panel(self)
        respect_mod.reset_respect(self)
        bee_mod.stop_bee_music(self)
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
        tk.Button(menu_frame, text=f"МАГАЗИН КУБИКОВ (Монеты: {self.shop_data['coins']})", font=("Sans", 11, "bold"), bg="#f39c12", fg="#12121a", relief=tk.FLAT, padx=18, pady=6, command=lambda: shop_mod.open_shop_ui(self)).pack(pady=(0, 15))
        tk.Button(menu_frame, text=f"РЕСУРСПАКИ ({self.active_pack})", font=("Sans", 10, "bold"), bg="#6c5ce7", fg="white", relief=tk.FLAT, padx=16, pady=5, command=lambda: pack_mod.open_packs_ui(self)).pack(pady=(0, 12))
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
            practice_mod.toggle_pause(self)

    def create_new_level(self):
        creator_mod.open_creator_dialog(self, GRID, FLOOR_Y)
        return
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
        self.bg_color = "#161626"
        self.bg_palette = ["#2c1638", "#3b141c", "#11382d", "#132a4a", "#161626"]
        self.bg_idx = 0

        toolbar = tk.Frame(self.main_container, bg="#1e1e2e", pady=7, padx=6)
        toolbar.pack(fill=tk.X)

        self.tool_buttons = {}
        self.cur_tool_lbl = tk.Label(toolbar, text="Предмет (колёсико): Блок", font=("Sans", 10, "bold"), bg="#1d4d4f", fg="#00ffcc", padx=12, pady=4)
        self.cur_tool_lbl.pack(side=tk.LEFT, padx=4)
        self.bg_col_btn = tk.Button(toolbar, text="Цвет фона", font=("Sans", 8, "bold"), bg="#2b2b40", fg="#00ffcc", relief=tk.FLAT, padx=8, pady=4, command=lambda: wheel_mod.pick_bg_color(self))
        self.bg_col_btn.pack(side=tk.LEFT, padx=2)
        self.pe_btn = tk.Button(toolbar, text="PE: ВКЛ 🐝", font=("Sans", 9, "bold"), bg="#f39c12", fg="#12121a", relief=tk.FLAT, padx=8, pady=4, command=self.toggle_pe)
        self.pe_btn.pack(side=tk.LEFT, padx=4)
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
            command=lambda: practice_mod.toggle_pause(self),
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
        self.jump_btn.bind("<ButtonPress-1>", lambda e: (setattr(self, "jump_just_pressed", True), setattr(self, "mouse_down", True), (self.checkpoints.clear(), self.reset_player()) if self.won else None))
        self.jump_btn.bind("<ButtonRelease-1>", lambda e: setattr(self, "mouse_down", False))

        self.canvas.bind("<ButtonPress-1>", self.on_left_down)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_up)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<Motion>", lambda e: setattr(self, "hover_pos", (e.x, e.y)))
        self.canvas.bind("<ButtonPress-2>", self.on_middle_down)
        self.canvas.bind("<B2-Motion>", self.on_drag_move)
        self.canvas.bind("<ButtonRelease-2>", self.on_drag_release)
        self.canvas.bind("<Shift-ButtonPress-1>", lambda e: setattr(self, "_fill_c1", self.screen_to_grid(e.x, e.y)))
        self.canvas.bind("<Shift-ButtonRelease-1>", lambda e: build_mod.fill_rect(self, getattr(self, "_fill_c1", (0,0)), self.screen_to_grid(e.x, e.y)))
        self.canvas.bind("<Alt-ButtonPress-1>", lambda e: (setattr(self, "sel_start", self.screen_to_grid(e.x, e.y)), setattr(self, "sel_end", self.screen_to_grid(e.x, e.y))))
        self.canvas.bind("<Alt-B1-Motion>", lambda e: setattr(self, "sel_end", self.screen_to_grid(e.x, e.y)))
        self.canvas.bind("<ButtonPress-3>", self.on_right_down)
        self.canvas.bind("<B3-Motion>", self.on_right_down)
        self.canvas.bind("<Motion>", lambda e: setattr(self, "hover_pos", (e.x, e.y)))
        self.canvas.bind("<Button-4>", lambda e: wheel_mod.cycle_tool(self, -1))
        self.canvas.bind("<Button-5>", lambda e: wheel_mod.cycle_tool(self, 1))
        self.canvas.bind("<MouseWheel>", lambda e: wheel_mod.cycle_tool(self, -1 if e.delta > 0 else 1))

        if start_mode == "play":
            self.checkpoints.clear(); self.reset_player()
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

        self.bg_col_btn.configure(state=tk.NORMAL if (is_edit and self.tool == "bg_trigger") else tk.DISABLED)
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
        bee_mod.stop_bee_music(self)
        self.player = {
            "x": 80.0,
            "y": float(FLOOR_Y - GRID),
            "vy": 0.0,
            "grounded": True,
            "dead": False,
            "mode": "cube",
            "grav": 1, "speed_mult": 1.0,
        }
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.won = False
        self.bg_color = "#161626"
        self.bg_palette = ["#2c1638", "#3b141c", "#11382d", "#132a4a", "#161626"]
        self.bg_idx = 0
        self.dead_timer = 0; self._tick = 0
        self.used_orbs.clear(); self.got_coins.clear(); respect_mod.reset_respect(self)
        if hasattr(self, "_backup_lvl"): self.level = dict(self._backup_lvl)
        move_mod.reset_moves(self)
        self.tp_cooldown = 0
        self.bg_color = "#161626"
        self.jump_just_pressed = False

    def toggle_pe(self):
        self.pe_mode = not getattr(self, "pe_mode", True)
        self.pe_btn.configure(text="PE: ВКЛ 🐝" if self.pe_mode else "PE: ВЫКЛ", bg="#f39c12" if self.pe_mode else "#2b2b40", fg="#12121a" if self.pe_mode else "white")

    def toggle_mode(self):
        if self.screen_state == "edit":
            self.screen_state = "play"; self._backup_lvl = dict(self.level); self.attempt_num = 1; modes_mod.calc_goal_x(self, GRID)
            self.dragging_obj = None
            self.checkpoints.clear(); self.reset_player()
        elif self.screen_state == "play":
            self.screen_state = "edit"; self.level = dict(getattr(self, "_backup_lvl", self.level))
            if hasattr(self, "_backup_lvl"): self.level = dict(self._backup_lvl)
            move_mod.reset_moves(self)
            self.camera_x = 0.0
            self.camera_y = 0.0
            self.won = False
        self.bg_color = "#161626"
        self.bg_palette = ["#2c1638", "#3b141c", "#11382d", "#132a4a", "#161626"]
        self.bg_idx = 0
        self.sync_toolbar_state()

    def bind_events(self):
        self.root.bind("<KeyPress>", self.on_key_down)
        self.root.bind("<Control-z>", lambda e: build_mod.undo(self))
        self.root.bind("<Control-y>", lambda e: build_mod.redo(self))
        self.root.bind("<Control-c>", lambda e: build_mod.copy_selection(self))
        self.root.bind("<Control-v>", lambda e: build_mod.paste_selection(self))
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
        if key == "q" and self.screen_state == "edit": build_mod.eyedropper(self)
        elif key == "r" and self.screen_state == "edit": tilt_mod.rotate_at_cursor(self)
        elif key == "z" and self.screen_state == "play": practice_mod.save_checkpoint(self)
        elif key == "x" and self.screen_state == "play": practice_mod.delete_checkpoint(self)
        elif key == "escape" and self.screen_state in ("edit", "play"):
            practice_mod.toggle_pause(self)
        elif key == "space" and self.screen_state == "play" and self.won:
            self.checkpoints.clear(); self.reset_player()

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
            self.drag_mouse_pos = (event.x, event.y); self.hover_pos = (event.x, event.y)

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
            self.checkpoints.clear(); self.reset_player()

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
        if self.tool == "edit_obj":
            obj_ctrl_mod.open_obj_panel(self, gx, gy)
            return
        if self.tool == "link_trigger":
            move_mod.handle_link_click(self, gx, gy)
            return
        if self.tool in move_mod.MOVE_DIRS:
            self.level[(gx, gy)] = move_mod.ask_distance(self, self.tool)
            return
        if erase or self.tool == "erase":
            self.level.pop((gx, gy), None)
        elif self.tool == "bg_trigger":
            self.mouse_down = False
            picked = colorchooser.askcolor(title="Выбери цвет фона при входе в эту зону", color="#2c1638")
            _, col = picked if picked and picked else (0, None); col = col or self.bg_palette[self.bg_idx % len(self.bg_palette)]
            self.bg_idx += 1
            self.level[(gx, gy)] = f"bg:{col}"
        else:
            self.level[(gx, gy)] = self.tool

    @staticmethod
    def rects_collide(r1, r2):
        ax1, ay1, ax2, ay2 = r1
        bx1, by1, bx2, by2 = r2
        return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1

    def update(self):
        if self.screen_state == "menu" or getattr(self, "paused", False):
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
                self.attempt_num = getattr(self, "attempt_num", 1) + 1
                self.checkpoints.clear(); self.reset_player()
            self.jump_just_pressed = False
            return

        practice_mod.update_checkpoints(self, FPS_MS)
        respect_mod.update_respect(self, FPS_MS)
        move_mod.check_triggers(self, GRID); move_mod.update_moves(self)
        action_pressed = ("space" in self.keys) or self.mouse_down

        g = self.player.get("grav", 1)
        if self.player["mode"] == "cube" and action_pressed:
            px, py = self.player["x"], self.player["y"]
            orb_p_box = (px - 14, py - 14, px + GRID + 14, py + GRID + 14)
            for (gx, gy), raw_obj in self.level.items():
                obj, _ = tilt_mod.parse_tilt(raw_obj)
                if obj == "orb_yellow" and (gx, gy) not in self.used_orbs:
                    o_box = (gx * GRID, gy * GRID, (gx + 1) * GRID, (gy + 1) * GRID)
                    if self.rects_collide(orb_p_box, o_box):
                        self.player["vy"] = JUMP_FORCE * g
                        self.player["grounded"] = False
                        self.used_orbs.add((gx, gy))
                        break

        if modes_mod.step_extra_physics(self, action_pressed, self.jump_just_pressed, SPEED, JUMP_FORCE, GRAVITY):
            pass
        elif self.player["mode"] == "cube":
            if action_pressed and self.player["grounded"]:
                self.player["vy"] = JUMP_FORCE * g
                self.player["grounded"] = False
            self.player["vy"] += GRAVITY * g
        else:
            if action_pressed:
                self.player["vy"] += SHIP_THRUST * g
            else:
                self.player["vy"] += SHIP_GRAVITY * g
            self.player["vy"] = max(-SHIP_MAX_VY, min(SHIP_MAX_VY, self.player["vy"]))

        self.jump_just_pressed = False

        self.player["x"] += SPEED * self.player.get("speed_mult", 1.0) * getattr(self, "hard_mult", 1.0)
        px, py = self.player["x"], self.player["y"]
        p_box = (px + 3, py + 3, px + GRID - 3, py + GRID - 3)

        for (gx, gy), raw_obj in self.level.items():
            obj, _ = tilt_mod.parse_tilt(raw_obj)
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
            if g == 1:
                self.player["grounded"] = True

        if self.player["y"] <= MAX_SKY_Y:
            self.player["y"] = float(MAX_SKY_Y)
            if self.player["vy"] < 0:
                self.player["vy"] = 0.0
            if g == -1:
                self.player["grounded"] = True

        px, py = self.player["x"], self.player["y"]
        p_box = (px + 3, py, px + GRID - 3, py + GRID)

        for (gx, gy), raw_obj in self.level.items():
            obj, _ = tilt_mod.parse_tilt(raw_obj)
            if isinstance(obj, str) and obj.startswith("bg:"):
                if abs(self.player["x"] - gx * GRID) <= SPEED:
                    _, _, hex_col = obj.partition(":")
                    if hex_col.startswith("#"):
                        self.bg_color = hex_col
            ox, oy = gx * GRID, gy * GRID
            if obj == "block":
                b_box = (ox, oy, ox + GRID, oy + GRID)
                if self.rects_collide(p_box, b_box):
                    if self.player["vy"] > 0:
                        if self.player["mode"] == "ship" or g == 1:
                            self.player["y"] = float(oy - GRID)
                            self.player["vy"] = 0.0
                            if g == 1:
                                self.player["grounded"] = True
                        else:
                            self.player["dead"] = True
                            return
                    elif self.player["vy"] < 0:
                        if self.player["mode"] == "ship" or g == -1:
                            self.player["y"] = float(oy + GRID)
                            self.player["vy"] = 0.0
                            if g == -1:
                                self.player["grounded"] = True
                        else:
                            self.player["dead"] = True
                            return
            elif obj == "pad_yellow":
                pad_box = (ox + 4, oy + GRID - 14, ox + GRID - 4, oy + GRID)
                if self.rects_collide(p_box, pad_box):
                    self.player["vy"] = JUMP_FORCE * 1.45 * g
                    self.player["grounded"] = False
            elif obj == "coin" and (gx, gy) not in self.got_coins and not getattr(self, "practice_mode", False):
                if self.rects_collide(p_box, (ox+6, oy+6, ox+GRID-6, oy+GRID-6)):
                    self.got_coins.add((gx, gy)); self.shop_data["coins"] += 10; shop_mod.save_shop(self.shop_data)
            elif obj == "kill_zone":
                if self.rects_collide(p_box, (ox + 2, oy + 2, ox + GRID - 2, oy + GRID - 2)):
                    self.player["dead"] = True; return
            elif obj == "spike":
                sc = getattr(self, "spike_scale", 0); s_box = (ox + 12 - sc, oy + 14 - sc, ox + GRID - 12 + sc, oy + GRID)
                if self.rects_collide(p_box, s_box):
                    self.player["dead"] = True
                    return
            elif obj == "tp_in" and getattr(self, "tp_cooldown", 0) == 0:
                p_portal = (ox + 8, oy, ox + GRID - 8, oy + GRID)
                if self.rects_collide(p_box, p_portal):
                    out = next((k for k, v in self.level.items() if v == "tp_out"), None)
                    if out:
                        tx, ty = out
                        self.player["x"] = float(tx * GRID)
                        self.player["y"] = float(ty * GRID)
                        self.tp_cooldown = 20
                        break
            elif obj in speed_mod.SPEEDS:
                if self.rects_collide(p_box, (ox + 6, oy, ox + GRID - 6, oy + GRID)):
                    self.player["speed_mult"] = speed_mod.SPEEDS[obj]["mult"]
            elif obj in modes_mod.EXTRA_PORTALS:
                if self.rects_collide(p_box, (ox + 8, oy, ox + GRID - 8, oy + GRID)):
                    self.player["mode"] = modes_mod.EXTRA_PORTALS[obj]["mode"]; bee_mod.stop_bee_music(self)
            elif obj == "portal_ship":
                p_portal = (ox + 8, oy, ox + GRID - 8, oy + GRID)
                if self.rects_collide(p_box, p_portal):
                    self.player["mode"] = "ship"; bee_mod.start_bee_music(self)
            elif obj == "portal_cube":
                p_portal = (ox + 8, oy, ox + GRID - 8, oy + GRID)
                if self.rects_collide(p_box, p_portal):
                    self.player["mode"] = "cube"; bee_mod.stop_bee_music(self)
            elif obj == "portal_grav_up":
                p_portal = (ox + 8, oy, ox + GRID - 8, oy + GRID)
                if self.rects_collide(p_box, p_portal):
                    if self.player.get("grav", 1) != -1:
                        self.player["grav"] = -1
                        self.player["grounded"] = False
            elif obj == "portal_grav_down":
                p_portal = (ox + 8, oy, ox + GRID - 8, oy + GRID)
                if self.rects_collide(p_box, p_portal):
                    if self.player.get("grav", 1) != 1:
                        self.player["grav"] = 1
                        self.player["grounded"] = False
            elif obj == "goal":
                g_box = (ox, oy, ox + GRID, oy + GRID)
                if self.rects_collide(p_box, g_box):
                    self.won = True
                    return

        self.camera_x = max(0.0, self.player["x"] - 180)
        target_cy = min(0.0, max(float(MAX_SKY_Y), self.player["y"] - HEIGHT * 0.45))
        self.camera_y += (target_cy - self.camera_y) * 0.15

    def draw_object(self, sx, sy, obj, highlight=False, used=False):
        if isinstance(obj, str) and obj.endswith(":inv"):
            if self.screen_state == "play" and not highlight: return
            self.draw_object(sx, sy, obj[:-4], highlight=True, used=used)
            self.canvas.create_text(sx + GRID/2, sy + GRID/2, text="НЕВИД", fill="#00ffcc", font=("Sans", 7, "bold"))
            return
        if build_mod.draw_extra_block(self.canvas, sx, sy, GRID, obj, highlight): return
        base_t, ang_t = tilt_mod.parse_tilt(obj)
        sc_t = tilt_mod.parse_scale(obj)
        if ang_t > 0 or sc_t != 1.0:
            if base_t == "ghost_block" and self.screen_state == "play" and not highlight: return
            if tilt_mod.draw_tilted(self.canvas, sx, sy, GRID, base_t, ang_t, highlight, sc_t): return
        if obj in modes_mod.EXTRA_PORTALS:
            modes_mod.draw_extra_portal(self.canvas, sx, sy, GRID, obj)
            return
        if pack_mod.draw_pack_obj(self, sx, sy, obj): return
        if move_mod.parse_move(obj)[0]:
            if self.screen_state == "edit" or highlight:
                move_mod.draw_trigger(self.canvas, sx, sy, HEIGHT, GRID, obj)
            return
        if obj in speed_mod.SPEEDS:
            speed_mod.draw_speed_portal(self.canvas, sx, sy, GRID, obj)
            return
        if obj == "coin":
            self.canvas.create_oval(sx+6, sy+6, sx+GRID-6, sy+GRID-6, fill="#ffd32a", outline="#fff200", width=3)
            self.canvas.create_text(sx+GRID/2, sy+GRID/2, text="$", fill="#805b00", font=("Sans", 12, "bold"))
            return
        if obj == "block":
            outline = "#00ffcc" if highlight else "#74b9ff"
            self.canvas.create_rectangle(sx, sy, sx + GRID, sy + GRID, fill="#2d3436", outline=outline, width=2)
        elif obj == "ghost_block":
            if self.screen_state == "play" and not highlight: return
            outline = "#00ffcc" if highlight else "#4b7bec"
            self.canvas.create_rectangle(sx, sy, sx + GRID, sy + GRID, fill="#1c2331", outline=outline, dash=(4, 4), width=2)
        elif isinstance(obj, str) and obj.startswith("bg:"):
            _, _, c = obj.partition(":")
            if not c.startswith("#"): c = "#7b0088"
            if self.screen_state == "edit" or highlight:
                self.canvas.create_line(sx+GRID/2, 0, sx+GRID/2, HEIGHT, fill=c, dash=(4, 4), width=2)
                self.canvas.create_oval(sx+4, sy+4, sx+GRID-4, sy+GRID-4, fill="#12121a", outline=c, width=4)
                self.canvas.create_oval(sx+11, sy+11, sx+GRID-11, sy+GRID-11, fill=c, outline="white", width=1.5)
                self.canvas.create_text(sx+GRID/2, sy-8, text="СВЕТ", fill="white", font=("Sans", 7, "bold"))
        elif obj == "pad_yellow":
            self.canvas.create_arc(sx+3, sy+GRID-22, sx+GRID-3, sy+GRID+10, start=0, extent=180, fill="#ffd32a", outline="#fff200", width=2)
        elif obj == "kill_zone":
            self.canvas.create_rectangle(sx+2, sy+2, sx+GRID-2, sy+GRID-2, fill="#4d0000", outline="#ff4757", dash=(4, 2), width=2)
            self.canvas.create_line(sx+8, sy+8, sx+GRID-8, sy+GRID-8, fill="#ff4757", width=2)
            self.canvas.create_line(sx+GRID-8, sy+8, sx+8, sy+GRID-8, fill="#ff4757", width=2)
        elif obj == "spike":
            outline = "#00ffcc" if highlight else "white"
            sc = getattr(self, "spike_scale", 0); self.canvas.create_polygon(sx + GRID / 2, sy + 4 - sc*1.5, sx + GRID - 3 + sc, sy + GRID, sx + 3 - sc, sy + GRID, fill="#ff4757", outline=outline, width=1.5)
        elif obj == "orb_yellow":
            fill_c = "#635a24" if used else "#ffd32a"
            ring_c = "#00ffcc" if highlight else ("#807840" if used else "#fff200")
            self.canvas.create_oval(sx - 6, sy - 6, sx + GRID + 6, sy + GRID + 6, outline=ring_c, width=3)
            self.canvas.create_oval(sx + 1, sy + 1, sx + GRID - 1, sy + GRID - 1, fill=fill_c, outline="")
        elif obj == "tp_in":
            self.canvas.create_oval(sx+6, sy+2, sx+GRID-6, sy+GRID-2, fill="#003d4d", outline="#00d2d3", width=3)
            self.canvas.create_text(sx+GRID/2, sy+GRID/2, text="ТЛП1", fill="#00d2d3", font=("Sans", 7, "bold"))
        elif obj == "tp_out":
            self.canvas.create_oval(sx+6, sy+2, sx+GRID-6, sy+GRID-2, fill="#4d2600", outline="#ff9f43", width=3)
            self.canvas.create_text(sx+GRID/2, sy+GRID/2, text="ТЛП2", fill="#ff9f43", font=("Sans", 7, "bold"))
        elif obj == "portal_ship":
            self.canvas.create_oval(sx + 6, sy + 2, sx + GRID - 6, sy + GRID - 2, fill="#4a154b", outline="#ff6b81", width=3)
            self.canvas.create_text(sx + GRID / 2, sy + GRID / 2, text="ПЧЕЛА", fill="#ff6b81", font=("Sans", 7, "bold"))
        elif obj == "portal_cube":
            self.canvas.create_oval(sx + 6, sy + 2, sx + GRID - 6, sy + GRID - 2, fill="#0b4619", outline="#2ed573", width=3)
            self.canvas.create_text(sx + GRID / 2, sy + GRID / 2, text="КУБ", fill="#2ed573", font=("Sans", 7, "bold"))
        elif obj == "portal_grav_up":
            self.canvas.create_oval(sx + 6, sy + 2, sx + GRID - 6, sy + GRID - 2, fill="#4d3b00", outline="#ffd32a", width=3)
            self.canvas.create_text(sx + GRID / 2, sy + GRID / 2, text="ГР▲", fill="#ffd32a", font=("Sans", 7, "bold"))
        elif obj == "portal_grav_down":
            self.canvas.create_oval(sx + 6, sy + 2, sx + GRID - 6, sy + GRID - 2, fill="#0a2e52", outline="#1e90ff", width=3)
            self.canvas.create_text(sx + GRID / 2, sy + GRID / 2, text="ГР▼", fill="#1e90ff", font=("Sans", 7, "bold"))
        elif obj == "goal":
            self.canvas.create_rectangle(sx, sy, sx + GRID, sy + GRID, fill="#165b54", outline="#00ffcc", width=2)
            self.canvas.create_text(sx + GRID / 2, sy + GRID / 2, text="ФИНИШ", fill="#00ffcc", font=("Sans", 7, "bold"))

    def draw_player(self, px, py):
        if modes_mod.draw_extra_player(self.canvas, px, py, GRID, self.player["mode"], self.player["vy"], getattr(self, "_tick", 0)): return
        if pack_mod.draw_pack_obj(self, px, py, "player" if self.player["mode"] == "cube" else "bee"): return
        if self.player["mode"] == "cube":
            self.canvas.create_rectangle(px, py, px + GRID, py + GRID, fill=shop_mod.SKINS[self.shop_data["selected"]]["fill"], outline=shop_mod.SKINS[self.shop_data["selected"]]["out"], width=3)

            self.canvas.create_rectangle(px + 22, py + 10, px + 28, py + 16, fill="#2d3436", outline="")
            self.canvas.create_rectangle(px + 31, py + 10, px + 37, py + 16, fill="#2d3436", outline="")
            self.canvas.create_rectangle(px + 22, py + 22, px + 37, py + 26, fill="#2d3436", outline="")
        elif getattr(self, "pe_mode", True):
            bee_mod.draw_bee(self.canvas, px, py, self.player["vy"], GRID, getattr(self, "_tick", 0), getattr(self, "pe_mode", True), shop_mod.SKINS.get(self.shop_data["selected"]))
        else:
            t = self.player["vy"] * 1.4
            self.canvas.create_polygon(px + 2, py + 22 - t * 0.4, px + 12, py + 36, px + 34, py + 36, px + GRID, py + 24 + t, px + 24, py + 18 + t * 0.5, fill="#ff6b81", outline="white", width=2)

    def draw(self):
        if self.screen_state == "menu" or getattr(self, "paused", False):
            return
        self.canvas.configure(bg=self.bg_color if self.screen_state == "play" else "#161626")
        self.canvas.delete("all")
        if "bg" in getattr(self, "pack_imgs", {}): self.canvas.create_image(0, 0, image=self.pack_imgs["bg"], anchor="nw")
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

        for (gx, gy), raw_obj in self.level.items():
            obj, _ = tilt_mod.parse_tilt(raw_obj)
            sx, sy = gx * GRID - cx, gy * GRID - cy
            if sx + GRID < 0 or sx > WIDTH or sy + GRID < 0 or sy > HEIGHT:
                continue
            self.draw_object(sx, sy, raw_obj, used=((gx, gy) in self.used_orbs))

        if self.screen_state == "edit" and self.dragging_obj is not None:
            mx, my = self.drag_mouse_pos
            self.draw_object(mx - GRID / 2, my - GRID / 2, self.dragging_obj, highlight=True)

        if self.screen_state == "play": practice_mod.draw_checkpoints(self, cx, cy)
        respect_mod.draw_angry_bees(self, cx, cy, getattr(self, "_tick", 0))
        if self.screen_state == "play" and not self.player["dead"]:
            self.draw_player(self.player["x"] - cx, self.player["y"] - cy)

        preview_mod.draw_hover_preview(self, cx, cy, GRID)
        if self.won:
            self.canvas.create_rectangle(150, HEIGHT / 2 - 75, WIDTH - 150, HEIGHT / 2 + 75, fill="#12121a", outline="#00ffcc", width=3)
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 - 25, text="УРОВЕНЬ ПРОЙДЕН!", fill="#00ffcc", font=("Sans", 26, "bold"))
            self.canvas.create_text(WIDTH / 2, HEIGHT / 2 + 20, text="Пробел / ЛКМ — заново  |  Esc — в главное меню", fill="white", font=("Sans", 11))

    def loop(self):
        self._tick = getattr(self, "_tick", 0) + 1
        self.update()
        self.draw()
        self.root.after(FPS_MS, self.loop)


root = tk.Tk()
app = CubeDashApp(root)
root.mainloop()
