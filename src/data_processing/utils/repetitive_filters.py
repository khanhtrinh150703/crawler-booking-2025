# utils/repetitive_filters.py
# Phiên bản mới: Làm sạch từ lặp liên tiếp và ký tự lặp liên tiếp (không xóa row)

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

import pandas as pd


def clean_repetitive_chars(text: Any) -> str:
    """
    Giảm các ký tự lặp liên tiếp xuống còn đúng 1 ký tự.

    Ví dụ:
        "sạch sẽeeeeeeeee" → "sạch sẽe"
        "Tuyệttttt vời"    → "Tuyệt vời"
        "goooood"          → "god"

    Args:
        text: Văn bản đầu vào (có thể là str, None, NaN...).

    Returns:
        Chuỗi đã loại bỏ lặp ký tự, strip khoảng trắng thừa.
    """
    if pd.isna(text) or text is None:
        return ""

    text_str = str(text).strip()
    if not text_str:
        return ""

    # Thay bất kỳ ký tự nào lặp >=2 lần liên tiếp bằng chỉ 1 ký tự đó
    cleaned = re.sub(r"(.)\1{1,}", r"\1", text_str)
    return cleaned.strip()


def clean_repetitive_words(text: Any) -> str:
    """
    Loại bỏ các từ/cụm từ lặp lại liên tiếp, chỉ giữ lại 1 lần.

    Ví dụ:
        "rất tốt rất tốt rất tốt" → "rất tốt"
        "good good good"          → "good"
        "ok ok everything ok"     → "ok everything ok" (chỉ xử lý lặp liền kề)

    Không phân biệt hoa thường khi so sánh.

    Args:
        text: Văn bản đầu vào.

    Returns:
        Chuỗi đã loại bỏ từ lặp liên tiếp.
    """
    if pd.isna(text) or text is None:
        return ""

    text_str = str(text).strip()
    if not text_str:
        return ""

    # Tìm cụm từ lặp ít nhất 2 lần liên tiếp (tổng >=3 từ giống nhau)
    # Ví dụ: "rất tốt rất tốt rất tốt" → thay bằng "rất tốt"
    cleaned = re.sub(
        r"\b(\w+)\b(?:\s+\1\b)+",
        r"\1",
        text_str,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def clean_repetitive(text: Any) -> str:
    """
    Kết hợp làm sạch cả từ lặp và ký tự lặp.

    Thứ tự: word repeat → char repeat (như logic gốc).

    Args:
        text: Văn bản đầu vào.

    Returns:
        Văn bản đã được làm sạch hoàn toàn repetitive.
    """
    text = clean_repetitive_words(text)
    text = clean_repetitive_chars(text)
    return text


def count_repetitive_before(df: pd.DataFrame, columns_list: List[str]) -> int:
    """
    Đếm số row có chứa nội dung repetitive (từ lặp hoặc ký tự lặp quá mức) trước khi làm sạch.

    Args:
        df: DataFrame cần kiểm tra.
        columns_list: Danh sách các cột cần kiểm tra.

    Returns:
        Số row có ít nhất một cột bị repetitive.
    """

    def has_word_repeat(text: Any) -> bool:
        if pd.isna(text) or text is None:
            return False
        return bool(
            re.search(r"\b(\w+)\b(?:\s+\1\b)+", str(text), flags=re.IGNORECASE)
        )

    def has_char_repeat(text: Any) -> bool:
        if pd.isna(text) or text is None:
            return False
        # Lặp ký tự >=4 lần liên tiếp (ngưỡng hợp lý để phát hiện spam)
        return bool(re.search(r"(.)\1{3,}", str(text)))

    if not columns_list:
        return 0

    # Tạo mask tổng hợp từ tất cả các cột
    mask = pd.Series([False] * len(df), index=df.index)
    for col in columns_list:
        if col in df.columns:
            mask |= df[col].apply(has_word_repeat) | df[col].apply(has_char_repeat)

    return int(mask.sum())


def clean_repetitive_in_columns(
    df: pd.DataFrame,
    columns: str | List[str],
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Làm sạch repetitive (từ lặp + ký tự lặp) trong một hoặc nhiều cột của DataFrame.

    Không xóa bất kỳ row nào – chỉ sửa nội dung để giữ lại đúng 1 lần của từ/ký tự bị lặp.

    Args:
        df: DataFrame đầu vào.
        columns: Tên cột hoặc danh sách tên cột cần làm sạch.

    Returns:
        Tuple gồm:
        - df_clean: DataFrame đã được cập nhật nội dung
        - stats: Dictionary thống kê trước/sau làm sạch
    """
    df_clean = df.copy()
    total_rows = len(df_clean)

    # Chuẩn hóa thành list
    columns_list = [columns] if isinstance(columns, str) else columns

    # Kiểm tra cột tồn tại
    missing_cols = [col for col in columns_list if col not in df_clean.columns]
    if missing_cols:
        return df_clean, {
            "Số đánh giá được làm sạch repetitive": f"0 (thiếu cột: {', '.join(missing_cols)})",
            "Giữ lại sau làm sạch repetitive": f"{total_rows:,} (100%)",
        }

    if not columns_list:
        return df_clean, {
            "Số đánh giá được làm sạch repetitive": "0",
            "Giữ lại sau làm sạch repetitive": f"{total_rows:,} (100%)",
        }

    # Đếm số row bị ảnh hưởng trước khi clean
    before_count = count_repetitive_before(df_clean, columns_list)

    # Áp dụng làm sạch cho từng cột
    for col in columns_list:
        df_clean[col] = df_clean[col].apply(clean_repetitive)

    # Tạo thống kê
    stats = {
        "Số đánh giá được làm sạch repetitive": f"{before_count:,} ({before_count/total_rows:.2%})",
        "Giữ lại sau làm sạch repetitive": f"{total_rows:,} (100%)",
    }

    return df_clean, stats