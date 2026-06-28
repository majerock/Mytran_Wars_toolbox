# --- START OF FILE text_arrays_maps.py ---
import os
import struct
import json
from text_utils import safe_backup
from text_arrays_helpers import read_str_fixed, write_str_fixed

def extract_mapdata(data, out_path):
    records = {}
    block_size = 1584
    count = len(data) // block_size

    for i in range(count):
        base = i * block_size
        path = read_str_fixed(data, base + 0x0000, 32)
        loc_name = read_str_fixed(data, base + 0x0060, 32)
        diary = read_str_fixed(data, base + 0x00AC, 540)
        intro = read_str_fixed(data, base + 0x0304, 30)
        outro = read_str_fixed(data, base + 0x0322, 30)
        mission_name = read_str_fixed(data, base + 0x03BC, 30)
        briefing = read_str_fixed(data, base + 0x03DA, 540)

        records[str(i)] = {
            "_Path": path, "Location": loc_name, "Intro": intro,
            "Outro": outro, "MissionName": mission_name,
            "Diary": diary, "Briefing": briefing
        }

    instructions = {
        "ROLE": "You are a professional game translator. Translate the English text to Russian.",
        "LIMITS": "Location (max 31 chars), Intro/Outro (max 29 chars), MissionName (max 29 chars), Diary/Briefing (max 539 chars).",
        "IGNORE_RULES": "Do NOT translate _Path.",
        "OUTPUT": "Return ONLY valid JSON with identical structure."
    }

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({"type": "MapData_Single", "_instructions": instructions, "records": records}, f, ensure_ascii=False, indent=4)
    print(f"-> Распаковано (MapData_Single): {os.path.basename(out_path)}")

def pack_mapdata(j_data, base_bin_path, out_path):
    target_path = base_bin_path
    bak_path = safe_backup(target_path)
    with open(bak_path, 'rb') as f: data = bytearray(f.read())
    block_size = 1584
    records = j_data.get("records", {})

    for idx_str, entry in records.items():
        i = int(idx_str)
        base = i * block_size
        if base + block_size > len(data): continue
        if "Location" in entry: write_str_fixed(data, base + 0x0060, 32, entry["Location"])
        if "Diary" in entry: write_str_fixed(data, base + 0x00AC, 540, entry["Diary"])
        if "Intro" in entry: write_str_fixed(data, base + 0x0304, 30, entry["Intro"])
        if "Outro" in entry: write_str_fixed(data, base + 0x0322, 30, entry["Outro"])
        if "MissionName" in entry: write_str_fixed(data, base + 0x03BC, 30, entry["MissionName"])
        if "Briefing" in entry: write_str_fixed(data, base + 0x03DA, 540, entry["Briefing"])

    with open(target_path, 'wb') as f: f.write(data)
    print(f"-> Запаковано (MapData_Single): {os.path.basename(target_path)}")

def extract_multimap(data, out_path):
    records = {}
    block_size = 1280
    count = len(data) // block_size

    for i in range(count):
        base = i * block_size
        name = read_str_fixed(data, base + 0x0000, 30)
        terrain = read_str_fixed(data, base + 0x001E, 30)
        music = read_str_fixed(data, base + 0x0044, 30)
        desc = read_str_fixed(data, base + 0x0062, 1182)
        records[str(i)] = {"_Music": music, "Name": name, "Terrain": terrain, "Description": desc}

    instructions = {
        "ROLE": "You are a professional game translator. Translate the English text to Russian.",
        "LIMITS": "Name (max 29 chars), Terrain (max 29 chars), Description (max 1181 chars).",
        "IGNORE_RULES": "Do NOT translate _Music.",
        "OUTPUT": "Return ONLY valid JSON with identical structure."
    }

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({"type": "MapData_Multi", "_instructions": instructions, "records": records}, f, ensure_ascii=False, indent=4)
    print(f"-> Распаковано (MapData_Multi): {os.path.basename(out_path)}")

def pack_multimap(j_data, base_bin_path, out_path):
    target_path = base_bin_path
    bak_path = safe_backup(target_path)
    with open(bak_path, 'rb') as f: data = bytearray(f.read())
    block_size = 1280
    records = j_data.get("records", {})

    for idx_str, entry in records.items():
        i = int(idx_str)
        base = i * block_size
        if base + block_size > len(data): continue
        if "Name" in entry: write_str_fixed(data, base + 0x0000, 30, entry["Name"])
        if "Terrain" in entry: write_str_fixed(data, base + 0x001E, 30, entry["Terrain"])
        if "Description" in entry: write_str_fixed(data, base + 0x0062, 1182, entry["Description"])

    with open(target_path, 'wb') as f: f.write(data)
    print(f"-> Запаковано (MapData_Multi): {os.path.basename(target_path)}")

def extract_blockmap(data, out_path):
    records = {}
    count = struct.unpack('<I', data[0:4])[0]
    offset = 4
    read_encoding = 'cp1251'
    try:
        for i in range(count):
            str_len = struct.unpack('<I', data[offset:offset+4])[0]
            offset += 4
            raw_name = data[offset : offset + str_len].split(b'\x00')[0]
            records[str(i)] = {"Name": raw_name.decode(read_encoding, errors='ignore').strip()}
            offset += str_len + 36 
    except Exception as e: pass

    instructions = {
        "ROLE": "Translate values in 'records'.",
        "LIMITS": "No strict length limits! Translate freely, the file dynamically resizes.",
        "IGNORE_RULES": "Do not translate system names (like 'onlywalker').",
        "OUTPUT": "Return ONLY valid JSON with identical structure."
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({"type": "Blockmap", "_instructions": instructions, "records": records}, f, ensure_ascii=False, indent=4)
    print(f"-> Распаковано (Blockmap): {os.path.basename(out_path)} ({count} типов местности)")

def pack_blockmap(j_data, base_bin_path, out_path):
    target_path = base_bin_path
    bak_path = safe_backup(target_path)
    with open(bak_path, 'rb') as f: data = f.read()
    records = j_data.get("records", {})
    count = struct.unpack('<I', data[0:4])[0]
    offset = 4
    new_data = bytearray()
    new_data.extend(struct.pack('<I', count))
    
    for i in range(count):
        rec = records.get(str(i), {})
        orig_len = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        orig_name = data[offset : offset + orig_len]
        offset += orig_len
        orig_stats = data[offset : offset + 36]
        offset += 36
        
        new_name = rec["Name"].encode('cp1251', errors='replace') + b'\x00' if "Name" in rec else orig_name
        new_data.extend(struct.pack('<I', len(new_name)))
        new_data.extend(new_name)
        new_data.extend(orig_stats)
        
    with open(target_path, 'wb') as f: f.write(new_data)
    print(f"-> Запаковано (Blockmap): {os.path.basename(target_path)}")