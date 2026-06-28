import os
import shutil

def safe_backup(file_path):
    if not os.path.exists(file_path):
        return file_path
    bak_path = file_path + ".bak"
    if not os.path.exists(bak_path):
        shutil.copy2(file_path, bak_path)
        print(f"-> Создан бэкап оригинала: {os.path.basename(bak_path)}")
    return bak_path

def extract_smart_text(block):
    chunks = block.split(b'\x00')
    for chunk in chunks:
        try:
            text = chunk.decode('cp1251').strip()
            if text and any(c.isalnum() for c in text) and "яя" not in text:
                return text
        except:
            pass
    return ""

def inject_smart_text(block, new_text):
    chunks = block.split(b'\x00')
    target_idx = 0
    found = False
    current_pos = 0
    
    for chunk in chunks:
        try:
            text = chunk.decode('cp1251').strip()
            if text and any(c.isalnum() for c in text) and "яя" not in text:
                target_idx = current_pos
                found = True
                break
        except:
            pass
        current_pos += len(chunk) + 1
        
    if not found:
        target_idx = 0
        
    new_bytes = new_text.encode('cp1251', errors='replace')
    max_len = len(block) - target_idx - 1
    if len(new_bytes) > max_len:
        new_bytes = new_bytes[:max_len]
        
    for i in range(target_idx, len(block)):
        block[i] = 0
        
    block[target_idx : target_idx + len(new_bytes)] = new_bytes
    return block