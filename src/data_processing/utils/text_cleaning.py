# src/data_processing/utils/text_cleaning.py

from __future__ import annotations

import re
import unicodedata
from typing import Any, List

import pandas as pd

from config.config import EMOJI_PATTERN


def normalize_vietnamese_text(text: Any) -> str:
    """
    Chuẩn hóa văn bản tiếng Việt để dùng cho preprocessing, vectorization hoặc so sánh.

    Các bước thực hiện (giữ nguyên logic gốc):
    1. NFC Unicode normalization (đảm bảo dấu tiếng Việt đúng chuẩn tổ hợp)
    2. Loại bỏ emoji và emoticon text bằng EMOJI_PATTERN
    3. Chỉ giữ lại chữ cái, số, khoảng trắng, dấu câu cơ bản và toàn bộ ký tự tiếng Việt có dấu
    4. Chuyển về chữ thường (lowercase)
    5. Collapse nhiều khoảng trắng thành một và strip đầu/cuối
    6. Loại bỏ dấu gạch ngang ở đầu chuỗi nếu có (ví dụ: "- Phòng sạch" → "Phòng sạch")

    Args:
        text: Văn bản đầu vào (str, None, NaN hoặc bất kỳ kiểu nào).

    Returns:
        Chuỗi tiếng Việt đã chuẩn hóa. Trả về "" nếu input rỗng/None/NaN.
    """
    if pd.isna(text) or text is None:
        return ""

    text_str = str(text)

    # 1. NFC normalization
    text_str = unicodedata.normalize("NFC", text_str)

    # 2. Loại bỏ emoji
    text_str = EMOJI_PATTERN.sub("", text_str)

    # 3. Giữ lại chỉ ký tự mong muốn
    text_str = re.sub(
        r"[^\w\s\.\,\;\:\?\!àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóọỏõôồốộổỗơờớợởỡùúủũụưừứựửữỳýỷỹỵđ]",
        " ",
        text_str,
    )

    # 4. Lowercase
    text_str = text_str.lower()

    # 5. Collapse khoảng trắng
    text_str = re.sub(r"\s+", " ", text_str).strip()

    # 6. Loại bỏ dấu gạch ngang ở đầu
    text_str = re.sub(r"^\s*-\s*", "", text_str)

    return text_str


def create_combined_text(
    df: pd.DataFrame,
    cols: List[str] = ["rating", "positive_comment"],
) -> pd.DataFrame:
    """
    Ghép nội dung từ nhiều cột văn bản thành một cột duy nhất 'combined_text'.

    Logic giữ nguyên:
    - Fill NaN bằng chuỗi rỗng
    - Ghép theo thứ tự các cột trong list (cách nhau khoảng trắng)
    - Strip khoảng trắng thừa
    - Nếu kết quả rỗng → chuyển thành NaN (dễ xử lý sau này)

    Args:
        df: DataFrame đầu vào.
        cols: Danh sách các cột cần ghép (mặc định ["rating", "positive_comment"]).

    Returns:
        DataFrame mới có thêm cột 'combined_text' (các cột gốc vẫn giữ nguyên).
    """
    df = df.copy()

    # Kiểm tra các cột tồn tại (tránh lỗi khi thiếu cột)
    missing_cols = [col for col in cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Các cột không tồn tại trong DataFrame: {missing_cols}")

    # Ghép các cột, fill NaN bằng "" trước khi ghép
    df["combined_text"] = (
        df[cols]
        .fillna("")
        .agg(" ".join, axis=1)
        .str.strip()
    )

    # Nếu sau khi ghép vẫn rỗng → chuyển thành NaN
    df["combined_text"] = df["combined_text"].replace("", pd.NA)

    return df