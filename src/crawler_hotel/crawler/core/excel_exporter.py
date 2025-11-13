# core/excel_exporter.py
import os
import pandas as pd
from error.check_json import process_json_file
from config import ROOT_DIR, EXCEL_DIR, EXCEL_NAME
from utils.helpers import ensure_dir

# core/excel_exporter.py

def collect_excel_data(path=ROOT_DIR, prefix="", data=None):
    if data is None:
        data = []
    for item in sorted(os.listdir(path)):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            new_prefix = f"{prefix}{item}/" if prefix else f"{item}/"
            collect_excel_data(item_path, new_prefix, data)
        elif item.endswith(".json"):
            has_error, reason, review_count, hotel_name, file_name, total_rating = process_json_file(item_path)
            rel_path = f"{prefix}{file_name}"
            status = "LỖI" if has_error else "HỢP LỆ"
            data.append({
                "File Path": rel_path,
                "Tên File": file_name,
                "Tên Khách Sạn": hotel_name,
                "Tổng Reviews Cào Được": review_count,
                "Total Rating": total_rating if total_rating is not None else "",  # ← CỘT MỚI
                "Trạng Thái": status,
                "Lỗi (nếu có)": reason or "",
            })
    return data


def export_to_excel():
    ensure_dir(EXCEL_DIR)
    print("\nĐang thu thập dữ liệu để xuất Excel...")
    data = collect_excel_data()
    if not data:
        print("Không có dữ liệu để xuất Excel.")
        return

    df = pd.DataFrame(data)
    excel_path = os.path.join(EXCEL_DIR, EXCEL_NAME)

    try:
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Hotels Report', index=False)
            ws = writer.sheets['Hotels Report']
            for i, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                ws.column_dimensions[chr(65 + i)].width = min(max_len, 50)
        print(f"Xuất Excel thành công: {excel_path}")
        print(f"   → Tổng cộng: {len(data)} khách sạn")
    except ImportError:
        print("Cảnh báo: Thiếu 'pandas' hoặc 'openpyxl'. Cài: pip install pandas openpyxl")
    except Exception as e:
        print(f"Lỗi xuất Excel: {e}")