import sys, math, random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QCheckBox, QSlider, QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QCursor, QPainterPath, QPolygonF, QPixmap, QIcon
from Xlib import display, X

MAX_WINDOW_SNOW = 14
MAX_GROUND_SNOW = 35
FPS = 40

class ControlPanel(QWidget):
    def __init__(self, snow_overlay):
        super().__init__()
        self.snow = snow_overlay
        self.setWindowTitle("SuperSnow Меню")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet("QWidget { background-color: #1e2430; color: #eceff4; font-family: sans-serif; font-size: 13px; } QPushButton { background-color: #3b4252; border: 1px solid #4c566a; border-radius: 6px; padding: 7px 12px; font-weight: bold; } QPushButton:hover { background-color: #4c566a; } QPushButton#santaBtn { background-color: #bf616a; color: white; } QPushButton#houseBtn { background-color: #5e81ac; color: white; }")

        layout = QVBoxLayout()
        layout.setSpacing(10)
        title = QLabel("Управление зимней сказкой")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #88c0d0;")
        layout.addWidget(title)

        btn_house = QPushButton("Добавить домик")
        btn_house.setObjectName("houseBtn")
        btn_house.clicked.connect(self.snow.add_house)
        layout.addWidget(btn_house)

        btn_santa = QPushButton("Запустить Санту с оленями")
        btn_santa.setObjectName("santaBtn")
        btn_santa.clicked.connect(self.snow.spawn_santa)
        layout.addWidget(btn_santa)

        self.chk_auto_santa = QCheckBox("Авто-вылет Санты")
        self.chk_auto_santa.setChecked(True)
        self.chk_auto_santa.stateChanged.connect(lambda state: setattr(self.snow, "auto_santa", state == Qt.Checked))
        layout.addWidget(self.chk_auto_santa)

        lbl_flakes = QLabel("Снежинок: 200")
        layout.addWidget(lbl_flakes)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(30, 500)
        slider.setValue(200)
        slider.valueChanged.connect(lambda v: (lbl_flakes.setText(f"Снежинок: {v}"), self.snow.set_flake_count(v)))
        layout.addWidget(slider)

        self.btn_pause = QPushButton("⏸ Пауза")
        self.btn_pause.setStyleSheet("background-color: #d08770; color: #2e3440;")
        self.btn_pause.clicked.connect(self.toggle_pause)
        layout.addWidget(self.btn_pause)

        row = QHBoxLayout()
        btn_clear = QPushButton("Очистить")
        btn_clear.clicked.connect(self.snow.clear_all)
        row.addWidget(btn_clear)
        btn_hide = QPushButton("Свернуть")
        btn_hide.clicked.connect(self.hide)
        row.addWidget(btn_hide)
        layout.addLayout(row)

        btn_quit = QPushButton("Выход")
        btn_quit.clicked.connect(QApplication.quit)
        layout.addWidget(btn_quit)

        self.setLayout(layout)
        self.move(40, 40)

    def toggle_pause(self):
        paused = self.snow.toggle_pause()
        if paused:
            self.btn_pause.setText("▶️ Продолжить")
            self.btn_pause.setStyleSheet("background-color: #a3be8c; color: #2e3440;")
        else:
            self.btn_pause.setText("⏸ Пауза")
            self.btn_pause.setStyleSheet("background-color: #d08770; color: #2e3440;")

    def closeEvent(self, event):
        self.snow.clear_all()
        self.snow.close()
        QApplication.quit()
        event.accept()

class Flake:
    def __init__(self, w, h, random_y=False):
        depth = random.uniform(0.4, 1.3)
        self.x = random.uniform(0, w)
        self.y = random.uniform(-h, 0) if random_y else random.uniform(-40, -5)
        self.size = int(3 * depth) + 2
        self.speed_y = random.uniform(1.5, 3.2) * depth
        self.phase = random.uniform(0, math.pi * 2)
        self.freq = random.uniform(0.03, 0.08)
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-2.0, 2.0)
        self.is_crystal = (self.size >= 4 and random.random() > 0.35)

class SuperSnow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        screen = QApplication.desktop().geometry()
        self.setGeometry(screen)
        self.w = screen.width()
        self.h = screen.height()

        self.x_disp = display.Display()
        self.x_root = self.x_disp.screen().root
        self.net_client_list = self.x_disp.intern_atom("_NET_CLIENT_LIST")
        self.net_wm_state = self.x_disp.intern_atom("_NET_WM_STATE")
        self.net_wm_state_hidden = self.x_disp.intern_atom("_NET_WM_STATE_HIDDEN")

        self.ground_snow = [0.0 for _ in range(self.w)]
        self.window_snow = {}
        self.windows_rects = []
        self.wind = 0.0
        self.target_wind = 0.0
        self.last_mouse = QCursor.pos()

        self.houses = []
        self.santa = {"active": False, "x": -300.0, "y": 120.0, "speed": 4.5, "phase": 0.0}
        self.santa_sparkles = []
        self.auto_santa = True
        self.paused = False

        self.flakes = [Flake(self.w, self.h, True) for _ in range(200)]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(int(1000 / FPS))

        self.win_timer = QTimer(self)
        self.win_timer.timeout.connect(self.scan_x11_windows)
        self.win_timer.start(150)
        self.scan_x11_windows()

    def set_flake_count(self, count):
        while len(self.flakes) < count:
            self.flakes.append(Flake(self.w, self.h, False))
        if len(self.flakes) > count:
            self.flakes = self.flakes[:count]

    def add_house(self):
        hw = random.randint(75, 115)
        hh = random.randint(55, 85)
        hx = random.randint(30, max(40, self.w - hw - 30))
        wall_colors = [QColor(163, 110, 72), QColor(135, 88, 60), QColor(180, 135, 95), QColor(120, 75, 65)]
        roof_colors = [QColor(150, 45, 45), QColor(60, 90, 120), QColor(95, 55, 45)]
        self.houses.append({"x": hx, "w": hw, "h": hh, "color": random.choice(wall_colors), "roof_color": random.choice(roof_colors), "smoke_phase": random.uniform(0, 6.28)})

    def spawn_santa(self):
        if not self.santa.get("active"):
            self.santa.update({"active": True, "x": -260.0, "y": random.uniform(70, self.h * 0.35), "speed": random.uniform(4.0, 6.0), "phase": 0.0})

    def toggle_pause(self):
        self.paused = not self.paused
        return self.paused

    def clear_all(self):
        self.houses.clear()
        self.ground_snow = [0.0 for _ in range(self.w)]
        for k, v in self.window_snow.items():
            self.window_snow[k] = [0.0 for _ in range(len(v))]
        self.santa["active"] = False
        self.santa_sparkles.clear()

    def scan_x11_windows(self):
        new_rects = []
        active_ids = set()
        try:
            prop = self.x_root.get_full_property(self.net_client_list, X.AnyPropertyType)
            if prop:
                for win_id in prop.value:
                    win = self.x_disp.create_resource_object("window", win_id)
                    if win.get_attributes().map_state != X.IsViewable:
                        continue
                    state = win.get_full_property(self.net_wm_state, X.AnyPropertyType)
                    if state and self.net_wm_state_hidden in state.value:
                        continue
                    geom = win.get_geometry()
                    coords = self.x_root.translate_coords(win, 0, 0)
                    wx, wy, ww, wh = coords.x, coords.y, geom.width, geom.height
                    if ww < 80 or wh < 50 or wy <= 5 or (ww >= self.w and wh >= self.h):
                        continue
                    active_ids.add(win_id)
                    new_rects.append((win_id, wx, wy, ww, wh))
                    if win_id not in self.window_snow or len(self.window_snow.get(win_id, [])) != ww:
                        self.window_snow[win_id] = [0.0 for _ in range(ww)]
        except Exception:
            pass
        for cid in set(self.window_snow.keys()) - active_ids:
            del self.window_snow[cid]
        self.windows_rects = new_rects

    def _deposit_snow(self, pile, idx, max_h):
        n = len(pile)
        if 0 <= idx < n and pile[idx] < max_h:
            pile[idx] += 1.0
            for offset in (-2, -1, 1, 2):
                ni = idx + offset
                if 0 <= ni < n and pile[ni] < pile[idx] - 1.2:
                    pile[ni] += 0.6

    def update_simulation(self):
        if self.paused:
            return
        if random.random() < 0.01:
            self.target_wind = random.uniform(-2.2, 2.2)
        self.wind += (self.target_wind - self.wind) * 0.02

        if self.auto_santa and not self.santa.get("active") and random.random() < 0.0015:
            self.spawn_santa()

        if self.santa.get("active"):
            self.santa["x"] += self.santa.get("speed", 4.5)
            self.santa["phase"] += 0.08
            sy = self.santa.get("y", 120) + math.sin(self.santa.get("phase", 0)) * 14
            for _ in range(2):
                self.santa_sparkles.append({"x": self.santa["x"] + random.uniform(0, 40), "y": sy + random.uniform(15, 25), "vx": random.uniform(-1.5, -0.2), "vy": random.uniform(-0.8, 1.2), "life": 1.0})
            if self.santa["x"] > self.w + 100:
                self.santa["active"] = False

        alive_sparkles = []
        for sp in self.santa_sparkles:
            sp["x"] += sp["vx"]
            sp["y"] += sp["vy"]
            sp["life"] -= 0.03
            if sp["life"] > 0:
                alive_sparkles.append(sp)
        self.santa_sparkles = alive_sparkles

        for h in self.houses:
            h["smoke_phase"] += 0.05

        curr_mouse = QCursor.pos()
        mdx = curr_mouse.x() - self.last_mouse.x()
        mdy = curr_mouse.y() - self.last_mouse.y()
        self.last_mouse = curr_mouse
        mx, my = curr_mouse.x(), curr_mouse.y()

        for i, f in enumerate(self.flakes):
            f.phase += f.freq
            f.x += self.wind * (f.size / 5.0) + math.sin(f.phase) * 0.8
            f.y += f.speed_y
            f.angle = (f.angle + f.rot_speed) % 360

            dx = f.x - mx
            dy = f.y - my
            dist_sq = dx * dx + dy * dy
            if 1 < dist_sq < 4900:
                dist = math.sqrt(dist_sq)
                force = (70 - dist) * 0.08
                f.x += (dx / dist) * force + mdx * 0.15
                f.y += (dy / dist) * force + mdy * 0.15

            if f.x < 0:
                f.x += self.w
            elif f.x >= self.w:
                f.x -= self.w

            ix, iy = int(f.x), int(f.y)
            landed = False

            if f.y > 0:
                for win_id, wx, wy, ww, wh in self.windows_rects:
                    if wx <= ix < wx + ww:
                        pile = self.window_snow.get(win_id)
                        if pile:
                            surface_y = wy - pile[ix - wx]
                            if surface_y - 3 <= iy <= wy + 4:
                                self._deposit_snow(pile, ix - wx, MAX_WINDOW_SNOW)
                                landed = True
                                break

            if not landed and 0 <= ix < self.w:
                if iy >= self.h - self.ground_snow[ix]:
                    self._deposit_snow(self.ground_snow, ix, MAX_GROUND_SNOW)
                    landed = True

            if landed or iy > self.h:
                self.flakes[i] = Flake(self.w, self.h, False)

        if random.random() < 0.15:
            idx = random.randint(0, self.w - 1)
            if self.ground_snow[idx] > 1:
                self.ground_snow[idx] -= 0.3
            for pile in self.window_snow.values():
                if pile:
                    w_idx = random.randint(0, len(pile) - 1)
                    if pile[w_idx] > 1:
                        pile[w_idx] -= 0.3

        self.update()

    def _draw_house(self, painter, house):
        x, w, h = house.get("x"), house.get("w"), house.get("h")
        base_y = self.h - 4
        wall_top = base_y - h
        roof_peak_y = wall_top - int(h * 0.55)

        chimney_x = x + int(w * 0.72)
        chimney_y = roof_peak_y + int(h * 0.18)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(110, 45, 45))
        painter.drawRect(chimney_x, chimney_y - 14, 12, 22)

        for s in range(4):
            t = (house.get("smoke_phase", 0) + s * 1.5) % 6.0
            sx = chimney_x + 6 + math.sin(t * 1.5) * 6 + self.wind * t * 3
            sy = chimney_y - 18 - t * 10
            alpha = max(0, int(160 * (1.0 - t / 6.0)))
            r = 3 + t * 1.8
            painter.setBrush(QColor(235, 240, 245, alpha))
            painter.drawEllipse(QPointF(sx, sy), r, r * 0.8)

        painter.setBrush(house.get("color"))
        painter.drawRect(x, wall_top, w, h)

        door_w, door_h = int(w * 0.22), int(h * 0.42)
        painter.setBrush(QColor(80, 45, 25))
        painter.drawRect(x + int(w * 0.18), base_y - door_h, door_w, door_h)

        win_size = int(min(w, h) * 0.28)
        win_x = x + int(w * 0.55)
        win_y = wall_top + int(h * 0.32)
        painter.setBrush(QColor(255, 220, 100))
        painter.drawRect(win_x, win_y, win_size, win_size)
        painter.setPen(QPen(QColor(90, 50, 30), 2))
        painter.drawLine(win_x + win_size // 2, win_y, win_x + win_size // 2, win_y + win_size)
        painter.drawLine(win_x, win_y + win_size // 2, win_x + win_size, win_y + win_size // 2)

        painter.setPen(Qt.NoPen)
        painter.setBrush(house.get("roof_color"))
        painter.drawPolygon(QPolygonF([QPointF(x - 8, wall_top + 2), QPointF(x + w / 2, roof_peak_y), QPointF(x + w + 8, wall_top + 2)]))

        painter.setPen(QPen(QColor(250, 252, 255), 5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(x - 8, wall_top + 1), QPointF(x + w / 2, roof_peak_y))
        painter.drawLine(QPointF(x + w / 2, roof_peak_y), QPointF(x + w + 8, wall_top + 1))

    def _draw_santa(self, painter):
        if not self.santa.get("active"):
            return
        painter.setPen(Qt.NoPen)
        for sp in self.santa_sparkles:
            life = sp.get("life", 0)
            painter.setBrush(QColor(255, 225, 110, int(255 * life)))
            painter.drawEllipse(QPointF(sp.get("x"), sp.get("y")), 2.5 * life, 2.5 * life)

        sx = self.santa.get("x")
        sy = self.santa.get("y") + math.sin(self.santa.get("phase", 0)) * 14
        painter.save()
        painter.translate(sx, sy)

        painter.setPen(QPen(QColor(210, 180, 120), 1.5))
        painter.drawLine(QPointF(55, 15), QPointF(165, 12))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(190, 35, 45))
        painter.drawPolygon(QPolygonF([QPointF(0, 5), QPointF(15, 22), QPointF(55, 22), QPointF(65, 8), QPointF(45, 12), QPointF(15, 12)]))

        painter.setPen(QPen(QColor(240, 200, 80), 2.5))
        painter.drawLine(QPointF(5, 26), QPointF(62, 26))
        painter.drawArc(QRectF(55, 16, 14, 10), -90 * 16, 180 * 16)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(135, 90, 50))
        painter.drawEllipse(QPointF(18, 8), 11, 9)

        painter.setBrush(QColor(210, 40, 45))
        painter.drawEllipse(QPointF(36, 8), 9, 10)
        painter.setBrush(QColor(255, 220, 190))
        painter.drawEllipse(QPointF(38, -2), 5, 5)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(QPointF(40, 1), 5, 4)
        painter.setBrush(QColor(210, 40, 45))
        painter.drawPolygon(QPolygonF([QPointF(33, -5), QPointF(43, -5), QPointF(32, -13)]))
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(QPointF(31, -13), 2.5, 2.5)

        for idx, rx in enumerate((110, 160)):
            bob = math.sin(self.santa.get("phase", 0) * 2 + idx) * 3
            painter.save()
            painter.translate(rx, 10 + bob)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(145, 95, 55))
            painter.drawEllipse(QPointF(0, 0), 14, 7)
            painter.drawEllipse(QPointF(12, -7), 6, 5)
            painter.setPen(QPen(QColor(120, 75, 40), 2))
            painter.drawLine(QPointF(-8, 5), QPointF(-11, 14))
            painter.drawLine(QPointF(8, 5), QPointF(11, 14))
            painter.setPen(QPen(QColor(210, 190, 150), 1.5))
            painter.drawLine(QPointF(11, -11), QPointF(8, -19))
            painter.drawLine(QPointF(8, -15), QPointF(13, -17))
            if idx == 1:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(255, 40, 40))
                painter.drawEllipse(QPointF(18, -7), 2.8, 2.8)
            painter.restore()
        painter.restore()

    def _draw_crystal(self, painter, x, y, radius, angle):
        painter.save()
        painter.translate(x, y)
        painter.rotate(angle)
        for _ in range(3):
            painter.drawLine(QPointF(-radius, 0), QPointF(radius, 0))
            b = radius * 0.55
            painter.drawLine(QPointF(b, 0), QPointF(radius * 0.85, radius * 0.3))
            painter.drawLine(QPointF(b, 0), QPointF(radius * 0.85, -radius * 0.3))
            painter.drawLine(QPointF(-b, 0), QPointF(-radius * 0.85, radius * 0.3))
            painter.drawLine(QPointF(-b, 0), QPointF(-radius * 0.85, -radius * 0.3))
            painter.rotate(60)
        painter.restore()

    def _draw_snow_pile(self, painter, start_x, base_y, pile):
        if not pile or max(pile) < 1:
            return
        path = QPainterPath()
        path.moveTo(start_x, base_y)
        for i in range(0, len(pile), 4):
            path.lineTo(start_x + i, base_y - pile[i])
        path.lineTo(start_x + len(pile), base_y - pile[-1])
        path.lineTo(start_x + len(pile), base_y)
        path.closeSubpath()
        painter.fillPath(path, QColor(245, 250, 255, 235))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for house in self.houses:
            self._draw_house(painter, house)
        self._draw_santa(painter)
        for win_id, wx, wy, ww, wh in self.windows_rects:
            pile = self.window_snow.get(win_id)
            if pile:
                self._draw_snow_pile(painter, wx, wy, pile)
        self._draw_snow_pile(painter, 0, self.h, self.ground_snow)
        pen = QPen(QColor(255, 255, 255, 225), 1.3)
        painter.setPen(pen)
        painter.setBrush(QColor(255, 255, 255, 210))
        for f in self.flakes:
            if f.is_crystal:
                self._draw_crystal(painter, f.x, f.y, f.size * 1.3, f.angle)
            else:
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(f.x, f.y), f.size / 2, f.size / 2)
                painter.setPen(pen)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    snow = SuperSnow()
    snow.show()
    panel = ControlPanel(snow)
    panel.show()

    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(94, 129, 172))
    tray = QSystemTrayIcon(QIcon(pixmap), app)
    tray_menu = QMenu()
    act_show = QAction("Открыть меню", tray_menu)
    act_show.triggered.connect(panel.show)
    act_house = QAction("Добавить домик", tray_menu)
    act_house.triggered.connect(snow.add_house)
    act_santa = QAction("Запустить Санту", tray_menu)
    act_santa.triggered.connect(snow.spawn_santa)
    act_quit = QAction("Выход", tray_menu)
    act_quit.triggered.connect(app.quit)
    tray_menu.addActions([act_show, act_house, act_santa, act_quit])
    tray.setContextMenu(tray_menu)
    tray.activated.connect(lambda r: panel.show() if r == QSystemTrayIcon.Trigger else None)
    tray.show()
    ret = app.exec_()
    tray.hide()
    sys.exit(ret)
