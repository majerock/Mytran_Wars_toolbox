import struct
import os

def unpack_ppk(file_path, output_dir):
    with open(file_path, 'rb') as f:
        magic = f.read(4)
        if magic != b'PPAK':
            print(f"Ошибка: {os.path.basename(file_path)} не является архивом PPAK!")
            return
        
        total_size, file_count = struct.unpack('<II', f.read(8))
        f.seek(16)
        
        archive_name = f.read(32).decode('ascii', errors='ignore').strip('\x00')
        
        offsets = []
        for _ in range(file_count):
            offsets.append(struct.unpack('<I', f.read(4))[0])
            
        abs_offsets = [0x30 + off for off in offsets]
        abs_offsets.append(total_size)
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Создаем манифест (список оригинальных файлов)
        manifest_path = os.path.join(output_dir, '_filelist.txt')
        with open(manifest_path, 'w', encoding='utf-8') as f_man:
            for i in range(file_count):
                start = abs_offsets[i]
                end = abs_offsets[i+1]
                size = end - start
                
                f.seek(start)
                file_data = f.read(size)
                
                magic_sub = file_data[:4].decode('ascii', errors='ignore').strip()
                ext = magic_sub.lower() if magic_sub.isalnum() else 'dat'
                
                out_filename = f"{archive_name}_{i:03d}.{ext}"
                out_path = os.path.join(output_dir, out_filename)
                
                with open(out_path, 'wb') as out_f:
                    out_f.write(file_data)
                
                # Записываем имя файла в манифест
                f_man.write(out_filename + '\n')
                
        print(f"-> Извлечено: {archive_name} ({file_count} файлов + _filelist.txt)")

def pack_ppk(folder_path, output_ppk_path):
    manifest_path = os.path.join(folder_path, '_filelist.txt')
    files = []
    
    # 1. Пытаемся собрать строго по манифесту (идеально отсекает ВООБЩЕ ВЕСЬ мусор)
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f_man:
            files = [line.strip() for line in f_man if line.strip() and os.path.exists(os.path.join(folder_path, line.strip()))]
            if files:
                print(f"-> Сборка по манифесту (_filelist.txt)...")
    
    # 2. Если манифеста нет или он пуст - собираем всё подряд, но фильтруем расширения
    if not files:
        all_files = sorted([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
        # Черный список расширений (мусор, картинки, исходники)
        blacklist = ('.png', '.jpg', '.jpeg', '.txt', '.psd', '.xcf', '.bak', '.old', '.ini')
        files = [f for f in all_files if not f.lower().endswith(blacklist)]
        print(f"-> Сборка без манифеста (работает фильтр от мусора)...")
    
    if not files:
        print(f"Ошибка: Нет файлов для сборки в {folder_path}!")
        return
    
    first_file = files[0]
    archive_name = first_file.rsplit('_', 1)[0]
    file_count = len(files)
    
    base_size = 48 + file_count * 4
    first_file_abs = (base_size + 15) // 16 * 16
    
    offsets = []
    current_abs = first_file_abs
    file_datas = []
    
    for f_name in files:
        file_path = os.path.join(folder_path, f_name)
        with open(file_path, 'rb') as f_in:
            data = f_in.read()
        file_datas.append(data)
        
        rel_offset = current_abs - 48
        offsets.append(rel_offset)
        
        next_abs = current_abs + len(data)
        current_abs = (next_abs + 15) // 16 * 16
        
    total_size = current_abs
    
    header = bytearray()
    header.extend(b'PPAK')
    header.extend(struct.pack('<I', total_size))
    header.extend(struct.pack('<I', file_count))
    header.extend(b'\x00' * 4)
    
    name_bytes = archive_name.encode('ascii')[:32]
    name_bytes = name_bytes.ljust(32, b'\x00')
    header.extend(name_bytes)
    
    for off in offsets:
        header.extend(struct.pack('<I', off))
        
    header = header.ljust(first_file_abs, b'\x00')
    
    with open(output_ppk_path, 'wb') as f_out:
        f_out.write(header)
        for idx, data in enumerate(file_datas):
            f_out.write(data)
            pos = f_out.tell()
            pad_len = (16 - (pos % 16)) % 16
            f_out.write(b'\x00' * pad_len)
            
    final_size = os.path.getsize(output_ppk_path)
    with open(output_ppk_path, 'r+b') as f_out:
        f_out.seek(4)
        f_out.write(struct.pack('<I', final_size))
        
    print(f"-> Успешно собрано: {os.path.basename(output_ppk_path)} ({file_count} файлов)")