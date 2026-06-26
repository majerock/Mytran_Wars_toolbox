import os
import random
import threading
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import warnings
import json
from PIL import Image, ImageTk, ImageDraw, ImageFont

warnings.filterwarnings("ignore", category=DeprecationWarning)

from module_utils import parse_metrics_file_safely

class AutoGenerateFontDialog(tk.Toplevel):
    def __init__(self, parent, original_png, original_txt, on_success):
        super().__init__(parent)
        self.title("Генератор Кириллицы")
        self.geometry("480x680")
        self.configure(bg="#2b2b2b", padx=15, pady=15)
        self.transient(parent)
        
        self.parent = parent
        self.original_png = original_png
        self.original_txt = original_txt
        self.on_success = on_success
        
        with Image.open(original_png) as temp_img:
            self.img_mode = temp_img.mode
            
        self.parent_img_backup = parent.atlas_img.copy()
        self.parent_metrics_backup = {cid: m.copy() for cid, m in parent.metrics.items()}
        self.generation_success = False
        self.all_placed = False
        
        self.is_running = False
        self.stop_event = threading.Event()
        
        self.original_metrics, _ = parse_metrics_file_safely(self.original_txt)
        orig_space = self.original_metrics.get(32, {}).get('adv', 4)
        
        self.ttf_path = tk.StringVar()
        self.font_size = tk.IntVar(value=14)
        
        self.left_padding = tk.IntVar(value=1) 
        self.spacing_upper = tk.IntVar(value=2) 
        self.spacing_lower = tk.IntVar(value=1) 
        
        self.override_space = tk.BooleanVar(value=False)
        self.space_width = tk.IntVar(value=orig_space)
        
        self.y_offset = tk.IntVar(value=0)
        self.stroke_width = tk.IntVar(value=0) 
        self.bottom_padding = tk.IntVar(value=6) 
        self.gen_mode = tk.IntVar(value=1)     
        self.max_attempts = tk.IntVar(value=50)
        self.aa_mode = tk.StringVar(value="1. Стандартное (Мягкое)")
        self.alpha_threshold = tk.IntVar(value=50) # НОВАЯ ПЕРЕМЕННАЯ (Порог альфы)
        self.fake_bold = tk.BooleanVar(value=False)
        
        self.repack_english = tk.BooleanVar(value=True)
        self.redraw_english = tk.BooleanVar(value=False)
        self.custom_chars_var = tk.StringVar(value="БГДЁЖЗИЙЛПУФЦЧШЩЪЫЬЭЮЯбвгдеёжзийклмнптфцчшщъыьэюя")
        
        self.load_config()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_ui()
        
        for var in (self.font_size, self.spacing_upper, self.spacing_lower, self.space_width, self.left_padding, 
                    self.y_offset, self.stroke_width, self.max_attempts, self.gen_mode, self.custom_chars_var, 
                    self.aa_mode, self.alpha_threshold, self.bottom_padding, self.fake_bold, self.repack_english, 
                    self.redraw_english, self.ttf_path, self.override_space):
            var.trace_add("write", lambda *a: self.btn_save.config(state=tk.DISABLED))

    def load_config(self):
        try:
            if os.path.exists("generator_cfg.json"):
                with open("generator_cfg.json", "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.ttf_path.set(cfg.get("ttf_path", ""))
                    self.font_size.set(cfg.get("font_size", 14))
                    self.y_offset.set(cfg.get("y_offset", 0))
                    self.left_padding.set(cfg.get("left_padding", 1))
                    self.spacing_upper.set(cfg.get("spacing_upper", 2))
                    self.spacing_lower.set(cfg.get("spacing_lower", 1))
                    self.override_space.set(cfg.get("override_space", False))
                    self.space_width.set(cfg.get("space_width", self.space_width.get()))
                    self.stroke_width.set(cfg.get("stroke_width", 0))
                    self.bottom_padding.set(cfg.get("bottom_padding", 6))
                    self.aa_mode.set(cfg.get("aa_mode", "1. Стандартное (Мягкое)"))
                    self.alpha_threshold.set(cfg.get("alpha_threshold", 50))
                    self.fake_bold.set(cfg.get("fake_bold", False))
                    self.max_attempts.set(cfg.get("max_attempts", 50))
                    self.gen_mode.set(cfg.get("gen_mode", 1))
                    self.repack_english.set(cfg.get("repack_english", True))
                    self.redraw_english.set(cfg.get("redraw_english", False))
        except: pass

    def save_config(self):
        try:
            cfg = {
                "ttf_path": self.ttf_path.get(),
                "font_size": self.font_size.get(),
                "y_offset": self.y_offset.get(),
                "left_padding": self.left_padding.get(),
                "spacing_upper": self.spacing_upper.get(),
                "spacing_lower": self.spacing_lower.get(),
                "override_space": self.override_space.get(),
                "space_width": self.space_width.get(),
                "stroke_width": self.stroke_width.get(),
                "bottom_padding": self.bottom_padding.get(),
                "aa_mode": self.aa_mode.get(),
                "alpha_threshold": self.alpha_threshold.get(),
                "fake_bold": self.fake_bold.get(),
                "max_attempts": self.max_attempts.get(),
                "gen_mode": self.gen_mode.get(),
                "repack_english": self.repack_english.get(),
                "redraw_english": self.redraw_english.get()
            }
            with open("generator_cfg.json", "w", encoding="utf-8") as f:
                json.dump(cfg, f)
        except: pass

    def apply_anti_aliasing(self, img):
        mode = self.aa_mode.get()
        if "2." in mode: 
            r, g, b, a = img.split()
            a = a.point(lambda p: 255 if p > 64 else 0)
            img.putalpha(a)
        elif "3." in mode: 
            r, g, b, a = img.split()
            a = a.point(lambda p: min(255, int(p * 1.5)))
            img.putalpha(a)
        elif "4." in mode:
            r, g, b, a = img.split()
            a = a.point(lambda p: int((p / 255.0)**2 * 255))
            img.putalpha(a)
        elif "5." in mode:
            r, g, b, a = img.split()
            a = a.point(lambda p: 255 if p > 100 else 0)
            img.putalpha(a)
        return img

    def draw_text_with_fake_bold(self, draw_obj, coords, char, font, fill, stroke_w):
        x, y = coords
        draw_obj.text((x, y), char, font=font, fill=fill, stroke_width=stroke_w)
        if self.fake_bold.get():
            draw_obj.text((x + 1, y), char, font=font, fill=fill, stroke_width=stroke_w)

    def setup_ui(self):
        f_font = tk.LabelFrame(self, text="Файл шрифта (.ttf / .otf)", bg="#2b2b2b", fg="white", padx=10, pady=5)
        f_font.pack(fill=tk.X, pady=(0, 5))
        tk.Entry(f_font, textvariable=self.ttf_path).pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        tk.Button(f_font, text="Обзор", command=self.browse_ttf).pack(side=tk.RIGHT)
        
        p_frame = tk.LabelFrame(self, text="Настройки размера и рендера", bg="#2b2b2b", fg="#ffcc00", font=("Arial", 9, "bold"), padx=10, pady=8)
        p_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(p_frame, text="Размер (pt):", bg="#2b2b2b", fg="white").grid(row=0, column=0, sticky="w")
        tk.Spinbox(p_frame, from_=5, to=40, textvariable=self.font_size, width=5).grid(row=0, column=1, padx=(5, 10), sticky="w")
        
        tk.Label(p_frame, text="Сдвиг по Y:", bg="#2b2b2b", fg="white").grid(row=0, column=2, sticky="w")
        tk.Spinbox(p_frame, from_=-15, to=15, textvariable=self.y_offset, width=5).grid(row=0, column=3, padx=(5, 0), sticky="w")

        tk.Label(p_frame, text="Отступ слева:", bg="#2b2b2b", fg="#00ff00").grid(row=1, column=0, sticky="w", pady=(8, 0))
        tk.Spinbox(p_frame, from_=0, to=10, textvariable=self.left_padding, width=5).grid(row=1, column=1, padx=(5, 10), pady=(8, 0), sticky="w")

        tk.Label(p_frame, text="Справа (ЗАГЛ):", bg="#2b2b2b", fg="#00ff00").grid(row=1, column=2, sticky="w", pady=(8, 0))
        tk.Spinbox(p_frame, from_=0, to=10, textvariable=self.spacing_upper, width=5).grid(row=1, column=3, padx=(5, 0), pady=(8, 0), sticky="w")

        tk.Label(p_frame, text="Справа (строч):", bg="#2b2b2b", fg="#00ff00").grid(row=2, column=0, sticky="w", pady=(8, 0))
        tk.Spinbox(p_frame, from_=0, to=10, textvariable=self.spacing_lower, width=5).grid(row=2, column=1, padx=(5, 10), pady=(8, 0), sticky="w")

        tk.Checkbutton(p_frame, text="Свой пробел:", variable=self.override_space, bg="#2b2b2b", fg="#00ff00", selectcolor="#444").grid(row=2, column=2, sticky="w", pady=(8, 0))
        tk.Spinbox(p_frame, from_=0, to=30, textvariable=self.space_width, width=5).grid(row=2, column=3, padx=(5, 0), pady=(8, 0), sticky="w")

        tk.Label(p_frame, text="Защита низа:", bg="#2b2b2b", fg="#ff6666").grid(row=3, column=0, sticky="w", pady=(8, 0))
        tk.Spinbox(p_frame, from_=0, to=30, textvariable=self.bottom_padding, width=5).grid(row=3, column=1, padx=(5, 10), pady=(8, 0), sticky="w")

        tk.Label(p_frame, text="Толщ. обводки:", bg="#2b2b2b", fg="white").grid(row=3, column=2, sticky="w", pady=(8, 0))
        tk.Spinbox(p_frame, from_=0, to=3, textvariable=self.stroke_width, width=5).grid(row=3, column=3, padx=(5, 0), pady=(8, 0), sticky="w")

        tk.Label(p_frame, text="Сглаживание:", bg="#2b2b2b", fg="#00ffff").grid(row=4, column=0, sticky="w", pady=(8, 0))
        aa_combo = ttk.Combobox(p_frame, textvariable=self.aa_mode, values=[
            "1. Стандартное (Мягкое)", 
            "2. Резкое (Жирное)", 
            "3. Насыщенное",
            "4. Тонкое (Истончение альфы)",
            "5. Без сглаживания (Пиксельный)"
        ], state="readonly", width=18)
        aa_combo.grid(row=4, column=1, columnspan=2, padx=(5, 0), pady=(8, 0), sticky="w")
        
        tk.Checkbutton(p_frame, text="Fake Bold", variable=self.fake_bold, bg="#2b2b2b", fg="#ff66ff", selectcolor="#444").grid(row=4, column=3, sticky="w", pady=(8, 0))
        
        # НОВЫЙ ПОЛЗУНОК ДЛЯ АЛЬФЫ
        tk.Label(p_frame, text="Порог обрезки альфы (0-255):", bg="#2b2b2b", fg="#ffaa00").grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))
        tk.Scale(p_frame, from_=0, to=255, orient=tk.HORIZONTAL, variable=self.alpha_threshold, bg="#2b2b2b", fg="white", highlightthickness=0).grid(row=5, column=2, columnspan=2, sticky="we", padx=(5, 0))
        
        m_frame = tk.LabelFrame(self, text="Глобальный Трассировщик", bg="#2b2b2b", fg="#00ff00", font=("Arial", 9, "bold"), padx=10, pady=5)
        m_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(m_frame, text="Кол-во попыток тасования:", bg="#2b2b2b", fg="white").grid(row=0, column=0, sticky="w")
        tk.Spinbox(m_frame, from_=1, to=500, textvariable=self.max_attempts, width=5).grid(row=0, column=1, padx=5, sticky="w")
        
        tk.Radiobutton(m_frame, text="1. МАКСИМАЛЬНАЯ ЭКОНОМИЯ (Клонирование)", variable=self.gen_mode, value=1, bg="#2b2b2b", fg="white", selectcolor="#444").grid(row=1, column=0, columnspan=2, sticky="w", pady=(5,0))
        
        tk.Entry(m_frame, textvariable=self.custom_chars_var, font=("Consolas", 9)).grid(row=2, column=0, columnspan=2, sticky="we", padx=15, pady=(0,5))
                       
        tk.Radiobutton(m_frame, text="2. МОНОЛИТ (Рисуем все 66 букв)", variable=self.gen_mode, value=2, bg="#2b2b2b", fg="#00ffff", selectcolor="#444").grid(row=3, column=0, columnspan=2, sticky="w")
        
        tk.Checkbutton(m_frame, text="3. Переупаковка (Чистый холст - МАКС места!)", variable=self.repack_english, bg="#2b2b2b", fg="#ffaa00", selectcolor="#444").grid(row=4, column=0, columnspan=2, sticky="w", pady=(5,0))
        tk.Checkbutton(m_frame, text="4. Перерисовать алфавит (A-Z, a-z) из TTF", variable=self.redraw_english, bg="#2b2b2b", fg="#ffaa00", selectcolor="#444").grid(row=5, column=0, columnspan=2, sticky="w")
        
        self.router_frame = tk.Frame(self, bg="#2b2b2b")
        self.router_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self.router_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, side=tk.TOP, pady=(0, 5))
        
        self.lbl_status = tk.Label(self.router_frame, text="Готов к трассировке. Нажмите старт.", bg="#2b2b2b", fg="#00ffff", font=("Consolas", 10, "bold"))
        self.lbl_status.pack(side=tk.TOP)
        
        btn_frame = tk.Frame(self, bg="#2b2b2b")
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        btn_orig = tk.Button(btn_frame, text="ПОДСМОТРЕТЬ ОРИГИНАЛЬНЫЙ ТЕКСТ (УДЕРЖИВАТЬ)", bg="#555555", fg="white", font=("Arial", 9, "bold"), height=1)
        btn_orig.pack(fill=tk.X, pady=(0, 5))
        btn_orig.bind("<ButtonPress-1>", self.show_original)
        btn_orig.bind("<ButtonRelease-1>", self.show_current)

        sub_btn_frame = tk.Frame(btn_frame, bg="#2b2b2b")
        sub_btn_frame.pack(fill=tk.X)
        
        self.btn_run_sim = tk.Button(sub_btn_frame, text="СТАРТ ТРАССИРОВКИ", bg="#d97a00", fg="white", font=("Arial", 10, "bold"), height=2, command=self.toggle_simulation)
        self.btn_run_sim.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.btn_save = tk.Button(sub_btn_frame, text="ЗАПИСАТЬ В ФАЙЛЫ", bg="#4a8b54", fg="white", font=("Arial", 10, "bold"), height=2, state=tk.DISABLED, command=self.generate)
        self.btn_save.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

    def browse_ttf(self):
        path = filedialog.askopenfilename(filetypes=[("TrueType Font", "*.ttf *.otf")])
        if path: self.ttf_path.set(path)

    def show_original(self, event):
        psp_screen = Image.new("RGBA", (480, 272), (26, 59, 92, 255))
        draw = ImageDraw.Draw(psp_screen)
        
        if self.parent.show_guidelines.get():
            for i in range(12):
                y_line = 30 + i * self.parent.line_height
                draw.line([0, y_line, 480, y_line], fill=(255, 255, 255, 50))
                
        cursor_x, cursor_y = 20, 30
        try: encoded_bytes = self.parent.text_input.get("1.0", tk.END).rstrip('\n').encode('cp1251', errors='replace')
        except: encoded_bytes = b''
        
        for b in encoded_bytes:
            if b == 10: 
                cursor_x = 20; cursor_y += self.parent.line_height; continue
                
            game_id = b + self.parent.sim_shift.get()
            if game_id in self.parent_metrics_backup:
                m = self.parent_metrics_backup[game_id]
                if m['adv'] > 0 or m['h'] > 0:
                    tw = m['adv'] if self.parent.sim_game_engine.get() else m['w']
                    try: 
                        crop = self.parent_img_backup.crop((m['tx'], m['ty'], m['tx'] + tw, m['ty'] + m['h']))
                        pos = (cursor_x + m['ox'], cursor_y + m['oy'])
                        psp_screen.paste(crop, pos, crop)
                        
                        if self.parent.show_debug_boxes.get():
                            draw.rectangle([pos[0], pos[1], pos[0] + tw - 1, pos[1] + m['h'] - 1], outline=(255, 68, 68, 180))
                    except: pass
                cursor_x += m['adv']
                
        if self.parent.scale_x2.get(): psp_screen = psp_screen.resize((960, 544), Image.Resampling.NEAREST)
        self.tk_temp_screen = ImageTk.PhotoImage(psp_screen)
        self.parent.screen_canvas.create_image(480, 272, anchor=tk.CENTER, image=self.tk_temp_screen)

    def show_current(self, event):
        self.parent.render_preview()

    def get_latin_clones_map(self):
        return {
            'А': 64, 'В': 65, 'Е': 68, 'К': 74, 'М': 76, 'Н': 71, 'О': 78, 'Р': 79, 'С': 66, 'Т': 83, 'Х': 87,
            'а': 96, 'е': 100, 'о': 110, 'р': 111, 'с': 98, 'у': 120, 'х': 119
        }

    def safe_ui_update(self, func):
        self.after(0, func)

    def toggle_simulation(self):
        ttf = self.ttf_path.get()
        if not ttf or not os.path.exists(ttf): 
            messagebox.showerror("Ошибка", "Выберите файл шрифта TTF!")
            return
            
        if self.is_running:
            self.stop_event.set()
            self.btn_run_sim.config(text="ОСТАНАВЛИВАЮ...", state=tk.DISABLED)
        else:
            self.is_running = True
            self.stop_event.clear()
            self.btn_run_sim.config(text="СТОП (Прервать)", bg="#cc0000")
            self.btn_save.config(state=tk.DISABLED)
            threading.Thread(target=self._router_worker, daemon=True).start()

    def _router_worker(self):
        ttf = self.ttf_path.get()
        size = self.font_size.get()
        left_pad = self.left_padding.get()
        y_off = self.y_offset.get()
        stroke, mode, max_tries = self.stroke_width.get(), self.gen_mode.get(), self.max_attempts.get()
        bottom_pad = self.bottom_padding.get()
        alpha_threshold = self.alpha_threshold.get() # Читаем порог из слайдера
        
        spacing_up = self.spacing_upper.get()
        spacing_low = self.spacing_lower.get()
        
        repack_en = self.repack_english.get()
        redraw_en = self.redraw_english.get()
        if redraw_en: repack_en = True 
        
        override_space = self.override_space.get()
        
        try:
            self.safe_ui_update(lambda: self.lbl_status.config(text="Инициализация масок и зачистка...", fg="yellow"))
            
            sim_metrics = {cid: m.copy() for cid, m in self.parent_metrics_backup.items()}
            font = ImageFont.truetype(ttf, size=size)
            row_h = self.original_metrics[65]['h'] if 65 in self.original_metrics else size
            
            cyrillic_tasks = []
            latin_tasks = []
            orig_tasks = []
            
            latin_map = self.get_latin_clones_map()
            custom_chars = self.custom_chars_var.get()
            
            for cid in range(191, 255):
                char = bytes([cid+1]).decode('cp1251', errors='replace')
                if mode == 1 and char not in custom_chars and char in latin_map: pass
                else: cyrillic_tasks.append((cid, char))
                    
            for cid, char in [(167, 'Ё'), (183, 'ё')]:
                if mode != 1 or char in custom_chars: cyrillic_tasks.append((cid, char))
            
            IMMUTABLE_IDS = {127, 128, 129, 130, 131, 132}
            
            if repack_en:
                for cid in range(32, 191):
                    if cid in IMMUTABLE_IDS or cid in (167, 183, 188, 189): continue
                    if cid == 32 and override_space: continue 
                        
                    if cid in self.original_metrics and self.original_metrics[cid]['adv'] > 0:
                        is_alpha = (65 <= cid <= 90) or (97 <= cid <= 122)
                        if is_alpha and redraw_en:
                            latin_tasks.append((cid, chr(cid)))
                        else:
                            orig_tasks.append(cid)

            base_unplaced = []
            
            if override_space:
                space_adv = self.space_width.get()
                space_img = Image.new("RGBA", (space_adv, row_h), (0,0,0,0))
                base_unplaced.append({
                    'cid': 32, 'char': 'Space', 'w': space_adv, 'adv': space_adv, 'pack_w': space_adv,
                    'img': space_img, 'exact_h': row_h, 'ox': 0, 'oy': 0
                })

            for cid, char in cyrillic_tasks + latin_tasks:
                canvas_h = max(row_h + 40, size * 2 + 20)
                temp_canvas = Image.new("RGBA", (100, canvas_h), (0,0,0,0)) 
                l_draw = ImageDraw.Draw(temp_canvas)
                
                DRAW_X = 30
                l_draw.text((DRAW_X, 0), char, font=font, fill=(255,255,255,255), stroke_width=stroke)
                if self.fake_bold.get(): l_draw.text((DRAW_X + 1, 0), char, font=font, fill=(255,255,255,255), stroke_width=stroke)
                temp_canvas = self.apply_anti_aliasing(temp_canvas)
                
                visual_w = int(font.getlength(char))
                if self.fake_bold.get(): visual_w += 1
                if stroke > 0: visual_w += stroke * 2
                
                current_space = spacing_low if char.islower() else spacing_up
                adv = left_pad + visual_w + current_space
                pack_w = max(visual_w + left_pad, adv) 
                
                alpha = temp_canvas.split()[-1]
                # Используем порог из интерфейса
                clean_alpha = alpha.point(lambda p: 255 if p > alpha_threshold else 0)
                bbox = clean_alpha.getbbox()
                crop_left = DRAW_X - left_pad
                
                if bbox:
                    exact_h = bbox[3] + 1
                    char_img = temp_canvas.crop((crop_left, 0, crop_left + pack_w, exact_h))
                else:
                    exact_h = row_h
                    char_img = temp_canvas.crop((crop_left, 0, crop_left + pack_w, row_h))

                base_unplaced.append({
                    'cid': cid, 'char': char, 'w': visual_w, 'adv': adv, 'pack_w': pack_w,
                    'img': char_img, 'exact_h': exact_h, 'ox': 0, 'oy': y_off 
                })

            for cid in orig_tasks:
                m = self.original_metrics[cid]
                pack_w = max(m['w'], m['adv'])
                if pack_w <= 0 or m['h'] <= 0: continue
                
                orig_crop = self.parent_img_backup.crop((m['tx'], m['ty'], m['tx'] + pack_w, m['ty'] + m['h']))
                bbox = orig_crop.split()[-1].getbbox()
                
                if bbox:
                    exact_h = bbox[3] + 1 
                    char_img = orig_crop.crop((0, 0, pack_w, exact_h))
                else:
                    exact_h = m['h']
                    char_img = orig_crop
                    
                base_unplaced.append({
                    'cid': cid, 'char': f"Orig_{cid}", 'w': m['w'], 'adv': m['adv'], 'pack_w': pack_w,
                    'img': char_img, 'exact_h': exact_h, 'ox': m['ox'], 'oy': m['oy']
                })

            total_chars = len(base_unplaced)

            if repack_en:
                sim_img = Image.new("RGBA", self.parent_img_backup.size, (0,0,0,0))
                for cid in IMMUTABLE_IDS:
                    if cid in self.original_metrics:
                        m = self.original_metrics[cid]
                        if m['adv'] > 0 and m['h'] > 0:
                            box = (m['tx'], m['ty'], m['tx'] + max(m['w'], m['adv']), m['ty'] + m['h'])
                            sim_img.paste(self.parent_img_backup.crop(box), (m['tx'], m['ty']))
                
                if bottom_pad > 0:
                    bottom_box = (0, sim_img.height - bottom_pad, sim_img.width, sim_img.height)
                    bottom_strip = self.parent_img_backup.crop(bottom_box)
                    sim_img.paste(bottom_strip, bottom_box[:2])
            else:
                sim_img = self.parent_img_backup.copy()
                
                safe_boxes = set()
                WALL_IDS = [c for c in range(32, 191) if c not in (188, 189, 167, 183)]
                
                if override_space and 32 in WALL_IDS:
                    WALL_IDS.remove(32)
                
                for cid in WALL_IDS:
                    if cid in self.original_metrics:
                        m = self.original_metrics[cid]
                        safe_boxes.add((m['tx'], m['ty'], m['w'], m['h']))
                
                WIPE_IDS = list(range(191, 255)) + [188, 189]
                if override_space:
                    WIPE_IDS.append(32)
                
                for cid in WIPE_IDS:
                    if cid in self.original_metrics:
                        m = self.original_metrics[cid]
                        box = (m['tx'], m['ty'], m['w'], m['h'])
                        if box not in safe_boxes and m['adv'] > 0 and m['h'] > 0:
                            x1, y1 = m['tx'], m['ty']
                            x2, y2 = x1 + max(m['adv'], m['w']), y1 + m['h']
                            sim_img.paste(Image.new("RGBA", (x2-x1, y2-y1), (0,0,0,0)), (x1, y1))

            base_mask_b = Image.new("1", (sim_img.width, sim_img.height), 0)
            draw_b = ImageDraw.Draw(base_mask_b)

            for cid in IMMUTABLE_IDS if repack_en else WALL_IDS:
                if cid in self.original_metrics:
                    m = self.original_metrics[cid]
                    if m['adv'] > 0 and m['h'] > 0:
                        box_w = max(m['w'], m['adv'])
                        if box_w > 0:
                            draw_b.rectangle([m['tx'], m['ty'], m['tx'] + box_w - 1, m['ty'] + m['h'] - 1], fill=1)

            if bottom_pad > 0:
                draw_b.rectangle([0, sim_img.height - bottom_pad, sim_img.width, sim_img.height], fill=1)

            best_placed_count = -1
            best_img = None
            best_metrics = None
            best_missing = []

            for attempt in range(max_tries):
                if self.stop_event.is_set(): break
                
                self.safe_ui_update(lambda att=attempt: self.progress_var.set((att / max_tries) * 100))
                self.safe_ui_update(lambda msg=f"Трассировка... Попытка {attempt+1} из {max_tries} (Лучший: {max(0, best_placed_count)}/{total_chars})": self.lbl_status.config(text=msg, fg="#ffcc00"))
                
                curr_img = sim_img.copy()
                curr_metrics = {k: v.copy() for k, v in sim_metrics.items()}
                curr_mask_b = base_mask_b.copy()
                draw_b_curr = ImageDraw.Draw(curr_mask_b)
                
                queue = list(base_unplaced)
                
                if attempt == 0: queue.sort(key=lambda x: x['exact_h'] * x['adv'], reverse=True) 
                elif attempt == 1: queue.sort(key=lambda x: x['exact_h'], reverse=True) 
                else: random.shuffle(queue) 
                
                unplaced_this_run = []
                placed_count = 0
                
                for c_data in queue:
                    placed = False
                    
                    for y in range(0, curr_img.height - c_data['exact_h'] - bottom_pad + 2):
                        for x in range(2, curr_img.width - c_data['pack_w'] + 1):
                            
                            b_check = (x, y, x + c_data['pack_w'], y + c_data['exact_h'])
                            if curr_mask_b.crop(b_check).getbbox() is not None: continue
                            
                            placed = True
                            curr_img.paste(c_data['img'], (x, y))
                            
                            curr_metrics[c_data['cid']] = {
                                'ox': c_data['ox'], 'oy': c_data['oy'], 'w': c_data['w'], 
                                'tx': x, 'ty': y, 'adv': c_data['adv'], 'h': c_data['exact_h']
                            }
                            
                            draw_b_curr.rectangle([x, y, x + c_data['pack_w'] - 1, y + c_data['exact_h'] - 1], fill=1)
                            
                            placed_count += 1
                            break
                        if placed: break
                    
                    if not placed:
                        unplaced_this_run.append(c_data['char'])
                
                if placed_count > best_placed_count:
                    best_placed_count = placed_count
                    best_img = curr_img
                    best_metrics = curr_metrics
                    best_missing = unplaced_this_run
                    
                    if mode == 1:
                        for cid in range(191, 255):
                            char = bytes([cid+1]).decode('cp1251', errors='replace')
                            if char not in custom_chars and char in latin_map:
                                lat_id = latin_map[char]
                                if lat_id in best_metrics:
                                    best_metrics[cid] = best_metrics[lat_id].copy()
                                    
                    if 187 in best_metrics:
                        best_metrics[188] = best_metrics[187].copy()
                        best_metrics[189] = best_metrics[187].copy()
                    
                    self.parent.atlas_img = best_img
                    self.parent.metrics = best_metrics
                    
                    # Сохраняем состояние для Ctrl+Z перед тем, как обновить Студию
                    self.safe_ui_update(self.parent.save_state)
                    self.safe_ui_update(self.parent.draw_atlas)
                    self.safe_ui_update(self.parent.render_preview)
                    
                if best_placed_count == total_chars:
                    break 
                    
            self.safe_ui_update(lambda: self.progress_var.set(100))
            
            if self.stop_event.is_set():
                self.safe_ui_update(lambda: self.lbl_status.config(text=f"ПРЕРВАНО ПОЛЬЗОВАТЕЛЕМ. Лучший результат: {best_placed_count}/{total_chars}", fg="#ffaa00"))
                self.all_placed = False
            elif best_placed_count == total_chars:
                self.safe_ui_update(lambda: self.lbl_status.config(text=f"УСПЕХ! Все {total_chars} символов идеально упакованы.", fg="#00ff00"))
                self.all_placed = True
            else:
                missing = "".join([m for m in best_missing if not m.startswith("Orig")])
                orig_miss = len([m for m in best_missing if m.startswith("Orig")])
                err_text = f"НЕ ВЛЕЗЛО {len(best_missing)}: "
                if missing: err_text += f"{missing} "
                if orig_miss: err_text += f"и {orig_miss} ориг."
                self.safe_ui_update(lambda: self.lbl_status.config(text=err_text + " Убавьте pt.", fg="#ff4444"))
                self.all_placed = False

        except Exception as e: 
            self.safe_ui_update(lambda: self.lbl_status.config(text=f"Ошибка: {e}", fg="red"))
            traceback.print_exc()
        finally:
            self.is_running = False
            self.safe_ui_update(lambda: self.btn_run_sim.config(text="СТАРТ ТРАССИРОВКИ", bg="#d97a00", state=tk.NORMAL))
            self.safe_ui_update(lambda: self.btn_save.config(state=tk.NORMAL))

    def generate(self):
        if not getattr(self, 'all_placed', False):
            if not messagebox.askyesno("Внимание", "Не все буквы влезли на текстуру!\n\nВы уверены, что хотите сохранить неполный шрифт?"):
                return
                
        ttf = self.ttf_path.get()
        if not ttf or not os.path.exists(ttf): return
            
        try:
            self.save_config()
            clean_base = self.original_png.replace(".png", "")
            while clean_base.endswith("_ru"): clean_base = clean_base[:-3]
            out_png = f"{clean_base}_ru.png"
            
            out_txt = self.original_txt.replace(".txt", "")
            while out_txt.endswith("_ru"): out_txt = out_txt[:-3]
            out_txt = f"{out_txt}_ru.txt"
            
            img = self.parent.atlas_img.copy()
            metrics = self.parent.metrics
            
            if self.img_mode == "P":
                img_indexed = img.convert("P", palette=Image.Palette.ADAPTIVE, colors=16)
                img_indexed.save(out_png)
            else:
                img.save(out_png)
            
            with open(self.original_txt, 'r', encoding='utf-8') as f:
                header_lines = f.readlines()[:3]
            
            with open(out_txt, 'w', encoding='utf-8') as f:
                for hl in header_lines: f.write(hl)
                for char_id in range(256):
                    if char_id in metrics:
                        m = metrics[char_id]
                        char_repr = chr(char_id) if 32 <= char_id <= 126 else "N/A"
                        f.write(f"{char_id:03d} | '{char_repr:4s}' | {m['ox']:5d} | {m['oy']:5d} | {m['w']:5d} | {m['tx']:5d} | {m['ty']:5d} | {m['adv']:7d} | {m['h']:6d}\n")
                    else:
                        f.write(f"{char_id:03d} | 'N/A ' |     0 |     0 |     0 |     0 |     0 |       0 |      0\n")
                        
            self.generation_success = True
            self.on_success(out_png, out_txt)
            messagebox.showinfo("Успех!", f"Шрифт успешно записан!\n\nФайлы сохранены:\n{os.path.basename(out_png)}\n{os.path.basename(out_txt)}")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка генерации", str(e))

    def on_close(self):
        self.stop_event.set()
        self.save_config()
        if not self.generation_success:
            self.parent.undo() # Откатываемся через систему истории, если не сохранили
        self.destroy()