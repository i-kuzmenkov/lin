import pygame
import sys
import random
import math

# Инициализация игрового движка
pygame.init()
pygame.font.init()

# Размеры окна
WIDTH, HEIGHT = 1000, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Симулятор Автобуса: Остановки на дорогах")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Courier", 18, bold=True)

# Игровые параметры
score = 0
passengers_in_bus = 0
max_capacity = 6

# Физика автобуса
bus_x, bus_y = 160, 170  # Спавн на перекрёстке
bus_angle = 0.0
bus_speed = 5

# Координаты дорожной сети (ширина дороги — 100 пикселей)
roads_x = [110, 450, 810]
roads_y = [120, 500]
ROAD_WIDTH = 100

# Дома смещены, чтобы освободить место у дорог
buildings = [
    (20, 65, 80, 60), (240, 65, 90, 65), (350, 65, 80, 65),
    (570, 65, 90, 65), (680, 65, 80, 65), (20, 280, 80, 80),
    (20, 400, 80, 80), (20, 670, 80, 60), (240, 670, 90, 65), (350, 670, 80, 65)
]

# ОСТАНОВКИ ПЕРЕНЕСЕНЫ: теперь они стоят строго на краях дорог (на обочинах/тротуарах)
stops_coords = [
    (70, 220),   # Слева от первой вертикальной дороги
    (410, 320),  # Слева от центральной вертикальной дороги
    (550, 220),  # Справа от центральной вертикальной дороги
    (770, 400)   # Слева от третьей вертикальной дороги
]
station_rect = pygame.Rect(840, 620, 120, 80)

passengers = []
def spawn_passengers():
    passengers.clear()
    for idx, (x, y) in enumerate(stops_coords):
        for i in range(random.randint(1, 3)):
            # Пассажиры стоят на тротуаре прямо возле знака остановки
            passengers.append({"x": x + 20, "y": y + 20 + (i * 12), "idx": idx})

spawn_passengers()

def is_on_road(x, y):
    on_vertical = any(rx <= x <= rx + ROAD_WIDTH for rx in roads_x)
    on_horizontal = any(ry <= y <= ry + ROAD_WIDTH for ry in roads_y)
    on_station = station_rect.collidepoint(x, y)
    
    # Разрешаем автобусу заезжать на остановки для посадки людей
    on_stop = any(sx <= x <= sx + 40 and sy <= y <= sy + 50 for sx, sy in stops_coords)
    
    return on_vertical or on_horizontal or on_station or on_stop

# Главный цикл игры
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    dx, dy = 0, 0
    moving = False

    if keys[pygame.K_UP] or keys[pygame.K_w]:
        dy = -bus_speed
        moving = True
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        dy = bus_speed
        moving = True
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        dx = -bus_speed
        moving = True
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        dx = bus_speed
        moving = True

    if moving:
        target_angle = math.degrees(math.atan2(-dy, dx))
        if target_angle < 0: target_angle += 360
        diff = (target_angle - bus_angle + 180) % 360 - 180
        bus_angle = (bus_angle + diff * 0.25) % 360

        move_rad = math.radians(-bus_angle)
        
        next_x = bus_x + bus_speed * math.cos(move_rad)
        next_y = bus_y + bus_speed * math.sin(move_rad)

        if is_on_road(next_x, next_y):
            bus_x = next_x
            bus_y = next_y

    bus_x = max(30, min(WIDTH - 30, bus_x))
    bus_y = max(65, min(HEIGHT - 30, bus_y))

    # Сбор людей на остановках (радиус уменьшен до 45, так как теперь мы подъезжаем вплотную на дороге)
    for idx, (sx, sy) in enumerate(stops_coords):
        if math.hypot(bus_x - (sx + 20), bus_y - (sy + 25)) < 45:
            for p in passengers[:]:
                if p["idx"] == idx:
                    if passengers_in_bus < max_capacity:
                        passengers_in_bus += 1
                        passengers.remove(p)

    # Разгрузка на Вокзале
    if station_rect.collidepoint(bus_x, bus_y):
        if passengers_in_bus > 0:
            score += passengers_in_bus * 150
            passengers_in_bus = 0
            spawn_passengers()

    # Отрисовка графики
    screen.fill((34, 139, 34))  # Газон

    # Вертикальные дороги
    for rx in roads_x:
        pygame.draw.rect(screen, (60, 60, 60), (rx, 45, ROAD_WIDTH, HEIGHT))
        pygame.draw.line(screen, (169, 169, 169), (rx, 45), (rx, HEIGHT), 4)
        pygame.draw.line(screen, (169, 169, 169), (rx + ROAD_WIDTH, 45), (rx + ROAD_WIDTH, HEIGHT), 4)
        for y in range(60, HEIGHT, 40):
            pygame.draw.line(screen, (255, 255, 255), (rx + 50, y), (rx + 50, y + 20), 2)

    # Горизонтальные дороги
    for ry in roads_y:
        pygame.draw.rect(screen, (60, 60, 60), (0, ry, WIDTH, ROAD_WIDTH))
        pygame.draw.line(screen, (169, 169, 169), (0, ry), (WIDTH, ry), 4)
        pygame.draw.line(screen, (169, 169, 169), (0, ry + ROAD_WIDTH), (WIDTH, ry + ROAD_WIDTH), 4)
        for x in range(20, WIDTH, 40):
            pygame.draw.line(screen, (255, 255, 255), (x, ry + 50), (x + 20, ry + 50), 2)

    # Сглаживание перекрестков
    for rx in roads_x:
        for ry in roads_y:
            pygame.draw.rect(screen, (60, 60, 60), (rx, ry, ROAD_WIDTH, ROAD_WIDTH))

    # Вокзал
    pygame.draw.rect(screen, (255, 215, 0), station_rect)
    pygame.draw.rect(screen, (184, 134, 11), station_rect, 3)
    screen.blit(font.render("ВОКЗАЛ", True, (0, 0, 0)), (station_rect.x + 25, station_rect.y + 30))

    # Дома
    for bx, by, bw, bh in buildings:
        pygame.draw.rect(screen, (205, 92, 92), (bx, by, bw, bh))
        pygame.draw.rect(screen, (34, 34, 34), (bx, by, bw, bh), 2)
        pygame.draw.polygon(screen, (139, 0, 0), [(bx - 4, by), (bx + bw // 2, by - 16), (bx + bw + 4, by)])

    # Остановки теперь стоят аккуратно "карманами" прямо у обочин дорог
    for sx, sy in stops_coords:
        pygame.draw.rect(screen, (255, 69, 0), (sx, sy, 40, 50))
        pygame.draw.rect(screen, (30, 144, 255), (sx + 10, sy - 15, 15, 12))
        screen.blit(pygame.font.SysFont("Arial", 10, bold=True).render("H", True, (255, 255, 255)), (sx + 14, sy - 15))

    # Пассажиры на остановках
    for p in passengers:
        pygame.draw.circle(screen, (0, 255, 255), (p["x"], p["y"]), 5)
        pygame.draw.circle(screen, (0, 0, 128), (p["x"], p["y"]), 5, 1)

    # Отрисовка автобуса с вращением
    bus_surf = pygame.Surface((50, 28), pygame.SRCALPHA)
    pygame.draw.rect(bus_surf, (255, 69, 0), (0, 0, 50, 28), border_radius=4)
    pygame.draw.rect(bus_surf, (255, 255, 255), (0, 0, 50, 28), 2, border_radius=4)
    pygame.draw.rect(bus_surf, (135, 206, 235), (38, 3, 8, 22))

    rotated_bus = pygame.transform.rotate(bus_surf, bus_angle)
    bus_rect = rotated_bus.get_rect(center=(bus_x, bus_y))
    screen.blit(rotated_bus, bus_rect.topleft)

    # Верхний интерфейс
    pygame.draw.rect(screen, (17, 17, 17), (0, 0, WIDTH, 45))
    ui_string = f"Салон: {passengers_in_bus}/{max_capacity} | Заработок: {score} руб."
    screen.blit(font.render(ui_string, True, (0, 255, 0)), (20, 12))

    pygame.display.flip()
    clock.tick(60)
