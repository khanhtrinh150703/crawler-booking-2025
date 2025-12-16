# export/export_data.py
import pandas as pd
import json
import os
from pathlib import Path
from typing import Dict, Any


def export_final_dataset(
    df: pd.DataFrame,
    output_folder: str | Path = "outputs",
    filename: str = "booking_reviews_vietnamese_final.csv"
) -> Path:
    """
    Xuất DataFrame đã xử lý sạch ra file CSV (utf-8-sig để Excel mở đẹp).
    """
    output_path = Path(output_folder) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    # print(f"\nĐã xuất dữ liệu cuối cùng:")
    # print(f"   File CSV: {output_path}")
    # print(f"   Số bản ghi: {len(df):,} đánh giá")
    # print(f"   Số cột: {len(df.columns)} cột")

    return output_path


def export_metadata_mapping(
    room_type_mapping: Dict[str, int],
    stay_duration_mapping: Dict[str, int],
    group_type_mapping: Dict[str, int],
    output_folder: str | Path = "outputs/charts",
    filename: str = "metadata_mapping.json"
) -> Path:
    """
    Lưu toàn bộ bảng ánh xạ (encoding) ra file JSON duy nhất.
    """
    output_path = Path(output_folder) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mapping = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "description": "Bảng ánh xạ metadata từ chuỗi → ID số (dùng cho modeling)",
        "room_type_mapping": room_type_mapping,
        "group_type_mapping": group_type_mapping,
        "stay_duration_mapping": stay_duration_mapping,
        "total_room_types": len(room_type_mapping),
        "total_group_types": len(group_type_mapping),
        "total_durations": len(stay_duration_mapping)
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=4)

    # print(f"\nĐã lưu bảng ánh xạ metadata:")
    # print(f"   File JSON: {output_path}")
    # print(f"   • {len(room_type_mapping):,} loại phòng")
    # print(f"   • {len(group_type_mapping):,} loại nhóm")
    # print(f"   • {len(stay_duration_mapping):,} thời gian lưu trú")

    return output_path