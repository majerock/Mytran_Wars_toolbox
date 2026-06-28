import os
import glob
from text_story import extract_loc, pack_loc, extract_bin, pack_bin
from text_ui import extract_ui, pack_ui
from text_arrays import extract_data_array, pack_data_array

def process_file_to_json(filepath, out_path=None):
    if not out_path:
        out_path = filepath + ".json"
        
    name = os.path.basename(filepath).lower()
    
    if name.endswith(".loc"):
        extract_loc(filepath, out_path)
    elif name.startswith("mission_") and name.endswith(".bin"):
        extract_bin(filepath, out_path)
    elif name == "menu.bin":
        extract_ui(filepath, out_path)
    else:
        extract_data_array(filepath, out_path)

def pack_json_to_file(json_path, base_orig_path=None):
    if not base_orig_path:
        base_orig_path = json_path.replace(".json", "")
        
    name = os.path.basename(base_orig_path).lower()
    
    if name.endswith(".loc"):
        pack_loc(json_path, base_orig_path)
    elif name.startswith("mission_") and name.endswith(".bin"):
        pack_bin(json_path, base_orig_path)
    elif name == "menu.bin":
        pack_ui(json_path, base_orig_path)
    else:
        pack_data_array(json_path, base_orig_path, base_orig_path)