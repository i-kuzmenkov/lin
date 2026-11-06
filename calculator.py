import tkinter as tk
from fractions import Fraction
import math
import re

# Функция для обработки нажатий кнопок
def button_click(item):
    global expression
    expression = expression + str(item)
    # Красивое визуальное отображение знаков
    display_expr = expression.replace('/', '÷').replace('*', '×').replace('_frac_', '⁄')
    input_text.set(display_expr)

# Функция для очистки экрана (кнопка C)
def button_clear():
    global expression
    expression = ""
    input_text.set("")

# Функция для вычисления результата (кнопка =)
def button_equal():
    global expression
    try:
        if not expression:
            return

        eval_expr = expression
        
        # 1. Сначала обрабатываем квадратные корни (например, √4 -> math.sqrt(4))
        eval_expr = re.sub(r'√(\d+\.?\d*)', r'math.sqrt(\1)', eval_expr)
        
        # 2. Переводим визуальные дроби вида "1_frac_2" в понятные для Python объекты Fraction(1, 2)
        # Это позволяет калькулятору считать дроби абсолютно без потери точности
        eval_expr = re.sub(r'(\d+)_frac_(\d+)', r'Fraction(\1, \2)', eval_expr)

        # Вычисляем итоговое выражение
        result_obj = eval(eval_expr)
        
        # Если результат вернулся в виде объекта дроби (например, Fraction(5, 6))
        if isinstance(result_obj, Fraction):
            # Если знаменатель равен 1, то это целое число (например, 4/1 -> 4)
            if result_obj.denominator == 1:
                result = str(result_obj.numerator)
            else:
                result = f"{result_obj.numerator}⁄{result_obj.denominator}"
        else:
            result = str(result_obj)
            # Убираем ".0" у обычных целых чисел
            if result.endswith('.0'):
                result = result[:-2]
            # Округляем длинные десятичные хвосты
            elif '.' in result and len(result) > 10:
                result = str(round(float(result), 6))
            
        input_text.set(result)
        expression = result.replace('⁄', '_frac_')  # Сохраняем для дальнейших вычислений
    except ZeroDivisionError:
        input_text.set("Деление на 0!")
        expression = ""
    except Exception:
        input_text.set("Ошибка")
        expression = ""

# Создание главного окна
root = tk.Tk()
root.title("Калькулятор с обыкновенными дробями")
root.geometry("430x540")
root.resizable(False, False)
root.configure(bg="#202020")

expression = ""
input_text = tk.StringVar()

# Поле ввода/вывода чисел
input_frame = tk.Frame(root, width=430, height=70, bd=0, highlightbackground="black", highlightcolor="black", highlightthickness=1)
input_frame.pack(side=tk.TOP)

input_field = tk.Entry(input_frame, font=('Arial', 24, 'bold'), textvariable=input_text, width=50, bg="#2d2d2d", fg="white", bd=0, justify=tk.RIGHT)
input_field.grid(row=0, column=0)
input_field.pack(ipady=15) 

# Фрейм для кнопок
btns_frame = tk.Frame(root, bg="#202020")
btns_frame.pack(pady=10)

# Обновленная сетка: добавлена кнопка 'a⁄b' для ввода простых дробей
grid_buttons = [
    ('C', 'C'), ('(', '('), (')', ')'), ('//', '//'), ('%', '%'),
    ('√', '√'), ('a⁄b', '_frac_'), ('÷', '/'), ('×', '*'), ('-', '-'),
    ('7', '7'), ('8', '8'), ('9', '9'), ('4', '4'), ('5', '5'),
    ('6', '6'), ('1', '1'), ('2', '2'), ('3', '3'), ('.', '.'),
    ('0', '0'), ('+', '+'), ('=', '=')
]

row = 0
col = 0

for display_text, system_value in grid_buttons:
    if system_value == '=':
        action = button_equal
        bg_color = "#fe9e09"
        fg_color = "white"
    elif system_value == 'C':
        action = button_clear
        bg_color = "#a5a5a5"
        fg_color = "black"
    else:
        action = lambda x=system_value: button_click(x)
        if system_value in ['/', '*', '-', '+', '//', '%', '√', '_frac_']:
            # Кнопка дроби выделена приятным оранжевым цветом операций
            bg_color = "#fe9e09"
            fg_color = "white"
        elif system_value in ['(', ')']:
            bg_color = "#555555"
            fg_color = "white"
        else:
            bg_color = "#333333"
            fg_color = "white"

    btn = tk.Button(btns_frame, text=display_text, fg=fg_color, bg=bg_color, font=('Arial', 14, 'bold'), width=5, height=2, bd=0, cursor="hand2", command=action)
    
    # Кнопку '=' в самом низу делаем шире для сохранения ровной геометрии сетки
    if system_value == '=':
        btn.configure(width=12)
        btn.grid(row=row, column=col, columnspan=2, padx=5, pady=5)
        col += 1
    else:
        btn.grid(row=row, column=col, padx=5, pady=5)
        
    col += 1
    if col > 4:
        col = 0
        row += 1

root.mainloop()
