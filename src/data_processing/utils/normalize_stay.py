from __future__ import annotations

import re
from typing import Any

import pandas as pd


def normalize_stay_duration(duration: Any) -> str:
    """
    Chuẩn hóa chuỗi thời gian lưu trú về dạng thống nhất "X đêm".

    Logic giữ nguyên hoàn toàn:
    - Tìm số đêm bằng regex (\d+\s*đêm)
    - Nếu tìm thấy → trả về "{số} đêm"
    - Nếu không tìm thấy → trả về chuỗi gốc đã strip
    - Nếu input là None/NaN/không phải str → trả về chuỗi rỗng

    Args:
        duration: Giá trị thời gian lưu trú (str, None, NaN, hoặc bất kỳ kiểu nào).

    Returns:
        Chuỗi đã chuẩn hóa dạng "X đêm" hoặc giá trị gốc nếu không chứa "đêm".
        Trả về "" nếu input rỗng hoặc không hợp lệ.
    """
    # Xử lý an toàn: None, NaN, hoặc không phải str
    if pd.isna(duration) or duration is None:
        return ""

    duration_str = str(duration).strip()
    if not duration_str:
        return ""

    # Tìm số đêm (không phân biệt hoa thường, khoảng trắng linh hoạt)
    match = re.search(r"(\d+)\s*đêm", duration_str.lower())

    if match:
        nights = match.group(1)
        return f"{nights} đêm"

    # Không tìm thấy → trả về chuỗi gốc đã strip
    return duration_str