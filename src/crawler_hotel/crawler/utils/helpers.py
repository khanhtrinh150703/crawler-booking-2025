# utils/helpers.py
import os
from datetime import datetime
from config import ERROR_ROOT_DIR

def is_valid_range_folder(name):
    return '-' in name and name.replace('-', '').isdigit()

def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M")

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M")

def get_main_error_dir():
    timestamp = get_timestamp()
    error_dir = f"{ERROR_ROOT_DIR}_{timestamp}"
    ensure_dir(error_dir)
    return error_dir

def is_valid_range_folder(name):
    return '-' in name and name.replace('-', '').isdigit()