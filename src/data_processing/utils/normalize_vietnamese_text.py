from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd

from config.config import EMOJI_PATTERN


def normalize_vietnamese_text(text: Any) -> str:
    """
    Chuẩn hóa văn bản tiếng Việt để phù hợp cho preprocessing, vectorization hoặc so sánh.

    Các bước thực hiện (giữ nguyên logic gốc 100%):
    1. NFC Unicode normalization (rất quan trọng với tiếng Việt có dấu)
    2. Loại bỏ toàn bộ emoji/emoticon bằng EMOJI_PATTERN
    3. Chỉ giữ lại: chữ cái, số, khoảng trắng và dấu câu cơ bản + toàn bộ ký tự tiếng Việt có dấu
    4. Chuyển về chữ thường (lowercase)
    5. Collapse nhiều khoảng trắng thành một
    6. Loại bỏ dấu gạch ngang ở đầu chuỗi nếu có (ví dụ: "- Phòng sạch sẽ" → "Phòng sạch sẽ")

    Args:
        text: Văn bản đầu vào (str, None, NaN hoặc bất kỳ kiểu nào).

    Returns:
        Chuỗi tiếng Việt đã được chuẩn hóa sạch sẽ. Trả về "" nếu input rỗng hoặc None.
    """
    # Xử lý an toàn None, NaN, giá trị không hợp lệ
    if pd.isna(text) or text is None:
        return ""

    text_str = str(text)

    # Bước 1: NFC normalization – chuẩn hóa tổ hợp dấu tiếng Việt
    text_str = unicodedata.normalize("NFC", text_str)

    # Bước 2: Loại bỏ emoji và emoticon text
    text_str = EMOJI_PATTERN.sub("", text_str)

    # Bước 3: Chỉ giữ chữ cái/số/khoảng trắng/dấu câu cơ bản + ký tự tiếng Việt có dấu
    text_str = re.sub(
        r"[^\w\s\.\,\;\:\?\!àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóọỏõôồốộổỗơờớợởỡùúủũụưừứựửữỳýỷỹỵđ]",
        " ",
        text_str,
    )

    # Bước 4: Chuyển về chữ thường
    text_str = text_str.lower()

    # Bước 5: Collapse khoảng trắng thừa
    text_str = re.sub(r"\s+", " ", text_str).strip()

    # Bước 6: Loại bỏ dấu gạch ngang ở đầu (nếu có)
    text_str = re.sub(r"^\s*-\s*", "", text_str)

    return text_str