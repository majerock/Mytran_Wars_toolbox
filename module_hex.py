import os

def decode_to_hex(input_files, output_file):
    print(f"Начинаю HEX-декодирование {len(input_files)} файлов...")
    try:
        with open(output_file, 'w', encoding='utf-8') as out_f:
            for path in input_files:
                file_name = os.path.basename(path)
                print(f"Обрабатывается: {file_name}")
                
                out_f.write(f"*{file_name}*\nhex:\n")
                
                try:
                    with open(path, 'rb') as in_f:
                        while True:
                            # Читаем блоками по 16 байт
                            chunk = in_f.read(16)
                            if not chunk:
                                break
                            
                            hex_line = chunk.hex(' ').upper()
                            out_f.write(hex_line + "\n")
                            
                except Exception as e:
                    out_f.write(f"[ОШИБКА ЧТЕНИЯ ФАЙЛА: {e}]\n")
                    print(f"Ошибка при чтении {file_name}: {e}")
                
                # Пустая строка между файлами
                out_f.write("\n")
                
        print(f"-> Готово! HEX-дамп сохранен: {os.path.basename(output_file)}")
        
    except Exception as e:
        print(f"Произошла ошибка при сохранении: {e}")