import os
from PIL import Image

def convert_scr(in_path, out_path, to_png=True):
    expected_size = 480 * 272 * 4
    if to_png:
        with open(in_path, 'rb') as f: data = f.read()
        if len(data) < expected_size: data += b'\x00' * (expected_size - len(data))
        elif len(data) > expected_size: data = data[:expected_size]
        Image.frombytes('RGBA', (480, 272), data).save(out_path)
    else:
        data = Image.open(in_path).convert('RGBA').resize((480, 272)).tobytes()
        with open(out_path, 'wb') as f: f.write(data)
    print(f"-> Сохранен: {os.path.basename(out_path)}")