import os
import struct
import glob
import module_ptex

def extract_font_metrics(data, font_folder):
    idx = 0
    font_count = 0
    while True:
        idx = data.find(b'FONT', idx)
        if idx == -1: break
        
        version = data[idx+8 : idx+12]
        if version == b'v100':
            font_count += 1
            font_block = data[idx : idx + 3608]
            log_name = os.path.join(font_folder, f"font_{font_count}_metrics.txt")
            with open(log_name, 'w', encoding='utf-8') as log_f:
                log_f.write(f"Шрифт №{font_count} в EBOOT (смещение 0x{idx:X})\n")
                log_f.write("ID  | Симв | Off_X | Off_Y | Width | Tex_X | Tex_Y | Advance | Height\n")
                log_f.write("-" * 75 + "\n")
                
                for char_id in range(256):
                    entry_offset = 24 + char_id * 14
                    if entry_offset + 14 <= len(font_block):
                        off_x, off_y, w, tex_x, tex_y, advance, h = struct.unpack('<hhhhhhh', font_block[entry_offset : entry_offset + 14])
                        char_repr = chr(char_id) if 32 <= char_id <= 126 else "N/A"
                        log_f.write(f"{char_id:03d} | '{char_repr:4s}' | {off_x:5d} | {off_y:5d} | {w:5d} | {tex_x:5d} | {tex_y:5d} | {advance:7d} | {h:6d}\n")
            print(f"-> Извлечены метрики: font_{font_count}_metrics.txt")
        idx += 4

def inject_font_metrics(data, font_folder):
    # Ищем все базовые файлы метрик, но ИСКЛЮЧАЕМ из списка _ru.txt, чтобы не было дублей
    base_txt_files = glob.glob(os.path.join(font_folder, "font_*_metrics.txt"))
    base_txt_files = [f for f in base_txt_files if not f.endswith("_ru.txt")]
    
    patched_count = 0
    for base_txt in base_txt_files:
        # Проверяем, существует ли модифицированная версия (_ru)
        ru_txt = base_txt.replace(".txt", "_ru.txt")
        txt_path = ru_txt if os.path.exists(ru_txt) else base_txt
        
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        try:
            offset_str = lines[0].split('0x')[1].split(')')[0]
            base_offset = int(offset_str, 16)
        except:
            print(f"Пропуск {os.path.basename(txt_path)}: не найдено смещение в первой строке.")
            continue
            
        local_patch_count = 0
        for line in lines:
            if '|' in line and not line.startswith('ID'):
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 9:
                    try:
                        char_id = int(parts[0])
                        off_x, off_y, w, tex_x, tex_y, advance, h = map(int, parts[2:9])
                        entry_offset = base_offset + 24 + char_id * 14
                        struct.pack_into('<hhhhhhh', data, entry_offset, off_x, off_y, w, tex_x, tex_y, advance, h)
                        local_patch_count += 1
                        patched_count += 1
                    except:
                        pass
        if local_patch_count > 0:
            print(f"-> Вшиты метрики из {os.path.basename(txt_path)} ({local_patch_count} символов).")
    return patched_count

def process_eboot_fonts(eboot_path, font_folder, mode="extract"):
    if not eboot_path or not os.path.exists(eboot_path):
        print("Ошибка: EBOOT файл не найден!")
        return
    if not font_folder:
        print("Ошибка: Не указана папка для шрифтов!")
        return

    with open(eboot_path, 'rb') as f: 
        data = bytearray(f.read())
        
    os.makedirs(font_folder, exist_ok=True)
        
    if mode == "extract":
        extract_font_metrics(data, font_folder)
        
    idx, found = 0, 0
    while True:
        idx = data.find(b'PTEX', idx)
        if idx == -1: break
        
        try:
            data_size = struct.unpack('<I', data[idx+4 : idx+8])[0]
            total_size = 8 + data_size
            name = data[idx+0x40 : idx+0x60].split(b'\x00')[0].decode('ascii', errors='ignore')
            
            if 'airstrip' in name.lower() or 'font' in name.lower():
                orig_ptex_data = data[idx : idx + total_size]
                
                if mode == "extract":
                    temp_ptex = os.path.join(font_folder, f"~temp_{name}.ptex")
                    out_png = os.path.join(font_folder, f"{name}.png")
                    
                    with open(temp_ptex, 'wb') as temp_f: 
                        temp_f.write(orig_ptex_data)
                        
                    module_ptex.ptex_to_png(temp_ptex, out_png, apply_swizzle=True)
                    os.remove(temp_ptex)
                    
                    found += 1
                    
                elif mode == "inject":
                    # Логика приоритета _ru.png над обычным .png
                    base_png = os.path.join(font_folder, f"{name}.png")
                    ru_png = os.path.join(font_folder, f"{name}_ru.png")
                    in_png = ru_png if os.path.exists(ru_png) else base_png
                    
                    temp_orig = os.path.join(font_folder, f"~orig_{name}.ptex")
                    temp_out = os.path.join(font_folder, f"~out_{name}.ptex")
                    
                    if os.path.exists(in_png):
                        print(f"-> Инжект текстуры: {os.path.basename(in_png)}")
                        with open(temp_orig, 'wb') as f_orig:
                            f_orig.write(orig_ptex_data)
                            
                        module_ptex.png_to_ptex(in_png, temp_orig, temp_out, apply_swizzle=True)
                        
                        with open(temp_out, 'rb') as f_new:
                            mod_data = f_new.read()
                            
                        if len(mod_data) < total_size: 
                            mod_data += b'\x00' * (total_size - len(mod_data))
                        elif len(mod_data) > total_size: 
                            mod_data = mod_data[:total_size]
                            
                        data[idx : idx + total_size] = mod_data
                        
                        os.remove(temp_orig)
                        os.remove(temp_out)
                        
                        found += 1
        except Exception as e: 
            pass
            
        idx += 4
        
    if mode == "inject":
        metrics_patched = inject_font_metrics(data, font_folder)
        if found > 0 or metrics_patched > 0:
            out_eboot = eboot_path.replace('.BIN', '_MODDED.BIN').replace('.bin', '_MODDED.bin')
            with open(out_eboot, 'wb') as f: 
                f.write(data)
            print(f"-> Готово! Сохранено как {os.path.basename(out_eboot)}")
    elif mode == "extract":
        print(f"-> Всего извлечено текстур шрифтов: {found}")