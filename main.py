import os
import re
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import module_ppk
import module_ptex
import module_scr
import module_eboot
import module_text 
import module_hex

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
        self.geometry("850x850") 
        self.configure(padx=10, pady=10)
        
        self.target_dir = tk.StringVar(value=os.getcwd())
        self.lang_vars = {
            "en": tk.BooleanVar(value=True),
            "fr": tk.BooleanVar(value=False),
            "de": tk.BooleanVar(value=False),
            "es": tk.BooleanVar(value=False),
            "it": tk.BooleanVar(value=False),
            "ru": tk.BooleanVar(value=True)
        }
        
        self.load_app_config()
        self.target_dir.trace_add("write", lambda *a: self.save_app_config())
        for var in self.lang_vars.values():
            var.trace_add("write", lambda *a: self.save_app_config())
        
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
        self.lbl_work_dir = ttk.Label(dir_frame, text="Workspace (Папка игры):")
        self.lbl_work_dir.pack(side=tk.LEFT)
        ttk.Entry(dir_frame, textvariable=self.target_dir).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.btn_browse = ttk.Button(dir_frame, text=_("browse"), command=self.browse_dir)
        self.btn_browse.pack(side=tk.LEFT)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.build_ppk_tab()
        self.build_ptex_tab()
        self.build_scr_tab()
        self.build_eboot_tab()
        self.build_text_tab() 
        self.build_hex_tab()

        self.log_frame = ttk.LabelFrame(self, text=_("console"))
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.log_text = tk.Text(self.log_frame, height=10, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        import sys
        sys.stdout = PrintLogger(self.log_text)
        print(_("welcome"))
        print("-> Инициализация Workspace: Конфигурация успешно загружена.")

    def load_app_config(self):
        try:
            if os.path.exists("app_cfg.json"):
                with open("app_cfg.json", "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if os.path.exists(cfg.get("workspace", "")):
                        self.target_dir.set(cfg["workspace"])
                    for lang, val in cfg.get("langs", {}).items():
                        if lang in self.lang_vars:
                            self.lang_vars[lang].set(val)
        except: pass

    def save_app_config(self):
        try:
            cfg = {
                "workspace": self.target_dir.get(),
                "langs": {lang: var.get() for lang, var in self.lang_vars.items()}
            }
            with open("app_cfg.json", "w", encoding="utf-8") as f:
                json.dump(cfg, f)
        except: pass

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

    # ==========================================
    # ВКЛАДКА ТЕКСТОВ (WORKSPACE)
    # ==========================================
    def build_text_tab(self):
        self.f_text = ttk.Frame(self.notebook)
        self.notebook.add(self.f_text, text="  Тексты (Workspace)  ")
        
        f_langs = ttk.LabelFrame(self.f_text, text=" 1. Фильтр обрабатываемых языков ")
        f_langs.pack(fill=tk.X, padx=20, pady=10)
        
        lang_container = ttk.Frame(f_langs)
        lang_container.pack(pady=5)
        for lang, var in self.lang_vars.items():
            ttk.Checkbutton(lang_container, text=lang.upper(), variable=var).pack(side=tk.LEFT, padx=10)

        f_batch = ttk.LabelFrame(self.f_text, text=" 2. Пакетная обработка (поиск по Workspace) ")
        f_batch.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(f_batch, text="РАСПАКОВАТЬ все .bin и .loc -> .json", command=lambda: self.run_thread(self.do_batch_unpack)).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(f_batch, text="ЗАПАКОВАТЬ все .json обратно в игру", command=lambda: self.run_thread(self.do_batch_pack)).pack(fill=tk.X, padx=10, pady=5)

        f_ai = ttk.LabelFrame(self.f_text, text=" 3. Инструменты для ИИ и Анализа ")
        f_ai.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(f_ai, text="Сгенерировать Дерево Файлов (_file_tree.txt)", command=lambda: self.run_thread(self.generate_tree)).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(f_ai, text="АНАЛИЗ ФОРМАТА (Собрать HEX + JSON со всех языков)", command=lambda: self.run_thread(self.do_analyze_format)).pack(fill=tk.X, padx=10, pady=5)

    def get_active_langs(self):
        return [lang for lang, var in self.lang_vars.items() if var.get()]

    def is_valid_file(self, filepath):
        active_langs = self.get_active_langs()
        parts = filepath.replace('\\', '/').split('/')
        for lang in active_langs:
            if lang in parts:
                return True
        if not any(l in parts for l in ["en", "fr", "de", "es", "it", "ru"]):
            return True
        return False

    def get_lang_suffix_path(self, filepath):
        parts = filepath.replace('\\', '/').split('/')
        lang = ""
        for p in parts:
            if p.lower() in ['en', 'fr', 'de', 'it', 'es', 'ru']:
                lang = p.lower()
                break
        if lang:
            base, ext = os.path.splitext(filepath)
            return f"{base}.{lang}{ext}.json"
        return filepath + ".json"

    def get_base_orig_path(self, json_path):
        base = json_path[:-5]
        base = re.sub(r'\.(en|fr|de|it|es|ru)\.(bin|loc)$', r'.\2', base, flags=re.IGNORECASE)
        return base

    def do_batch_unpack(self):
        workspace = self.target_dir.get()
        print(f"-> Начинаю поиск файлов в {workspace}...")
        found = 0
        for root, dirs, files in os.walk(workspace):
            if "_ANALYSIS_" in root: continue
            for f in files:
                if f.endswith(".bin") or f.endswith(".loc"):
                    if "_mod.bin" in f or ".bak" in f: continue
                    filepath = os.path.join(root, f)
                    if self.is_valid_file(filepath):
                        lang_tag = "orig"
                        parts = filepath.replace('\\', '/').split('/')
                        for p in parts:
                            if p in self.lang_vars.keys(): lang_tag = p
                                
                        out_json = os.path.join(root, f"{f.replace('.bin', '').replace('.loc', '')}.{lang_tag}.{f.split('.')[-1]}.json")
                        module_text.process_file_to_json(filepath, out_json)
                        found += 1
        print(f"-> Пакетная распаковка завершена! Обработано файлов: {found}")

    def do_batch_pack(self):
        workspace = self.target_dir.get()
        print(f"-> Начинаю поиск JSON-переводов в {workspace}...")
        found = 0
        for root, dirs, files in os.walk(workspace):
            if "_ANALYSIS_" in root: continue
            for f in files:
                if f.endswith(".json"):
                    json_path = os.path.join(root, f)
                    if self.is_valid_file(json_path):
                        base_name = re.sub(r'\.(en|fr|de|it|es|ru)\.(bin|loc)\.json$', '', f, flags=re.IGNORECASE)
                        base_name = base_name.replace(".bin.json", "").replace(".loc.json", "").replace(".json", "")
                        
                        orig_bin = os.path.join(root, base_name + ".bin")
                        orig_loc = os.path.join(root, base_name + ".loc")
                        orig_pure = os.path.join(root, base_name)
                        
                        target_orig = None
                        if os.path.exists(orig_pure): target_orig = orig_pure
                        elif os.path.exists(orig_bin): target_orig = orig_bin
                        elif os.path.exists(orig_loc): target_orig = orig_loc
                        
                        if target_orig:
                            module_text.pack_json_to_file(json_path, target_orig)
                            found += 1
                        else:
                            print(f"Пропуск {f}: Оригинальный файл не найден!")
        print(f"-> Пакетная сборка завершена! Упаковано файлов: {found}")

    def generate_tree(self):
        d = self.target_dir.get()
        out_path = os.path.join(d, "_file_tree.txt")
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"Структура папки: {d}\n")
                f.write("="*50 + "\n")
                for root, dirs, files in os.walk(d):
                    if "_ANALYSIS_" in root: continue
                    level = root.replace(d, '').count(os.sep)
                    indent = ' ' * 4 * level
                    f.write(f"{indent}[{os.path.basename(root)}/]\n")
                    subindent = ' ' * 4 * (level + 1)
                    for file in files:
                        f.write(f"{subindent}{file}\n")
            print(f"-> Дерево файлов успешно сохранено: {out_path}")
        except Exception as e:
            print(f"Ошибка при создании дерева файлов: {e}")

    def do_analyze_format(self):
        filepath = filedialog.askopenfilename(title="Выберите бинарник (например affections.bin)", filetypes=[("BIN/LOC", "*.bin *.loc")])
        if not filepath: return
        
        filename = os.path.basename(filepath)
        workspace = self.target_dir.get()
        out_dir = os.path.join(workspace, "_ANALYSIS_", filename)
        os.makedirs(out_dir, exist_ok=True)
        
        print(f"\n>>> АНАЛИЗ ФОРМАТА: {filename} <<<")
        found = 0
        for root, dirs, files in os.walk(workspace):
            if "_ANALYSIS_" in root: continue
            if filename in files:
                src = os.path.join(root, filename)
                lang = "unknown"
                for p in src.replace('\\', '/').split('/'):
                    if p.lower() in ['en', 'fr', 'de', 'it', 'es', 'ru']:
                        lang = p.lower()
                
                hex_path = os.path.join(out_dir, f"{filename}.{lang}.hex.txt")
                module_hex.decode_to_hex([src], hex_path)
                
                json_path = os.path.join(out_dir, f"{filename}.{lang}.json")
                module_text.process_file_to_json(src, json_path)
                found += 1
                
        print(f"-> Анализ завершен! Найдено {found} вариантов файла.")
        print(f"-> Зайдите в папку: {out_dir}")

    # ==========================================
    # ОСТАЛЬНЫЕ ВКЛАДКИ
    # ==========================================
    def build_ppk_tab(self):
        self.f_ppk = ttk.Frame(self.notebook)
        self.notebook.add(self.f_ppk, text=_("tab_ppk"))
        self.lbl_ppk_desc = ttk.Label(self.f_ppk, text=_("ppk_desc"))
        self.lbl_ppk_desc.pack(pady=10)
        self.btn_unpack_ppk = ttk.Button(self.f_ppk, text=_("btn_unpack_ppk"), width=50, command=lambda: self.run_thread(self.do_unpack_ppk))
        self.btn_unpack_ppk.pack(pady=5)
        self.btn_pack_ppk = ttk.Button(self.f_ppk, text=_("btn_pack_ppk"), width=50, command=lambda: self.run_thread(self.do_pack_ppk))
        self.btn_pack_ppk.pack(pady=5)

    def build_ptex_tab(self):
        self.f_ptex = ttk.Frame(self.notebook)
        self.notebook.add(self.f_ptex, text=_("tab_ptex"))
        self.lbl_ptex_desc = ttk.Label(self.f_ptex, text=_("ptex_desc"))
        self.lbl_ptex_desc.pack(pady=10)
        self.btn_unpack_ptex = ttk.Button(self.f_ptex, text=_("btn_unpack_ptex"), width=50, command=lambda: self.run_thread(self.do_ptex_to_png))
        self.btn_unpack_ptex.pack(pady=5)
        self.btn_pack_ptex = ttk.Button(self.f_ptex, text=_("btn_pack_ptex"), width=50, command=lambda: self.run_thread(self.do_png_to_ptex))
        self.btn_pack_ptex.pack(pady=5)

    def build_scr_tab(self):
        self.f_scr = ttk.Frame(self.notebook)
        self.notebook.add(self.f_scr, text=_("tab_scr"))
        self.lbl_scr_desc = ttk.Label(self.f_scr, text=_("scr_desc"))
        self.lbl_scr_desc.pack(pady=10)
        self.btn_scr_to_png = ttk.Button(self.f_scr, text=_("btn_scr_to_png"), width=50, command=lambda: self.run_thread(self.do_scr, True))
        self.btn_scr_to_png.pack(pady=5)
        self.btn_png_to_scr = ttk.Button(self.f_scr, text=_("btn_png_to_scr"), width=50, command=lambda: self.run_thread(self.do_scr, False))
        self.btn_png_to_scr.pack(pady=5)

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

# ==========================================
    # ИСПОЛНИТЕЛЬНЫЕ МЕТОДЫ ДЛЯ КНОПОК
    # ==========================================
    def do_unpack_ppk(self):
        workspace = self.target_dir.get()
        print(f"-> Поиск .ppk архивов в {workspace}...")
        found = 0
        for root, dirs, files in os.walk(workspace):
            for f in files:
                if f.lower().endswith('.ppk') and not f.lower().endswith('_new.ppk'):
                    ppk_path = os.path.join(root, f)
                    out_dir = ppk_path + "_extracted"
                    module_ppk.unpack_ppk(ppk_path, out_dir)
                    found += 1
        print(f"-> Готово! Распаковано архивов: {found}")

    def do_pack_ppk(self):
        workspace = self.target_dir.get()
        print(f"-> Поиск папок *_extracted в {workspace}...")
        found = 0
        for root, dirs, files in os.walk(workspace):
            for d in dirs:
                if d.endswith('.ppk_extracted') or d.endswith('.PPK_extracted'):
                    folder_path = os.path.join(root, d)
                    out_ppk = folder_path.replace('_extracted', '_new.ppk')
                    module_ppk.pack_ppk(folder_path, out_ppk)
                    found += 1
        print(f"-> Готово! Собрано архивов: {found}")

    def do_ptex_to_png(self):
        workspace = self.target_dir.get()
        print(f"-> Поиск текстур .ptex в {workspace}...")
        found = 0
        for root, dirs, files in os.walk(workspace):
            for f in files:
                if f.lower().endswith('.ptex') and not f.startswith('~'):
                    ptex_path = os.path.join(root, f)
                    png_path = ptex_path.replace('.ptex', '.png').replace('.PTEX', '.png')
                    module_ptex.ptex_to_png(ptex_path, png_path)
                    found += 1
        print(f"-> Готово! Извлечено текстур: {found}")

    def do_png_to_ptex(self):
        workspace = self.target_dir.get()
        print(f"-> Поиск .png для запаковки обратно в .ptex в {workspace}...")
        found = 0
        for root, dirs, files in os.walk(workspace):
            for f in files:
                if f.lower().endswith('.png') and not f.lower().endswith('_ru.png'):
                    png_path = os.path.join(root, f)
                    # Ищем оригинальный .ptex файл рядом
                    orig_ptex = png_path.rsplit('.', 1)[0] + '.ptex'
                    if not os.path.exists(orig_ptex):
                        orig_ptex = png_path.rsplit('.', 1)[0] + '.PTEX'
                        
                    if os.path.exists(orig_ptex):
                        out_ptex = png_path.rsplit('.', 1)[0] + '_new.ptex'
                        module_ptex.png_to_ptex(png_path, orig_ptex, out_ptex)
                        found += 1
        print(f"-> Готово! Запаковано текстур: {found}")

    def do_scr(self, to_png):
        workspace = self.target_dir.get()
        found = 0
        if to_png:
            print(f"-> Поиск экранов .scr в {workspace}...")
            for root, dirs, files in os.walk(workspace):
                for f in files:
                    if f.lower().endswith('.scr'):
                        in_path = os.path.join(root, f)
                        out_path = in_path.replace('.scr', '.png').replace('.SCR', '.png')
                        module_scr.convert_scr(in_path, out_path, to_png=True)
                        found += 1
        else:
            print(f"-> Поиск экранов .png для запаковки в {workspace}...")
            for root, dirs, files in os.walk(workspace):
                for f in files:
                    if f.lower().endswith('.png'):
                        in_path = os.path.join(root, f)
                        orig_scr = in_path.rsplit('.', 1)[0] + '.scr'
                        if not os.path.exists(orig_scr):
                            orig_scr = in_path.rsplit('.', 1)[0] + '.SCR'
                            
                        # Пакуем только если рядом есть оригинальный .scr (защита от мусора)
                        if os.path.exists(orig_scr):
                            out_path = in_path.rsplit('.', 1)[0] + '_new.scr'
                            module_scr.convert_scr(in_path, out_path, to_png=False)
                            found += 1
        print(f"-> Готово! Обработано экранов: {found}")

if __name__ == "__main__":
    app = MytranApp()
    app.mainloop()