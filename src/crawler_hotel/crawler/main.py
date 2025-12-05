# main.py
import os
import time
from multiprocessing import Manager, freeze_support

from config.settings import (
    BASE_INPUT_DIR_MODE1, BASE_INPUT_DIR_MODE2,
    OUTPUT_DIR_MODE1, OUTPUT_DIR_MODE2,
    MAX_WORKERS, MAX_RUNTIME_MINUTES, LOGS_DIR
)
from modes.mode1 import run_mode1
from modes.mode2 import run_mode2
from utils.helpers import setup_auto_stop, setup_manual_stop, show_menu

def main():
    choice = show_menu()
    if choice == '0':
        print("Thoát chương trình.")
        return

    # Chọn cấu hình theo mode
    if choice == '1':
        BASE_INPUT_DIR = BASE_INPUT_DIR_MODE1
        OUTPUT_DIR = OUTPUT_DIR_MODE1
        mode_name = "Range Province (Mode 1)"
        mode_func = run_mode1
    else:  # choice == '2'
        BASE_INPUT_DIR = BASE_INPUT_DIR_MODE2
        OUTPUT_DIR = OUTPUT_DIR_MODE2
        mode_name = "One Province (Mode 2)"
        mode_func = run_mode2

    # Tìm các thư mục range (chỉ lấy thư mục có tên dạng số hoặc số-số)
    range_dirs = sorted(
        [d for d in os.listdir(BASE_INPUT_DIR)
         if os.path.isdir(os.path.join(BASE_INPUT_DIR, d)) and d.replace('-', '').isdigit()],
        key=lambda x: int(x.split('-')[0])
    )

    if not range_dirs:
        print(f"Không tìm thấy thư mục range trong: {BASE_INPUT_DIR}")
        return

    print(f"\nDuyệt {len(range_dirs)} range trong MODE {choice} ({mode_name}):")
    for r in range_dirs:
        print(f"   • {r}")
    print(f"Workers: {MAX_WORKERS} | Dừng bằng phím ENTER")
    print("=" * 80 + "\n")

    # Quản lý dừng chương trình
    manager = Manager()
    stop_event = manager.Event()
    setup_auto_stop(MAX_RUNTIME_MINUTES, stop_event)
    setup_manual_stop(stop_event)

    # Tạo thư mục output chính cho mode
    mode_output_root = os.path.join(OUTPUT_DIR, f"mode{choice}")
    os.makedirs(mode_output_root, exist_ok=True)

    for range_name in range_dirs:
        if stop_event.is_set():
            print("Đã nhận tín hiệu dừng. Thoát vòng lặp...")
            break

        input_dir = os.path.join(BASE_INPUT_DIR, range_name)
        range_output_dir = os.path.join(mode_output_root, range_name)
        os.makedirs(range_output_dir, exist_ok=True)

        print(f"\n{'-' * 60}")
        print(f" BẮT ĐẦU RANGE: {range_name} | MODE {choice}")
        print(f"   → Input : {input_dir}")
        print(f"   → Output: {range_output_dir}")
        print(f"{'-' * 60}\n")

        # Gọi hàm mode tương ứng
        mode_func(input_dir, range_output_dir, MAX_WORKERS, MAX_RUNTIME_MINUTES, stop_event)

        print(f"\nHOÀN THÀNH RANGE: {range_name}\n")
        print("=" * 80)

    # Hoàn thành
    log_path = os.path.join(LOGS_DIR, "crawler.log")
    print("\n" + "=" * 70)
    print("          HOÀN THÀNH TẤT CẢ!")
    print(f"          Dữ liệu: {os.path.abspath(mode_output_root)}")
    print(f"          Log: {os.path.abspath(log_path)}")
    print("=" * 70)
    print("          Thoát trong 5 giây...")
    time.sleep(5)


if __name__ == "__main__":
    freeze_support()
    main()