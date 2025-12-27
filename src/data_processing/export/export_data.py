# export/export_data.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pandas as pd


def export_final_dataset(
    df: pd.DataFrame,
    output_folder: str | Path = "outputs",
    filename: str = "booking_reviews_vietnamese_final.csv",
) -> Path:
    """
    Xuất DataFrame đã xử lý sạch sẽ ra file CSV.

    Sử dụng encoding='utf-8-sig' để Excel mở file không bị lỗi font tiếng Việt.
    Tự động tạo thư mục nếu chưa tồn tại.

    Args:
        df: DataFrame chứa dữ liệu đánh giá cuối cùng.
        output_folder: Thư mục lưu file (mặc định "outputs").
        filename: Tên file CSV đầu ra.

    Returns:
        Đường dẫn đầy đủ đến file CSV vừa xuất.
    """
    output_path = Path(output_folder) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    # Các dòng print bị comment để tránh in thừa khi chạy pipeline tự động.
    # Nếu cần thông báo, có thể bỏ comment hoặc dùng logger thay thế.

    return output_path


def export_metadata_mapping(
    room_type_mapping: Dict[str, int],
    stay_duration_mapping: Dict[str, int],
    group_type_mapping: Dict[str, int],
    output_folder: str | Path = "outputs/charts",
    filename: str = "metadata_mapping.json",
) -> Path:
    """
    Lưu toàn bộ bảng ánh xạ (mapping) từ chuỗi gốc → ID số vào một file JSON.

    Mục đích:
        - Tra cứu ngược lại (ID → tên gốc)
        - Giải thích kết quả model
        - Lưu lịch sử encoding để tái sử dụng

    Args:
        room_type_mapping: dict {"Deluxe Double Room": 0, ...}
        stay_duration_mapping: dict {"2 nights": 0, ...}
        group_type_mapping: dict {"Couple": 0, ...}
        output_folder: Thư mục lưu file (mặc định "outputs/charts").
        filename: Tên file JSON đầu ra.

    Returns:
        Đường dẫn đầy đủ đến file JSON vừa lưu.
    """
    output_path = Path(output_folder) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mapping_data = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "description": "Bảng ánh xạ metadata từ chuỗi → ID số (dùng cho modeling)",
        "room_type_mapping": room_type_mapping,
        "group_type_mapping": group_type_mapping,
        "stay_duration_mapping": stay_duration_mapping,
        "total_room_types": len(room_type_mapping),
        "total_group_types": len(group_type_mapping),
        "total_durations": len(stay_duration_mapping),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mapping_data, f, ensure_ascii=False, indent=4)

    return output_path