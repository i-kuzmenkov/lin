NAMES = {
    "block": "Блок", "ghost_block": "Призрачный блок", "slab": "Полублок",
    "bounce_block": "Пружинящий блок", "break_block": "Хрупкий блок",
    "spike": "Шип", "kill_zone": "Смертельная зона", "orb_yellow": "Сфера прыжка",
    "pad_yellow": "Батут", "coin": "Монета", "goal": "Финиш",
    "portal_ship": "Портал: Пчела/Самолёт", "portal_cube": "Портал: Куб",
    "portal_ball": "Портал: Шар", "portal_ufo": "Портал: НЛО", "portal_wave": "Портал: Волна",
    "portal_grav_up": "Гравитация ▲", "portal_grav_down": "Гравитация ▼",
    "spd_slow": "Скорость 0.75x", "spd_norm": "Скорость 1x",
    "spd_fast": "Скорость 1.5x", "spd_vfast": "Скорость 2x",
    "bg_trigger": "Триггер фона", "move_up": "Триггер ▲", "move_down": "Триггер ▼",
    "move_left": "Триггер ◄", "move_right": "Триггер ►",
    "link_trigger": "Связь триггера", "edit_obj": "Двигать / Вращать",
    "move": "Перетащить", "erase": "Ластик"
}

def draw_hover_preview(app, cx, cy, grid):
    if app.screen_state != "edit":
        return
    mx, my = getattr(app, "hover_pos", (-100, -100))
    if mx < 0 or my < 0:
        return
    gx, gy = app.screen_to_grid(mx, my)
    if not app.is_valid_cell(gx, gy):
        return
    sx, sy = gx * grid - cx, gy * grid - cy
    tool = getattr(app, "tool", "block")
    if tool not in ("move", "erase", "link_trigger", "edit_obj"):
        obj = f"bg:{getattr(app, 'selected_bg_col', '#2c1638')}" if tool == "bg_trigger" else tool
        app.draw_object(sx, sy, obj, highlight=True)
    col = "#ff4757" if tool == "erase" else "#00ffcc"
    app.canvas.create_rectangle(sx + 1, sy + 1, sx + grid - 1, sy + grid - 1, outline=col, dash=(4, 2), width=2)
    label = NAMES.get(tool, tool)
    app.canvas.create_rectangle(sx, sy - 20, sx + max(grid, len(label) * 7 + 10), sy - 2, fill="#12121a", outline=col, width=1)
    app.canvas.create_text(sx + 5, sy - 11, text=label, fill=col, font=("Sans", 8, "bold"), anchor="w")
    app.canvas.create_rectangle(14, app.canvas.winfo_height() - 62, 230, app.canvas.winfo_height() - 12, fill="#12121a", outline=col, width=2)
    if tool not in ("move", "erase", "link_trigger", "edit_obj"):
        app.draw_object(20, app.canvas.winfo_height() - 57, tool, highlight=True)
    app.canvas.create_text(68, app.canvas.winfo_height() - 37, text=label, fill="white", font=("Sans", 10, "bold"), anchor="w")
