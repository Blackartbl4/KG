import tkinter as tk
from tkinter import ttk
import time
import math

class RasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №3: Растровые алгоритмы")
        self.root.geometry("1200x800")

        # --- Переменные ---
        self.scale = 20  # Размер одной клетки в пикселях
        self.grid_color = "#ddd"
        self.axis_color = "#333"
        self.pixel_color = "blue"
        
        # Логические координаты центра
        self.offset_x = 0
        self.offset_y = 0

        # --- Layout ---
        # Левая панель управления
        control_frame = tk.Frame(root, width=300, padx=10, pady=10, bg="#f0f0f0")
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        control_frame.pack_propagate(False)

        # Правая панель (Canvas)
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.canvas.bind("<Configure>", self.draw_grid)

        # --- Элементы управления ---
        
        tk.Label(control_frame, text="Координаты отрезка:", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(pady=(0, 5))
        
        input_frame = tk.Frame(control_frame, bg="#f0f0f0")
        input_frame.pack(fill=tk.X)
        
        tk.Label(input_frame, text="X1:", bg="#f0f0f0").grid(row=0, column=0)
        self.entry_x1 = tk.Entry(input_frame, width=5)
        self.entry_x1.grid(row=0, column=1)
        self.entry_x1.insert(0, "-5")
        
        tk.Label(input_frame, text="Y1:", bg="#f0f0f0").grid(row=0, column=2)
        self.entry_y1 = tk.Entry(input_frame, width=5)
        self.entry_y1.grid(row=0, column=3)
        self.entry_y1.insert(0, "-3")
        
        tk.Label(input_frame, text="X2:", bg="#f0f0f0").grid(row=1, column=0)
        self.entry_x2 = tk.Entry(input_frame, width=5)
        self.entry_x2.grid(row=1, column=1)
        self.entry_x2.insert(0, "8")
        
        tk.Label(input_frame, text="Y2:", bg="#f0f0f0").grid(row=1, column=2)
        self.entry_y2 = tk.Entry(input_frame, width=5)
        self.entry_y2.grid(row=1, column=3)
        self.entry_y2.insert(0, "5")

        tk.Label(control_frame, text="Алгоритмы для отрезка:", bg="#f0f0f0").pack(pady=(10, 2))
        tk.Button(control_frame, text="1. Пошаговый алгоритм", command=self.run_step_by_step).pack(fill=tk.X)
        tk.Button(control_frame, text="2. Алгоритм ЦДА (DDA)", command=self.run_dda).pack(fill=tk.X)
        tk.Button(control_frame, text="3. Брезенхем (Отрезок)", command=self.run_bresenham_line).pack(fill=tk.X)

        tk.Label(control_frame, text="_______________________", bg="#f0f0f0").pack(pady=5)
        
        tk.Label(control_frame, text="Координаты окружности:", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(pady=(10, 5))
        circle_frame = tk.Frame(control_frame, bg="#f0f0f0")
        circle_frame.pack(fill=tk.X)
        
        tk.Label(circle_frame, text="X:", bg="#f0f0f0").grid(row=0, column=0)
        self.entry_cx = tk.Entry(circle_frame, width=5)
        self.entry_cx.grid(row=0, column=1)
        self.entry_cx.insert(0, "0")
        
        tk.Label(circle_frame, text="Y:", bg="#f0f0f0").grid(row=0, column=2)
        self.entry_cy = tk.Entry(circle_frame, width=5)
        self.entry_cy.grid(row=0, column=3)
        self.entry_cy.insert(0, "0")
        
        tk.Label(circle_frame, text="R:", bg="#f0f0f0").grid(row=0, column=4)
        self.entry_r = tk.Entry(circle_frame, width=5)
        self.entry_r.grid(row=0, column=5)
        self.entry_r.insert(0, "8")

        tk.Button(control_frame, text="4. Брезенхем (Окружность)", command=self.run_bresenham_circle).pack(fill=tk.X, pady=(5, 0))

        tk.Label(control_frame, text="_______________________", bg="#f0f0f0").pack(pady=10)

        # Масштаб
        tk.Label(control_frame, text="Масштаб (px на клетку):", bg="#f0f0f0").pack()
        self.scale_slider = tk.Scale(control_frame, from_=5, to=50, orient=tk.HORIZONTAL, command=self.update_scale)
        self.scale_slider.set(20)
        self.scale_slider.pack(fill=tk.X)

        tk.Button(control_frame, text="Очистить экран", command=self.clear_canvas, bg="#ffcccc").pack(fill=tk.X, pady=10)

        # Лог и Время
        tk.Label(control_frame, text="Лог вычислений и Время:", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        self.log_text = tk.Text(control_frame, height=15, width=30, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Для хранения нарисованных пикселей (чтобы перерисовывать при зуме)
        self.drawn_points = [] # list of (x, y, color)

    def update_scale(self, val):
        self.scale = int(val)
        self.draw_grid()
        self.redraw_points()

    def clear_canvas(self):
        self.drawn_points = []
        self.draw_grid()
        self.log_text.delete(1.0, tk.END)

    def draw_grid(self, event=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        cx = w // 2 + self.offset_x
        cy = h // 2 + self.offset_y

        # Вертикальные линии
        # Начинаем от центра и идем в стороны
        for i in range(cx % self.scale, w, self.scale):
            color = self.axis_color if abs(i - cx) < self.scale / 2 else self.grid_color
            width = 2 if abs(i - cx) < self.scale / 2 else 1
            self.canvas.create_line(i, 0, i, h, fill=color, width=width)
            
            # Подписи осей X
            grid_x = (i - cx) // self.scale
            if grid_x != 0:
                self.canvas.create_text(i, cy + 15, text=str(grid_x), fill="#555", font=("Arial", 8))

        # Горизонтальные линии
        for i in range(cy % self.scale, h, self.scale):
            color = self.axis_color if abs(i - cy) < self.scale / 2 else self.grid_color
            width = 2 if abs(i - cy) < self.scale / 2 else 1
            self.canvas.create_line(0, i, w, i, fill=color, width=width)
            
            # Подписи осей Y
            grid_y = -((i - cy) // self.scale)
            if grid_y != 0:
                self.canvas.create_text(cx - 15, i, text=str(grid_y), fill="#555", font=("Arial", 8))
        
        # Центр
        self.canvas.create_text(cx - 10, cy + 15, text="0", fill="black", font=("Arial", 8, "bold"))
        self.canvas.create_text(w - 20, cy - 10, text="X", fill="black", font=("Arial", 10, "bold"))
        self.canvas.create_text(cx + 10, 20, text="Y", fill="black", font=("Arial", 10, "bold"))

        # Перерисовка точек, если есть
        self.redraw_points()

    def plot_pixel(self, x, y, color=None):
        """ Рисует пиксель в логических координатах """
        if color is None: color = self.pixel_color
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        cx = w // 2 + self.offset_x
        cy = h // 2 + self.offset_y

        # Экранные координаты (верхний левый угол клетки)
        screen_x = cx + x * self.scale
        screen_y = cy - y * self.scale - self.scale # -scale потому что y растет вниз на экране

        # Рисуем квадрат
        self.canvas.create_rectangle(screen_x, screen_y, 
                                     screen_x + self.scale, screen_y + self.scale, 
                                     fill=color, outline="gray")

    def redraw_points(self):
        """ Перерисовывает все сохраненные точки (нужно при смене масштаба) """
        for p in self.drawn_points:
            self.plot_pixel(p[0], p[1], p[2])

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    # ================= АЛГОРИТМЫ =================

    def run_step_by_step(self):
        try:
            x1, y1 = int(self.entry_x1.get()), int(self.entry_y1.get())
            x2, y2 = int(self.entry_x2.get()), int(self.entry_y2.get())
        except ValueError:
            return

        self.drawn_points = []
        self.draw_grid()
        self.log("--- Пошаговый алгоритм ---")
        
        start_time = time.perf_counter()
        
        points = []
        if x1 == x2:
            # Вертикальная линия
            step = 1 if y2 > y1 else -1
            for y in range(y1, y2 + step, step):
                points.append((x1, y))
        else:
            k = (y2 - y1) / (x2 - x1)
            b = y1 - k * x1
            
            # Определяем, по какой оси идем (где изменение больше)
            if abs(x2 - x1) >= abs(y2 - y1):
                step = 1 if x2 > x1 else -1
                for x in range(x1, x2 + step, step):
                    y = k * x + b
                    points.append((x, round(y)))
                    # Демонстрация вычислений (для первых точек)
                    if len(points) < 4:
                        self.log(f"x={x}, y={y:.2f} -> round({round(y)})")
            else:
                step = 1 if y2 > y1 else -1
                for y in range(y1, y2 + step, step):
                    x = (y - b) / k
                    points.append((round(x), y))
        
        end_time = time.perf_counter()
        
        for p in points:
            self.drawn_points.append((p[0], p[1], "red"))
            self.plot_pixel(p[0], p[1], "red")
            
        self.log(f"Время: {(end_time - start_time)*1000:.4f} мс")

    def run_dda(self):
        try:
            x1, y1 = int(self.entry_x1.get()), int(self.entry_y1.get())
            x2, y2 = int(self.entry_x2.get()), int(self.entry_y2.get())
        except ValueError:
            return

        self.drawn_points = []
        self.draw_grid()
        self.log("--- Алгоритм ЦДА (DDA) ---")

        start_time = time.perf_counter()

        length = max(abs(x2 - x1), abs(y2 - y1))
        dx = (x2 - x1) / length if length != 0 else 0
        dy = (y2 - y1) / length if length != 0 else 0

        x = x1 + 0.5 * (1 if dx > 0 else -1) # Сдвиг для корректного округления
        y = y1 + 0.5 * (1 if dy > 0 else -1)
        
        # Для ЦДА обычно берется просто float
        x, y = x1, y1
        
        points = []
        for i in range(length + 1):
            points.append((round(x), round(y)))
            if i < 3:
                self.log(f"i={i}: x={x:.2f}, y={y:.2f} -> ({round(x)}, {round(y)})")
            x += dx
            y += dy

        end_time = time.perf_counter()

        for p in points:
            self.drawn_points.append((p[0], p[1], "green"))
            self.plot_pixel(p[0], p[1], "green")
        
        self.log(f"Время: {(end_time - start_time)*1000:.4f} мс")

    def run_bresenham_line(self):
        try:
            x1, y1 = int(self.entry_x1.get()), int(self.entry_y1.get())
            x2, y2 = int(self.entry_x2.get()), int(self.entry_y2.get())
        except ValueError:
            return

        self.drawn_points = []
        self.draw_grid()
        self.log("--- Брезенхем (Отрезок) ---")

        start_time = time.perf_counter()

        points = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1
        
        while True:
            points.append((x, y))
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

        end_time = time.perf_counter()
        
        # Демонстрация (логарифмирование первых шагов)
        self.log(f"dx={dx}, dy={dy}, err_start={dx-dy}")

        for p in points:
            self.drawn_points.append((p[0], p[1], "blue"))
            self.plot_pixel(p[0], p[1], "blue")
            
        self.log(f"Время: {(end_time - start_time)*1000:.4f} мс")

    def run_bresenham_circle(self):
        try:
            xc, yc = int(self.entry_cx.get()), int(self.entry_cy.get())
            r = int(self.entry_r.get())
        except ValueError:
            return

        self.drawn_points = []
        self.draw_grid()
        self.log("--- Брезенхем (Окружность) ---")

        start_time = time.perf_counter()

        points = []
        x = 0
        y = r
        d = 3 - 2 * r

        def add_circle_points(xc, yc, x, y):
            pts = [
                (xc+x, yc+y), (xc-x, yc+y), (xc+x, yc-y), (xc-x, yc-y),
                (xc+y, yc+x), (xc-y, yc+x), (xc+y, yc-x), (xc-y, yc-x)
            ]
            for p in pts:
                points.append(p)

        add_circle_points(xc, yc, x, y)
        
        step_count = 0
        while y >= x:
            x += 1
            if d > 0:
                y -= 1
                d = d + 4 * (x - y) + 10
            else:
                d = d + 4 * x + 6
            add_circle_points(xc, yc, x, y)
            
            if step_count < 3:
                self.log(f"x={x}, y={y}, d={d}")
            step_count += 1

        end_time = time.perf_counter()

        # Удаляем дубликаты точек (бывают на осях)
        unique_points = list(set(points))
        
        for p in unique_points:
            self.drawn_points.append((p[0], p[1], "purple"))
            self.plot_pixel(p[0], p[1], "purple")

        self.log(f"Время: {(end_time - start_time)*1000:.4f} мс")

if __name__ == "__main__":
    root = tk.Tk()
    app = RasterApp(root)
    root.mainloop()