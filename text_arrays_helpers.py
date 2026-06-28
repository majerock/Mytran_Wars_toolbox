# --- START OF FILE text_arrays_helpers.py ---

def read_str_fixed(data, offset, max_len):
    raw = data[offset : offset + max_len]
    idx = raw.find(b'\x00')
    if idx != -1:
        raw = raw[:idx]
    return raw.decode('cp1251', errors='ignore').strip()

def write_str_fixed(data, offset, max_len, text):
    encoded = text.encode('cp1251', errors='ignore')
    if len(encoded) > max_len - 1:
        encoded = encoded[:max_len - 1]
    padded = encoded.ljust(max_len, b'\x00')
    data[offset : offset + max_len] = padded

def is_valid_text(b_chunk, encoding):
    if len(b_chunk) < 3: return False
    try:
        if b'\xff\xff' in b_chunk: return False
        text = b_chunk.decode(encoding).strip()
        if len(text) < 3: return False
        if sum(1 for c in text if c.isalnum()) < 3: return False
        if text[0].isalpha() and text[0].islower(): return False
        if "яя" in text or "ÿÿ" in text or "Î" in text: return False
        return True
    except:
        return False