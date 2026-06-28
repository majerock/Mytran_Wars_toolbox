import os
import struct
import json
from text_utils import safe_backup

# --- ФАЙЛЫ ИНТЕРФЕЙСА (menu.bin) ---
def extract_ui(file_path, out_path):
    with open(file_path, 'rb') as f:
        num_sections = struct.unpack('<I', f.read(4))[0]
        sections = []
        
        for _ in range(num_sections):
            s_len = struct.unpack('<I', f.read(4))[0]
            section_name = f.read(s_len).decode('ascii', errors='ignore').strip('\x00')
            
            pairs = {}
            num_pairs = struct.unpack('<I', f.read(4))[0]
            
            for _ in range(num_pairs):
                k_len = struct.unpack('<I', f.read(4))[0]
                key_bytes = f.read(k_len)
                v_len = struct.unpack('<I', f.read(4))[0]
                val_bytes = f.read(v_len)

                # ЖЕСТКАЯ cp1251, чтобы маппинг байтов на твой перерисованный шрифт совпадал!
                key = key_bytes.decode('cp1251', errors='ignore').strip('\x00')
                val = val_bytes.decode('cp1251', errors='ignore').strip('\x00')
                pairs[key] = val
            
            sections.append({
                "SectionName": section_name,
                "Pairs": pairs
            })

    instructions = {
        "ROLE": "You are a professional game translator. Translate the values in 'Pairs' to Russian.",
        "LIMITS": "UI space is often limited. Keep words short (e.g., 'Options' -> 'Опции').",
        "IGNORE_RULES": "Do NOT change the keys (left side). Only translate the values (right side).",
        "OUTPUT": "Return ONLY valid JSON with identical structure."
    }

    with open(out_path, 'w', encoding='utf-8') as fout:
        json.dump({"type": "UI", "_instructions": instructions, "sections": sections}, fout, ensure_ascii=False, indent=4)
    print(f"-> Распаковано (Интерфейс): {os.path.basename(out_path)} ({num_sections} секций)")

def pack_ui(json_path, out_path):
    target_path = out_path
    safe_backup(target_path)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    sections = data.get("sections", [])
    
    with open(target_path, 'wb') as f:
        if isinstance(sections, dict):
            f.write(struct.pack('<I', len(sections)))
            for sec_name, pairs in sections.items():
                s_bytes = sec_name.encode('ascii', errors='ignore') + b'\x00'
                f.write(struct.pack('<I', len(s_bytes)))
                f.write(s_bytes)

                f.write(struct.pack('<I', len(pairs)))
                for k, v in pairs.items():
                    k_bytes = k.encode('cp1251', errors='replace') + b'\x00'
                    v_bytes = v.encode('cp1251', errors='replace') + b'\x00'

                    f.write(struct.pack('<I', len(k_bytes)))
                    f.write(k_bytes)
                    f.write(struct.pack('<I', len(v_bytes)))
                    f.write(v_bytes)
        else:
            f.write(struct.pack('<I', len(sections)))
            for sec in sections:
                sec_name = sec.get("SectionName", "")
                pairs = sec.get("Pairs", {})
                
                s_bytes = sec_name.encode('ascii', errors='ignore') + b'\x00'
                f.write(struct.pack('<I', len(s_bytes)))
                f.write(s_bytes)

                f.write(struct.pack('<I', len(pairs)))
                for k, v in pairs.items():
                    k_bytes = k.encode('cp1251', errors='replace') + b'\x00'
                    v_bytes = v.encode('cp1251', errors='replace') + b'\x00'

                    f.write(struct.pack('<I', len(k_bytes)))
                    f.write(k_bytes)
                    f.write(struct.pack('<I', len(v_bytes)))
                    f.write(v_bytes)
                    
    print(f"-> Запаковано (Интерфейс): {os.path.basename(target_path)}")