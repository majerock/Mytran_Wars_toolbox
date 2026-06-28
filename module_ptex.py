import os
import struct
from PIL import Image

def unswizzle_bytes(source, width_in_bytes, height):
    padded_width = (width_in_bytes + 15) // 16 * 16
    padded_height = (height + 7) // 8 * 8
    dest = bytearray(padded_width * padded_height)
    src_offset = 0
    for blocky in range(padded_height // 8):
        for blockx in range(padded_width // 16):
            for j in range(8):
                dest_offset = (blocky * 8 + j) * padded_width + blockx * 16
                if src_offset + 16 <= len(source) and dest_offset + 16 <= len(dest):
                    dest[dest_offset : dest_offset + 16] = source[src_offset : src_offset + 16]
                src_offset += 16
    unpadded_dest = bytearray(width_in_bytes * height)
    for y in range(height):
        unpadded_dest[y*width_in_bytes : (y+1)*width_in_bytes] = dest[y*padded_width : y*padded_width + width_in_bytes]
    return unpadded_dest

def swizzle_bytes(source, width_in_bytes, height):
    padded_width = (width_in_bytes + 15) // 16 * 16
    padded_height = (height + 7) // 8 * 8
    work_source = bytearray(padded_width * padded_height)
    for y in range(height):
        work_source[y*padded_width : y*padded_width + width_in_bytes] = source[y*width_in_bytes : (y+1)*width_in_bytes]
    dest = bytearray(padded_width * padded_height)
    dest_offset = 0
    for blocky in range(padded_height // 8):
        for blockx in range(padded_width // 16):
            for j in range(8):
                src_offset = (blocky * 8 + j) * padded_width + blockx * 16
                if src_offset + 16 <= len(work_source) and dest_offset + 16 <= len(dest):
                    dest[dest_offset : dest_offset + 16] = work_source[src_offset : src_offset + 16]
                dest_offset += 16
    return dest

def decode_16bpp(data, width, height, fmt):
    dest = bytearray(width * height * 4)
    for i in range(width * height):
        val = struct.unpack('<H', data[i*2:i*2+2])[0]
        if fmt == '4444': r, g, b, a = (val&0xF)*17, ((val>>4)&0xF)*17, ((val>>8)&0xF)*17, ((val>>12)&0xF)*17
        elif fmt == '5551': r, g, b, a = (val&0x1F)*8, ((val>>5)&0x1F)*8, ((val>>10)&0x1F)*8, 255 if (val&0x8000) else 0
        else: r, g, b, a = (val&0x1F)*8, ((val>>5)&0x3F)*4, ((val>>11)&0x1F)*8, 255
        dest[i*4 : i*4+4] = [r, g, b, a]
    return dest

def encode_16bpp(rgba, width, height, fmt):
    dest = bytearray(width * height * 2)
    for i in range(width * height):
        r, g, b, a = rgba[i]
        if fmt == '4444': val = (r//17) | ((g//17)<<4) | ((b//17)<<8) | ((a//17)<<12)
        elif fmt == '5551': val = (r//8) | ((g//8)<<5) | ((b//8)<<10) | ((1 if a>127 else 0)<<15)
        else: val = (r//8) | ((g//4)<<5) | ((b//8)<<11)
        struct.pack_into('<H', dest, i*2, val)
    return dest

def ptex_to_png(ptex_path, png_path, apply_swizzle=True):
    with open(ptex_path, 'rb') as f:
        header = f.read(128)
        width, height = struct.unpack('<II', header[0x28:0x30])
        pixel_chunk_base = struct.unpack('<I', header[0x30:0x34])[0]
        palette_chunk_base = struct.unpack('<I', header[0x38:0x3C])[0]
        palette_size = struct.unpack('<I', header[0x3C:0x40])[0]

        # Динамически вычисляем оффсеты для палитры и пикселей
        palette_offset = palette_chunk_base + 32 if palette_chunk_base > 0 else 144
        
        if pixel_chunk_base > 0:
            pixel_offset = pixel_chunk_base + 32
        else:
            pixel_offset = palette_offset + palette_size

        if palette_size > 0:
            bpp = 4 if palette_size <= 64 else 8
            
            f.seek(palette_offset)
            palette_data = f.read(palette_size)
            
            f.seek(pixel_offset)
            width_in_bytes = width // 2 if bpp == 4 else width
            pixel_data = f.read(width_in_bytes * height)
            
            if apply_swizzle:
                unswizzled = unswizzle_bytes(pixel_data, width_in_bytes, height)
            else:
                unswizzled = bytearray(pixel_data)
            
            if bpp == 4:
                expanded = bytearray(width * height)
                for i in range(width_in_bytes * height):
                    expanded[i*2] = unswizzled[i] & 0x0F
                    expanded[i*2+1] = (unswizzled[i] >> 4) & 0x0F
                unswizzled = expanded
                
            img = Image.new('P', (width, height))
            img.putdata(unswizzled)
            rgb_pal, alpha_ch = [], []
            for i in range(0, len(palette_data), 4):
                if i + 4 <= len(palette_data):
                    r, g, b, a = palette_data[i:i+4]
                    rgb_pal.extend([r, g, b])
                    alpha_ch.append(a)
            while len(rgb_pal) < 768:
                rgb_pal.extend([0, 0, 0])
                alpha_ch.append(0)
            img.putpalette(rgb_pal)
            rgba_img = img.convert('RGBA')
            final_pixels = [(r, g, b, alpha_ch[idx] if idx < len(alpha_ch) else 255) 
                            for (r, g, b, _), idx in zip(rgba_img.getdata(), unswizzled)]
            rgba_img.putdata(final_pixels)
            rgba_img.save(png_path)
            print(f"-> Успешно извлечено: {os.path.basename(png_path)}")
        else:
            f.seek(pixel_offset)
            expected_32 = width * height * 4
            bpp = 16 if expected_32 > (os.path.getsize(ptex_path) - pixel_offset) else 32
            if bpp == 16:
                pixel_data = f.read(width * height * 2)
                unswizzled = unswizzle_bytes(pixel_data, width * 2, height) if apply_swizzle else bytearray(pixel_data)
                for fmt in ['4444', '5551', '5650']:
                    Image.frombytes('RGBA', (width, height), bytes(decode_16bpp(unswizzled, width, height, fmt))).save(png_path.replace('.png', f'_{fmt}.png'))
                print(f"-> Успешно извлечено: {os.path.basename(png_path)}")
            else:
                pixel_data = f.read(width * height * 4)
                unswizzled = unswizzle_bytes(pixel_data, width * 4, height) if apply_swizzle else bytearray(pixel_data)
                Image.frombytes('RGBA', (width, height), bytes(unswizzled)).save(png_path)
                print(f"-> Успешно извлечено: {os.path.basename(png_path)}")

def png_to_ptex(png_path, original_ptex_path, output_ptex_path, apply_swizzle=True):
    with open(original_ptex_path, 'rb') as f:
        orig_data = f.read()
        
    header = orig_data[:128]
    width, height = struct.unpack('<II', header[0x28:0x30])
    pixel_chunk_base = struct.unpack('<I', header[0x30:0x34])[0]
    palette_chunk_base = struct.unpack('<I', header[0x38:0x3C])[0]
    palette_size = struct.unpack('<I', header[0x3C:0x40])[0]

    # Вычисляем оффсеты для паковщика
    palette_offset = palette_chunk_base + 32 if palette_chunk_base > 0 else 144
    
    if pixel_chunk_base > 0:
        pixel_offset = pixel_chunk_base + 32
    else:
        pixel_offset = palette_offset + palette_size

    img = Image.open(png_path).convert('RGBA')
    
    if palette_size > 0:
        bpp = 4 if palette_size <= 64 else 8
        original_palette = orig_data[palette_offset : palette_offset+palette_size]
            
        palette_lookup = {tuple(original_palette[i:i+4]): i//4 for i in range(0, len(original_palette), 4)}
        indexed_pixels = bytearray(width * height)
        for idx, pixel in enumerate(img.getdata()):
            if pixel in palette_lookup:
                indexed_pixels[idx] = palette_lookup[pixel]
            else:
                best_match, min_dist = 0, float('inf')
                for color_bytes, color_idx in palette_lookup.items():
                    dist = sum((px - cx)**2 for px, cx in zip(pixel, color_bytes))
                    if dist < min_dist: min_dist, best_match = dist, color_idx
                indexed_pixels[idx] = best_match
                
        if bpp == 4:
            compressed = bytearray(width // 2 * height)
            for i in range(len(compressed)):
                p0 = indexed_pixels[i*2] & 0x0F
                p1 = indexed_pixels[i*2+1] & 0x0F if (i*2+1) < len(indexed_pixels) else 0
                compressed[i] = (p1 << 4) | p0
            swizzled = swizzle_bytes(compressed, width // 2, height) if apply_swizzle else compressed
        else:
            swizzled = swizzle_bytes(indexed_pixels, width, height) if apply_swizzle else indexed_pixels
            
        with open(output_ptex_path, 'wb') as f_out:
            f_out.write(orig_data[:pixel_offset])
            width_in_bytes = width // 2 if bpp == 4 else width
            f_out.write(swizzled[:width_in_bytes * height])
            if len(orig_data) > pixel_offset + (width_in_bytes * height):
                f_out.write(orig_data[pixel_offset + (width_in_bytes * height):])
        print(f"-> Успешно запакован: {os.path.basename(output_ptex_path)}")
    else:
        fmt_type = None
        for fmt in ['4444', '5551', '5650']:
            if f'_{fmt}' in os.path.basename(png_path).lower():
                fmt_type = fmt
                break
                
        bpp = 16 if fmt_type else 32
        mipmap_data = bytearray()
        w, h = width, height
        temp_img = img.copy()
        current_size_written = 0
        original_pixel_size = len(orig_data) - pixel_offset
        
        while w >= 1 and h >= 1:
            level_pixels = list(temp_img.getdata())
            if bpp == 16:
                level_bytes = encode_16bpp(level_pixels, w, h, fmt_type)
                swizzled_level = swizzle_bytes(level_bytes, w * 2, h) if apply_swizzle else level_bytes
            else:
                level_bytes = bytearray()
                for r, g, b, a in level_pixels: level_bytes.extend([r, g, b, a])
                swizzled_level = swizzle_bytes(level_bytes, w * 4, h) if apply_swizzle else level_bytes
                
            mipmap_data.extend(swizzled_level)
            current_size_written += len(swizzled_level)
            
            if current_size_written >= original_pixel_size: break
            w, h = max(1, w // 2), max(1, h // 2)
            temp_img = temp_img.resize((w, h), Image.Resampling.LANCZOS)
            
        with open(output_ptex_path, 'wb') as f_out:
            f_out.write(orig_data[:pixel_offset])
            f_out.write(mipmap_data[:original_pixel_size])
            if len(orig_data) > pixel_offset + original_pixel_size:
                f_out.write(orig_data[pixel_offset + original_pixel_size:])
        print(f"-> Успешно запакован: {os.path.basename(output_ptex_path)}")