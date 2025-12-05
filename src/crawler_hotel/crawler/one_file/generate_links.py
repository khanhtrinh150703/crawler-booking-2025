import os
import re
import pandas as pd
from datetime import datetime

# ================================
# ĐƯỜNG DẪN - GIỮ NGUYÊN CỦA BẠN
# ================================

HOTEL_LINKS_DIR = r"D:\private\crawler-booking-2025\src\crawler_province\hotel_links"
SUCCESS_JSON_DIR = r"D:\private\crawler-booking-2025\src\crawler_hotel\data_final"
ERROR_JSON_DIR = r"D:\private\crawler-booking-2025\src\crawler_hotel\crawler\output_2025\errors_detected_20251117_1427"
TIMEOUT_ERROR_DIR = r"D:\private\crawler-booking-2025\src\crawler_hotel\crawler\output_error_link"

OUTPUT_DIR = r"D:\private\crawler-booking-2025\src\crawler_hotel\crawler\province_crawler_again"
os.makedirs(OUTPUT_DIR, exist_ok=True)

ALL_CRAWLER_AGAIN_FILE = os.path.join(OUTPUT_DIR, "ALL_CRAWLER_AGAIN.txt")
EXCEL_FILE = os.path.join(OUTPUT_DIR, f"CRAWLER_AGAIN_FINAL_{datetime.now():%Y%m%d_%H%M}.xlsx")

# ================================
# HÀM CHUYỂN ĐỔI
# ================================

def url_to_json_name(url):
    try:
        path = url.strip().split('/hotel/vn/')[-1]
        path = re.sub(r'\.html.*$', '', path)
        return f"{path.replace('-', '_')}.json"
    except:
        return None

def json_to_url(json_file):
    name = json_file[:-5] if json_file.endswith(".json") else json_file
    return f"https://www.booking.com/hotel/vn/{name.replace('_', '-')}.html"

# ================================
# LOAD TẤT CẢ LINK TIMEOUT VĨNH VIỄN
# ================================

def load_timeout_permanent():
    s = set()
    if not os.path.exists(TIMEOUT_ERROR_DIR):
        return s
    for root, _, files in os.walk(TIMEOUT_ERROR_DIR):
        for file in files:
            if file.lower() == "link.txt":
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        for line in f:
                            url = line.strip()
                            if url.startswith("http"):
                                s.add(url)
                except:
                    pass
    print(f"[INFO] Đã đánh dấu {len(s)} link timeout vĩnh viễn (sẽ loại khỏi crawl lại)")
    return s

# ================================
# CHẠY CHÍNH
# ================================

def main():
    timeout_permanent = load_timeout_permanent()
    excel_data = []
    crawl_again_urls = set()

    print("Bắt đầu quét toàn bộ tỉnh...\n")

    for province in sorted(os.listdir(HOTEL_LINKS_DIR)):
        province_path = os.path.join(HOTEL_LINKS_DIR, province)
        if not os.path.isdir(province_path):
            continue

        txt_file = os.path.join(province_path, f"{province}_hotel_links.txt")
        if not os.path.exists(txt_file):
            continue

        with open(txt_file, 'r', encoding='utf-8') as f:
            all_urls = [u.strip() for u in f if u.strip().startswith("http")]

        # Success & Error JSONs
        success_dir = os.path.join(SUCCESS_JSON_DIR, province)
        success_jsons = {f for f in os.listdir(success_dir) if f.endswith(".json")} if os.path.exists(success_dir) else set()

        error_dir = os.path.join(ERROR_JSON_DIR, province)
        error_jsons = {f for f in os.listdir(error_dir) if f.endswith(".json")} if os.path.exists(error_dir) else set()

        province_display = province.replace("-", " ").replace("_", " ").title()

        # === 1. XỬ LÝ TẤT CẢ ERROR JSON TRƯỚC ===
        for json_file in error_jsons:
            url = json_to_url(json_file)
            if url in timeout_permanent:
                excel_data.append([province_display, url, "Timeout Permanent", "Time out retry -> maybe no review"])
            else:
                excel_data.append([province_display, url, "Error", "Có JSON lỗi → cần crawl lại"])
                crawl_again_urls.add(url)

        # === 2. XỬ LÝ MISSING (chỉ những link chưa có success) ===
        for url in all_urls:
            json_name = url_to_json_name(url)
            if json_name in success_jsons:
                continue  # bỏ qua success

            # Nếu đã là Error thì đã xử lý ở trên → bỏ qua để tránh trùng
            if json_name in error_jsons:
                continue

            # Còn lại là Missing thật sự
            if url in timeout_permanent:
                excel_data.append([province_display, url, "Timeout Permanent", "Time out retry -> maybe no review"])
            else:
                excel_data.append([province_display, url, "Missing", "Chưa có dữ liệu"])
                crawl_again_urls.add(url)

        print(f"✓ {province_display}")

    # === GHI FILE CRAWL LẠI ===
    if crawl_again_urls:
        sorted_urls = sorted(crawl_again_urls)
        with open(ALL_CRAWLER_AGAIN_FILE, 'w', encoding='utf-8') as f:
            for url in sorted_urls:
                f.write(url + "\n")
        print(f"\n→ ALL_CRAWLER_AGAIN.txt: {len(sorted_urls)} link cần crawl lại")

    # === XUẤT EXCEL – ĐẢM BẢO CÓ ĐỦ TIMEOUT ===
    df = pd.DataFrame(excel_data, columns=["Province", "URL", "Type", "Note"])

    # Sắp xếp: theo tỉnh → Error trước → Missing → Timeout cuối
    type_order = {"Timeout Permanent": 0 , "Error": 1, "Missing": 2}
    df["order"] = df["Type"].map(type_order)
    df = df.sort_values(["Province", "order", "URL"]).drop("order", axis=1)

    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Need Crawl Again', index=False)
        ws = writer.sheets['Need Crawl Again']
        ws.column_dimensions['A'].width = 22
        ws.column_dimensions['B'].width = 95
        ws.column_dimensions['C'].width = 18
        ws.column_dimensions['D'].width = 55

    # Thống kê chính xác
    stat = df['Type'].value_counts()
    total_in_excel = len(df)
    print(f"\nHOÀN TẤT 100%!")
    print(f"   • Error             : {stat.get('Error', 0)}")
    print(f"   • Missing           : {stat.get('Missing', 0)}")
    print(f"   • Timeout Permanent : {stat.get('Timeout Permanent', 0)}")
    print(f"   • Tổng trong Excel  : {total_in_excel} link (đã có đủ 2 timeout)")
    print(f"   → Cần crawl lại     : {len(crawl_again_urls)} link (không có timeout)")
    print(f"   → Excel             : {os.path.basename(EXCEL_FILE)}")

if __name__ == "__main__":
    main()