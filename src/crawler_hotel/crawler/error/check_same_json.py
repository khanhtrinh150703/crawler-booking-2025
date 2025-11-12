import os
import json
import difflib
from pathlib import Path
from datetime import datetime

# === CẤU HÌNH ===
MAX_DIFF_LINES = 15  # Số dòng diff hiển thị trên terminal
OUTPUT_DIR = "json_compare_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === TÔ MÀU ===
class bcolors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'

def color(text, code):
    return f"{code}{text}{bcolors.ENDC}" if os.name != 'nt' else text

# === ĐỌC JSON ===
def load_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(color(f"[LỖI JSON] {filepath}\n    → {e}", bcolors.RED))
        return None
    except Exception as e:
        print(color(f"[LỖI] {filepath} → {e}", bcolors.RED))
        return None

# === SO SÁNH JSON ===
def compare_json_content(json1, json2, file1, file2):
    if json1 == json2:
        return True, "GIỐNG NHAU", []

    str1 = json.dumps(json1, ensure_ascii=False, indent=2, sort_keys=True)
    str2 = json.dumps(json2, ensure_ascii=False, indent=2, sort_keys=True)

    diff = list(difflib.unified_diff(
        str1.splitlines(keepends=True),
        str2.splitlines(keepends=True),
        fromfile=os.path.basename(file1),
        tofile=os.path.basename(file2),
        n=3
    ))
    return False, "KHÁC NHAU", diff

# === HIỂN THỊ DIFF AN TOÀN ===
def show_safe_diff(diff_lines, file1, file2):
    total = len(diff_lines)
    if total == 0:
        return

    print(f"   → {color('KHÁC NHAU', bcolors.RED)} ({total} dòng thay đổi)")

    # Hiển thị đầu
    head = diff_lines[:MAX_DIFF_LINES]
    for line in head:
        line = line.rstrip()
        if line.startswith('---') or line.startswith('+++'):
            print(color(f"   {line}", bcolors.YELLOW))
        elif line.startswith('-'):
            print(color(f"   {line}", bcolors.RED))
        elif line.startswith('+'):
            print(color(f"   {line}", bcolors.GREEN))
        else:
            print(f"   {line}")

    # Nếu quá dài → hiện dấu ...
    if total > MAX_DIFF_LINES:
        print(color(f"   ... (ẩn {total - MAX_DIFF_LINES} dòng) ...", bcolors.YELLOW))

    # Hỏi xem có muốn xem hết không
    try:
        choice = input(color("\n   [?] Xem toàn bộ diff? (y/N): ", bcolors.BLUE)).strip().lower()
        if choice == 'y':
            for line in diff_lines:
                line = line.rstrip()
                if line.startswith('-'): print(color(line, bcolors.RED))
                elif line.startswith('+'): print(color(line, bcolors.GREEN))
                else: print(line)
    except KeyboardInterrupt:
        print(color("\n   Bỏ qua.", bcolors.YELLOW))

    # === XUẤT RA FILE ===
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    diff_filename = f"diff_{Path(file1).stem}_{timestamp}.diff"
    diff_path = Path(OUTPUT_DIR) / diff_filename

    with open(diff_path, 'w', encoding='utf-8') as f:
        f.writelines(diff_lines)

    print(color(f"   Đã lưu diff đầy đủ: {diff_path}", bcolors.GREEN))

# === SO SÁNH THƯ MỤC ===
def compare_folders(folder1, folder2):
    path1 = Path(folder1)
    path2 = Path(folder2)

    if not path1.is_dir():
        print(color(f"[LỖI] Thư mục 1 không tồn tại: {folder1}", bcolors.RED))
        return
    if not path2.is_dir():
        print(color(f"[LỖI] Thư mục 2 không tồn tại: {folder2}", bcolors.RED))
        return

    json_files1 = {f.name: f for f in path1.glob("*.json")}
    json_files2 = {f.name: f for f in path2.glob("*.json")}
    common = set(json_files1.keys()) & set(json_files2.keys())

    print(f"\nTìm thấy {len(json_files1)} file trong thư mục 1")
    print(f"Tìm thấy {len(json_files2)} file trong thư mục 2")
    print(f"File chung: {len(common)}\n")
    print("="*80)

    if not common:
        print("Không có file chung để so sánh!")
        return

    for filename in sorted(common):
        f1 = json_files1[filename]
        f2 = json_files2[filename]

        print(f"So sánh: {filename}")

        data1 = load_json_file(f1)
        data2 = load_json_file(f2)
        if data1 is None or data2 is None:
            print("   → Bỏ qua do lỗi đọc file.\n")
            continue

        same, msg, diff = compare_json_content(data1, data2, str(f1), str(f2))

        if same:
            print(color(f"   → {msg}\n", bcolors.GREEN))
        else:
            show_safe_diff(diff, str(f1), str(f2))
            print()

    # File thừa/thiếu
    only1 = set(json_files1.keys()) - common
    only2 = set(json_files2.keys()) - common

    if only1:
        print(color("File chỉ có trong thư mục 1:", bcolors.RED))
        for f in sorted(only1): print(f"   + {f}")
        print()

    if only2:
        print(color("File chỉ có trong thư mục 2:", bcolors.GREEN))
        for f in sorted(only2): print(f"   - {f}")
        print()

    print("="*80)
    print(color("HOÀN TẤT! Kết quả được lưu trong thư mục:", bcolors.BLUE))
    print(color(f"    {Path(OUTPUT_DIR).resolve()}", bcolors.YELLOW))

# === CHẠY ===
if __name__ == "__main__":
    print(color("SO SÁNH JSON AN TOÀN - KHÔNG BỊ TRÀN TERMINAL", bcolors.BLUE))
    print("-"*60)

    folder1 = r"D:\private\crawler-booking-2025\src\crawler_hotel\data_test\0-50\binh-phuoc"
    folder2 = r"D:\private\crawler-booking-2025\src\crawler_hotel\data\0-50\binh-phuoc"

    if folder1 and folder2:
        compare_folders(folder1, folder2)
    else:
        print(color("Vui lòng nhập 2 thư mục!", bcolors.RED))