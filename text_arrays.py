# --- START OF FILE text_arrays.py ---

import os
import struct
import json
from text_utils import safe_backup, extract_smart_text, inject_smart_text

# Подключаем наши модули
from text_arrays_maps import (
    extract_mapdata, pack_mapdata,
    extract_multimap, pack_multimap,
    extract_blockmap, pack_blockmap
)
from text_arrays_entities import (
    extract_hero, pack_hero,
    extract_aiarmies, pack_aiarmies,
    extract_skills_affections, pack_skills_affections,
    extract_quiz, pack_quiz,
    extract_equipment, pack_equipment,
    extract_units, pack_units
)

# =====================================================================
# СТАНДАРТНЫЕ ФОРМАТЫ СИСТЕМНЫХ МАССИВОВ
# =====================================================================
DATA_FORMATS = [
    {
        "name": "Tips",
        "record_size": 64,
        "header_size": 0,
        "strings": [("Title", 30, 30)],
        "context": [("_Filename", 0, 30)]
    },
    {
        "name": "StartParam",
        "record_size": 32,
        "header_size": 16,
        "strings": [],
        "context": [("_PMF_Path", 0, 32)]
    }
]

def determine_format(filename):
    name = filename.lower()
    if "blockmap" in name: return "Blockmap"
    if "aiarmies" in name: return "AIArmies"
    if "hero" in name: return "Hero"
    if "quiz" in name: return "Quiz"
    if "reshuman" in name or "resmyth" in name or "resalien" in name: return "Equipment_Weapons"
    if "units" in name: return "Units"
    if "multimap" in name: return "MapData_Multi"
    if "mapdata" in name: return "MapData_Single"
    if "tips" in name: return "Tips"
    if "affection" in name or "skills" in name: return "Skills_Affections"
    if "startparam" in name: return "IGNORE"
    return None

# =====================================================================
# ГЛАВНЫЙ РОУТЕР
# =====================================================================
def extract_data_array(file_path, out_path):
    with open(file_path, 'rb') as f:
        data = f.read()

    file_size = len(data)
    file_name = os.path.basename(file_path)
    fmt_name = determine_format(file_name)
    
    if not fmt_name or fmt_name == "IGNORE":
        print(f"Пропуск: файл {file_name} не содержит переводимого текста.")
        return

    # Перехватываем кастомные сложные форматы (Роутинг в другие файлы)
    if fmt_name == "Blockmap": return extract_blockmap(data, out_path)
    if fmt_name == "AIArmies": return extract_aiarmies(data, out_path)
    if fmt_name == "Skills_Affections": return extract_skills_affections(data, out_path)
    if fmt_name == "Hero": return extract_hero(data, out_path)
    if fmt_name == "MapData_Single": return extract_mapdata(data, out_path)
    if fmt_name == "MapData_Multi": return extract_multimap(data, out_path)
    if fmt_name == "Quiz": return extract_quiz(data, out_path)
    if fmt_name == "Equipment_Weapons": return extract_equipment(data, out_path)
    if fmt_name == "Units": return extract_units(data, out_path)

    # Стандартный парсер для остальных форматов
    fmt = next((f for f in DATA_FORMATS if f["name"] == fmt_name), None)
    count = (file_size - fmt["header_size"]) // fmt["record_size"]
    
    if fmt["header_size"] == 4:
        header_count = struct.unpack('<I', data[0:4])[0]
        if header_count <= count:
            count = header_count

    records = {}
    offset = fmt["header_size"]
    
    for i in range(count):
        rec = {}
        for s_name, s_off, s_len in fmt.get("context", []):
            s_data = data[offset + s_off : offset + s_off + s_len]
            rec[s_name] = s_data.split(b'\x00')[0].decode('ascii', errors='ignore')
            
        for s_name, s_off, s_len in fmt["strings"]:
            block = data[offset + s_off : offset + s_off + s_len]
            clean_str = extract_smart_text(block)
            if clean_str:
                rec[s_name] = clean_str
            
        if rec:
            records[str(i)] = rec
        offset += fmt["record_size"]
        
    limits_text = []
    if fmt:
        for s_name, _, s_len in fmt["strings"]:
            limits_text.append(f"'{s_name}' MUST NOT exceed {s_len - 1} chars.")
            
    instructions = {
        "ROLE": "You are a professional game translator. Translate the English text in 'records' to Russian.",
        "LIMITS": " ".join(limits_text),
        "IGNORE_RULES": "Do NOT translate system variables, internal IDs, or paths (e.g., words with underscores).",
        "OUTPUT": "Return ONLY valid JSON with identical structure."
    }

    with open(out_path, 'w', encoding='utf-8') as fout:
        json.dump({"type": fmt['name'], "_instructions": instructions, "records": records}, fout, ensure_ascii=False, indent=4)
    print(f"-> Распаковано ({fmt['name']}): {os.path.basename(out_path)}")

def pack_data_array(json_path, base_bin_path, out_path):
    target_path = base_bin_path
    
    with open(json_path, 'r', encoding='utf-8') as f:
        j_data = json.load(f)
        
    fmt_name = j_data.get("type", "")
    
    # Перехватываем кастомные сложные форматы (Роутинг в другие файлы)
    if fmt_name == "Blockmap": return pack_blockmap(j_data, base_bin_path, out_path)
    if fmt_name == "AIArmies": return pack_aiarmies(j_data, base_bin_path, out_path)
    if fmt_name == "Skills_Affections": return pack_skills_affections(j_data, base_bin_path, out_path)
    if fmt_name == "Hero": return pack_hero(j_data, base_bin_path, out_path)
    if fmt_name == "MapData_Single": return pack_mapdata(j_data, base_bin_path, out_path)
    if fmt_name == "MapData_Multi": return pack_multimap(j_data, base_bin_path, out_path)
    if fmt_name == "Quiz": return pack_quiz(j_data, base_bin_path, out_path)
    if fmt_name == "Equipment_Weapons": return pack_equipment(j_data, base_bin_path, out_path)
    if fmt_name == "Units": return pack_units(j_data, base_bin_path, out_path)

    # Стандартная упаковка
    bak_path = safe_backup(target_path)
    with open(bak_path, 'rb') as f:
        data = bytearray(f.read())
        
    fmt = next((f for f in DATA_FORMATS if f["name"] == fmt_name), None)
    if not fmt:
        print(f"Ошибка: Формат {fmt_name} не найден в базе!")
        return

    records = j_data.get("records", {})
    for rec_idx_str, fields in records.items():
        rec_idx = int(rec_idx_str)
        offset = fmt["header_size"] + rec_idx * fmt["record_size"]
        
        if offset + fmt["record_size"] > len(data):
            continue
            
        for s_name, s_off, s_len in fmt["strings"]:
            if s_name in fields:
                block = bytearray(data[offset + s_off : offset + s_off + s_len])
                new_block = inject_smart_text(block, fields[s_name])
                data[offset + s_off : offset + s_off + s_len] = new_block
                
    with open(target_path, 'wb') as f: f.write(data)
    print(f"-> Запаковано ({fmt['name']}): {os.path.basename(target_path)}")