import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import module_ppk
import module_ptex
import module_scr
import module_eboot
import module_text 
import module_hex  # <--- Новый модуль для HEX-декодера

from module_lang import init_langs, load_lang, get_available_langs, _
from module_studio import FontStudioWindow

class PrintLogger:
    def __init__(self, textbox):
        self.textbox = textbox
    def write(self, text):
        self.textbox.after(0, self._append, text)
    def _append(self, text):
        self.textbox.insert(tk.END, text)
        self.textbox.see(tk.END)
    def flush(self): pass

class MytranApp(tk.Tk):
    def __init__(self):
        super().__init__()
        init_langs()
        
        self.title(_("title"))
        self.geometry("750x820") # Чуть увеличили высоту под новую панель массивов
        self.configure(padx=10, pady=10)
        
        self.target_dir = tk.StringVar(value=os.getcwd())
        
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        lang_frame = ttk.Frame(top_frame)
        lang_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        self.lbl_lang = ttk.Label(lang_frame, text=_("lang_label"))
        self.lbl_lang.pack(side=tk.LEFT)
        
        from module_lang import current_lang_code
        self.lang_var = tk.StringVar(value=current_lang_code.upper())
        self.cb_lang = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=get_available_langs(), state="readonly", width=5)
        self.cb_lang.pack(side=tk.LEFT, padx=5)
        self.cb_lang.bind("<<ComboboxSelected>>", self.on_lang_changed)
        
        dir_frame = ttk.Frame(top_frame)
        dir_frame.pack(side=tk.TOP, fill=tk.X)
        self.lbl_work_dir = ttk.Label(dir_frame, text=_("work_dir"))
        self.lbl_work_dir.pack(side=tk.LEFT)
        ttk.Entry(dir_frame, textvariable=self.target_dir, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.btn_browse = ttk.Button(dir_frame, text=_("browse"), command=self.browse_dir)
        self.btn_browse.pack(side=tk.LEFT)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.build_ppk_tab()
        self.build_ptex_tab()
        self.build_scr_tab()
        self.build_eboot_tab()
        self.build_text_tab() 
        self.build_hex_tab()  # <--- Добавлена новая вкладка HEX-декодера

        self.log_frame = ttk.LabelFrame(self, text=_("console"))
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.log_text = tk.Text(self.log_frame, height=10, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        import sys
        sys.stdout = PrintLogger(self.log_text)
        print(_("welcome"))

    def browse_dir(self):
        d = filedialog.askdirectory(initialdir=self.target_dir.get())
        if d: self.target_dir.set(d)

    def run_thread(self, func, *args):
        threading.Thread(target=func, args=args, daemon=True).start()

    def on_lang_changed(self, event):
        load_lang(self.lang_var.get().lower())
        self.update_texts()

    def update_texts(self):
        self.title(_("title"))
        self.lbl_lang.config(text=_("lang_label"))
        self.lbl_work_dir.config(text=_("work_dir"))
        self.btn_browse.config(text=_("browse"))
        
        self.notebook.tab(0, text=_("tab_ppk"))
        self.lbl_ppk_desc.config(text=_("ppk_desc"))
        self.btn_unpack_ppk.config(text=_("btn_unpack_ppk"))
        self.btn_pack_ppk.config(text=_("btn_pack_ppk"))

        self.notebook.tab(1, text=_("tab_ptex"))
        self.lbl_ptex_desc.config(text=_("ptex_desc"))
        self.btn_unpack_ptex.config(text=_("btn_unpack_ptex"))
        self.btn_pack_ptex.config(text=_("btn_pack_ptex"))

        self.notebook.tab(2, text=_("tab_scr"))
        self.lbl_scr_desc.config(text=_("scr_desc"))
        self.btn_scr_to_png.config(text=_("btn_scr_to_png"))
        self.btn_png_to_scr.config(text=_("btn_png_to_scr"))

        self.notebook.tab(3, text=_("tab_eboot"))
        self.lbl_eboot_desc.config(text=_("eboot_desc"))
        self.btn_select_eboot.config(text=_("btn_select_eboot"))
        self.btn_select_font_dir.config(text=_("btn_select_font_dir"))
        self.btn_extract_fonts.config(text=_("btn_extract_fonts"))
        self.btn_inject_fonts.config(text=_("btn_inject_fonts"))
        self.btn_font_studio.config(text=_("btn_font_studio"))
        
        self.log_frame.config(text=_("console"))
        print("\n" + _("welcome"))

    def build_ppk_tab(self):
        self.f_ppk = ttk.Frame(self.notebook)
        self.notebook.add(self.f_ppk, text=_("tab_ppk"))
        self.lbl_ppk_desc = ttk.Label(self.f_ppk, text=_("ppk_desc"))
        self.lbl_ppk_desc.pack(pady=10)
        self.btn_unpack_ppk = ttk.Button(self.f_ppk, text=_("btn_unpack_ppk"), width=50, command=lambda: self.run_thread(self.do_unpack_ppk))
        self.btn_unpack_ppk.pack(pady=5)
        self.btn_pack_ppk = ttk.Button(self.f_ppk, text=_("btn_pack_ppk"), width=50, command=lambda: self.run_thread(self.do_pack_ppk))
        self.btn_pack_ppk.pack(pady=5)

    def do_unpack_ppk(self):
        d = self.target_dir.get()
        files = [f for f in os.listdir(d) if f.endswith('.ppk') and not f.endswith('_new.ppk')]
        for f in files: module_ppk.unpack_ppk(os.path.join(d, f), os.path.join(d, f.replace('.ppk', '_extracted')))

    def do_pack_ppk(self):
        d = self.target_dir.get()
        folders = [f for f in os.listdir(d) if os.path.isdir(os.path.join(d, f)) and f.endswith('_extracted')]
        for f in folders: module_ppk.pack_ppk(os.path.join(d, f), os.path.join(d, f.replace('_extracted', '_new.ppk')))

    def build_ptex_tab(self):
        self.f_ptex = ttk.Frame(self.notebook)
        self.notebook.add(self.f_ptex, text=_("tab_ptex"))
        self.lbl_ptex_desc = ttk.Label(self.f_ptex, text=_("ptex_desc"))
        self.lbl_ptex_desc.pack(pady=10)
        self.btn_unpack_ptex = ttk.Button(self.f_ptex, text=_("btn_unpack_ptex"), width=50, command=lambda: self.run_thread(self.do_ptex_to_png))
        self.btn_unpack_ptex.pack(pady=5)
        self.btn_pack_ptex = ttk.Button(self.f_ptex, text=_("btn_pack_ptex"), width=50, command=lambda: self.run_thread(self.do_png_to_ptex))
        self.btn_pack_ptex.pack(pady=5)

    def get_ext_folders(self):
        d = self.target_dir.get()
        subs = [os.path.join(d, f) for f in os.listdir(d) if os.path.isdir(os.path.join(d, f)) and f.endswith('_extracted')]
        return subs if subs else [d]

    def do_ptex_to_png(self):
        for d in self.get_ext_folders():
            for f in os.listdir(d):
                if f.endswith('.ptex'):
                    try: module_ptex.ptex_to_png(os.path.join(d, f), os.path.join(d, f.replace('.ptex', '.png')))
                    except Exception as e: print(f"Ошибка {f}: {e}")

    def do_png_to_ptex(self):
        for d in self.get_ext_folders():
            for f in os.listdir(d):
                if f.endswith('.png'):
                    orig = f
                    for suf in ['_4444', '_5551', '_5650']: orig = orig.lower().replace(suf, "")
                    pt_path = os.path.join(d, orig.replace('.png', '.ptex'))
                    if os.path.exists(pt_path):
                        try: module_ptex.png_to_ptex(os.path.join(d, f), pt_path, pt_path)
                        except Exception as e: print(f"Ошибка {f}: {e}")

    def build_scr_tab(self):
        self.f_scr = ttk.Frame(self.notebook)
        self.notebook.add(self.f_scr, text=_("tab_scr"))
        self.lbl_scr_desc = ttk.Label(self.f_scr, text=_("scr_desc"))
        self.lbl_scr_desc.pack(pady=10)
        self.btn_scr_to_png = ttk.Button(self.f_scr, text=_("btn_scr_to_png"), width=50, command=lambda: self.run_thread(self.do_scr, True))
        self.btn_scr_to_png.pack(pady=5)
        self.btn_png_to_scr = ttk.Button(self.f_scr, text=_("btn_png_to_scr"), width=50, command=lambda: self.run_thread(self.do_scr, False))
        self.btn_png_to_scr.pack(pady=5)

    def do_scr(self, to_png):
        d = self.target_dir.get()
        ext_in, ext_out = ('.scr', '.png') if to_png else ('.png', '.scr')
        for f in [x for x in os.listdir(d) if x.lower().endswith(ext_in)]:
            module_scr.convert_scr(os.path.join(d, f), os.path.join(d, f.replace(ext_in, ext_out)), to_png)

    def build_eboot_tab(self):
        self.f_eboot = ttk.Frame(self.notebook)
        self.notebook.add(self.f_eboot, text=_("tab_eboot"))
        self.lbl_eboot_desc = ttk.Label(self.f_eboot, text=_("eboot_desc"))
        self.lbl_eboot_desc.pack(pady=10)
        
        self.eboot_path = tk.StringVar()
        self.font_dir = tk.StringVar(value=os.getcwd() + "/EBOOT_FONTS")
        
        fr1 = ttk.Frame(self.f_eboot)
        fr1.pack(fill=tk.X, padx=20, pady=5)
        ttk.Entry(fr1, textvariable=self.eboot_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn_select_eboot = ttk.Button(fr1, text=_("btn_select_eboot"), command=lambda: self.eboot_path.set(filedialog.askopenfilename(filetypes=[("EBOOT", "*.BIN *.bin")])))
        self.btn_select_eboot.pack(side=tk.LEFT)
        
        fr2 = ttk.Frame(self.f_eboot)
        fr2.pack(fill=tk.X, padx=20, pady=5)
        ttk.Entry(fr2, textvariable=self.font_dir).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn_select_font_dir = ttk.Button(fr2, text=_("btn_select_font_dir"), command=lambda: self.font_dir.set(filedialog.askdirectory()))
        self.btn_select_font_dir.pack(side=tk.LEFT)

        self.btn_extract_fonts = ttk.Button(self.f_eboot, text=_("btn_extract_fonts"), width=50, command=lambda: self.run_thread(module_eboot.process_eboot_fonts, self.eboot_path.get(), self.font_dir.get(), "extract"))
        self.btn_extract_fonts.pack(pady=10)
        
        self.btn_inject_fonts = ttk.Button(self.f_eboot, text=_("btn_inject_fonts"), width=50, command=lambda: self.run_thread(module_eboot.process_eboot_fonts, self.eboot_path.get(), self.font_dir.get(), "inject"))
        self.btn_inject_fonts.pack(pady=5)
        
        ttk.Separator(self.f_eboot, orient="horizontal").pack(fill=tk.X, padx=20, pady=10)
        
        self.btn_font_studio = ttk.Button(self.f_eboot, text=_("btn_font_studio"), width=50, command=self.open_font_studio)
        self.btn_font_studio.pack(pady=5)

    def build_text_tab(self):
        self.f_text = ttk.Frame(self.notebook)
        self.notebook.add(self.f_text, text="  Тексты (.loc / .bin)  ")
        
        ttk.Label(self.f_text, text="Конвертация текстов игры в .txt с кодировкой Windows-1251").pack(pady=10)

        # LOC
        f_loc = ttk.LabelFrame(self.f_text, text=" Цели миссий (.loc) ")
        f_loc.pack(fill=tk.X, padx=20, pady=5)
        ttk.Button(f_loc, text="Распаковать .loc -> .txt", command=self.do_unpack_loc).pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        ttk.Button(f_loc, text="Собрать .txt -> .loc", command=self.do_pack_loc).pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)

        # BIN (Dialogues)
        f_dlg = ttk.LabelFrame(self.f_text, text=" Диалоги (mission_*.bin) ")
        f_dlg.pack(fill=tk.X, padx=20, pady=5)
        ttk.Button(f_dlg, text="Распаковать .bin -> .txt", command=self.do_unpack_dlg).pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        ttk.Button(f_dlg, text="Собрать .txt -> .bin", command=self.do_pack_dlg).pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)

        # BIN (UI)
        f_ui = ttk.LabelFrame(self.f_text, text=" Интерфейс игры (menu.bin) ")
        f_ui.pack(fill=tk.X, padx=20, pady=5)
        ttk.Button(f_ui, text="Распаковать .bin -> .txt", command=self.do_unpack_ui).pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        ttk.Button(f_ui, text="Собрать .txt -> .bin", command=self.do_pack_ui).pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)

        # BIN (Data Arrays - Герои, Вопросы, Навыки, Предметы, Blockmap)
        f_arr = ttk.LabelFrame(self.f_text, text=" Системные массивы (hero, quiz, blockmap, предметы...) ")
        f_arr.pack(fill=tk.X, padx=20, pady=5)
        ttk.Button(f_arr, text="Умная распаковка .bin -> .txt", command=self.do_unpack_data_arrays).pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        ttk.Button(f_arr, text="Сборка .txt -> .bin", command=self.do_pack_data_arrays).pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        
    def build_hex_tab(self):
        self.f_hex = ttk.Frame(self.notebook)
        self.notebook.add(self.f_hex, text="  HEX Декодер  ")
        
        ttk.Label(self.f_hex, text="Быстрый конвертер любых файлов в текстовый HEX-дамп для анализа.").pack(pady=10)
        
        f_container = ttk.LabelFrame(self.f_hex, text=" Генерация HEX-дампа ")
        f_container.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Button(
            f_container, 
            text="Выбрать файлы и сгенерировать HEX-дамп", 
            command=self.do_hex_decode
        ).pack(side=tk.LEFT, padx=5, pady=10, expand=True, fill=tk.X)

    # --- Функции обработчиков кнопок текста ---
    def do_unpack_loc(self):
        files = filedialog.askopenfilenames(filetypes=[("LOC Files", "*.loc")])
        for f in files: self.run_thread(module_text.extract_loc, f, f + ".txt")

    def do_pack_loc(self):
        files = filedialog.askopenfilenames(filetypes=[("TXT Files", "*.txt")])
        for f in files: 
            out = f.replace(".txt", "") if f.endswith(".loc.txt") else f + ".loc"
            self.run_thread(module_text.pack_loc, f, out)

    def do_unpack_dlg(self):
        files = filedialog.askopenfilenames(filetypes=[("BIN Files", "*.bin")])
        for f in files: self.run_thread(module_text.extract_bin, f, f + ".txt")

    def do_pack_dlg(self):
        files = filedialog.askopenfilenames(filetypes=[("TXT Files", "*.txt")])
        for f in files: 
            out = f.replace(".txt", "") if f.endswith(".bin.txt") else f + ".bin"
            self.run_thread(module_text.pack_bin, f, out)

    def do_unpack_ui(self):
        files = filedialog.askopenfilenames(filetypes=[("BIN Files", "*.bin")])
        for f in files: self.run_thread(module_text.extract_ui, f, f + ".txt")

    def do_pack_ui(self):
        files = filedialog.askopenfilenames(filetypes=[("TXT Files", "*.txt")])
        for f in files: 
            out = f.replace(".txt", "") if f.endswith(".bin.txt") else f + ".bin"
            self.run_thread(module_text.pack_ui, f, out)

    def do_unpack_data_arrays(self):
        files = filedialog.askopenfilenames(filetypes=[("BIN Files", "*.bin")])
        for f in files: self.run_thread(module_text.extract_data_array, f, f + ".txt")

    def do_pack_data_arrays(self):
        files = filedialog.askopenfilenames(filetypes=[("TXT Files", "*.txt")])
        for f in files: 
            out = f.replace(".txt", "") if f.endswith(".bin.txt") else f + ".bin"
            # Оригинальный BIN нужен как база для запаковки (мы редактируем только строковые блоки)
            base_bin = out if os.path.exists(out) else f.replace(".txt", "")
            self.run_thread(module_text.pack_data_array, f, base_bin, out.replace(".bin", "_mod.bin"))
            
    def do_hex_decode(self):
        input_files = filedialog.askopenfilenames(
            title="Выберите файлы для HEX-декодирования",
            filetypes=[("All Files", "*.*")]
        )
        if not input_files:
            return
            
        output_file = filedialog.asksaveasfilename(
            title="Сохранить результат как...",
            defaultextension=".txt",
            filetypes=[("Text Document", "*.txt"), ("All Files", "*.*")],
            initialfile="hex_analysis_result.txt"
        )
        if not output_file:
            return
            
        self.run_thread(module_hex.decode_to_hex, input_files, output_file)

    def open_font_studio(self):
        FontStudioWindow(self)

if __name__ == "__main__":
    app = MytranApp()
    app.mainloop()