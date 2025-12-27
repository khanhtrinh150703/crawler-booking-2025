# src/data_processing/utils/language_detection.py

import re
from typing import Any

import pandas as pd
from langdetect import LangDetectException, detect

from config.config import (
    EMOJI_PATTERN,
    NON_VIETNAMESE_LANGS,
    VIETNAMESE_CHARS,
    VIETNAMESE_WORDS,
)
from .filters import contains_foreign_words


def is_vietnamese(text: Any, country: str | None = None) -> bool:
    """
    Kiểm tra văn bản có phải tiếng Việt không (phiên bản cải tiến - rule-based + langdetect).

    Logic được giữ nguyên 100% như phiên bản cũ:
    - Ưu tiên quốc gia Việt Nam + có ký tự tiếng Việt
    - Loại sớm nếu text quá ngắn hoặc có nhiều từ ngoại lai
    - Làm sạch emoji và ký tự không phải chữ cái/khoảng trắng/ký tự tiếng Việt
    - Kiểm tra số lượng từ phổ biến tiếng Việt
    - Kiểm tra tỷ lệ/số lượng ký tự có dấu tiếng Việt
    - Fallback sang langdetect với một số điều kiện bảo vệ tránh false positive

    Args:
        text: Văn bản cần kiểm tra (str, None, NaN... đều được xử lý an toàn).
        country: Quốc gia của reviewer (dùng để ưu tiên nếu từ Việt Nam).

    Returns:
        True nếu xác định là tiếng Việt, False nếu không.
    """
    # Xử lý an toàn None, NaN, chuỗi rỗng
    if pd.isna(text) or text is None:
        return False

    text_str = str(text).strip()
    if not text_str:
        return False

    # Kiểm tra quốc gia Việt Nam + có ít nhất 1 ký tự tiếng Việt → chắc chắn là VN
    is_vn_country = country and "vietnam" in str(country).lower()
    if is_vn_country and len(text_str) >= 5:
        if any(c.lower() in VIETNAMESE_CHARS.lower() for c in text_str):
            return True

    # Text quá ngắn (<15 ký tự) → không đủ cơ sở để xác định → False
    if len(text_str) < 15:
        return False

    # Nếu có tỷ lệ từ ngoại lai >20% → chắc chắn không phải tiếng Việt
    if contains_foreign_words(text_str):
        return False

    # Làm sạch: loại bỏ emoji + giữ lại chỉ chữ cái, khoảng trắng và ký tự tiếng Việt có dấu
    cleaned = EMOJI_PATTERN.sub("", text_str)
    cleaned = re.sub(
        r"[^\w\sàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóọỏõôồốộổỗơờớợởỡùúủũụưừứựửữỳýỷỹỵđ]",
        " ",
        cleaned,
    )

    if len(cleaned.strip()) < 15:
        return False

    # Đếm số từ phổ biến tiếng Việt xuất hiện
    text_lower = text_str.lower()
    vn_word_hits = sum(word in text_lower for word in VIETNAMESE_WORDS)
    if vn_word_hits >= 2:
        return True

    # Đếm và tính tỷ lệ ký tự có dấu tiếng Việt
    vn_char_count = sum(c.lower() in VIETNAMESE_CHARS.lower() for c in text_lower)
    text_no_space = text_str.replace(" ", "")

    if vn_char_count >= 6:
        return True
    if len(text_no_space) > 0 and vn_char_count / len(text_no_space) > 0.15:
        return True

    # Fallback sang langdetect với điều kiện bảo vệ
    try:
        lang = detect(text_str)
        # Nếu langdetect trả "vi" nhưng không có ký tự tiếng Việt nào → có thể nhầm → False
        if lang == "vi" and vn_char_count == 0:
            return False
        # Nếu langdetect trả ngôn ngữ khác và ít ký tự tiếng Việt → tin tưởng → False
        if lang in NON_VIETNAMESE_LANGS and vn_char_count <= 5:
            return False
        # Các trường hợp còn lại: tin langdetect
        return lang == "vi"
    except LangDetectException:
        # Nếu langdetect lỗi → fallback về rule ký tự: có >=6 ký tự tiếng Việt → True
        return vn_char_count >= 6