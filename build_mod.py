import copy
def init_build(app): app.undo_stack, app.redo_stack, app.sel_start, app.sel_end, app.clipboard = [], [], None, None, {}
def push_undo(app): app.undo_stack.append(copy.deepcopy(app.level))
def undo(app):
    if app.screen_state == "edit" and app.undo_stack: app.level = app.undo_stack.pop()
def redo(app): pass
def eyedropper(app):
    gx, gy = app.screen_to_grid(*getattr(app, "hover_pos", (-100, -100)))
    raw = app.level.get((gx, gy))
    if raw: app.tool = "bg_trigger" if raw.startswith("bg:") else raw.split("*").split("@")
def fill_rect(app, c1, c2):
    push_undo(app)
    for gx in range(min(c1, c2), max(c1, c2) + 1):
        for gy in range(min(c1, c2), max(c1, c2) + 1):
            if app.is_valid_cell(gx, gy) and app.tool not in ("erase", "move", "link_trigger", "edit_obj"):
                app.level[(gx, gy)] = app.tool
def copy_selection(app):
    if app.sel_start and app.sel_end:
        x1, x2, y1, y2 = min(app.sel_start, app.sel_end), max(app.sel_start, app.sel_end), min(app.sel_start, app.sel_end), max(app.sel_start, app.sel_end)
        app.clipboard = {(gx-x1, gy-y1): v for (gx, gy), v in app.level.items() if x1<=gx<=x2 and y1<=gy<=y2}
def paste_selection(app):
    tx, ty = app.screen_to_grid(*getattr(app, "hover_pos", (-100, -100)))
    for (dx, dy), v in app.clipboard.items():
        if app.is_valid_cell(tx+dx, ty+dy): app.level[(tx+dx, ty+dy)] = v
def draw_build_overlay(app, cx, cy, grid):
    if app.screen_state == "edit" and app.sel_start and app.sel_end:
        x1, x2, y1, y2 = min(app.sel_start, app.sel_end), max(app.sel_start, app.sel_end), min(app.sel_start, app.sel_end), max(app.sel_start, app.sel_end)
        app.canvas.create_rectangle(x1*grid-cx, y1*grid-cy, (x2+1)*grid-cx, (y2+1)*grid-cy, outline="#ffd32a", dash=(5,3), width=2)
def draw_extra_block(c, sx, sy, g, obj, hi=False):
    if obj == "slab": c.create_rectangle(sx, sy, sx+g, sy+g//2, fill="#34495e", outline="#00ffcc" if hi else "#74b9ff", width=2); return True
    if obj == "bounce_block": c.create_rectangle(sx, sy, sx+g, sy+g, fill="#6c5ce7", outline="#a29bfe", width=2); return True
    if obj == "break_block": c.create_rectangle(sx, sy, sx+g, sy+g, fill="#7f5539", outline="#ddb892", width=2); return True
    return False
