import os
import struct

# Универсальные форматы для Array of Structs
DATA_FORMATS = [
    {
        "name": "Quiz",
        "record_size": 256,
        "header_size": 4,
        "strings": [("Question", 0, 128), ("Answer1", 128, 32), ("Answer2", 160, 32), ("Answer3", 192, 32), ("Answer4", 224, 32)]
    },
    {
        "name": "Hero",
        "record_size": 324,
        "header_size": 0,
        "strings": [("Name", 0, 64), ("Description", 68, 256)]
    },
    {
        "name": "Equipment_Weapons",
        "record_size": 448,
        "header_size": 0,
        "strings": [("Name", 0, 52), ("Description", 64, 256), ("InternalName", 384, 32), ("Slot", 416, 32)]
    },
    {
        "name": "MapData_Scenarios",
        "record_size": 616,
        "header_size": 0,
        "strings": [("Name", 0, 32), ("Terrain", 32, 32), ("Music", 72, 32), ("Description", 104, 512)]
    },
    {
        "name": "Tips",
        "record_size": 64,
        "header_size": 0,
        "strings": [("Filename", 0, 30), ("Title", 30, 30)]
    },
    {
        "name": "Skills_Affections",
        "record_size": 128,
        "header_size": 0,
        "strings": [("ID_or_Name", 0, 32), ("Description", 32, 56)]
    },
    {
        "name": "StartParam",
        "record_size": 32,
        "header_size": 16,
        "strings": [("PMF_Path", 0, 32)]
    }
]

# --- СПЕЦИАЛЬНЫЙ ПАРСЕР ДЛЯ BLOCKMAP.BIN (Плавающие структуры) ---
def extract_blockmap(data, out_path):
    strings = []
    count = struct.unpack('<I', data[0:4])[0]
    offset = 4
    found = 0
    while offset < len(data) - 54 and found < count:
        str_len = struct.unpack('<I', data[offset:offset+4])[0]
        if 0 < str_len <= 50:
            s_data = data[offset+4 : offset+4+str_len-1]
            padding = data[offset+4+str_len : offset+54]
            # Проверяем, что паддинг состоит из нулей, а строка закрыта нуль-терминатором
            if all(b == 0 for b in padding) and data[offset+4+str_len-1] == 0:
                if all(b >= 32 or b in (9, 10, 13) for b in s_data):
                    strings.append({
                        'offset': offset,
                        'text': s_data.decode('cp1251', errors='ignore')
                    })
                    found += 1
                    offset += 54
                    continue
        offset += 4
        
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("### FORMAT: Blockmap ###\n\n")
        for s in strings:
            f.write(f"[{s['offset']}]\n{s['text']}\n\n")

def pack_blockmap(txt_path, base_bin_path, out_path):
    with open(base_bin_path, 'rb') as f:
        data = bytearray(f.read())
        
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    cur_offset = None
    cur_text = []
    for line in lines[1:]:
        line = line.rstrip('\n')
        if line.startswith('[') and line.endswith(']'):
            if cur_offset is not None:
                text_bytes = "\\n".join(cur_text).encode('cp1251', errors='replace')
                if len(text_bytes) < 50:
                    struct.pack_into('<I', data, cur_offset, len(text_bytes) + 1)
                    data[cur_offset+4 : cur_offset+54] = text_bytes + b'\x00' + b'\x00' * (49 - len(text_bytes))
            cur_offset = int(line[1:-1])
            cur_text = []
        elif cur_offset is not None:
            if line.strip() != "" or len(cur_text) > 0:
                cur_text.append(line)
                
    if cur_offset is not None:
        text_bytes = "\\n".join(cur_text).encode('cp1251', errors='replace')
        if len(text_bytes) < 50:
            struct.pack_into('<I', data, cur_offset, len(text_bytes) + 1)
            data[cur_offset+4 : cur_offset+54] = text_bytes + b'\x00' + b'\x00' * (49 - len(text_bytes))
            
    with open(out_path, 'wb') as f: f.write(data)

# --- УНИВЕРСАЛЬНЫЙ АНАЛИЗАТОР И ПАРСЕР ДАМПОВ ---
def extract_data_array(file_path, out_path):
    with open(file_path, 'rb') as f:
        data = f.read()

    file_size = len(data)
    fmt = None
    
    # Пытаемся угадать формат файла по размеру и кратности
    for f_fmt in DATA_FORMATS:
        if f_fmt["header_size"] > 0:
            if file_size >= f_fmt["header_size"]:
                count = struct.unpack('<I', data[0:4])[0]
                if file_size == f_fmt["header_size"] + count * f_fmt["record_size"]:
                    fmt = f_fmt
                    break
        else:
            if file_size > 0 and file_size % f_fmt["record_size"] == 0:
                offset = f_fmt["header_size"] + f_fmt["strings"][0][1]
                s_len = f_fmt["strings"][0][2]
                s_data = data[offset : offset+s_len].split(b'\x00')[0]
                if len(s_data) > 0 and all(b >= 32 or b in (9, 10, 13) for b in s_data):
                    fmt = f_fmt
                    break
                elif len(s_data) == 0: 
                    fmt = f_fmt
                    break
                
    if not fmt:
        if "blockmap" in file_path.lower():
            extract_blockmap(data, out_path)
            print(f"-> Распаковано (Blockmap): {os.path.basename(out_path)}")
        else:
            print(f"Ошибка: Неизвестный формат данных или неверный размер для {os.path.basename(file_path)}")
        return

    count = (file_size - fmt["header_size"]) // fmt["record_size"]
    
    with open(out_path, 'w', encoding='utf-8') as fout:
        fout.write(f"### FORMAT: {fmt['name']} ###\n\n")
        offset = fmt["header_size"]
        for i in range(count):
            fout.write(f"=== Record {i} ===\n")
            for s_name, s_off, s_len in fmt["strings"]:
                s_data = data[offset + s_off : offset + s_off + s_len]
                s_str = s_data.split(b'\x00')[0].decode('cp1251', errors='ignore').replace('\n', '\\n')
                fout.write(f"[{s_name}]\n{s_str}\n")
            fout.write("\n")
            offset += fmt["record_size"]
            
    print(f"-> Распаковано ({fmt['name']}): {os.path.basename(out_path)}")

def pack_data_array(txt_path, base_bin_path, out_path):
    with open(base_bin_path, 'rb') as f:
        data = bytearray(f.read())
        
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    fmt_name = None
    if lines and lines[0].startswith("### FORMAT:"):
        fmt_name = lines[0].split("FORMAT:")[1].split("###")[0].strip()
        
    if not fmt_name:
        print(f"Ошибка: Неизвестный формат в txt: {os.path.basename(txt_path)}")
        return
        
    if fmt_name == "Blockmap":
        pack_blockmap(txt_path, base_bin_path, out_path)
        print(f"-> Запаковано (Blockmap): {os.path.basename(out_path)}")
        return

    fmt = next((f for f in DATA_FORMATS if f["name"] == fmt_name), None)
    if not fmt:
        print(f"Ошибка: Формат {fmt_name} не найден в базе!")
        return

    cur_record, cur_key, cur_val = -1, None, []
    records = {}
    
    for line in lines[1:]:
        line = line.rstrip('\n')
        if line.startswith('=== Record ') and line.endswith(' ==='):
            if cur_key is not None and cur_record != -1:
                records[cur_record][cur_key] = "\\n".join(cur_val)
            cur_record = int(line[11:-4])
            records[cur_record] = {}
            cur_key, cur_val = None, []
        elif line.startswith('[') and line.endswith(']'):
            if cur_key is not None and cur_record != -1:
                records[cur_record][cur_key] = "\\n".join(cur_val)
            cur_key = line[1:-1]
            cur_val = []
        elif cur_key is not None:
            if line.strip() != "" or len(cur_val) > 0:
                cur_val.append(line)
                
    if cur_key is not None and cur_record != -1:
        records[cur_record][cur_key] = "\\n".join(cur_val)
        
    for rec_idx, fields in records.items():
        offset = fmt["header_size"] + rec_idx * fmt["record_size"]
        for s_name, s_off, s_len in fmt["strings"]:
            if s_name in fields:
                val = fields[s_name].replace('\\n', '\n').encode('cp1251', errors='replace')
                if len(val) >= s_len: val = val[:s_len-1] # Защита от переполнения
                data[offset + s_off : offset + s_off + s_len] = b'\x00' * s_len
                data[offset + s_off : offset + s_off + len(val)] = val
                
    with open(out_path, 'wb') as f: f.write(data)
    print(f"-> Запаковано ({fmt['name']}): {os.path.basename(out_path)}")

# ------------------------------------------------------------
# НИЖЕ ОСТАЕТСЯ ТВОЙ СТАРЫЙ КОД (extract_loc, extract_bin и т.д.)
# ------------------------------------------------------------
def extract_loc(file_path, out_path):
    with open(file_path, 'rb') as f:
        count = struct.unpack('<I', f.read(4))[0]
        with open(out_path, 'w', encoding='utf-8') as fout:
            for _ in range(count):
                k_len = struct.unpack('<I', f.read(4))[0]
                key = f.read(k_len).decode('ascii', errors='ignore').strip('\x00')
                v_len = struct.unpack('<I', f.read(4))[0]
                val = f.read(v_len).decode('cp1251', errors='replace').strip('\x00')
                fout.write(f"[{key}]\n{val}\n\n")
    print(f"-> Распаковано (LOC): {os.path.basename(out_path)}")

def pack_loc(txt_path, out_path):
    entries = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_key = None
    current_val = []
    for line in lines:
        line = line.replace('\n', '')
        if line.startswith('[') and line.endswith(']'):
            if current_key is not None:
                entries.append((current_key, "\\n".join(current_val)))
            current_key = line[1:-1]
            current_val = []
        elif current_key is not None:
            if line.strip() != "":
                current_val.append(line)
                
    if current_key is not None:
        entries.append((current_key, "\\n".join(current_val)))

    with open(out_path, 'wb') as f:
        f.write(struct.pack('<I', len(entries)))
        for k, v in entries:
            v = v.replace('\\n', '\n')
            k_bytes = k.encode('ascii') + b'\x00'
            v_bytes = v.encode('cp1251', errors='replace') + b'\x00'
            f.write(struct.pack('<I', len(k_bytes)))
            f.write(k_bytes)
            f.write(struct.pack('<I', len(v_bytes)))
            f.write(v_bytes)
    print(f"-> Запаковано (LOC): {os.path.basename(out_path)}")

def extract_bin(file_path, out_path):
    with open(file_path, 'rb') as f:
        c_count = struct.unpack('<I', f.read(4))[0]
        with open(out_path, 'w', encoding='utf-8') as fout:
            for _ in range(c_count):
                d_count = struct.unpack('<I', f.read(4))[0]
                name_len = struct.unpack('<I', f.read(4))[0]
                name = f.read(name_len).decode('ascii', errors='ignore').strip('\x00')
                fout.write(f"=== {name} ===\n")
                for _ in range(d_count):
                    speaker = struct.unpack('<I', f.read(4))[0]
                    v_len = struct.unpack('<I', f.read(4))[0]
                    val = f.read(v_len).decode('cp1251', errors='replace').strip('\x00')
                    fout.write(f"[{speaker}]\n{val}\n\n")
    print(f"-> Распаковано (Диалоги): {os.path.basename(out_path)}")

def pack_bin(txt_path, out_path):
    cutscenes = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    cur_name = None
    cur_dialogues = []
    cur_speaker = None
    cur_text = []
    
    for line in lines:
        line = line.replace('\n', '')
        if line.startswith('=== ') and line.endswith(' ==='):
            if cur_speaker is not None:
                cur_dialogues.append((cur_speaker, "\\n".join(cur_text)))
            if cur_name is not None:
                cutscenes.append((cur_name, cur_dialogues))
            cur_name = line[4:-4]
            cur_dialogues = []
            cur_speaker = None
            cur_text = []
        elif line.startswith('[') and line.endswith(']'):
            if cur_speaker is not None:
                cur_dialogues.append((cur_speaker, "\\n".join(cur_text)))
            cur_speaker = int(line[1:-1])
            cur_text = []
        elif cur_speaker is not None:
            if line.strip() != "":
                cur_text.append(line)
                
    if cur_speaker is not None:
        cur_dialogues.append((cur_speaker, "\\n".join(cur_text)))
    if cur_name is not None:
        cutscenes.append((cur_name, cur_dialogues))

    with open(out_path, 'wb') as f:
        f.write(struct.pack('<I', len(cutscenes)))
        for name, dialogues in cutscenes:
            f.write(struct.pack('<I', len(dialogues)))
            n_bytes = name.encode('ascii') + b'\x00'
            f.write(struct.pack('<I', len(n_bytes)))
            f.write(n_bytes)
            for spk, txt in dialogues:
                f.write(struct.pack('<I', spk))
                txt = txt.replace('\\n', '\n')
                t_bytes = txt.encode('cp1251', errors='replace') + b'\x00'
                f.write(struct.pack('<I', len(t_bytes)))
                f.write(t_bytes)
    print(f"-> Запаковано (Диалоги): {os.path.basename(out_path)}")

def extract_ui(file_path, out_path):
    with open(file_path, 'rb') as f:
        num_sections = struct.unpack('<I', f.read(4))[0]
        with open(out_path, 'w', encoding='utf-8') as fout:
            for _ in range(num_sections):
                s_len = struct.unpack('<I', f.read(4))[0]
                section_name = f.read(s_len).decode('ascii', errors='ignore').strip('\x00')
                fout.write(f"### {section_name} ###\n")

                num_pairs = struct.unpack('<I', f.read(4))[0]
                for _ in range(num_pairs):
                    k_len = struct.unpack('<I', f.read(4))[0]
                    key_bytes = f.read(k_len)
                    v_len = struct.unpack('<I', f.read(4))[0]
                    val_bytes = f.read(v_len)

                    if k_len == 1 and key_bytes == b'\x00' and v_len == 0:
                        continue 

                    key = key_bytes.decode('cp1251', errors='ignore').strip('\x00')
                    val = val_bytes.decode('cp1251', errors='ignore').strip('\x00')
                    val = val.replace('\n', '\\n')

                    fout.write(f"[{key}]\n{val}\n\n")
    print(f"-> Распаковано (Интерфейс): {os.path.basename(out_path)}")

def pack_ui(txt_path, out_path):
    sections = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    cur_section = None
    cur_key = None
    cur_val = []
    pairs = []

    for line in lines:
        line = line.rstrip('\n')
        if line.startswith('### ') and line.endswith(' ###'):
            if cur_key is not None:
                pairs.append((cur_key, "\\n".join(cur_val)))
            if cur_section is not None:
                sections.append((cur_section, pairs))

            cur_section = line[4:-4]
            pairs = []
            cur_key = None
            cur_val = []
        elif line.startswith('[') and line.endswith(']'):
            if cur_key is not None:
                pairs.append((cur_key, "\\n".join(cur_val)))
            cur_key = line[1:-1]
            cur_val = []
        elif cur_key is not None:
            if line.strip() != "" or len(cur_val) > 0:
                cur_val.append(line)

    if cur_key is not None:
        pairs.append((cur_key, "\\n".join(cur_val)))
    if cur_section is not None:
        sections.append((cur_section, pairs))

    with open(out_path, 'wb') as f:
        f.write(struct.pack('<I', len(sections)))
        for sec_name, sec_pairs in sections:
            s_bytes = sec_name.encode('ascii', errors='ignore') + b'\x00'
            f.write(struct.pack('<I', len(s_bytes)))
            f.write(s_bytes)

            f.write(struct.pack('<I', len(sec_pairs) + 1))

            for k, v in sec_pairs:
                v = v.replace('\\n', '\n')
                k_bytes = k.encode('cp1251', errors='replace') + b'\x00'
                v_bytes = v.encode('cp1251', errors='replace') + b'\x00'

                f.write(struct.pack('<I', len(k_bytes)))
                f.write(k_bytes)
                f.write(struct.pack('<I', len(v_bytes)))
                f.write(v_bytes)

            f.write(struct.pack('<I', 1))
            f.write(b'\x00')
            f.write(struct.pack('<I', 0))
    print(f"-> Запаковано (Интерфейс): {os.path.basename(out_path)}")