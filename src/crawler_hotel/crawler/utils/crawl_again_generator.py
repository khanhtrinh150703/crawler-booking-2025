# utils/crawl_again_generator.py
import os
import re
import pandas as pd
from datetime import datetime
from config.config import (
    HOTEL_LINKS_DIR,
    SUCCESS_JSON_DIR,
    TIMEOUT_ERROR_DIR_ROOT,
    CRAWLER_AGAIN_ROOT_DIR,
)
from utils.helpers import ensure_dir


def url_to_json_name(url: str) -> str | None:
    try:
        path = url.strip().split('/hotel/vn/')[-1]
        path = re.sub(r'\.html.*$', '', path)
        return f"{path.replace('-', '_')}.json"
    except Exception:
        return None


def json_to_url(json_file: str) -> str:
    name = json_file[:-5] if json_file.endswith(".json") else json_file
    return f"https://www.booking.com/hotel/vn/{name.replace('_', '-')}.html"


def load_timeout_permanent() -> set[str]:
    """Đọc danh sách link bị timeout vĩnh viễn từ các file link.txt trong TIMEOUT_ERROR_DIR_ROOT"""
    s = set()
    if not os.path.exists(TIMEOUT_ERROR_DIR_ROOT):
        return s
    for root, _, files in os.walk(TIMEOUT_ERROR_DIR_ROOT):
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
    return s


def generate_crawl_again_final(main_error_dir: str):
    if not os.path.exists(main_error_dir):
        print(f"[WARNING] Không tìm thấy thư mục lỗi: {main_error_dir}")
        return

    # Xóa thư mục cũ
    if os.path.exists(CRAWLER_AGAIN_ROOT_DIR):
        import shutil
        shutil.rmtree(CRAWLER_AGAIN_ROOT_DIR)
        print(f"Đã xóa thư mục cũ: {CRAWLER_AGAIN_ROOT_DIR}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    summary_dir = os.path.join(CRAWLER_AGAIN_ROOT_DIR, f"_SUMMARY_{timestamp}")
    ensure_dir(summary_dir)

    all_txt_file = os.path.join(summary_dir, "ALL_CRAWLER_AGAIN.txt")
    excel_file = os.path.join(summary_dir, f"CRAWLER_AGAIN_REPORT_{timestamp}.xlsx")

    # Tải danh sách timeout permanent (chỉ dùng để lọc missing)
    timeout_permanent = load_timeout_permanent()

    province_dict = {}
    all_need_crawl = []
    excel_rows = []

    print("\nBắt đầu tạo danh sách crawl lại (ưu tiên Error JSON > Timeout Permanent)...\n")

    for province in sorted(os.listdir(HOTEL_LINKS_DIR)):
        province_path = os.path.join(HOTEL_LINKS_DIR, province)
        if not os.path.isdir(province_path):
            continue

        txt_file = os.path.join(province_path, f"{province}_hotel_links.txt")
        if not os.path.exists(txt_file):
            continue

        with open(txt_file, 'r', encoding='utf-8') as f:
            all_urls = [u.strip() for u in f if u.strip().startswith("http")]

        success_dir = os.path.join(SUCCESS_JSON_DIR, province)
        success_jsons = {f for f in os.listdir(success_dir) if f.endswith(".json")} if os.path.exists(success_dir) else set()

        error_dir = os.path.join(main_error_dir, province)
        error_jsons = {f for f in os.listdir(error_dir) if f.endswith(".json")} if os.path.exists(error_dir) else set()

        need_crawl = []
        province_display = province.replace("-", " ").replace("_", " ").title()

        # 1. Ưu tiên cao nhất: Có JSON lỗi → BẮT BUỘC crawl lại (bỏ qua timeout permanent)
        for json_file in error_jsons:
            url = json_to_url(json_file)
            need_crawl.append(url)
            all_need_crawl.append(url)
            excel_rows.append([
                province_display,
                url,
                "Error",
                "Có file JSON lỗi → ưu tiên crawl lại (bỏ qua timeout permanent)"
            ])

        # 2. Missing: chỉ thêm nếu KHÔNG nằm trong timeout_permanent
        for url in all_urls:
            json_name = url_to_json_name(url)
            if not json_name:
                continue
            if json_name in success_jsons:
                continue  # Đã thành công
            if json_name in error_jsons:
                continue  # Đã được thêm ở trên

            # Chỉ ở đây mới kiểm tra timeout_permanent
            if url in timeout_permanent:
                excel_rows.append([province_display, url, "Timeout Permanent", "Missing + nằm trong danh sách timeout → bỏ qua"])
                continue

            # An toàn để thêm vào crawl lại
            need_crawl.append(url)
            all_need_crawl.append(url)
            excel_rows.append([province_display, url, "Missing", "Chưa có dữ liệu → sẽ crawl lại"])

        if need_crawl:
            province_dict[province] = need_crawl
            print(f"{province_display:35} → {len(need_crawl):,} link cần crawl lại")

    # ================== GHI KẾT QUẢ ==================
    total_links = 0
    for province, urls in province_dict.items():
        prov_dir = os.path.join(CRAWLER_AGAIN_ROOT_DIR, province)
        ensure_dir(prov_dir)
        out_file = os.path.join(prov_dir, f"{province}_hotel_links.txt")
        with open(out_file, 'w', encoding='utf-8') as f:
            for url in sorted(urls):
                f.write(url + "\n")
        total_links += len(urls)

    with open(all_txt_file, 'w', encoding='utf-8') as f:
        for url in sorted(all_need_crawl):
            f.write(url + "\n")

    df = pd.DataFrame(excel_rows, columns=["Province", "URL", "Type", "Note"])
    order = {"Error": 0, "Missing": 1, "Timeout Permanent": 2}
    df["sort"] = df["Type"].map(order)
    df = df.sort_values(["Province", "sort", "URL"]).drop("sort", axis=1)

    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Crawl Again Report', index=False)
        ws = writer.sheets['Crawl Again Report']
        for col, w in zip("ABCD", [22, 95, 20, 70]):
            ws.column_dimensions[col].width = w

    stat = df['Type'].value_counts()

    print("\n" + "="*100)
    print("HOÀN TẤT! ĐÃ TẠO DANH SÁCH CRAWL LẠI THEO ĐÚNG ƯU TIÊN")
    print("→ Error JSON có mặt → bắt buộc crawl lại (bỏ qua timeout permanent)")
    print("→ Missing + nằm trong timeout permanent → bỏ qua")
    print("="*100)
    print(f"Thư mục output       : {CRAWLER_AGAIN_ROOT_DIR}")
    print(f"Tổng tỉnh có link    : {len(province_dict)}")
    print(f"TỔNG LINK CẦN CRAWL  : {total_links:,}")
    print(f"File tổng            : {all_txt_file}")
    print(f"Báo cáo Excel        : {excel_file}")
    print("\nChi tiết theo loại:")
    print(f"   • Error JSON       : {stat.get('Error', 0):,} (ưu tiên cao nhất)")
    print(f"   • Missing          : {stat.get('Missing', 0):,}")
    print(f"   • Timeout Permanent: {stat.get('Timeout Permanent', 0):,} (bị loại)")
    print(f"   → TỔNG CẦN CRAWL   : {total_links:,} link")
    print("="*100)


def run_crawl_again_generator(main_error_dir: str):
    generate_crawl_again_final(main_error_dir)