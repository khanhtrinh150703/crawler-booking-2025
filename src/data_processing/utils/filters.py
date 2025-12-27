# src/data_processing/utils/filters.py

import re
import pandas as pd
from config.config import EMOJI_PATTERN, FOREIGN_WORDS


def contains_emoji(text: str | None) -> bool:
    """
    Kiểm tra xem văn bản có chứa emoji, emoticon text (:D, :(, <3, ...) hoặc ký tự spam không.

    Sử dụng EMOJI_PATTERN (regex đã định nghĩa trước đó) để tìm kiếm.
    Xử lý an toàn với None, NaN (pandas), chuỗi rỗng hoặc các kiểu dữ liệu khác.

    Args:
        text: Văn bản đầu vào (str, None, NaN, hoặc bất kỳ kiểu nào).

    Returns:
        True nếu tìm thấy ít nhất một emoji/emoticon trong pattern, False nếu không.
    """
    if not text:
        return False
    return bool(EMOJI_PATTERN.search(text))


def contains_foreign_words(text: str | None) -> bool:
    """
    Kiểm tra xem văn bản có chứa tỷ lệ từ ngoại lai (tiếng Anh/Pháp/Tây Ban Nha/Đức/Ý...) lớn hơn 20% không.

    Dựa trên tập hợp FOREIGN_WORDS (các stopword phổ biến của các ngôn ngữ châu Âu).
    Thường dùng để phát hiện nhanh review từ khách quốc tế mà không cần thư viện detect language phức tạp.

    Args:
        text: Văn bản đầu vào (str, None, NaN, hoặc bất kỳ kiểu nào).

    Returns:
        True nếu:
            - Có ít nhất một từ nằm trong FOREIGN_WORDS
            - Và tỷ lệ từ ngoại lai > 20% tổng số từ
        False trong các trường hợp còn lại (bao gồm text rỗng, chỉ emoji, chỉ tiếng Việt...).
    """
    # Xử lý an toàn các trường hợp None, NaN, hoặc chuỗi rỗng
    if not text or not text.strip():
        return False

    # Tách từ: chỉ lấy các từ chữ cái/số (loại bỏ punctuation, emoji đã được clean trước đó)
    words = re.findall(r"\b\w+\b", text.lower())
    if not words:
        return False

    # Đếm số từ nằm trong FOREIGN_WORDS (set nên lookup O(1) rất nhanh)
    foreign_count = sum(word in FOREIGN_WORDS for word in words)
    
    # Điều kiện: có ít nhất 1 từ ngoại lai VÀ tỷ lệ > 20%
    return foreign_count > 0 and (foreign_count / len(words) > 0.2)

def check_repetitive(text: str) -> bool:
    """
    Kiểm tra xem văn bản có phải là spam lặp ký tự không (một ký tự chiếm >70% tổng độ dài).

    Ví dụ spam sẽ bị phát hiện:
        - "aaaaaAAAAaaaaaaa" → True (chữ 'a' lặp quá nhiều)
        - "hahahahahahahaha" → True
        - "111111111111"     → True
        - "Phở ngon!!!"     → False (dấu ! chỉ chiếm ít)

    Logic giữ nguyên 100%: chỉ trả về True nếu tồn tại ít nhất một ký tự xuất hiện
    với tần suất > 70% tổng độ dài chuỗi.

    Args:
        text: Văn bản đầu vào (str, None, NaN, hoặc bất kỳ kiểu nào).

    Returns:
        True nếu văn bản bị nghi ngờ spam do lặp ký tự quá mức, False nếu không.
    """
    # Xử lý an toàn: None, NaN, chuỗi rỗng hoặc quá ngắn
    if pd.isna(text) or text is None:
        return False

    text_str = str(text).strip()

    if len(text_str) < 5:
        return False

    # Đếm tần suất từng ký tự duy nhất và kiểm tra điều kiện >70%
    return any(text_str.count(char) > len(text_str) * 0.7 for char in set(text_str))