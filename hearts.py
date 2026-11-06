import turtle

# Настройки экрана
screen = turtle.Screen()
screen.setup(width=600, height=600)
screen.title("Большое сердце на Python")
screen.bgcolor("black")

# Настройки рисовальщика
t = turtle.Turtle()
t.color("red")
t.fillcolor("red")
t.speed(0)  # Поставили максимальную скорость, чтобы рисовало быстрее
t.hideturtle()

# ИСПРАВЛЕНИЕ: Перемещаем черепашку в нижнюю часть экрана перед стартом
t.penup()
t.goto(0, -150)  # Сместились на 150 пикселей вниз
t.pendown()

# Начало рисования
t.begin_fill()

# Левая сторона сердца
t.left(140)
t.forward(170)  # Немного уменьшили длину основания

# Левое ушко (плавная дуга)
for _ in range(200):
    t.right(1)
    t.forward(1.5)  # ИСПРАВЛЕНИЕ: Уменьшили шаг с 2 до 1.5, чтобы ушки не обрезались

# Правое ушко (плавная дуга)
t.left(120)
for _ in range(200):
    t.right(1)
    t.forward(1.5)  # ИСПРАВЛЕНИЕ: Здесь тоже 1.5

# Правая сторона сердца
t.forward(170)

t.end_fill()

# Держит окно открытым после завершения рисунка
turtle.done()
