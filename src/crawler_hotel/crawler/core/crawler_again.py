# core/crawler_again.py
import os
import pandas as pd
from datetime import datetime
from config.paths import *
from utils.helpers import url_to_json_name, json_to_url

def load_timeout_permanent():
    s = set()
    if not os.path.exists(TIMEOUT_ERROR_DIR):
        print(f"[INFO] Không tìm thấy thư mục timeout: {TIMEOUT_ERROR_DIR}")
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
    print(f"[INFO] Đã đánh dấu {len(s)} link timeout vĩnh viễn")
    return s

def generate_crawler_again():
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

        # 1. Xử lý Error trước
        for json_file in error_jsons:
            url = json_to_url(json_file)
            if url in timeout_permanent:
                excel_data.append([province_display, url, "Timeout Permanent", "Time out retry -> maybe no review"])
            else:
                excel_data.append([province_display, url, "Error", "Có JSON lỗi → cần crawl lại"])
                crawl_again_urls.add(url)

        # 2. Xử lý Missing
        for url in all_urls:
            json_name = url_to_json_name(url)
            if json_name in success_jsons:
                continue
            if json_name in error_jsons:
                continue

            if url in timeout_permanent:
                excel_data.append([province_display, url, "Timeout Permanent", "Time out retry -> maybe no review"])
            else:
                excel_data.append([province_display, url, "Missing", "Chưa có dữ liệu"])
                crawl_again_urls.add(url)

        print(f"✓ {province_display}")

    # Ghi file crawl lại
    if crawl_again_urls:
        with open(ALL_CRAWLER_AGAIN_FILE, 'w', encoding='utf-8') as f:
            for url in sorted(crawl_again_urls):
                f.write(url + "\n")
        print(f"\n→ ALL_CRAWLER_AGAIN.txt: {len(crawl_again_urls)} link cần crawl lại")

    # Xuất Excel
    df = pd.DataFrame(excel_data, columns=["Province", "URL", "Type", "Note"])
    type_order = {"Error": 0, "Missing": 1, "Timeout Permanent": 2}
    df["order"] = df["Type"].map(type_order)
    df = df.sort_values(["Province", "order", "URL"]).drop("order", axis=1)

    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Need Crawl Again', index=False)
        ws = writer.sheets['Need Crawl Again']
        ws.column_dimensions['A'].width = 22
        ws.column_dimensions['B'].width = 95
        ws.column_dimensions['C'].width = 18
        ws.column_dimensions['D'].width = 55

    stat = df['Type'].value_counts()
    print(f"\nHOÀN TẤT 100%!")
    print(f"   • Error             : {stat.get('Error', 0):,}")
    print(f"   • Missing           : {stat.get('Missing', 0):,}")
    print(f"   • Timeout Permanent : {stat.get('Timeout Permanent', 0):,}")
    print(f"   → Cần crawl lại     : {len(crawl_again_urls):,} link")
    print(f"   → Excel             : {os.path.basename(EXCEL_FILE)}")
    print(f"   → File crawl        : ALL_CRAWLER_AGAIN.txt")
