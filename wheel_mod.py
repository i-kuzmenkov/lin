TOOL_ORDER = [
    ("move", "Двигать"),
    ("block", "Блок"),
    ("ghost_block", "Призрачный блок"), ("slab", "Полублок (верхний)"), ("bounce_block", "Пружинящий блок"), ("break_block", "Хрупкий блок"),
    ("spike", "Шип"), ("kill_zone", "Смертельная зона"),
    ("orb_yellow", "Жёлтая сфера"),
    ("coin", "Монета (+10)"),
    ("pad_yellow", "Батут"),
    ("portal_ship", "Портал: Пчела"),
    ("portal_cube", "Портал: Куб"), ("portal_ball", "Портал: Шар"), ("portal_ufo", "Портал: НЛО"), ("portal_wave", "Портал: Волна"),
    ("portal_grav_up", "Гравитация Вверх"),
    ("portal_grav_down", "Гравитация Вниз"),
    ("tp_in", "Телепорт: Вход"),
    ("tp_out", "Телепорт: Выход"),
    ("spd_075", "Скорость 0.75x"),
    ("spd_1", "Скорость 1x"),
    ("spd_2", "Скорость 2x"),
    ("spd_3", "Скорость 3x"),
    ("spd_4", "Скорость 4x"),
    ("bg_trigger", "Триггер фона"), ("move_up", "Триггер: Двиг. Вверх"), ("move_down", "Триггер: Двиг. Вниз"), ("move_left", "Триггер: Двиг. Влево"), ("move_right", "Триггер: Двиг. Вправо"), ("link_trigger", "Связь триггера с блоком"), ("edit_obj", "Двигать и вращать блок"),
    ("goal", "Финиш"),
    ("erase", "Ластик"),
]

def cycle_tool(app, direction):
    if app.screen_state != "edit":
        return
    ids = [t for t, _ in TOOL_ORDER]
    idx = ids.index(app.tool) if app.tool in ids else 0
    new_id = ids[(idx + direction) % len(ids)]
    app.tool = new_id
    if hasattr(app, "cur_tool_lbl"):
        name = dict(TOOL_ORDER).get(new_id, new_id)
        app.cur_tool_lbl.configure(text=f"Предмет (колёсико): {name}")
    app.sync_toolbar_state()

def pick_bg_color(app):
    from tkinter import colorchooser
    picked = colorchooser.askcolor(title="Цвет фона", color=getattr(app, "selected_bg_col", "#2c1638"))
    _, col = picked if picked and picked else (0, None)
    app.selected_bg_col = col or "#2c1638"
