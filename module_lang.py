import os
import glob

DEFAULT_LANG_RU = {
    "title": "Mytran Wars Modding Toolbox (Modular)",
    "work_dir": "Рабочая папка:",
    "browse": "Обзор",
    "tab_ppk": "  PPK Архивы  ",
    "ppk_desc": "Распаковка с созданием списка (_filelist.txt) и чистая сборка без мусора.",
    "btn_unpack_ppk": "Распаковать ВСЕ .ppk в папки *_extracted",
    "btn_pack_ppk": "Собрать все папки *_extracted обратно в _new.ppk",
    "tab_ptex": "  PTEX Текстуры  ",
    "ptex_desc": "Поиск и обработка .ptex во всех папках *_extracted",
    "btn_unpack_ptex": "Распаковать ВСЕ .ptex -> .png",
    "btn_pack_ptex": "Запаковать ВСЕ .png -> .ptex",
    "tab_scr": "  SCR Экраны  ",
    "scr_desc": "Обработка загрузочных экранов (RAW RGBA 480x272)",
    "btn_scr_to_png": "Конвертировать .scr -> .png",
    "btn_png_to_scr": "Собрать .png -> .scr",
    "tab_eboot": "  EBOOT Шрифты  ",
    "eboot_desc": "Извлечение и инжект шрифтов (PNG текстуры + Метрики в .txt) <-> EBOOT.BIN",
    "btn_select_eboot": "Выбрать EBOOT",
    "btn_select_font_dir": "Папка шрифтов",
    "btn_extract_fonts": "1. Вытащить шрифты (PNG + TXT метрики) из EBOOT",
    "btn_inject_fonts": "2. Вшить измененные PNG и TXT обратно в EBOOT",
    "btn_font_studio": "Открыть Font Studio (Визуальный редактор метрик)",
    "console": "Консоль",
    "welcome": "Добро пожаловать! Модульная структура и локализация активированы.\n" + "="*50,
    "lang_label": "Язык (Language):"
}

DEFAULT_LANG_EN = {
    "title": "Mytran Wars Modding Toolbox (Modular)",
    "work_dir": "Working directory:",
    "browse": "Browse",
    "tab_ppk": "  PPK Archives  ",
    "ppk_desc": "Unpack with manifest (_filelist.txt) and clean pack without trash.",
    "btn_unpack_ppk": "Unpack ALL .ppk to *_extracted folders",
    "btn_pack_ppk": "Pack ALL *_extracted folders back to _new.ppk",
    "tab_ptex": "  PTEX Textures  ",
    "ptex_desc": "Find and process .ptex in all *_extracted folders",
    "btn_unpack_ptex": "Unpack ALL .ptex -> .png",
    "btn_pack_ptex": "Pack ALL .png -> .ptex",
    "tab_scr": "  SCR Screens  ",
    "scr_desc": "Processing loading screens (RAW RGBA 480x272)",
    "btn_scr_to_png": "Convert .scr -> .png",
    "btn_png_to_scr": "Pack .png -> .scr",
    "tab_eboot": "  EBOOT Fonts  ",
    "eboot_desc": "Extract and inject fonts directly (PNG textures + .txt metrics) <-> EBOOT.BIN",
    "btn_select_eboot": "Select EBOOT",
    "btn_select_font_dir": "Fonts Folder",
    "btn_extract_fonts": "1. Extract fonts (PNG + TXT metrics) from EBOOT",
    "btn_inject_fonts": "2. Inject modified PNGs and TXTs back to EBOOT",
    "btn_font_studio": "Open Font Studio (Visual Metrics Editor)",
    "console": "Console",
    "welcome": "Welcome! Modular structure and localization activated.\n" + "="*50,
    "lang_label": "Language:"
}

LANG = {}
current_lang_code = "ru"

def init_langs():
    global current_lang_code
    if not glob.glob("lang_*.txt"):
        with open("lang_ru.txt", "w", encoding="utf-8") as f:
            for k, v in DEFAULT_LANG_RU.items(): f.write(f"{k}={v}\n")
        with open("lang_en.txt", "w", encoding="utf-8") as f:
            for k, v in DEFAULT_LANG_EN.items(): f.write(f"{k}={v}\n")

    if os.path.exists("lang.conf"):
        with open("lang.conf", "r", encoding="utf-8") as f:
            cfg_code = f.read().strip().lower()
            if os.path.exists(f"lang_{cfg_code}.txt"):
                current_lang_code = cfg_code

    load_lang(current_lang_code)

def load_lang(code):
    global LANG, current_lang_code
    LANG.clear()
    LANG.update(DEFAULT_LANG_RU)
    file_path = f"lang_{code}.txt"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    LANG[k] = v
        current_lang_code = code
        with open("lang.conf", "w", encoding="utf-8") as f:
            f.write(code)

def get_available_langs():
    langs = []
    for file in glob.glob("lang_*.txt"):
        code = os.path.basename(file).replace("lang_", "").replace(".txt", "")
        langs.append(code.upper())
    return sorted(langs)

def _(key):
    return LANG.get(key, key)