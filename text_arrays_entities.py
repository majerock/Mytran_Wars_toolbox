# --- START OF FILE text_arrays_entities.py ---

import os
import struct
import json
from text_utils import safe_backup
from text_arrays_helpers import read_str_fixed, write_str_fixed, is_valid_text

def extract_hero(data, out_path):
    records = {}
    record_size = 268 
    count = len(data) // record_size
    for i in range(count):
        offset = i * record_size
        name = read_str_fixed(data, offset, 60)
        desc = read_str_fixed(data, offset + 64, 204)
        rec = {}
        if name: rec["Name"] = name
        if desc: rec["Description"] = desc
        if rec: records[str(i)] = rec

    instructions = {
        "ROLE": "You are a professional game translator. Translate the values in 'records' to Russian.",
        "LIMITS": "Name MUST NOT exceed 59 chars. Description MUST NOT exceed 203 chars.",
        "OUTPUT": "Return ONLY valid JSON with identical structure."
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({"type": "Hero", "_instructions": instructions, "records": records}, f, ensure_ascii=False, indent=4)
    print(f"-> Распаковано (Hero): {os.path.basename(out_path)}")

def pack_hero(j_data, base_bin_path, out_path):
    target_path = out_path if out_path else base_bin_path
    bak_path = safe_backup(base_bin_path)
    with open(bak_path, 'rb') as f: data = bytearray(f.read())
    records = j_data.get("records", {})
    record_size = 268
    
    for idx_str, fields in records.items():
        idx = int(idx_str)
        offset = idx * record_size
        if offset + record_size > len(data): continue
        if "Name" in fields: write_str_fixed(data, offset, 60, fields["Name"])
        if "Description" in fields: write_str_fixed(data, offset + 64, 204, fields["Description"])
            
    with open(target_path, 'wb') as f: f.write(data)
    print(f"-> Запаковано (Hero): {os.path.basename(target_path)}")

def extract_aiarmies(data, out_path):
    records = {}
    count = struct.unpack('<I', data[0:4])[0]
    offset = 4
    read_encoding = 'cp1251'
    try:
        for i in range(count):
            rec = {}
            name_len = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4
            rec["GroupName"] = data[offset : offset + name_len].split(b'\x00')[0].decode(read_encoding, errors='ignore').strip()
            offset += name_len + 4 
            
            desc_len = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4
            rec["Description"] = data[offset : offset + desc_len].split(b'\x00')[0].decode(read_encoding, errors='ignore').strip()
            offset += desc_len + 4 
            
            unit_count = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4
            for _ in range(unit_count):
                cls_len = struct.unpack('<I', data[offset:offset+4])[0]
                offset += 4 + cls_len + 32
            records[str(i)] = rec
    except Exception as e: pass

    instructions = {
        "ROLE": "Translate the English text in 'records' to Russian.",
        "LIMITS": "No strict length limits!",
        "OUTPUT": "Return ONLY valid JSON with identical structure."
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({"type": "AIArmies", "_instructions": instructions, "records": records}, f, ensure_ascii=False, indent=4)
    print(f"-> Распаковано (AIArmies): {os.path.basename(out_path)}")

def pack_aiarmies(j_data, base_bin_path, out_path):
    target_path = out_path if out_path else base_bin_path
    bak_path = safe_backup(base_bin_path)
    with open(bak_path, 'rb') as f: data = f.read()
    records = j_data.get("records", {})
    count = struct.unpack('<I', data[0:4])[0]
    offset = 4
    new_data = bytearray()
    new_data.extend(struct.pack('<I', count))
    
    for i in range(count):
        rec = records.get(str(i), {})
        orig_name_len = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        orig_name = data[offset : offset + orig_name_len]
        offset += orig_name_len
        unk_1 = data[offset : offset+4]
        offset += 4
        
        orig_desc_len = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        orig_desc = data[offset : offset + orig_desc_len]
        offset += orig_desc_len
        unk_2 = data[offset : offset+4]
        offset += 4
        
        unit_count = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        units_data = bytearray()
        for _ in range(unit_count):
            cls_len = struct.unpack('<I', data[offset:offset+4])[0]
            chunk_len = 4 + cls_len + 32
            units_data.extend(data[offset : offset + chunk_len])
            offset += chunk_len
            
        new_name = rec["GroupName"].encode('cp1251', errors='replace') + b'\x00' if "GroupName" in rec else orig_name
        new_data.extend(struct.pack('<I', len(new_name)))
        new_data.extend(new_name)
        new_data.extend(unk_1)
        
        new_desc = rec["Description"].encode('cp1251', errors='replace') + b'\x00' if "Description" in rec else orig_desc
        new_data.extend(struct.pack('<I', len(new_desc)))
        new_data.extend(new_desc)
        new_data.extend(unk_2)
        new_data.extend(struct.pack('<I', unit_count))
        new_data.extend(units_data)
        
    with open(target_path, 'wb') as f: f.write(new_data)
    print(f"-> Запаковано (AIArmies): {os.path.basename(target_path)}")

def extract_skills_affections(data, out_path):
    records = {}
    record_size = 176 if len(data) % 176 == 0 else 180
    count = len(data) // record_size
    read_encoding = 'cp1251'
    
    for i in range(count):
        offset = i * record_size
        text_block = data[offset : offset + record_size - 16]
        strings = {}
        current_offset = 0
        while current_offset < len(text_block):
            null_pos = text_block.find(b'\x00', current_offset)
            if null_pos == -1: null_pos = len(text_block)
            chunk = text_block[current_offset:null_pos]
            if current_offset in (0, 30) and is_valid_text(chunk, read_encoding):
                text = chunk.decode(read_encoding).strip()
                if text: strings[str(current_offset)] = text
            current_offset = null_pos + 1
        if strings: records[str(i)] = strings

    instructions = {
        "ROLE": "Translate the values to Russian.",
        "LIMITS": "Keep string lengths close to the original.",
        "IGNORE_RULES": "Keys are exact memory offsets. DO NOT change the keys.",
        "OUTPUT": "Return ONLY valid JSON with identical structure."
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({"type": "Skills_Affections", "_instructions": instructions, "records": records}, f, ensure_ascii=False, indent=4)
    print(f"-> Распаковано (Skills/Affections): {os.path.basename(out_path)}")

def pack_skills_affections(j_data, base_bin_path, out_path):
    target_path = out_path if out_path else base_bin_path
    bak_path = safe_backup(base_bin_path)
    with open(bak_path, 'rb') as f: data = bytearray(f.read())
    record_size = 176 if len(data) % 176 == 0 else 180
    records = j_data.get("records", {})
    
    for idx_str, strings in records.items():
        idx = int(idx_str)
        block_offset = idx * record_size
        if block_offset + record_size > len(data): continue
        block_len = record_size - 16
        block = bytearray(data[block_offset : block_offset + block_len])
        offsets = sorted([int(k) for k in strings.keys()])
        
        for j, str_off in enumerate(offsets):
            if str_off >= block_len: continue
            text_bytes = strings[str(str_off)].encode('cp1251', errors='replace')
            max_len = (offsets[j+1] if j < len(offsets) - 1 else block_len) - str_off - 1
            for k in range(str_off, str_off + max_len): block[k] = 0
            if len(text_bytes) > max_len: text_bytes = text_bytes[:max_len]
            block[str_off : str_off + len(text_bytes)] = text_bytes
        data[block_offset : block_offset + block_len] = block
            
    with open(target_path, 'wb') as f: f.write(data)
    print(f"-> Запаковано (Skills/Affections): {os.path.basename(target_path)}")

def extract_quiz(data, out_path):
    records = {}
    count = struct.unpack('<I', data[0:4])[0]
    record_size = 360
    
    for i in range(count):
        offset = 4 + i * record_size
        if offset + record_size > len(data): break
        
        q = read_str_fixed(data, offset, 200)
        a1 = read_str_fixed(data, offset + 200, 40)
        a2 = read_str_fixed(data, offset + 240, 40)
        a3 = read_str_fixed(data, offset + 280, 40)
        a4 = read_str_fixed(data, offset + 320, 40)
        
        rec = {}
        if q: rec["Question"] = q
        if a1: rec["Answer1"] = a1
        if a2: rec["Answer2"] = a2
        if a3: rec["Answer3"] = a3
        if a4: rec["Answer4"] = a4
        
        if rec:
            records[str(i)] = rec

    instructions = {
        "ROLE": "You are a professional game translator. Translate the quiz to Russian.",
        "LIMITS": "'Question' (max 199 chars). 'Answer1'..'Answer4' (max 39 chars each).",
        "IGNORE_RULES": "Answer1 is always the correct answer. The game shuffles them automatically.",
        "OUTPUT": "Return ONLY valid JSON with identical structure."
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({"type": "Quiz", "_instructions": instructions, "records": records}, f, ensure_ascii=False, indent=4)
    print(f"-> Распаковано (Quiz): {os.path.basename(out_path)} ({count} вопросов)")

def pack_quiz(j_data, base_bin_path, out_path):
    target_path = out_path if out_path else base_bin_path
    bak_path = safe_backup(base_bin_path)
    with open(bak_path, 'rb') as f: data = bytearray(f.read())
    records = j_data.get("records", {})
    record_size = 360
    
    for idx_str, fields in records.items():
        idx = int(idx_str)
        offset = 4 + idx * record_size
        if offset + record_size > len(data): continue
        
        if "Question" in fields: write_str_fixed(data, offset, 200, fields["Question"])
        if "Answer1" in fields: write_str_fixed(data, offset + 200, 40, fields["Answer1"])
        if "Answer2" in fields: write_str_fixed(data, offset + 240, 40, fields["Answer2"])
        if "Answer3" in fields: write_str_fixed(data, offset + 280, 40, fields["Answer3"])
        if "Answer4" in fields: write_str_fixed(data, offset + 320, 40, fields["Answer4"])
        
    with open(target_path, 'wb') as f: f.write(data)
    print(f"-> Запаковано (Quiz): {os.path.basename(target_path)}")

def extract_equipment(data, out_path):
    records = {}
    
    # Математическая карта файла: (количество_предметов, размер_каждого_блока)
    blocks = [
        (24, 632),  # 0-23   Оружие
        (72, 584),  # 24-95  Шасси, Ноги, Визоры
        (24, 492),  # 96-119 Логистика
        (24, 496),  # 120-143 Спец-экипировка
        (24, 632)   # 144-167 Турели
    ]
    
    offset = 0
    idx = 0
    
    for count, size in blocks:
        for _ in range(count):
            if offset + size > len(data):
                break
                
            # Имя всегда начинается с 0-го байта блока (макс 40 байт)
            name = read_str_fixed(data, offset, 40)
            
            # Описание всегда начинается с 44-го байта блока (макс 200 байт)
            desc = read_str_fixed(data, offset + 44, 200)
            
            rec = {}
            if name: rec["Name"] = name
            if desc: rec["Description"] = desc
            
            if rec: 
                records[str(idx)] = rec
                
            offset += size
            idx += 1

    instructions = {
        "ROLE": "You are a professional game translator. Translate the English text to Russian.",
        "LIMITS": "'Name' MUST NOT exceed 39 chars. 'Description' MUST NOT exceed 199 chars.",
        "IGNORE_RULES": "If 'Name' is '?', strictly leave it as '?'. If 'Description' is missing, DO NOT invent one. Do not translate system words.",
        "OUTPUT": "Return ONLY valid JSON with identical structure."
    }
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({"type": "Equipment_Weapons", "_instructions": instructions, "records": records}, f, ensure_ascii=False, indent=4)
    print(f"-> Распаковано (Equipment): {os.path.basename(out_path)} ({len(records)} предметов)")

def pack_equipment(j_data, base_bin_path, out_path):
    target_path = out_path if out_path else base_bin_path
    bak_path = safe_backup(base_bin_path)
    
    with open(bak_path, 'rb') as f: 
        data = bytearray(f.read())
        
    records = j_data.get("records", {})
    
    blocks = [
        (24, 632), (72, 584), (24, 492), (24, 496), (24, 632)
    ]
    
    offset = 0
    idx = 0
    
    for count, size in blocks:
        for _ in range(count):
            if offset + size > len(data):
                break
                
            idx_str = str(idx)
            if idx_str in records:
                fields = records[idx_str]
                
                # Функция write_str_fixed автоматически заполнит остаток блока нулями!
                if "Name" in fields:
                    write_str_fixed(data, offset, 40, fields["Name"])
                    
                if "Description" in fields:
                    write_str_fixed(data, offset + 44, 200, fields["Description"])
                    
            offset += size
            idx += 1
            
    with open(target_path, 'wb') as f: 
        f.write(data)
    print(f"-> Запаковано (Equipment): {os.path.basename(target_path)}")

# =====================================================================
# УМНЫЙ ПАРСЕР ЮНИТОВ И СТРОЕНИЙ (АБСОЛЮТНЫЙ ОФФСЕТ-МАППЕР)
# =====================================================================
def is_translatable_unit_text(text):
    if len(text) < 3: return False
    
    # Системные пути/ID с нижним подчеркиванием
    if "_" in text: return False
    
    # Чисто строчные слова без пробелов (bugs, powerstation)
    if " " not in text and text.islower(): return False
    
    # CamelCase C++ классы (LightMecha, HeavyMythra)
    if " " not in text and text[0].isupper() and any(c.isupper() for c in text[1:]): return False
        
    # ID заканчивающиеся на цифру (Stonebarricade1, Surya2)
    if " " not in text and text[-1].isdigit(): return False
    
    # Валидный текст всегда начинается с Заглавной буквы, Цифры, + или -
    if not (text[0].isupper() or text[0].isdigit() or text[0] in "+-"): return False
        
    # Мусор от кодировок
    if "яя" in text or "ÿÿ" in text or "Î" in text: return False
    
    return True
# =====================================================================
# ИДЕАЛЬНЫЙ ПАРСЕР ЮНИТОВ И СТРОЕНИЙ (UNITS.BIN)
# =====================================================================
def extract_units(data, out_path):
    records = {}
    record_size = 504  # Математически точный размер!
    count = len(data) // record_size
    
    for i in range(count):
        offset = i * record_size
        
        # Читаем системный контекст (чтобы переводчик понимал, что это за юнит)
        sys_class = read_str_fixed(data, offset + 0, 30)
        sys_id = read_str_fixed(data, offset + 360, 62)
        
        # Точные координаты текста (Имя: 30-й байт, Описание: 60-й байт)
        name = read_str_fixed(data, offset + 30, 30)
        desc = read_str_fixed(data, offset + 60, 300)
        
        rec = {}
        if sys_class: rec["_Class"] = sys_class
        if sys_id: rec["_InternalID"] = sys_id
        if name: rec["Name"] = name
        if desc: rec["Description"] = desc
        
        records[str(i)] = rec

    instructions = {
        "ROLE": "You are a professional game translator. Translate the values to Russian.",
        "LIMITS": "'Name' MUST NOT exceed 29 chars. 'Description' MUST NOT exceed 299 chars.",
        "IGNORE_RULES": "Do NOT translate fields starting with underscore (e.g. '_Class', '_InternalID').",
        "OUTPUT": "Return ONLY valid JSON with identical structure."
    }

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({"type": "Units", "_instructions": instructions, "records": records}, f, ensure_ascii=False, indent=4)
    print(f"-> Распаковано (Units): {os.path.basename(out_path)} ({len(records)} юнитов/строений)")

def pack_units(j_data, base_bin_path, out_path):
    target_path = out_path if out_path else base_bin_path
    bak_path = safe_backup(base_bin_path)
    
    with open(bak_path, 'rb') as f:
        data = bytearray(f.read())
        
    records = j_data.get("records", {})
    record_size = 504
    
    for idx_str, fields in records.items():
        idx = int(idx_str)
        offset = idx * record_size
        
        if offset + record_size > len(data):
            continue
            
        # Записываем перевод строго на свои места, затирая старые хвосты нулями
        if "Name" in fields:
            write_str_fixed(data, offset + 30, 30, fields["Name"])
            
        if "Description" in fields:
            write_str_fixed(data, offset + 60, 300, fields["Description"])
            
    with open(target_path, 'wb') as f: 
        f.write(data)
    print(f"-> Запаковано (Units): {os.path.basename(target_path)}")