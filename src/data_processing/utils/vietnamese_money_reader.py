# utils/vietnamese_money_reader.py
import re
from typing import Union

# utils/remove_phone_numbers.py
import re

def is_vietnamese_phone_number(input_str: Union[str, int, float]) -> bool:
    """
    Kiểm tra xem chuỗi có phải là số điện thoại Việt Nam hợp lệ không.
    Hỗ trợ các định dạng phổ biến: 090xxxxxxx, 84xxxxxxxxx, +849xxxxxxx, có dấu cách/gạch ngang/chấm.
    """
    if input_str is None:
        return False

    # Chuẩn hóa: loại bỏ mọi ký tự không phải số, trừ dấu + ở đầu
    text = re.sub(r'[\s\.\-+()]', '', str(input_str).strip())

    # Nếu có + ở đầu thì bỏ nó đi để kiểm tra
    if text.startswith('+'):
        text = text[1:]

    if not text.isdigit():
        return False

    # Các đầu số hợp lệ của Việt Nam (mobile): 03,05,07,08,09
    valid_second_digits = '35789'

    if len(text) == 10 and text.startswith('0'):
        return text[1] in valid_second_digits

    elif len(text) == 11 and text.startswith('84'):
        return text[2] in valid_second_digits

    # Không chấp nhận các dạng khác như 12 số hoặc hotline đặc biệt (1800, 1900) để tránh nhầm với tiền
    return False

def remove_phone_numbers(text: str) -> str:
    """
    Xóa TẤT CẢ số điện thoại Việt Nam trong câu, giữ lại phần văn bản còn lại.
    Ví dụ:
    - "liên hệ 0912345678" → "liên hệ"
    - "zalo 0901234567" → "zalo" 
    - "0912345678" → "" (sau đó sẽ bị lọc ở bước empty)
    - "call 0123456789 nhé" → "call nhé"
    """
    if not text or not str(text).strip():
        return ""
    
    text = str(text).strip()
    
    # Pattern số điện thoại Việt Nam CHI TIẾT (xóa TẤT CẢ trong câu)
    phone_patterns = [
        r'\b\+?84[\s\-\.\)]?\(?0?\)?[\s\-\.\)]?([3|5|7|8|9])+[\s\-\.\)]?\d{3}[\s\-\.\)]?\d{4}\b',  # +84901234567, 090.123.4567
        r'\b0[\s\-\.]?(3|5|7|8|9)[\s\-\.]?\d{3}[\s\-\.]?\d{4}\b',                              # 090 123 4567
        r'\b0\d{9}\b',                                                                       # 0912345678 thuần
        r'\b84\d{9}\b',                                                                      # 84901234567
        r'\b\d{3}[\s\-\.]?\d{3}[\s\-\.]?\d{4}\b',                                            # 0901 234 567  
    ]
    
    cleaned = text
    for pattern in phone_patterns:
        # Thay SDT bằng khoảng trắng (giữ cấu trúc câu)
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
    
    # Làm sạch khoảng trắng thừa
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


def number_to_vietnamese(n: int) -> str:
    """Chuyển số nguyên thành chữ tiếng Việt (tối đa hàng trăm triệu)."""
    if n == 0:
        return "không"

    units = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    tens = ["", "mười", "hai mươi", "ba mươi", "bốn mươi", "năm mươi",
            "sáu mươi", "bảy mươi", "tám mươi", "chín mươi"]

    def _convert_group(hundred: int, ten: int, unit: int) -> str:
        parts = []
        if hundred > 0:
            parts.append(f"{units[hundred]} trăm")
        if ten > 0:
            parts.append(tens[ten])
        if unit > 0:
            unit_str = units[unit]
            if ten >= 2:
                if unit == 1:
                    unit_str = "mốt"
                elif unit == 5:
                    unit_str = "lăm"
            parts.append(unit_str)
        return " ".join(parts) if parts else ""

    digits = [int(d) for d in str(n)]
    original_len = len(digits)
    while len(digits) < 9:
        digits.insert(0, 0)

    result_parts = []
    places = ["triệu", "nghìn", ""]
    has_higher_group = False

    for i in range(3):
        start = i * 3
        group = digits[start:start+3]
        hundred, ten, unit = group

        if hundred == ten == unit == 0:
            continue

        group_str = _convert_group(hundred, ten, unit)
        if not group_str:
            group_str = "một" if places[i] else ""

        place = places[i]
        if place:
            if group_str == "một":
                group_str = f"một {place}"
            else:
                group_str += f" {place}"
            has_higher_group = True

        result_parts.append(group_str)

    # Xử lý "lẻ" cho hàng đơn vị khi có nhóm cao hơn và hàng trăm bằng 0
    if has_higher_group and result_parts:
        last_part = result_parts[-1]
        if "trăm" not in last_part and not last_part.endswith(("triệu", "nghìn")):
            if digits[6] == 0:  # hàng trăm của nhóm đơn vị = 0
                result_parts[-1] = "lẻ " + last_part

    return " ".join(result_parts)


def read_money_amount(input_str: Union[str, int, float]) -> str:
    """
    Chuyển đổi biểu diễn tiền (500k, 1.5M, 1000000, v.v.) thành chữ tiếng Việt.
    Nếu là số điện thoại Việt Nam → trả về chuỗi rỗng "" (để lọc bỏ).
    """
    original = str(input_str).strip()

    # 1. Kiểm tra số điện thoại trước → loại bỏ ngay
    if is_vietnamese_phone_number(original):
        return ""

    # 2. Chuẩn hóa input tiền
    text = original.lower()
    text = text.replace(",", ".").replace(" ", "")

    # Phát hiện hậu tố k/m (có hoặc không)
    match = re.match(r'^(\d+(?:\.\d+)?)([km]?)$', text)
    if not match:
        return ""  # Không phải định dạng tiền hợp lệ → coi như không phải tiền

    num_str, suffix = match.groups()
    try:
        num = float(num_str)
    except ValueError:
        return ""

    if suffix == 'k':
        amount = int(num * 1000)
    elif suffix == 'm':
        amount = int(num * 1000000)
    else:
        amount = int(num)

    if amount == 0:
        return "không đồng"

    words = number_to_vietnamese(amount)
    return f"{words} đồng"