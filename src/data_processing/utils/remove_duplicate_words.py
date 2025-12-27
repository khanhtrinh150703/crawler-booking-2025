# utils/remove_duplicate_words.py

from __future__ import annotations

import re
from typing import Any

import pandas as pd

def remove_consecutive_duplicates(text: Any) -> str:
    """
    Loại bỏ các từ trùng lặp liên tiếp trong văn bản (case-insensitive).

    Ví dụ:
        "sạch sẽ sẽ" → "sạch sẽ"
        "Khách sạn KHÁCH SẠN đẹp" → "Khách sạn đẹp"
        "rất rất rất tốt" → "rất tốt"
        "haha haha haha" → "haha"

    Args:
        text: Văn bản đầu vào (str, None, NaN hoặc bất kỳ kiểu nào).

    Returns:
        Văn bản đã loại bỏ từ lặp liên tiếp, trả về "" nếu input rỗng hoặc None.
    """
    if pd.isna(text) or text is None:
        return ""

    text_str = str(text).strip()
    if not text_str:
        return ""

    # Regex: \b(\w+)\b\s+\1\b → tìm từ lặp liền kề, không phân biệt hoa thường
    pattern = re.compile(r"\b(\w+)\b\s+\1\b", re.IGNORECASE)

    while True:
        new_text = pattern.sub(r"\1", text_str)
        if new_text == text_str:
            break
        text_str = new_text

    return text_str.strip()


def remove_consecutive_duplicates_in_column(
    df: pd.DataFrame,
    column: str,
    new_column: str | None = None,
) -> pd.DataFrame:
    """
    Áp dụng hàm remove_consecutive_duplicates cho một cột trong DataFrame.

    Tạo cột mới (hoặc ghi đè cột cũ) và in thống kê chi tiết về số dòng bị ảnh hưởng.

    Args:
        df: DataFrame đầu vào.
        column: Tên cột cần xử lý.
        new_column: Tên cột kết quả (nếu None thì ghi đè lên cột gốc).

    Returns:
        DataFrame đã được cập nhật với cột mới/chỉnh sửa.

    Raises:
        ValueError: Nếu cột đầu vào không tồn tại.
    """
    if column not in df.columns:
        raise ValueError(f"Cột '{column}' không tồn tại trong DataFrame.")

    if new_column is None:
        new_column = column

    print(f"Đang loại bỏ từ lặp liên tiếp trong cột '{column}' → '{new_column}'...")

    # Áp dụng xử lý
    df[new_column] = df[column].apply(remove_consecutive_duplicates)

    # Thống kê: số dòng có thay đổi (tức là có từ lặp bị loại bỏ)
    changed_rows = (df[column] != df[new_column]) & df[new_column].notna()
    changed_count = int(changed_rows.sum())

    # Kiểm tra xem sau xử lý còn trường hợp lặp nào không (dùng pattern đơn giản để phát hiện 2 từ liên tiếp giống nhau)
    # Pattern này tránh capture group → không gây warning pandas
    remaining_pattern = re.compile(r"\b(\w+)\b\s+\1\b", re.IGNORECASE)
    remaining_count = int(
        df[new_column]
        .apply(lambda x: bool(remaining_pattern.search(str(x))) if pd.notna(x) else False)
        .sum()
    )

    print(f"Hoàn tất: Đã xử lý {len(df):,} dòng.")
    if changed_count > 0:
        print(f"   → Đã xử lý {changed_count:,} dòng có từ lặp liên tiếp.")
    else:
        print("   → Không phát hiện trường hợp từ lặp liên tiếp nào.")

    if remaining_count > 0:
        print(f"   → Cảnh báo: Còn {remaining_count:,} dòng vẫn có khả năng lặp (có thể do lặp không liền kề hoặc phức tạp hơn).")
    else:
        print("   → Không còn trường hợp từ lặp liên tiếp nào.")

    return df