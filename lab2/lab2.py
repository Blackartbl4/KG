import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageTk

class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №2 - Вариант 3")
        self.root.geometry("1200x700")

        # Переменные для хранения изображений
        self.original_image = None  # Оригинал (OpenCV формат - BGR)
        self.processed_image = None # Обработанное (OpenCV формат - BGR)
        self.display_image_ref = None # Ссылка для Tkinter, чтобы не удалилось сборщиком мусора

        # --- Элементы интерфейса ---
        
        # Левая панель (Кнопки)
        self.control_frame = tk.Frame(root, width=250, bg="#f0f0f0")
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Button(self.control_frame, text="Загрузить изображение", command=self.load_image, bg="#ddd", height=2).pack(fill=tk.X, pady=5)
        
        # Секция 1: Гистограммы и контраст
        tk.Label(self.control_frame, text="--- Гистограмма и Контраст ---", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        
        tk.Button(self.control_frame, text="1. Линейное контрастирование", command=self.apply_linear_contrast).pack(fill=tk.X, pady=2)
        tk.Button(self.control_frame, text="2. Эквализация (поканально RGB)", command=self.apply_equalization_rgb).pack(fill=tk.X, pady=2)
        tk.Button(self.control_frame, text="3. Эквализация (HSV - Яркость)", command=self.apply_equalization_hsv).pack(fill=tk.X, pady=2)
        tk.Button(self.control_frame, text="Показать гистограммы", command=self.show_histograms, bg="#add8e6").pack(fill=tk.X, pady=10)

        # Секция 2: Высокочастотные фильтры (Резкость)
        tk.Label(self.control_frame, text="--- Повышение резкости ---", bg="#f0f0f0", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        
        tk.Button(self.control_frame, text="Фильтр Лапласа", command=self.apply_laplacian).pack(fill=tk.X, pady=2)
        tk.Button(self.control_frame, text="Unsharp Masking (Нечеткое маскирование)", command=self.apply_unsharp_mask).pack(fill=tk.X, pady=2)
        tk.Button(self.control_frame, text="Ядро повышения резкости (Kernel)", command=self.apply_sharpening_kernel).pack(fill=tk.X, pady=2)

        tk.Button(self.control_frame, text="Сбросить изменения", command=self.reset_image, bg="#ffcccb").pack(fill=tk.X, pady=(30, 5))

        # Правая панель (Отображение)
        self.image_frame = tk.Frame(root, bg="white")
        self.image_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.image_label = tk.Label(self.image_frame, text="Загрузите изображение для начала работы")
        self.image_label.pack(expand=True)

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if file_path:
            # Читаем изображение через OpenCV
            img = cv2.imread(file_path)
            if img is None:
                messagebox.showerror("Ошибка", "Не удалось открыть изображение.")
                return
            
            self.original_image = img
            self.processed_image = img.copy()
            self.show_image(self.processed_image)

    def show_image(self, cv_img):
        # Конвертация BGR -> RGB для отображения в Tkinter/PIL
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        im_pil = Image.fromarray(rgb_img)

        # Ресайз под размер окна (сохраняя пропорции)
        canvas_width = self.image_frame.winfo_width()
        canvas_height = self.image_frame.winfo_height()
        
        if canvas_width > 10 and canvas_height > 10: # Проверка, что окно отрисовалось
            im_pil.thumbnail((canvas_width, canvas_height))
        
        self.display_image_ref = ImageTk.PhotoImage(im_pil)
        self.image_label.config(image=self.display_image_ref, text="")

    def reset_image(self):
        if self.original_image is not None:
            self.processed_image = self.original_image.copy()
            self.show_image(self.processed_image)

    # ---------------- МЕТОДЫ ГРУППЫ 1: ГИСТОГРАММА И КОНТРАСТ ----------------

    def apply_linear_contrast(self):
        """Линейное контрастирование (растяжение гистограммы)"""
        if self.processed_image is None: return
        
        # Нормализация изображения от min до max -> 0 до 255
        img = self.processed_image.copy()
        # Используем normalize MinMax
        res = cv2.normalize(img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        
        self.processed_image = res
        self.show_image(self.processed_image)

    def apply_equalization_rgb(self):
        """Эквализация гистограммы (поканальная RGB)"""
        if self.processed_image is None: return
        
        img = self.processed_image.copy()
        # Разделяем каналы
        b, g, r = cv2.split(img)
        # Эквализируем каждый
        b_eq = cv2.equalizeHist(b)
        g_eq = cv2.equalizeHist(g)
        r_eq = cv2.equalizeHist(r)
        # Собираем обратно
        res = cv2.merge((b_eq, g_eq, r_eq))
        
        self.processed_image = res
        self.show_image(self.processed_image)

    def apply_equalization_hsv(self):
        """Эквализация гистограммы (только яркость в HSV)"""
        if self.processed_image is None: return
        
        img = self.processed_image.copy()
        # BGR -> HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # Эквализируем только V (яркость)
        v_eq = cv2.equalizeHist(v)
        
        # Собираем обратно
        hsv_eq = cv2.merge((h, s, v_eq))
        # HSV -> BGR
        res = cv2.cvtColor(hsv_eq, cv2.COLOR_HSV2BGR)
        
        self.processed_image = res
        self.show_image(self.processed_image)

    def show_histograms(self):
        """Построение гистограмм (сравнение Оригинала и Текущего)"""
        if self.original_image is None or self.processed_image is None: return
        
        plt.figure(figsize=(10, 5))
        
        # Гистограмма оригинала
        plt.subplot(1, 2, 1)
        plt.title("Оригинал (Гистограмма яркости)")
        gray_orig = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        plt.hist(gray_orig.ravel(), 256, [0, 256], color='gray')
        
        # Гистограмма обработанного
        plt.subplot(1, 2, 2)
        plt.title("Результат (Гистограмма яркости)")
        gray_proc = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2GRAY)
        plt.hist(gray_proc.ravel(), 256, [0, 256], color='blue')
        
        plt.show()

    # ---------------- МЕТОДЫ ГРУППЫ 2: ВЫСОКОЧАСТОТНЫЕ ФИЛЬТРЫ (РЕЗКОСТЬ) ----------------

    def apply_sharpening_kernel(self):
        """Применение стандартной матрицы свертки для резкости"""
        if self.processed_image is None: return
        
        # Ядро повышающее резкость (сумма элементов = 1, центр положительный большой)
        kernel = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]])
        
        # ddepth=-1 означает, что глубина выходного изображения такая же, как у исходного
        res = cv2.filter2D(self.processed_image, -1, kernel)
        
        self.processed_image = res
        self.show_image(self.processed_image)

    def apply_laplacian(self):
        """Добавление Лапласиана к изображению"""
        if self.processed_image is None: return

        img = self.processed_image.copy()
        # Убираем шумы перед поиском граней (опционально, но полезно)
        img_blur = cv2.GaussianBlur(img, (3, 3), 0)
        
        # Вычисляем Лапласиан (границы)
        laplacian = cv2.Laplacian(img_blur, cv2.CV_64F)
        # Преобразуем обратно в uint8
        laplacian = cv2.convertScaleAbs(laplacian)
        
        # Для увеличения резкости добавляем края к оригинальному изображению
        # alpha * src1 + beta * src2 + gamma
        res = cv2.addWeighted(img, 1.0, laplacian, -0.5, 0) # Коэффициенты можно менять
        
        # Простой вариант: резкое изображение = оригинал - k * Лапласиан (или + в зависимости от ядра)
        # Здесь используем более контролируемый addWeighted. 
        # Примечание: часто для резкости используют формулу: Image - Laplacian.
        
        # Вариант "в лоб" с готовым ядром часто работает нагляднее, попробуем ручное вычитание для наглядности:
        # res = cv2.subtract(img, laplacian) 
        
        # Но вернемся к проверенному методу "Unsharp Masking style via Laplacian"
        # Для простоты реализации в лабе часто достаточно просто показать сам Лапласиан
        # или использовать фильтр 2D. 
        # Если нужно именно "увеличение резкости", используем kernel метод выше.
        # Но раз кнопка отдельная, сделаем вариант сильного выделения краев:
        
        kernel_strong = np.array([[-1, -1, -1],
                                  [-1,  9, -1],
                                  [-1, -1, -1]])
        res = cv2.filter2D(img, -1, kernel_strong)

        self.processed_image = res
        self.show_image(self.processed_image)

    def apply_unsharp_mask(self):
        """Метод нечеткого маскирования (Unsharp Masking)"""
        if self.processed_image is None: return
        
        image = self.processed_image.copy()
        # 1. Размываем изображение (Gaussian Blur)
        gaussian = cv2.GaussianBlur(image, (9, 9), 10.0)
        
        # 2. Вычисляем маску (Оригинал - Размытое) - это детали
        # 3. Прибавляем маску к оригиналу: Sharp = Original + Amount * (Original - Blurred)
        
        res = cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)
        
        self.processed_image = res
        self.show_image(self.processed_image)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()