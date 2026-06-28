import os
import struct
import json
from text_utils import safe_backup

# --- ФАЙЛЫ ЛОКАЛИЗАЦИИ МИССИЙ (.loc) ---
def extract_loc(file_path, out_path):
    with open(file_path, 'rb') as f:
        count = struct.unpack('<I', f.read(4))[0]
        entries = {}
        for _ in range(count):
            k_len = struct.unpack('<I', f.read(4))[0]
            key = f.read(k_len).decode('ascii', errors='ignore').strip('\x00')
            v_len = struct.unpack('<I', f.read(4))[0]
            val = f.read(v_len).decode('cp1251', errors='replace').strip('\x00')
            entries[key] = val
            
    instructions = {
        "ROLE": "You are a professional game translator. Translate the values in 'entries' to Russian.",
        "LIMITS": "No strict byte limit, but keep it concise and natural.",
        "IGNORE_RULES": "Do NOT change the keys (the left side of the JSON). Only translate the values (the right side).",
        "OUTPUT": "Return ONLY valid JSON with identical structure."
    }
            
    with open(out_path, 'w', encoding='utf-8') as fout:
        json.dump({"type": "LOC", "_instructions": instructions, "entries": entries}, fout, ensure_ascii=False, indent=4)
    print(f"-> Распаковано (LOC): {os.path.basename(out_path)}")

def pack_loc(json_path, out_path):
    target_path = out_path
    safe_backup(target_path)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    entries = data.get("entries", {})
    with open(target_path, 'wb') as f:
        f.write(struct.pack('<I', len(entries)))
        for k, v in entries.items():
            k_bytes = k.encode('ascii') + b'\x00'
            v_bytes = v.encode('cp1251', errors='replace') + b'\x00'
            f.write(struct.pack('<I', len(k_bytes)))
            f.write(k_bytes)
            f.write(struct.pack('<I', len(v_bytes)))
            f.write(v_bytes)
    print(f"-> Запаковано (LOC): {os.path.basename(target_path)}")

# --- ФАЙЛЫ ДИАЛОГОВ (mission_XX.bin) ---
def extract_bin(file_path, out_path):
    with open(file_path, 'rb') as f:
        c_count = struct.unpack('<I', f.read(4))[0]
        cutscenes = {}
        for _ in range(c_count):
            d_count = struct.unpack('<I', f.read(4))[0]
            name_len = struct.unpack('<I', f.read(4))[0]
            name = f.read(name_len).decode('ascii', errors='ignore').strip('\x00')
            
            dialogues = []
            for _ in range(d_count):
                speaker = struct.unpack('<I', f.read(4))[0]
                v_len = struct.unpack('<I', f.read(4))[0]
                val = f.read(v_len).decode('cp1251', errors='replace').strip('\x00')
                dialogues.append({"speaker": speaker, "text": val})
            
            cutscenes[name] = dialogues
            
    instructions = {
        "ROLE": "You are a professional game translator. Translate the 'text' fields in 'cutscenes'.",
        "LIMITS": "No strict byte limit for dialogue text. Keep it natural.",
        "IGNORE_RULES": "Do NOT change 'speaker' IDs or any other structure.",
        "OUTPUT": "Return ONLY valid JSON with identical structure."
    }
            
    with open(out_path, 'w', encoding='utf-8') as fout:
        json.dump({"type": "DIALOGUE", "_instructions": instructions, "cutscenes": cutscenes}, fout, ensure_ascii=False, indent=4)
    print(f"-> Распаковано (Диалоги): {os.path.basename(out_path)}")

def pack_bin(json_path, out_path):
    target_path = out_path
    safe_backup(target_path)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    cutscenes = data.get("cutscenes", {})
    with open(target_path, 'wb') as f:
        f.write(struct.pack('<I', len(cutscenes)))
        for name, dialogues in cutscenes.items():
            f.write(struct.pack('<I', len(dialogues)))
            n_bytes = name.encode('ascii') + b'\x00'
            f.write(struct.pack('<I', len(n_bytes)))
            f.write(n_bytes)
            
            for dlg in dialogues:
                f.write(struct.pack('<I', dlg.get("speaker", 0)))
                t_bytes = dlg.get("text", "").encode('cp1251', errors='replace') + b'\x00'
                f.write(struct.pack('<I', len(t_bytes)))
                f.write(t_bytes)
    print(f"-> Запаковано (Диалоги): {os.path.basename(target_path)}")