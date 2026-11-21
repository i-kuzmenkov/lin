SPEEDS = {
    "spd_075": {"mult": 0.75, "label": "0.75x", "fill": "#4d3300", "out": "#ffa502"},
    "spd_1":   {"mult": 1.00, "label": "1x",    "fill": "#0a2e52", "out": "#1e90ff"},
    "spd_2":   {"mult": 2.00, "label": "2x",    "fill": "#0b4619", "out": "#2ed573"},
    "spd_3":   {"mult": 3.00, "label": "3x",    "fill": "#4a154b", "out": "#ff6b81"},
    "spd_4":   {"mult": 4.00, "label": "4x",    "fill": "#4d0000", "out": "#ff4757"},
}

def draw_speed_portal(canvas, sx, sy, grid, obj):
    info = SPEEDS[obj]
    canvas.create_polygon(
        sx + grid/2, sy + 2,
        sx + grid - 4, sy + grid/2,
        sx + grid/2, sy + grid - 2,
        sx + 4, sy + grid/2,
        fill=info["fill"], outline=info["out"], width=3
    )
    canvas.create_text(
        sx + grid/2, sy + grid/2,
        text=info["label"], fill=info["out"], font=("Sans", 7, "bold")
    )
