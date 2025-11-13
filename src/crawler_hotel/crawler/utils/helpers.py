# utils/helpers.py
import os
import random
import time
import threading
import logging
import os
from datetime import datetime
from config.config  import ERROR_ROOT_DIR
from config.settings import LOGS_DIR

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

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(LOGS_DIR, "crawler.log"), encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

def delay(min_sec=1.5, max_sec=3.5, stop_event=None):
    if stop_event and stop_event.is_set():
        return
    delay_time = random.uniform(min_sec, max_sec)
    print(f"Delay {delay_time:.1f}s...")
    time.sleep(delay_time)

def show_menu():
    print("\n" + "="*80)
    print(" " * 20 + "BOOKING.COM CRAWLER - MENU")
    print("="*80)
    print("  [1] Chế độ 1: Mỗi TỈNH = 1 PROCESS")
    print("  [2] Chế độ 2: Mỗi TỈNH = NHIỀU WORKER (chia URL)")
    print("  [0] Thoát")
    print("="*80)
    while True:
        choice = input("\nChọn chế độ (0-2): ").strip()
        if choice in ['0', '1', '2']:
            return choice
        print("Vui lòng chọn 0, 1 hoặc 2!")

def setup_auto_stop(max_runtime_minutes, stop_event):
    if max_runtime_minutes:
        def auto_stop():
            time.sleep(max_runtime_minutes * 60)
            logging.info(f"Auto-stop after {max_runtime_minutes} minutes.")
            stop_event.set()
        threading.Thread(target=auto_stop, daemon=True).start()

def setup_manual_stop(stop_event):
    def wait_enter():
        print("\n" + "!"*60)
        print("     NHẤN ENTER ĐỂ DỪNG TOÀN BỘ")
        print("!"*60)
        input()
        stop_event.set()
        logging.info("ENTER pressed. Stopping...")
    threading.Thread(target=wait_enter, daemon=True).start()