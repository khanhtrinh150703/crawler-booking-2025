import os
import shutil
from pathlib import Path

def get_range_folder(count):
    """Xác định thư mục theo khoảng 100"""
    if count <= 50:
        return "0-50"
    else:
        # Chia cho 100, lấy nguyên, nhân lại 100 + 1 → ra đầu mút
        lower = ((count - 1) // 100) * 100 + 1
        upper = lower + 99
        return f"{lower}-{upper}"

def group_by_link_range(input_root, output_root):
    input_path = Path(input_root)
    output_path = Path(output_root)
    output_path.mkdir(exist_ok=True)

    print("Bắt đầu gom nhóm theo khoảng link (0-50, 51-100, 101-200, ...)\n")

    processed = 0

    for province_dir in sorted(input_path.iterdir()):
        if not province_dir.is_dir():
            continue

        # Tìm file .txt đầu tiên trong thư mục tỉnh
        txt_files = list(province_dir.glob("*.txt"))
        if not txt_files:
            continue

        original_txt = txt_files[0]

        # Đọc và đếm link hợp lệ
        try:
            with open(original_txt, 'r', encoding='utf-8') as f:
                links = [line.strip() for line in f if line.strip() and line.startswith('http')]
        except Exception as e:
            print(f"[LỖI] Đọc {original_txt}: {e}")
            continue

        count = len(links)
        if count == 0:
            continue

        # Xác định thư mục theo khoảng
        range_folder_name = get_range_folder(count)
        group_folder = output_path / range_folder_name / province_dir.name
        group_folder.mkdir(parents=True, exist_ok=True)

        # Copy file vào
        dest_file = group_folder / "links.txt"
        shutil.copy2(original_txt, dest_file)

        print(f"{province_dir.name:15} → {count:4} link → {range_folder_name}/{province_dir.name}/links.txt")
        processed += 1

    print(f"\nHOÀN TẤT!")
    print(f"   Đã xử lý: {processed} tỉnh")
    print(f"   Kết quả: {output_path.resolve()}")

# ====================== CHỈ SỬA 1 DÒNG ======================
if __name__ == "__main__":
    INPUT_FOLDER = r"D:\private\crawler-booking-2025\src\crawler_province\hotel_links"
    OUTPUT_FOLDER = r"D:\private\crawler-booking-2025\src\crawler_province\hotel_group_by_range"

    group_by_link_range(INPUT_FOLDER, OUTPUT_FOLDER)