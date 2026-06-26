import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw

from module_utils import parse_metrics_file_safely
from module_generator import AutoGenerateFontDialog

class FontStudioWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Mytran Wars - Font Atlas Studio (VISUAL METRICS EDITOR)")
        self.geometry("1650x880")
        self.configure(bg="#2b2b2b")
        self.transient(parent)
        
        self.img_path = tk.StringVar()
        self.txt_path = tk.StringVar()
        self.scale_x2 = tk.BooleanVar(value=True)
        self.sim_game_engine = tk.BooleanVar(value=True) 
        self.show_debug_boxes = tk.BooleanVar(value=True)
        self.show_guidelines = tk.BooleanVar(value=True)
        self.sim_shift = tk.IntVar(value=-1)   
        
        self.atlas_img = None
        self.tk_atlas = None
        self.tk_screen = None
        
        self.metrics = {}
        self.line_height = 20
        self.selected_id = None
        
        # СИСТЕМА ИСТОРИИ (Ctrl+Z)
        self.history = []
        
        self.setup_ui()
        self.load_studio_config()
        
        # Биндим Ctrl+Z глобально на окно
        self.bind("<Control-z>", self.undo)
        self.bind("<Control-Z>", self.undo)
        self.bind("<Control-я>", self.undo)
        self.bind("<Control-Я>", self.undo)

    def load_studio_config(self):
        if os.path.exists("studio_cfg.txt"):
            try:
                with open("studio_cfg.txt", "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f.readlines()]
                    if len(lines) >= 2:
                        self.img_path.set(lines[0])
                        self.txt_path.set(lines[1])
                        self.load_font_data(silent=True)
            except: pass

    def save_studio_config(self):
        try:
            with open("studio_cfg.txt", "w", encoding="utf-8") as f:
                f.write(f"{self.img_path.get()}\n{self.txt_path.get()}\n")
        except: pass

    # --- ЛОГИКА ИСТОРИИ (UNDO) ---
    def save_state(self):
        if not self.atlas_img or not self.metrics: return
        img_copy = self.atlas_img.copy()
        met_copy = {cid: m.copy() for cid, m in self.metrics.items()}
        self.history.append((img_copy, met_copy))
        if len(self.history) > 20: # Храним последние 20 действий
            self.history.pop(0)

    def undo(self, event=None):
        # Игнорируем, если фокус в текстовом поле (там свой Ctrl+Z)
        if event and event.widget == self.text_input:
            return
            
        if not self.history:
            self.txt_info.delete("1.0", tk.END)
            self.txt_info.insert("1.0", "История пуста, отменять нечего!")
            return
            
        img, met = self.history.pop()
        self.atlas_img = img
        self.metrics = met
        self.draw_atlas()
        self.render_preview()
        
        if self.selected_id is not None and self.selected_id in self.metrics:
            self.update_info_panel(self.selected_id)
            
        self.txt_info.delete("1.0", tk.END)
        self.txt_info.insert("1.0", "Отмена выполнена (Ctrl+Z)!")

    def setup_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        
        top_frame = tk.Frame(self, bg="#3c3f41", pady=10, padx=10)
        top_frame.pack(fill=tk.X)
        
        tk.Label(top_frame, text="Текстура (.png):", bg="#3c3f41", fg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(top_frame, textvariable=self.img_path, width=28).grid(row=0, column=1, padx=5)
        tk.Button(top_frame, text="Обзор", command=lambda: self.browse_file(self.img_path, [("PNG", "*.png")])).grid(row=0, column=2)
        
        tk.Label(top_frame, text="Метрики (.txt):", bg="#3c3f41", fg="white").grid(row=1, column=0, sticky="w", pady=5)
        tk.Entry(top_frame, textvariable=self.txt_path, width=28).grid(row=1, column=1, padx=5)
        tk.Button(top_frame, text="Обзор", command=lambda: self.browse_file(self.txt_path, [("TXT", "*.txt")])).grid(row=1, column=2)
        
        tk.Button(top_frame, text="ЗАГРУЗИТЬ", bg="#4a8b54", fg="white", font=("Arial", 9, "bold"), command=self.load_font_data).grid(row=0, column=3, rowspan=2, padx=10, sticky="ns")
        tk.Button(top_frame, text="АВТО-ГЕНЕРАТОР КИРИЛЛИЦЫ", bg="#d97a00", fg="white", font=("Arial", 9, "bold"), command=self.open_auto_generator).grid(row=0, column=4, rowspan=2, padx=10, sticky="ns")
        
        tk.Label(top_frame, text="Сдвиг Ввода ID:", bg="#3c3f41", fg="#ffcc00").grid(row=0, column=5, padx=(10, 2), sticky="e")
        tk.Spinbox(top_frame, from_=-5, to=5, textvariable=self.sim_shift, width=3, command=self.render_preview).grid(row=0, column=6, sticky="w")
        
        tk.Button(top_frame, text="СОХРАНИТЬ МЕТРИКИ", bg="#0066cc", fg="white", font=("Arial", 9, "bold"), command=self.save_metrics).grid(row=0, column=7, rowspan=2, padx=15, sticky="ns")
        
        tk.Checkbutton(top_frame, text="PSP Экран x2", variable=self.scale_x2, command=self.render_preview, bg="#3c3f41", fg="white", selectcolor="#2b2b2b").grid(row=0, column=8, padx=5, sticky="w")
        tk.Checkbutton(top_frame, text="Игровой рендер (W = Advance)", variable=self.sim_game_engine, command=self.render_preview, bg="#3c3f41", fg="#00ffff", selectcolor="#2b2b2b").grid(row=1, column=8, padx=5, sticky="w")
        
        tk.Checkbutton(top_frame, text="Debug Рамки движка", variable=self.show_debug_boxes, command=self.render_preview, bg="#3c3f41", fg="#ff6666", selectcolor="#2b2b2b").grid(row=0, column=9, padx=5, sticky="w")
        tk.Checkbutton(top_frame, text="Опорные линии (Baseline)", variable=self.show_guidelines, command=self.render_preview, bg="#3c3f41", fg="#00ff00", selectcolor="#2b2b2b").grid(row=1, column=9, padx=5, sticky="w")

        main_frame = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = tk.Frame(main_frame, bg="#2b2b2b")
        main_frame.add(left_frame, minsize=450)
        tk.Label(left_frame, text="Карта Атласа (Клик для выбора)", bg="#2b2b2b", fg="#a9b7c6", font=("Arial", 12, "bold")).pack(pady=5)
        
        self.atlas_canvas = tk.Canvas(left_frame, bg="black", cursor="crosshair")
        self.atlas_canvas.pack(fill=tk.BOTH, expand=True)
        self.atlas_canvas.bind("<Button-1>", self.on_atlas_click)
        
        right_frame = tk.Frame(main_frame, bg="#2b2b2b")
        main_frame.add(right_frame, minsize=550)
        
        info_container = tk.Frame(right_frame, bg="#2b2b2b")
        info_container.pack(fill=tk.X, pady=(0, 5))
        self.info_frame = tk.LabelFrame(info_container, text="Информация", bg="#2b2b2b", fg="#ffcc00", font=("Arial", 10, "bold"))
        self.info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.txt_info = tk.Text(self.info_frame, height=5, width=35, font=("Consolas", 11), bg="#1e1e1e", fg="#00ffff", relief=tk.FLAT)
        self.txt_info.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.fix_text_bindings(self.txt_info)
        
        self.edit_frame = tk.LabelFrame(info_container, text="Ручная подгонка (Live)", bg="#2b2b2b", fg="#00ff00", font=("Arial", 10, "bold"))
        self.edit_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        self.build_edit_buttons()

        sim_header_frame = tk.Frame(right_frame, bg="#2b2b2b")
        sim_header_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Label(sim_header_frame, text="Симулятор экрана (Ввод в Windows-1251):", bg="#2b2b2b", fg="#a9b7c6", font=("Arial", 11, "bold")).pack(side=tk.LEFT)
        tk.Button(sim_header_frame, text="Вывести ВСЕ активные символы", bg="#444", fg="white", command=self.show_all_active_chars).pack(side=tk.RIGHT)
        
        self.text_input = tk.Text(right_frame, height=7, font=("Consolas", 12), bg="#1e1e1e", fg="white", insertbackground="white", undo=True)
        self.text_input.pack(fill=tk.X, pady=5)
        self.fix_text_bindings(self.text_input)
        self.text_input.bind("<KeyRelease>", lambda e: self.render_preview())
        
        self.screen_canvas = tk.Canvas(right_frame, width=960, height=544, bg="#1a3b5c", highlightthickness=0)
        self.screen_canvas.pack(pady=5)

    def fix_text_bindings(self, widget):
        def on_keypress(event):
            if event.state & 0x0004:  
                char = event.char.lower()
                if char in ('c', 'с'): widget.event_generate("<<Copy>>"); return "break"
                if char in ('v', 'м'): widget.event_generate("<<Paste>>"); return "break"
                if char in ('x', 'ч'): widget.event_generate("<<Cut>>"); return "break"
                if char in ('z', 'я'): widget.event_generate("<<Undo>>"); return "break"
                if char in ('a', 'ф'): widget.tag_add("sel", "1.0", "end"); return "break"
        widget.bind("<KeyPress>", on_keypress)

    def build_edit_buttons(self):
        id_frame = tk.Frame(self.edit_frame, bg="#2b2b2b")
        id_frame.pack(side=tk.LEFT, padx=10, pady=5)
        tk.Label(id_frame, text="Выбор ID:", bg="#2b2b2b", fg="#00ffff").pack(side=tk.TOP)
        self.selected_id_var = tk.IntVar(value=0)
        tk.Spinbox(id_frame, from_=0, to=255, textvariable=self.selected_id_var, width=5, command=self.on_spinbox_id_change).pack(side=tk.TOP)

        grid_frame = tk.Frame(self.edit_frame, bg="#2b2b2b")
        grid_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        metrics_list = [
            ("Tex_X", 'tx'), ("Tex_Y", 'ty'), ("Width", 'w'), 
            ("Advance", 'adv'), ("Off_X", 'ox'), ("Off_Y", 'oy'), ("Height", 'h')
        ]
        
        for col, (label, key) in enumerate(metrics_list):
            tk.Label(grid_frame, text=label, bg="#2b2b2b", fg="white", font=("Arial", 9)).grid(row=0, column=col, padx=4)
            btn_frame = tk.Frame(grid_frame, bg="#2b2b2b")
            btn_frame.grid(row=1, column=col)
            tk.Button(btn_frame, text="-1", width=2, bg="#7a3b3b", fg="white", command=lambda k=key: self.adjust_metric(k, -1)).pack(side=tk.LEFT, padx=1)
            tk.Button(btn_frame, text="+1", width=2, bg="#3b7a48", fg="white", command=lambda k=key: self.adjust_metric(k, 1)).pack(side=tk.LEFT, padx=1)

        tools_frame = tk.Frame(self.edit_frame, bg="#2b2b2b")
        tools_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        top_tool = tk.Frame(tools_frame, bg="#2b2b2b")
        top_tool.pack(fill=tk.X)
        tk.Label(top_tool, text="Утилиты:", bg="#2b2b2b", fg="#ffcc00").pack(side=tk.LEFT)
        tk.Button(top_tool, text="ОТМЕНИТЬ (Ctrl+Z)", bg="#cc5500", fg="white", font=("Arial", 8, "bold"), command=self.undo).pack(side=tk.RIGHT, padx=5)
        
        btn_row1 = tk.Frame(tools_frame, bg="#2b2b2b")
        btn_row1.pack(side=tk.TOP, pady=2)
        tk.Button(btn_row1, text="Экспорт (PNG)", bg="#444", fg="white", font=("Arial", 8), command=self.export_char).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row1, text="Импорт (PNG)", bg="#444", fg="white", font=("Arial", 8), command=self.import_char).pack(side=tk.LEFT, padx=2)
        
        btn_row2 = tk.Frame(tools_frame, bg="#2b2b2b")
        btn_row2.pack(side=tk.TOP, pady=2)
        tk.Button(btn_row2, text="Стереть верх", bg="#7a3b3b", fg="white", font=("Arial", 8), command=lambda: self.wipe_char_edge('top')).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row2, text="Стереть низ", bg="#7a3b3b", fg="white", font=("Arial", 8), command=lambda: self.wipe_char_edge('bottom')).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row2, text="Растянуть Y", bg="#3b7a48", fg="white", font=("Arial", 8), command=lambda: self.scale_char_y(1)).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row2, text="Сжать Y", bg="#7a3b3b", fg="white", font=("Arial", 8), command=lambda: self.scale_char_y(-1)).pack(side=tk.LEFT, padx=2)

    def scale_char_y(self, delta):
        if self.selected_id is None or not self.atlas_img: return
        self.save_state()
        
        m = self.metrics[self.selected_id]
        crop_w = max(m['w'], m['adv'])
        if crop_w <= 0 or m['h'] <= 0: return
        
        crop_w = min(crop_w, self.atlas_img.width - m['tx'])
        crop_h = min(m['h'], self.atlas_img.height - m['ty'])
        
        new_h = crop_h + delta
        if new_h < 1 or m['ty'] + new_h > self.atlas_img.height:
            self.history.pop() # Отменяем, если вышли за границы
            return
            
        box = (m['tx'], m['ty'], m['tx'] + crop_w, m['ty'] + crop_h)
        chunk = self.atlas_img.crop(box)
        
        # Растягиваем/сжимаем билинейной интерполяцией
        resized = chunk.resize((crop_w, new_h), Image.Resampling.BILINEAR)
        
        # Сначала затираем старое место (особенно важно при сжатии)
        wipe_img = Image.new("RGBA", (crop_w, crop_h), (0,0,0,0))
        self.atlas_img.paste(wipe_img, (m['tx'], m['ty']))
        
        # Вставляем новую растянутую картинку
        self.atlas_img.paste(resized, (m['tx'], m['ty']))
        
        m['h'] = new_h
        self.draw_atlas()
        self.render_preview()
        
        self.txt_info.delete("1.0", tk.END)
        self.txt_info.insert("1.0", f"Символ {self.selected_id} масштабирован! Новая высота: {new_h}")

    def export_char(self):
        if self.selected_id is None or not self.atlas_img: return
        m = self.metrics[self.selected_id]
        crop_w = m['adv'] if self.sim_game_engine.get() else m['w']
        if crop_w <= 0 or m['h'] <= 0: return
        crop = self.atlas_img.crop((m['tx'], m['ty'], m['tx']+crop_w, m['ty']+m['h']))
        path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=f"char_{self.selected_id}.png")
        if path: 
            crop.save(path)
            messagebox.showinfo("Успех", f"Символ {self.selected_id} сохранен!\nОтредактируйте его (не меняя размер холста) и нажмите 'Импорт'.")

    def import_char(self):
        if self.selected_id is None or not self.atlas_img: return
        path = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
        if not path: return
        try:
            self.save_state()
            m = self.metrics[self.selected_id]
            new_img = Image.open(path).convert("RGBA")
            
            wipe_img = Image.new("RGBA", (new_img.width, new_img.height), (0,0,0,0))
            self.atlas_img.paste(wipe_img, (m['tx'], m['ty']))
            
            self.atlas_img.paste(new_img, (m['tx'], m['ty']))
            
            self.draw_atlas()
            self.render_preview()
            self.txt_info.delete("1.0", tk.END)
            self.txt_info.insert("1.0", f"Символ {self.selected_id} успешно импортирован!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка импорта: {e}")

    def wipe_char_edge(self, edge):
        if self.selected_id is None or not self.atlas_img: return
        self.save_state()
        m = self.metrics[self.selected_id]
        
        crop_w = max(m['w'], m['adv'])
        if crop_w <= 0: crop_w = 30
        crop_h = max(m['h'], 30)
        
        crop_w = min(crop_w, self.atlas_img.width - m['tx'])
        crop_h = min(crop_h, self.atlas_img.height - m['ty'])
        if crop_w <= 0 or crop_h <= 0: return
        
        box = (m['tx'], m['ty'], m['tx'] + crop_w, m['ty'] + crop_h)
        chunk = self.atlas_img.crop(box)
        
        alpha = chunk.split()[-1]
        bbox = alpha.getbbox()
        if not bbox: 
            self.txt_info.delete("1.0", tk.END)
            self.txt_info.insert("1.0", "Буква уже полностью прозрачная!")
            return
        
        left, top, right, bottom = bbox
        pixels = chunk.load()
        
        if edge == 'top':
            for x in range(left, right):
                pixels[x, top] = (0, 0, 0, 0)
            msg = f"Стёрт ВЕРХНИЙ ряд пикселей. Метрики не изменены."
        else:
            for x in range(left, right):
                pixels[x, bottom - 1] = (0, 0, 0, 0)
            if m['h'] > 1:
                m['h'] -= 1
            msg = f"Стёрт НИЖНИЙ ряд пикселей. Метрика Height уменьшена!"
                
        self.atlas_img.paste(chunk, (m['tx'], m['ty']))
            
        self.draw_atlas()
        self.render_preview()
        
        self.txt_info.delete("1.0", tk.END)
        self.txt_info.insert("1.0", f"{msg}\nID {self.selected_id}: [Height = {m['h']}]")

    def on_spinbox_id_change(self):
        try:
            val = self.selected_id_var.get()
            if 0 <= val <= 255:
                self.selected_id = val
                if val in self.metrics: self.update_info_panel(val)
                self.draw_atlas()
        except: pass

    def adjust_metric(self, key, delta):
        if self.selected_id is not None and self.selected_id in self.metrics:
            self.save_state()
            self.metrics[self.selected_id][key] += delta
            if self.metrics[self.selected_id][key] < 0 and key in ('tx', 'ty', 'w', 'adv', 'h'): 
                self.metrics[self.selected_id][key] = 0
            self.update_info_panel(self.selected_id)
            self.draw_atlas()
            self.render_preview()

    def browse_file(self, var, filetypes):
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path: var.set(path)

    def open_auto_generator(self):
        png, txt = self.img_path.get(), self.txt_path.get()
        if not os.path.exists(png) or not os.path.exists(txt): return messagebox.showerror("Ошибка", "Сначала выберите текстуру и метрики!")
        AutoGenerateFontDialog(self, png, txt, self.reload_generated_files)

    def reload_generated_files(self, new_png, new_txt):
        self.img_path.set(new_png)
        self.txt_path.set(new_txt)
        self.load_font_data()

    def load_font_data(self, silent=False):
        if not os.path.exists(self.img_path.get()) or not os.path.exists(self.txt_path.get()): return
        
        self.atlas_img = Image.open(self.img_path.get()).convert("RGBA")
        self.metrics, _ = parse_metrics_file_safely(self.txt_path.get())
        
        self.line_height = 20
        if 65 in self.metrics: 
            self.line_height = max(18, self.metrics[65]['h'] + 4)
        
        self.draw_atlas()
        self.render_preview()
        self.save_studio_config()
        if not silent:
            self.txt_info.delete("1.0", tk.END)
            self.txt_info.insert("1.0", f"Успешно загружено: {len(self.metrics)} символов.\nКликните на атлас для редактирования.")

    def save_metrics(self):
        if not self.metrics: return
        out_path = self.txt_path.get() 
        with open(out_path, 'r', encoding='utf-8') as orig_f: lines = orig_f.readlines()
        with open(out_path, 'w', encoding='utf-8') as f:
            for i in range(min(3, len(lines))): f.write(lines[i])
            for char_id in range(256):
                if char_id in self.metrics:
                    m = self.metrics[char_id]
                    char_repr = chr(char_id) if 32 <= char_id <= 126 else "N/A"
                    f.write(f"{char_id:03d} | '{char_repr:4s}' | {m['ox']:5d} | {m['oy']:5d} | {m['w']:5d} | {m['tx']:5d} | {m['ty']:5d} | {m['adv']:7d} | {m['h']:6d}\n")
                else: f.write(f"{char_id:03d} | 'N/A ' |     0 |     0 |     0 |     0 |     0 |       0 |      0\n")
        self.txt_info.delete("1.0", tk.END)
        self.txt_info.insert("1.0", f"УСПЕШНО СОХРАНЕНО В:\n{out_path}")
        self.atlas_img.save(self.img_path.get())

    def show_all_active_chars(self):
        if not self.metrics: return
        active_text = ""
        for cid in range(256):
            if cid in self.metrics and (self.metrics[cid]['adv'] > 0 or self.metrics[cid]['w'] > 0):
                try:
                    if 32 <= (cid - self.sim_shift.get()) <= 255: active_text += bytes([cid - self.sim_shift.get()]).decode('cp1251')
                except: pass
        self.text_input.delete("1.0", tk.END)
        self.text_input.insert("1.0", '\n'.join([active_text[i:i+40] for i in range(0, len(active_text), 40)]))
        self.render_preview()

    def draw_atlas(self):
        if not self.atlas_img: return
        display_img = self.atlas_img.copy()
        draw = ImageDraw.Draw(display_img)
        for cid, m in self.metrics.items():
            if m['adv'] > 0 or m['w'] > 0:
                draw_w = m['adv'] if self.sim_game_engine.get() else m['w']
                color = "yellow" if cid == self.selected_id else "red"
                thick = 2 if cid == self.selected_id else 1
                try: draw.rectangle([m['tx'], m['ty'], m['tx']+draw_w, m['ty']+m['h']], outline=color, width=thick)
                except: pass
        display_img = display_img.resize((display_img.width * 2, display_img.height * 2), Image.Resampling.NEAREST)
        self.tk_atlas = ImageTk.PhotoImage(display_img)
        self.atlas_canvas.config(scrollregion=(0, 0, display_img.width, display_img.height))
        self.atlas_canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_atlas)

    def on_atlas_click(self, event):
        if not self.metrics: return
        cx, cy = event.x // 2, event.y // 2
        for cid, m in self.metrics.items():
            check_w = m['adv'] if self.sim_game_engine.get() else m['w']
            if (m['adv'] > 0 or m['w'] > 0) and m['tx'] <= cx <= m['tx'] + check_w and m['ty'] <= cy <= m['ty'] + m['h']:
                self.selected_id = cid
                self.selected_id_var.set(cid)
                self.update_info_panel(cid)
                self.draw_atlas()
                break

    def update_info_panel(self, cid):
        m = self.metrics[cid]
        try: char_repr = bytes([cid - self.sim_shift.get()]).decode('cp1251')
        except: char_repr = "?"
        self.txt_info.delete("1.0", tk.END)
        self.txt_info.insert("1.0", f"ID в EBOOT: {cid:03d} | СИМВОЛ: '{char_repr}'\nTex_X: {m['tx']:<4} Width: {m['w']:<4} Off_X: {m['ox']}\nTex_Y: {m['ty']:<4} Height: {m['h']:<3} Off_Y: {m['oy']}\nAdvance: {m['adv']}")

    def render_preview(self):
        if not self.atlas_img or not self.metrics: return
        self.screen_canvas.delete("all")
        
        psp_screen = Image.new("RGBA", (480, 272), (26, 59, 92, 255))
        draw = ImageDraw.Draw(psp_screen)
        
        if self.show_guidelines.get():
            for i in range(12):
                y_line = 30 + i * self.line_height
                draw.line([0, y_line, 480, y_line], fill=(255, 255, 255, 50))
        
        cursor_x, cursor_y = 20, 30
        try: encoded_bytes = self.text_input.get("1.0", tk.END).rstrip('\n').encode('cp1251', errors='replace')
        except: encoded_bytes = b''
        
        for b in encoded_bytes:
            if b == 10: 
                cursor_x = 20; cursor_y += self.line_height; continue
                
            game_id = b + self.sim_shift.get()
            if game_id in self.metrics:
                m = self.metrics[game_id]
                if m['adv'] > 0 or m['h'] > 0:
                    tw = m['adv'] if self.sim_game_engine.get() else m['w']
                    try: 
                        crop = self.atlas_img.crop((m['tx'], m['ty'], m['tx'] + tw, m['ty'] + m['h']))
                        pos = (cursor_x + m['ox'], cursor_y + m['oy'])
                        psp_screen.paste(crop, pos, crop)
                        
                        if self.show_debug_boxes.get():
                            draw.rectangle([pos[0], pos[1], pos[0] + tw - 1, pos[1] + m['h'] - 1], outline=(255, 68, 68, 180))
                            
                    except: pass
                cursor_x += m['adv']
                
        if self.scale_x2.get(): psp_screen = psp_screen.resize((960, 544), Image.Resampling.NEAREST)
        self.tk_screen = ImageTk.PhotoImage(psp_screen)
        self.screen_canvas.create_image(480, 272, anchor=tk.CENTER, image=self.tk_screen)
        self.draw_atlas()