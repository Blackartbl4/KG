import tkinter as tk
from tkinter import ttk, colorchooser

# --- Вспомогательные функции преобразования ---

def rgb_to_cmyk(r, g, b):
    """Преобразует RGB [0, 255] в CMYK [0, 100]"""
    # Нормализуем значения RGB к [0, 1]
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    # Находим максимальное значение (белый компонент)
    k = 1 - max(r_norm, g_norm, b_norm)

    if k == 1:
        # Если это чистый черный, все цветные компоненты равны 0
        c, m, y = 0, 0, 0
    else:
        # Вычисляем CMY
        c = (1 - r_norm - k) / (1 - k)
        m = (1 - g_norm - k) / (1 - k)
        y = (1 - b_norm - k) / (1 - k)

    # Преобразуем в проценты [0, 100] и округляем
    return (
        round(c * 100),
        round(m * 100),
        round(y * 100),
        round(k * 100)
    )

def cmyk_to_rgb(c, m, y, k):
    """Преобразует CMYK [0, 100] в RGB [0, 255]"""
    # Нормализуем проценты к [0, 1]
    c_norm = c / 100.0
    m_norm = m / 100.0
    y_norm = y / 100.0
    k_norm = k / 100.0

    # Вычисляем RGB
    r = 255 * (1 - c_norm) * (1 - k_norm)
    g = 255 * (1 - m_norm) * (1 - k_norm)
    b = 255 * (1 - y_norm) * (1 - k_norm)

    # Округляем и ограничиваем [0, 255]
    return (
        max(0, min(255, round(r))),
        max(0, min(255, round(g))),
        max(0, min(255, round(b)))
    )

def rgb_to_hls(r, g, b):
    """Преобразует RGB [0, 255] в HLS [H: 0-360, L: 0-100, S: 0-100]"""
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    max_val = max(r_norm, g_norm, b_norm)
    min_val = min(r_norm, g_norm, b_norm)
    diff = max_val - min_val

    # Lightness
    l = (max_val + min_val) / 2

    # Saturation
    s = 0 if (max_val == min_val) else (diff / (2 * l) if l < 0.5 else diff / (2 - 2 * l))

    # Hue
    h = 0
    if max_val != min_val:
        if max_val == r_norm:
            h = (g_norm - b_norm) / diff + (6 if g_norm < b_norm else 0)
        elif max_val == g_norm:
            h = (b_norm - r_norm) / diff + 2
        elif max_val == b_norm:
            h = (r_norm - g_norm) / diff + 4
        h /= 6

    # Преобразуем в градусы и проценты
    h_deg = round(h * 360)
    l_percent = round(l * 100)
    s_percent = round(s * 100)

    return h_deg, l_percent, s_percent

def hls_to_rgb(h, l, s):
    """Преобразует HLS [H: 0-360, L: 0-100, S: 0-100] в RGB [0, 255]"""
    h_norm = h / 360.0
    l_norm = l / 100.0
    s_norm = s / 100.0

    if s_norm == 0:
        r = g = b = l_norm
    else:
        def hue_to_rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p

        q = l_norm * (1 + s_norm) if l_norm < 0.5 else l_norm + s_norm - l_norm * s_norm
        p = 2 * l_norm - q
        r = hue_to_rgb(p, q, h_norm + 1/3)
        g = hue_to_rgb(p, q, h_norm)
        b = hue_to_rgb(p, q, h_norm - 1/3)

    return (
        max(0, min(255, round(r * 255))),
        max(0, min(255, round(g * 255))),
        max(0, min(255, round(b * 255)))
    )

# --- Класс приложения ---

class ColorConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер Цветовых Моделей (CMYK-RGB-HLS)")

        # --- Переменные для хранения значений ---
        # RGB
        self.r_var = tk.IntVar(value=255)
        self.g_var = tk.IntVar(value=255)
        self.b_var = tk.IntVar(value=255)

        # CMYK
        self.c_var = tk.IntVar()
        self.m_var = tk.IntVar()
        self.y_var = tk.IntVar()
        self.k_var = tk.IntVar()

        # HLS
        self.h_var = tk.IntVar()
        self.l_var = tk.IntVar(value=50)
        self.s_var = tk.IntVar()

        # --- Создание интерфейса ---
        self.create_widgets()

        # --- Инициализация начального цвета ---
        self.update_display_from_rgb()

    def create_widgets(self):
        # --- Контейнер для отображения цвета ---
        display_frame = tk.Frame(self.root, padx=10, pady=10)
        display_frame.pack(fill=tk.X)

        self.color_label = tk.Label(
            display_frame,
            text="Текущий Цвет",
            font=("Arial", 12, "bold"),
            anchor="center",
            width=20
        )
        self.color_label.pack()

        self.color_display = tk.Label(
            display_frame,
            bg="#FFFFFF",
            width=20,
            height=5,
            relief="sunken",
            borderwidth=2
        )
        self.color_display.pack(pady=(5, 0))

        # --- Контейнер для всех моделей ---
        models_frame = tk.Frame(self.root, padx=10, pady=10)
        models_frame.pack(fill=tk.BOTH, expand=True)

        # --- CMYK ---
        cmyk_frame = tk.LabelFrame(models_frame, text="CMYK", padx=10, pady=10)
        cmyk_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        tk.Label(cmyk_frame, text="C (%)").grid(row=0, column=0, sticky="w")
        self.c_scale = tk.Scale(cmyk_frame, from_=0, to=100, orient="horizontal", variable=self.c_var, command=self.on_cmyk_change)
        self.c_scale.grid(row=0, column=1, sticky="ew", padx=5)
        self.c_entry = tk.Entry(cmyk_frame, width=5, textvariable=self.c_var, justify='center')
        self.c_entry.grid(row=0, column=2, padx=5)
        self.c_entry.bind("<Return>", lambda e: self.on_cmyk_entry_change())

        tk.Label(cmyk_frame, text="M (%)").grid(row=1, column=0, sticky="w")
        self.m_scale = tk.Scale(cmyk_frame, from_=0, to=100, orient="horizontal", variable=self.m_var, command=self.on_cmyk_change)
        self.m_scale.grid(row=1, column=1, sticky="ew", padx=5)
        self.m_entry = tk.Entry(cmyk_frame, width=5, textvariable=self.m_var, justify='center')
        self.m_entry.grid(row=1, column=2, padx=5)
        self.m_entry.bind("<Return>", lambda e: self.on_cmyk_entry_change())

        tk.Label(cmyk_frame, text="Y (%)").grid(row=2, column=0, sticky="w")
        self.y_scale = tk.Scale(cmyk_frame, from_=0, to=100, orient="horizontal", variable=self.y_var, command=self.on_cmyk_change)
        self.y_scale.grid(row=2, column=1, sticky="ew", padx=5)
        self.y_entry = tk.Entry(cmyk_frame, width=5, textvariable=self.y_var, justify='center')
        self.y_entry.grid(row=2, column=2, padx=5)
        self.y_entry.bind("<Return>", lambda e: self.on_cmyk_entry_change())

        tk.Label(cmyk_frame, text="K (%)").grid(row=3, column=0, sticky="w")
        self.k_scale = tk.Scale(cmyk_frame, from_=0, to=100, orient="horizontal", variable=self.k_var, command=self.on_cmyk_change)
        self.k_scale.grid(row=3, column=1, sticky="ew", padx=5)
        self.k_entry = tk.Entry(cmyk_frame, width=5, textvariable=self.k_var, justify='center')
        self.k_entry.grid(row=3, column=2, padx=5)
        self.k_entry.bind("<Return>", lambda e: self.on_cmyk_entry_change())

        # --- RGB ---
        rgb_frame = tk.LabelFrame(models_frame, text="RGB", padx=10, pady=10)
        rgb_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        tk.Label(rgb_frame, text="R").grid(row=0, column=0, sticky="w")
        self.r_scale = tk.Scale(rgb_frame, from_=0, to=255, orient="horizontal", variable=self.r_var, command=self.on_rgb_change)
        self.r_scale.grid(row=0, column=1, sticky="ew", padx=5)
        self.r_entry = tk.Entry(rgb_frame, width=5, textvariable=self.r_var, justify='center')
        self.r_entry.grid(row=0, column=2, padx=5)
        self.r_entry.bind("<Return>", lambda e: self.on_rgb_entry_change())

        tk.Label(rgb_frame, text="G").grid(row=1, column=0, sticky="w")
        self.g_scale = tk.Scale(rgb_frame, from_=0, to=255, orient="horizontal", variable=self.g_var, command=self.on_rgb_change)
        self.g_scale.grid(row=1, column=1, sticky="ew", padx=5)
        self.g_entry = tk.Entry(rgb_frame, width=5, textvariable=self.g_var, justify='center')
        self.g_entry.grid(row=1, column=2, padx=5)
        self.g_entry.bind("<Return>", lambda e: self.on_rgb_entry_change())

        tk.Label(rgb_frame, text="B").grid(row=2, column=0, sticky="w")
        self.b_scale = tk.Scale(rgb_frame, from_=0, to=255, orient="horizontal", variable=self.b_var, command=self.on_rgb_change)
        self.b_scale.grid(row=2, column=1, sticky="ew", padx=5)
        self.b_entry = tk.Entry(rgb_frame, width=5, textvariable=self.b_var, justify='center')
        self.b_entry.grid(row=2, column=2, padx=5)
        self.b_entry.bind("<Return>", lambda e: self.on_rgb_entry_change())

        # --- HLS ---
        hls_frame = tk.LabelFrame(models_frame, text="HLS", padx=10, pady=10)
        hls_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        tk.Label(hls_frame, text="H (°)").grid(row=0, column=0, sticky="w")
        self.h_scale = tk.Scale(hls_frame, from_=0, to=360, orient="horizontal", variable=self.h_var, command=self.on_hls_change)
        self.h_scale.grid(row=0, column=1, sticky="ew", padx=5)
        self.h_entry = tk.Entry(hls_frame, width=5, textvariable=self.h_var, justify='center')
        self.h_entry.grid(row=0, column=2, padx=5)
        self.h_entry.bind("<Return>", lambda e: self.on_hls_entry_change())

        tk.Label(hls_frame, text="L (%)").grid(row=1, column=0, sticky="w")
        self.l_scale = tk.Scale(hls_frame, from_=0, to=100, orient="horizontal", variable=self.l_var, command=self.on_hls_change)
        self.l_scale.grid(row=1, column=1, sticky="ew", padx=5)
        self.l_entry = tk.Entry(hls_frame, width=5, textvariable=self.l_var, justify='center')
        self.l_entry.grid(row=1, column=2, padx=5)
        self.l_entry.bind("<Return>", lambda e: self.on_hls_entry_change())

        tk.Label(hls_frame, text="S (%)").grid(row=2, column=0, sticky="w")
        self.s_scale = tk.Scale(hls_frame, from_=0, to=100, orient="horizontal", variable=self.s_var, command=self.on_hls_change)
        self.s_scale.grid(row=2, column=1, sticky="ew", padx=5)
        self.s_entry = tk.Entry(hls_frame, width=5, textvariable=self.s_var, justify='center')
        self.s_entry.grid(row=2, column=2, padx=5)
        self.s_entry.bind("<Return>", lambda e: self.on_hls_entry_change())

        # --- Кнопка выбора цвета ---
        button_frame = tk.Frame(self.root, padx=10, pady=10)
        button_frame.pack(fill=tk.X)

        self.color_picker_btn = tk.Button(button_frame, text="Выбрать Цвет", command=self.choose_color)
        self.color_picker_btn.pack(side=tk.LEFT)

        # --- Настройка растягивания сетки ---
        models_frame.columnconfigure(0, weight=1)
        models_frame.columnconfigure(1, weight=1)
        models_frame.columnconfigure(2, weight=1)

    # --- Обработчики событий ---
    def on_rgb_change(self, val):
        """Вызывается при изменении слайдера RGB"""
        self.update_display_from_rgb()

    def on_rgb_entry_change(self):
        """Вызывается при вводе значения в поле RGB"""
        # Ограничиваем значения от 0 до 255
        r = max(0, min(255, self.r_var.get()))
        g = max(0, min(255, self.g_var.get()))
        b = max(0, min(255, self.b_var.get()))
        self.r_var.set(r)
        self.g_var.set(g)
        self.b_var.set(b)
        self.update_display_from_rgb()

    def on_cmyk_change(self, val):
        """Вызывается при изменении слайдера CMYK"""
        self.update_display_from_cmyk()

    def on_cmyk_entry_change(self):
        """Вызывается при вводе значения в поле CMYK"""
        # Ограничиваем значения от 0 до 100
        c = max(0, min(100, self.c_var.get()))
        m = max(0, min(100, self.m_var.get()))
        y = max(0, min(100, self.y_var.get()))
        k = max(0, min(100, self.k_var.get()))
        self.c_var.set(c)
        self.m_var.set(m)
        self.y_var.set(y)
        self.k_var.set(k)
        self.update_display_from_cmyk()

    def on_hls_change(self, val):
        """Вызывается при изменении слайдера HLS"""
        self.update_display_from_hls()

    def on_hls_entry_change(self):
        """Вызывается при вводе значения в поле HLS"""
        # Ограничиваем значения H: 0-360, L,S: 0-100
        h = max(0, min(360, self.h_var.get()))
        l = max(0, min(100, self.l_var.get()))
        s = max(0, min(100, self.s_var.get()))
        self.h_var.set(h)
        self.l_var.set(l)
        self.s_var.set(s)
        self.update_display_from_hls()

    def choose_color(self):
        """Открывает окно выбора цвета"""
        color_code = colorchooser.askcolor(title="Выберите цвет")
        if color_code[0]: # Если пользователь не отменил выбор
            r, g, b = [int(c) for c in color_code[0]]
            self.r_var.set(r)
            self.g_var.set(g)
            self.b_var.set(b)
            self.update_display_from_rgb()

    # --- Функции обновления ---
    def update_display_from_rgb(self):
        """Обновляет все модели и отображение на основе текущего RGB"""
        r, g, b = self.r_var.get(), self.g_var.get(), self.b_var.get()
        # Обновляем CMYK
        c, m, y, k = rgb_to_cmyk(r, g, b)
        self.c_var.set(c)
        self.m_var.set(m)
        self.y_var.set(y)
        self.k_var.set(k)
        # Обновляем HLS
        h, l, s = rgb_to_hls(r, g, b)
        self.h_var.set(h)
        self.l_var.set(l)
        self.s_var.set(s)
        # Обновляем отображение цвета
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.color_display.config(bg=hex_color)
        self.color_label.config(text=f"Текущий Цвет: {hex_color.upper()}")

    def update_display_from_cmyk(self):
        """Обновляет все модели и отображение на основе текущего CMYK"""
        c, m, y, k = self.c_var.get(), self.m_var.get(), self.y_var.get(), self.k_var.get()
        # Обновляем RGB
        r, g, b = cmyk_to_rgb(c, m, y, k)
        self.r_var.set(r)
        self.g_var.set(g)
        self.b_var.set(b)
        # Обновляем HLS через RGB
        h, l, s = rgb_to_hls(r, g, b)
        self.h_var.set(h)
        self.l_var.set(l)
        self.s_var.set(s)
        # Обновляем отображение цвета
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.color_display.config(bg=hex_color)
        self.color_label.config(text=f"Текущий Цвет: {hex_color.upper()}")

    def update_display_from_hls(self):
        """Обновляет все модели и отображение на основе текущего HLS"""
        h, l, s = self.h_var.get(), self.l_var.get(), self.s_var.get()
        # Обновляем RGB
        r, g, b = hls_to_rgb(h, l, s)
        self.r_var.set(r)
        self.g_var.set(g)
        self.b_var.set(b)
        # Обновляем CMYK через RGB
        c, m, y, k = rgb_to_cmyk(r, g, b)
        self.c_var.set(c)
        self.m_var.set(m)
        self.y_var.set(y)
        self.k_var.set(k)
        # Обновляем отображение цвета
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.color_display.config(bg=hex_color)
        self.color_label.config(text=f"Текущий Цвет: {hex_color.upper()}")

# --- Запуск приложения ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ColorConverterApp(root)
    root.mainloop()