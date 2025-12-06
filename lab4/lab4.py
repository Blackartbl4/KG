import tkinter as tk
from tkinter import filedialog, messagebox

class ClippingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №4: Алгоритмы отсечения (Вариант 22)")
        self.root.geometry("1200x800")

        # --- Данные ---
        self.segments = []       # Список отрезков [(x1, y1, x2, y2), ...]
        self.clip_rect = [-50, -50, 50, 50] # [xmin, ymin, xmax, ymax]
        self.clip_poly = []      # Список вершин выпуклого многоугольника [(x,y), ...]
        
        # Настройки отображения
        self.scale = 20          # Пикселей в единице
        self.offset_x = 0
        self.offset_y = 0
        
        # Цвета
        self.color_grid = "#e0e0e0"
        self.color_axis = "#000000"
        self.color_segment_raw = "#aaaaaa"   # Серый для исходных
        self.color_clipper = "#0000ff"       # Синий для окна/многоугольника
        self.color_visible = "#ff0000"       # Красный для видимой части

        # Режим (1 - Сазерленд-Коэн, 2 - Кирус-Бек)
        self.mode = 1 
        self.poly_building = False # Флаг рисования полигона

        # --- Интерфейс ---
        self.setup_ui()
        
        # Инициализация дефолтного многоугольника
        self.set_default_polygon()

        # --- Привязка клавиш (Биндинги) ---
        
        # 1. Рисование (Левый клик)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # 2. Перемещение (Правый клик - старт, Правый драг - движение)
        self.canvas.bind("<ButtonPress-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.perform_pan)
        
        # 3. Завершение полигона (Enter или Колесико)
        self.root.bind("<Return>", self.finish_polygon)
        self.canvas.bind("<Button-2>", self.finish_polygon) # Средняя кнопка

        # 4. Отмена действия (Ctrl+Z)
        self.root.bind("<Control-z>", self.undo_vertex)
        self.root.bind("<Control-Z>", self.undo_vertex) # Для CapsLock

    def set_default_polygon(self):
        self.clip_poly = [
            (0, 10), (10, 5), (10, -5), 
            (0, -10), (-10, -5), (-10, 5)
        ]

    def setup_ui(self):
        # Панель управления
        control_frame = tk.Frame(self.root, width=250, bg="#f0f0f0", padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(control_frame, text="Управление", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=10)
        
        tk.Button(control_frame, text="Загрузить из файла", command=self.load_file).pack(fill=tk.X, pady=5)
        tk.Button(control_frame, text="Очистить отрезки", command=self.clear_segments).pack(fill=tk.X, pady=5)
        
        tk.Label(control_frame, text="--- Режим работы ---", bg="#f0f0f0").pack(pady=10)
        self.mode_var = tk.IntVar(value=1)
        tk.Radiobutton(control_frame, text="1. Сазерленд-Коэн\n(Прямоугольник)", variable=self.mode_var, value=1, command=self.change_mode, bg="#f0f0f0", justify=tk.LEFT).pack(anchor="w")
        tk.Radiobutton(control_frame, text="2. Кирус-Бек\n(Выпуклый многоугольник)", variable=self.mode_var, value=2, command=self.change_mode, bg="#f0f0f0", justify=tk.LEFT).pack(anchor="w")

        tk.Label(control_frame, text="--- Добавить отрезок ---", bg="#f0f0f0").pack(pady=(20, 5))
        input_frame = tk.Frame(control_frame, bg="#f0f0f0")
        input_frame.pack(fill=tk.X)
        
        self.entries = []
        labels = ['x1', 'y1', 'x2', 'y2']
        for i, lbl in enumerate(labels):
            tk.Label(input_frame, text=lbl, bg="#f0f0f0").grid(row=i//2, column=(i%2)*2)
            ent = tk.Entry(input_frame, width=5)
            ent.grid(row=i//2, column=(i%2)*2+1)
            self.entries.append(ent)
            
        tk.Button(control_frame, text="Добавить", command=self.add_segment_manual).pack(fill=tk.X, pady=5)

        tk.Label(control_frame, text="--- Масштаб ---", bg="#f0f0f0").pack(pady=(20, 5))
        self.scale_scale = tk.Scale(control_frame, from_=5, to=100, orient=tk.HORIZONTAL, command=self.update_scale)
        self.scale_scale.set(20)
        self.scale_scale.pack(fill=tk.X)

        # Инструкция
        info_text = (
            "УПРАВЛЕНИЕ:\n"
            "• ЛКМ: Рисовать точки полигона (Режим 2)\n"
            "• ПКМ (зажать): Перемещение холста\n"
            "• Enter: Замкнуть полигон\n"
            "• Ctrl+Z: Удалить последнюю точку"
        )
        tk.Label(control_frame, text=info_text, bg="#ddd", font=("Arial", 9), justify=tk.LEFT, padx=5, pady=5).pack(pady=20, fill=tk.X)

        # Холст
        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.last_mouse = (0, 0)

    # --- Логика отрисовки ---
    
    def update_scale(self, val):
        self.scale = int(val)
        self.draw()

    def change_mode(self):
        self.mode = self.mode_var.get()
        self.poly_building = False
        self.draw()

    def to_screen(self, x, y):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        sx = w // 2 + self.offset_x + x * self.scale
        sy = h // 2 + self.offset_y - y * self.scale
        return sx, sy

    def to_logical(self, sx, sy):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        x = (sx - (w // 2 + self.offset_x)) / self.scale
        y = ((h // 2 + self.offset_y) - sy) / self.scale
        return x, y

    def draw(self):
        self.canvas.delete("all")
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        # Оси
        c0 = self.to_screen(0, 0)
        self.canvas.create_line(0, c0[1], w, c0[1], fill=self.color_axis, width=2) # X
        self.canvas.create_line(c0[0], 0, c0[0], h, fill=self.color_axis, width=2) # Y
        
        # Сетка
        step = self.scale
        cx, cy = c0
        for i in range(int(cx) % step, w, step):
            self.canvas.create_line(i, 0, i, h, fill=self.color_grid)
        for i in range(int(cy) % step, h, step):
            self.canvas.create_line(0, i, w, i, fill=self.color_grid)

        # Исходные отрезки
        for seg in self.segments:
            p1 = self.to_screen(seg[0], seg[1])
            p2 = self.to_screen(seg[2], seg[3])
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=self.color_segment_raw, width=2)

        # Отсекатель
        if self.mode == 1:
            xmin, ymin, xmax, ymax = self.clip_rect
            p1 = self.to_screen(xmin, ymin)
            p2 = self.to_screen(xmax, ymax)
            self.canvas.create_rectangle(p1[0], p1[1], p2[0], p2[1], outline=self.color_clipper, width=2)
        else:
            # Полигон
            if len(self.clip_poly) > 0:
                pts = [self.to_screen(x, y) for x, y in self.clip_poly]
                flat_pts = [val for sublist in pts for val in sublist]
                
                # Если рисуем, показываем незамкнутую линию, иначе замкнутый полигон
                if len(pts) > 1:
                    if self.poly_building:
                        self.canvas.create_line(flat_pts, fill=self.color_clipper, width=2)
                        # Рисуем точки вершин
                        for p in pts:
                            r = 3
                            self.canvas.create_oval(p[0]-r, p[1]-r, p[0]+r, p[1]+r, fill=self.color_clipper)
                    else:
                        self.canvas.create_polygon(flat_pts, outline=self.color_clipper, fill='', width=2)

        # Результат отсечения
        if self.mode == 1:
            self.run_sutherland_cohen()
        else:
            # Запускаем отсечение только если полигон завершен (не строится)
            if not self.poly_building and len(self.clip_poly) > 2:
                self.run_cyrus_beck()

    # --- Обработчики событий (Новые) ---

    def on_canvas_click(self, event):
        """Добавление точки полигона (ЛКМ)"""
        x, y = self.to_logical(event.x, event.y)
        
        if self.mode == 2:
            if not self.poly_building:
                self.clip_poly = [] 
                self.poly_building = True
            
            self.clip_poly.append((x, y))
            self.draw()

    def start_pan(self, event):
        """Начало перемещения (ПКМ нажатие)"""
        self.last_mouse = (event.x, event.y)

    def perform_pan(self, event):
        """Перемещение холста (ПКМ движение)"""
        dx = event.x - self.last_mouse[0]
        dy = event.y - self.last_mouse[1]
        self.offset_x += dx
        self.offset_y += dy
        self.last_mouse = (event.x, event.y)
        self.draw()

    def finish_polygon(self, event=None):
        """Завершение рисования полигона (Enter)"""
        if self.mode == 2 and self.poly_building:
            if len(self.clip_poly) < 3:
                messagebox.showwarning("Внимание", "Полигон должен иметь минимум 3 вершины")
                return
            self.poly_building = False
            self.draw()

    def undo_vertex(self, event=None):
        """Отмена последней вершины (Ctrl+Z)"""
        if self.mode == 2 and self.poly_building:
            if len(self.clip_poly) > 0:
                self.clip_poly.pop()
                self.draw()
        elif self.mode == 2 and not self.poly_building:
            # Если полигон уже построен, Ctrl+Z может вернуть его в режим редактирования
            # удалив последнюю точку (опционально)
            if len(self.clip_poly) > 0:
                self.poly_building = True
                self.clip_poly.pop()
                self.draw()

    # --- Алгоритмы (Без изменений) ---

    # 1. Сазерленд-Коэн
    INSIDE = 0; LEFT = 1; RIGHT = 2; BOTTOM = 4; TOP = 8

    def compute_code(self, x, y, xmin, ymin, xmax, ymax):
        code = self.INSIDE
        if x < xmin:      code |= self.LEFT
        elif x > xmax:    code |= self.RIGHT
        if y < ymin:      code |= self.BOTTOM
        elif y > ymax:    code |= self.TOP
        return code

    def run_sutherland_cohen(self):
        xmin, ymin, xmax, ymax = self.clip_rect
        
        for seg in self.segments:
            x1, y1, x2, y2 = seg
            code1 = self.compute_code(x1, y1, xmin, ymin, xmax, ymax)
            code2 = self.compute_code(x2, y2, xmin, ymin, xmax, ymax)
            accept = False

            while True:
                if code1 == 0 and code2 == 0:
                    accept = True
                    break
                elif (code1 & code2) != 0:
                    break
                else:
                    x = 0; y = 0
                    code_out = code1 if code1 != 0 else code2

                    if code_out & self.TOP:
                        x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)
                        y = ymax
                    elif code_out & self.BOTTOM:
                        x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
                        y = ymin
                    elif code_out & self.RIGHT:
                        y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
                        x = xmax
                    elif code_out & self.LEFT:
                        y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
                        x = xmin

                    if code_out == code1:
                        x1 = x; y1 = y
                        code1 = self.compute_code(x1, y1, xmin, ymin, xmax, ymax)
                    else:
                        x2 = x; y2 = y
                        code2 = self.compute_code(x2, y2, xmin, ymin, xmax, ymax)

            if accept:
                p1 = self.to_screen(x1, y1)
                p2 = self.to_screen(x2, y2)
                self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=self.color_visible, width=3)

    # 2. Кирус-Бек
    def run_cyrus_beck(self):
        if len(self.clip_poly) < 3: return
        n = len(self.clip_poly)
        
        # Проверяем направление обхода (площадь). Если по часовой - разворачиваем.
        # Формула шнурков (Shoelace formula)
        area = 0
        for i in range(n):
            j = (i + 1) % n
            area += self.clip_poly[i][0] * self.clip_poly[j][1]
            area -= self.clip_poly[j][0] * self.clip_poly[i][1]
        
        poly = list(self.clip_poly)
        if area < 0: # По часовой (для экранных координат Y вверх это было бы против, но тут Y логический)
            # В моей логике координат Y вверх, area > 0 это CCW. Если area < 0 - реверс.
            poly.reverse()

        for seg in self.segments:
            p1 = [seg[0], seg[1]]
            p2 = [seg[2], seg[3]]
            D = [p2[0] - p1[0], p2[1] - p1[1]]
            tE = 0.0
            tL = 1.0
            visible = True
            
            for i in range(n):
                curr_v = poly[i]
                next_v = poly[(i + 1) % n]
                edge = [next_v[0] - curr_v[0], next_v[1] - curr_v[1]]
                # Внутренняя нормаль (поворот влево)
                normal = [-edge[1], edge[0]]
                
                W = [p1[0] - curr_v[0], p1[1] - curr_v[1]]
                D_dot_n = D[0] * normal[0] + D[1] * normal[1]
                W_dot_n = W[0] * normal[0] + W[1] * normal[1]
                
                if D_dot_n == 0:
                    if W_dot_n < 0: 
                        visible = False; break
                else:
                    t = -W_dot_n / D_dot_n
                    if D_dot_n > 0: # Вход
                         tE = max(tE, t)
                    else: # Выход
                         tL = min(tL, t)
            
            if visible and tE <= tL:
                if tE < 0: tE = 0
                if tL > 1: tL = 1
                if tE <= tL:
                    new_x1 = p1[0] + D[0] * tE
                    new_y1 = p1[1] + D[1] * tE
                    new_x2 = p1[0] + D[0] * tL
                    new_y2 = p1[1] + D[1] * tL
                    scr_p1 = self.to_screen(new_x1, new_y1)
                    scr_p2 = self.to_screen(new_x2, new_y2)
                    self.canvas.create_line(scr_p1[0], scr_p1[1], scr_p2[0], scr_p2[1], fill=self.color_visible, width=3)

    # --- Загрузка/Очистка ---
    def load_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not filename: return
        try:
            with open(filename, 'r') as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
                n = int(lines[0])
                self.segments = []
                idx = 1
                for _ in range(n):
                    self.segments.append(tuple(map(float, lines[idx].split())))
                    idx += 1
                if idx < len(lines):
                    self.clip_rect = list(map(float, lines[idx].split()))
            self.draw()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка: {e}")

    def add_segment_manual(self):
        try:
            self.segments.append(tuple([float(e.get()) for e in self.entries]))
            self.draw()
        except: pass

    def clear_segments(self):
        self.segments = []
        self.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = ClippingApp(root)
    root.mainloop()