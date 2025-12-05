import os
from pathlib import Path

# ================= CHỈ CẦN SỬA 3 DÒNG NÀY =================
folder_A = r"D:\private\crawler-booking-2025\src\crawler_province\links_hotel_temp"      # ← Thư mục thứ nhất
folder_B = r"D:\private\crawler-booking-2025\src\crawler_province\hotel_links_final"    # ← Thư mục thứ hai
output   = r"D:\private\crawler-booking-2025\src\crawler_province\hotel_links_city_UNIQUE" # ← Thư mục kết quả (sẽ tạo mới)
# =========================================================

def normalize(link):
    return link.strip().lower()

# Tự động lấy danh sách tất cả thư mục tỉnh từ cả 2 folder
provinces_A = {p.name: p for p in Path(folder_A).iterdir() if p.is_dir()}
provinces_B = {p.name: p for p in Path(folder_B).iterdir() if p.is_dir()}

all_provinces = set(provinces_A.keys()) | set(provinces_B.keys())
print(f"Đã phát hiện {len(all_provinces)} tỉnh/thành phố")

os.makedirs(output, exist_ok=True)
total_unique = 0

for province in sorted(all_provinces):
    dir_A = provinces_A.get(province)
    dir_B = provinces_B.get(province)
    
    file_A = dir_A / f"{province}_hotel_links.txt" if dir_A else None
    file_B = dir_B / f"{province}_hotel_links.txt" if dir_B else None
    
    links = set()
    
    for file_path in (file_A, file_B):
        if file_path and file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        link = normalize(line)
                        if link.startswith('http'):
                            links.add(link)
            except Exception as e:
                print(f"  Lỗi đọc {file_path.name}: {e}")
    
    # Tạo thư mục tỉnh trong output và ghi file mới
    out_dir = Path(output) / province
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{province}_hotel_links.txt"
    
    with open(out_file, 'w', encoding='utf-8') as f:
        for link in sorted(links):
            f.write(link + '\n')
    
    total_unique += len(links)
    print(f"  {province:25} → {len(links):5} link duy nhất")

print("\nHOÀN TẤT!")
print(f"Tổng cộng: {total_unique:,} link không trùng lặp")
print(f"Thư mục kết quả: {output}")