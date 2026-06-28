# --- START OF FILE module_hex.py ---
import os

def decode_to_hex(input_files, output_file):
    print(f"Начинаю умное AI-декодирование {len(input_files)} файлов...")
    try:
        with open(output_file, 'w', encoding='utf-8') as out_f:
            for path in input_files:
                file_name = os.path.basename(path)
                print(f"Обрабатывается: {file_name}")
                
                out_f.write(f"=== FILE: {file_name} ===\n")
                
                try:
                    with open(path, 'rb') as in_f:
                        offset = 0
                        while True:
                            # Читаем блоками по 64 байта для максимальной компактности
                            chunk = in_f.read(64)
                            if not chunk:
                                break
                            
                            # Используем repr(), который сожмет текст и покажет байты как \x00
                            # [1:] убирает букву 'b' в начале b'...' для чистоты
                            chunk_repr = repr(chunk)[1:] 
                            
                            out_f.write(f"[{offset:04X}] {chunk_repr}\n")
                            offset += len(chunk)
                            
                except Exception as e:
                    out_f.write(f"[ОШИБКА ЧТЕНИЯ ФАЙЛА: {e}]\n")
                    print(f"Ошибка при чтении {file_name}: {e}")
                
                out_f.write("\n")
                
        print(f"-> Готово! AI-дамп сохранен: {os.path.basename(output_file)}")
        
    except Exception as e:
        print(f"Произошла ошибка при сохранении: {e}")