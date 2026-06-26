import os

def parse_metrics_file_safely(txt_path, row_height_fallback=18):
    metrics = {}
    header_lines = []
    if not os.path.exists(txt_path):
        return metrics, header_lines
        
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines[:3]: 
            header_lines.append(line)
        for line in lines[3:]:
            if '|' in line and not line.startswith('ID'):
                parts = line.split('|')
                if len(parts) >= 6: 
                    try:
                        cid = int(parts[0].strip())
                        vals = []
                        for p in parts[-7:]:
                            clean_p = ''.join(c for c in p if c.isdigit() or c == '-')
                            if clean_p: vals.append(int(clean_p))
                        
                        if len(vals) >= 5:
                            ox = vals[0]
                            oy = vals[1]
                            w = vals[2]
                            tx = vals[3]
                            ty = vals[4]
                            
                            if len(vals) >= 7:
                                adv = vals[5]
                                h = vals[6]
                            else:
                                adv = w
                                h = row_height_fallback
                                
                            metrics[cid] = {'ox': ox, 'oy': oy, 'w': w, 'tx': tx, 'ty': ty, 'adv': adv, 'h': h}
                    except Exception:
                        pass
    return metrics, header_lines