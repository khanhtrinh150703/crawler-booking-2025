# src/data_processing/utils/metadata_encoding.py

from __future__ import annotations

import re
from typing import Dict, Tuple

import pandas as pd
from sklearn.preprocessing import LabelEncoder


def encode_metadata_columns(
    df: pd.DataFrame,
) -> Tuple[Dict[str, Dict[str, int]], pd.DataFrame]:
    """
    Encode các cột metadata categorical thành ID số để dùng cho modeling.

    Các cột được xử lý:
    - room_type      → room_type_id (LabelEncoder)
    - group_type     → group_type_id (LabelEncoder)
    - stay_duration  → stay_duration_id (custom mapping dựa trên số đêm)

    Logic giữ nguyên hoàn toàn như phiên bản cũ:
    - Dùng LabelEncoder cho room_type và group_type (fillna "Unknown")
    - Với stay_duration: trích xuất số đêm từ chuỗi có chứa "đêm"
    - Nếu không trích xuất được → gán ID theo thứ tự xuất hiện (tăng dần)
    - Các giá trị có số đêm hợp lệ sẽ được ưu tiên sắp xếp theo số đêm

    Args:
        df: DataFrame chứa các cột 'room_type', 'group_type', 'stay_duration'

    Returns:
        Tuple gồm:
        - encodings: dict {"room_type": {str → int}, "group_type": {...}, "stay_duration": {...}}
        - df_encoded: DataFrame gốc + 3 cột ID mới (room_type_id, group_type_id, stay_duration_id)
    """
    df = df.copy()
    encodings: Dict[str, Dict[str, int]] = {}

    # ============================= room_type =============================
    le_room = LabelEncoder()
    df["room_type_id"] = le_room.fit_transform(df["room_type"].fillna("Unknown"))
    encodings["room_type"] = {
        str(label): int(code) for label, code in zip(le_room.classes_, le_room.transform(le_room.classes_))
    }

    # ============================= group_type =============================
    le_group = LabelEncoder()
    df["group_type_id"] = le_group.fit_transform(df["group_type"].fillna("Unknown"))
    encodings["group_type"] = {
        str(label): int(code) for label, code in zip(le_group.classes_, le_group.transform(le_group.classes_))
    }

    # ============================= stay_duration =============================
    def extract_nights(text: str | None) -> int:
        """Trích xuất số đêm từ chuỗi (ví dụ: '2 đêm' → 2, 'Đã lưu trú: 5 đêm' → 5)."""
        if pd.isna(text):
            return -1
        match = re.search(r"(\d+)\s*đêm", str(text).lower())
        return int(match.group(1)) if match else -1

    df["stay_duration_nights"] = df["stay_duration"].apply(extract_nights)

    # Lấy danh sách unique và sắp xếp theo số đêm (các giá trị không parse được sẽ ở cuối)
    unique_pairs = (
        df[["stay_duration", "stay_duration_nights"]]
        .drop_duplicates()
        .sort_values(by="stay_duration_nights", ascending=True)
    )

    # Tạo mapping: ưu tiên theo số đêm, các giá trị không có số đêm sẽ được gán ID tăng dần
    stay_mapping: Dict[str, int] = {}
    custom_id = 0
    for _, row in unique_pairs.iterrows():
        nights = row["stay_duration_nights"]
        if nights >= 0:
            stay_mapping[row["stay_duration"]] = nights
        else:
            stay_mapping[row["stay_duration"]] = len(stay_mapping) + custom_id
            custom_id += 1

    df["stay_duration_id"] = df["stay_duration"].map(stay_mapping)
    encodings["stay_duration"] = stay_mapping

    return encodings, df