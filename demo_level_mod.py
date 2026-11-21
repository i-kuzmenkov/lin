import json, os

LVL_NAME = "Мега-Демо: Все возможности"

def build_mega_demo(app, grid, floor_y):
    gy = (floor_y // grid) - 1
    lvl = {
        (5, gy): "pad_yellow",
        (9, gy - 2): "orb_yellow",
        (12, gy): "spike",
        (13, gy): "bounce_block",
        (17, gy - 2): "break_block",
        (20, gy): "move_up:2",
        (22, gy): "block",
        (23, gy): "block",
        (25, gy): "move_down:2",
        (27, gy - 2): "block:inv",
        (28, gy - 2): "block:inv",
        (29, gy - 3): "coin",
        (32, gy - 1): "portal_ship",
        (33, gy - 2): "bg:#221033",
        (34, gy - 1): "spd_fast",
        (38, gy): "kill_zone",
        (38, gy - 5): "block@45",
        (42, gy): "block*1.5",
        (46, gy - 2): "portal_ball",
        (47, gy - 2): "bg:#11382d",
        (48, gy - 1): "spd_norm",
        (51, gy): "spike",
        (51, gy - 5): "block",
        (52, gy - 5): "block",
        (55, gy - 4): "spike@180",
        (59, gy - 2): "portal_ufo",
        (63, gy - 4): "slab",
        (67, gy - 1): "ghost_block",
        (71, gy - 2): "portal_wave",
        (72, gy - 2): "bg:#3b141c",
        (76, gy - 1): "block*0.5",
        (76, gy - 3): "block*0.5",
        (80, gy - 2): "portal_grav_up",
        (84, gy - 5): "block",
        (85, gy - 5): "block",
        (88, gy - 3): "portal_grav_down",
        (92, gy - 1): "portal_cube",
        (95, gy - 1): "coin",
        (99, gy): "goal",
    }
    app.level = lvl
    app.move_links = {
        (20, gy): [(22, gy), (23, gy)],
        (25, gy): [(22, gy), (23, gy)],
    }
    app.current_level_name = LVL_NAME
    save_to_menu(app)

def save_to_menu(app):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels.json")
    data = {}
    if os.path.exists(p):
        try:
            data = json.load(open(p, "r", encoding="utf-8"))
        except Exception:
            data = {}
    new_data = {LVL_NAME: app.serialize_level(app.level)}
    for k, v in data.items():
        if k != LVL_NAME:
            new_data[k] = v
    json.dump(new_data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
