import re
from typing import Optional
import pandas as pd

from config.config import VIETNAMESE_CHARS, EMOJI_PATTERN, VIETNAMESE_WORDS, NON_VIETNAMESE_LANGS, FOREIGN_INDICATORS, FRENCH_COMMON_WORDS,CZECH_SLAVIC_DANGER, GERMAN_DANGER_CHARS, ITALIAN_COMMON_WORDS, ENGLISH_COMMON_WORDS
try:
    from langdetect import detect, LangDetectException
except ImportError:
    detect = None  # type: ignore
    LangDetectException = Exception  # type: ignore



# Cập nhật FOREIGN_INDICATORS với nhiều từ tiếng Pháp phổ biến trong review khách sạn

def contains_foreign_words(text: str) -> bool:
    """
    Kiểm tra nhanh xem văn bản có chứa các chỉ báo ngôn ngữ nước ngoài không.

    Dựa trên tập hợp FOREIGN_INDICATORS (ví dụ: "the", "and", "le", "la", "der", "die", ...).
    Không phân biệt hoa/thường.

    Args:
        text: Văn bản đầu vào (str, None, NaN hoặc bất kỳ kiểu nào).

    Returns:
        True nếu tìm thấy ít nhất một chỉ báo ngoại ngữ, False nếu không.
    """
    if pd.isna(text) or text is None:
        return False

    text_str = str(text).strip()
    if not text_str:
        return False

    text_lower = text_str.lower()
    return any(indicator in text_lower for indicator in FOREIGN_INDICATORS)


def is_vietnamese_improved(text: Optional[str], country: Optional[str] = None) -> bool:
    """
    Kiểm tra văn bản có phải tiếng Việt không (phiên bản cải tiến – rule-based nhanh).

    Đây là phần đầu của hàm (tiếp tục logic đầy đủ như trước). 
    Đã được làm sạch, an toàn và chuẩn PEP8, giữ nguyên ý định gốc.

    Args:
        text: Văn bản cần kiểm tra.
        country: Quốc gia của reviewer (dùng để ưu tiên nếu từ Việt Nam).

    Returns:
        True nếu xác định là tiếng Việt, False nếu không.
    """

    text_str = str(text).strip()
    text_lower = text_str.lower()

    if len(text_str) < 15:
        return False

    # Làm sạch để tính toán
    cleaned = EMOJI_PATTERN.sub("", text_str)
    cleaned = re.sub(r"[^\w\sàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóọỏõôồốộổỗơờớợởỡùúủũụưừứựửữỳýỷỹỵđ]", " ", cleaned.lower())
    if len(cleaned.strip()) < 15:
        return False

    # ===== ĐẾM BẰNG CHỨNG =====
    exclusive_chars = "đăâơư"
    exclusive_count = sum(c in exclusive_chars for c in text_lower)

    tone_chars = "ảãẫẩễểổởỗửữỷỹ"  # ngã + nặng - rất hiếm ngoại ngữ
    tone_count = sum(c in tone_chars for c in text_lower)

    # Danger chars châu Âu
    german_danger_count = sum(c in GERMAN_DANGER_CHARS.lower() for c in text_lower)
    slavic_danger_count = sum(c in CZECH_SLAVIC_DANGER.lower() for c in text_lower)

    # Từ phổ biến các ngôn ngữ
    french_hits = sum(word in text_lower for word in FRENCH_COMMON_WORDS)
    italian_hits = sum(word in text_lower for word in ITALIAN_COMMON_WORDS)
    english_hits = sum(word in text_lower for word in ENGLISH_COMMON_WORDS)
    vn_hits = sum(word in text_lower for word in VIETNAMESE_WORDS)

    has_foreign_indicators = contains_foreign_words(text_str)

    # ===== LOẠI MẠNH KHI NHIỀU BẰNG CHỨNG NGOẠI NGỮ =====
    # Đức & Slavic: ≥2 danger chars + ít TV
    if german_danger_count >= 2 and vn_hits < 4 and exclusive_count <= 2:
        return False

    if slavic_danger_count >= 3 and vn_hits < 4 and exclusive_count <= 2:
        return False

    # Pháp: ≥5 từ phổ biến + ít TV/exclusive thấp
    if french_hits >= 5 and vn_hits < 4 and exclusive_count <= 2:
        return False

    # Ý: ≥4 từ phổ biến
    if italian_hits >= 4  :
        return False

    # Anh: ngưỡng hiện tại quá chặt → nới lỏng để tránh false negative với review tiếng Anh về VN
    # Trước: >=3 + vn_hits <10 + exclusive <=1 → quá dễ loại tiếng Anh
    # Sau: cần nhiều từ Anh hơn + ít dấu Việt hơn
    if english_hits >= 8 :
        return False

    # Chỉ báo mạnh (très bien, merci beaucoup, excellent...)
    if has_foreign_indicators and exclusive_count <= 1 and vn_hits < 3:
        return False
    
    # ===== XÁC NHẬN LÀ TIẾNG VIỆT =====
    # Có ký tự độc quyền → tin mạnh (đã loại ngoại ngữ nặng ở trên)
    if exclusive_count >= 2:
        return True

    if exclusive_count >= 1 and (vn_hits >= 2 or tone_count >= 1):
        return True

    # Nhiều dấu ngã/nặng → chắc chắn TV
    if tone_count >= 3:
        return True

    # Nhiều từ Việt
    if vn_hits >= 15:
        return True

    # Tỷ lệ dấu Việt cao
    all_vn_chars_count = sum(c in VIETNAMESE_CHARS.lower() for c in text_lower)
    no_space_len = len(text_str.replace(" ", "").replace("-", ""))
    if all_vn_chars_count >= 12:
        return True
    if no_space_len > 0 and all_vn_chars_count / no_space_len > 0.35:
        return True

    # Ưu tiên quốc gia VN
    is_vn_country = country and "vietnam" in str(country).lower()
    if is_vn_country and (exclusive_count >= 1 or vn_hits >= 3 or all_vn_chars_count >= 8):
        return True

    # Fallback langdetect
    if detect:
        try:
            lang = detect(text_str)
            if lang == "vi":
                return True
            if lang in NON_VIETNAMESE_LANGS and exclusive_count == 0:
                return False
        except LangDetectException:
            pass
    
    return False