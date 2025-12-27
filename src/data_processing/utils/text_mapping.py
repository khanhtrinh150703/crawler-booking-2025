# utils/text_mapping.py

from typing import Dict, List, Tuple
import re
import pandas as pd
from config.config import DEFAULT_VIETNAMESE_ABBREVIATION_MAPPING 


def get_mapping_dict() -> Dict[str, str]:
    """
    Trả về dictionary ánh xạ từ mặc định.
    Bạn có thể override bằng cách thay đổi biến DEFAULT_VIETNAMESE_ABBREVIATION_MAPPING
    hoặc load từ file config riêng.
    """
    return DEFAULT_VIETNAMESE_ABBREVIATION_MAPPING.copy()

def list_mappings(sorted_by_key: bool = True) -> List[Tuple[str, str]]:
    """
    Liệt kê tất cả các ánh xạ hiện có dưới dạng list of tuples.
    
    Args:
        sorted_by_key: Nếu True, sắp xếp theo từ gốc (key), ngược lại theo từ đích.
    
    Returns:
        List các tuple (từ_gốc, từ_đích)
    """
    mapping = get_mapping_dict()
    items = list(mapping.items())
    
    if sorted_by_key:
        items.sort(key=lambda x: x[0].lower())
    else:
        items.sort(key=lambda x: x[1].lower())
    
    return items

def print_mapping_table():
    """
    In ra bảng ánh xạ đẹp mắt trên console – tiện để kiểm tra nhanh.
    """
    mappings = list_mappings(sorted_by_key=True)
    
    print("\n" + "="*60)
    print("          BẢNG ÁNH XẠ TỪ VIẾT TẮT → TỪ ĐẦY ĐỦ")
    print("="*60)
    print(f"{'Từ gốc':<20} {'→':<5} {'Từ đích'}")
    print("-"*60)
    
    for key, value in mappings:
        print(f"{key:<20} {'→':<5} {value}")
    
    print("="*60)
    print(f"Tổng cộng: {len(mappings)} ánh xạ\n")

def apply_text_mapping(text: str, mapping: Dict[str, str] | None = None) -> str:
    """
    Thay thế các từ viết tắt trong văn bản bằng từ đầy đủ.
    Thay thế theo thứ tự từ dài đến ngắn để tránh xung đột (ví dụ: "ksan" trước "ks").
    
    Args:
        text: Văn bản cần xử lý
        mapping: Dictionary ánh xạ tùy chỉnh. Nếu None thì dùng mặc định.
    
    Returns:
        Văn bản sau khi đã thay thế
    """
    if text is None or pd.isna(text):
        return text
    
    if mapping is None:
        mapping = get_mapping_dict()
    
    if not mapping:
        return text
    
    # Sắp xếp key từ dài đến ngắn để ưu tiên thay thế cụm dài trước
    sorted_keys = sorted(mapping.keys(), key=len, reverse=True)
    
    pattern = re.compile(r'\b(' + '|'.join(re.escape(k) for k in sorted_keys) + r')\b', re.IGNORECASE)
    
    def replace_match(match):
        original = match.group(0)
        # Giữ nguyên chữ hoa/thường của từ gốc nếu có thể
        replacement = mapping.get(original.lower(), original)
        if original.isupper():
            return replacement.upper()
        elif original[0].isupper():
            return replacement.capitalize()
        else:
            return replacement
    
    return pattern.sub(replace_match, text)

# -----------------------------
# Hàm tiện ích để tích hợp vào pipeline
# -----------------------------
def apply_mapping_to_dataframe(
    df: pd.DataFrame,
    column: str,
    mapping: Dict[str, str] | None = None,
    new_column: str | None = None
) -> pd.DataFrame:
    """
    Áp dụng ánh xạ từ cho một cột trong DataFrame.
    
    Args:
        df: DataFrame
        column: Tên cột cần xử lý
        mapping: Ánh xạ tùy chỉnh
        new_column: Nếu cung cấp, tạo cột mới, ngược lại ghi đè lên cột cũ
    
    Returns:
        DataFrame đã được cập nhật
    """
    if column not in df.columns:
        raise ValueError(f"Cột '{column}' không tồn tại trong DataFrame")
    
    target_col = new_column or column
    df[target_col] = df[column].apply(lambda x: apply_text_mapping(x, mapping))
    
    return df

# Hàm phụ để đếm số lượng thay thế cho một dòng
def count_replacements(row: pd.Series, mapping: Dict[str, str] | None = None) -> int:
    original = row['normalized_text']
    mapped = row['normalized_text_mapped']
    
    if pd.isna(original) or original == mapped:
        return 0
    
    if mapping is None:
        mapping = get_mapping_dict()
    
    if not mapping:
        return 0
    
    count = 0
    text_lower = original.lower()  # Chỉ đếm case-insensitive
    
    # Sắp xếp key dài trước để tránh overlap (giống trong hàm mapping)
    sorted_keys = sorted(mapping.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        pattern = r'\b' + re.escape(key.lower()) + r'\b'
        matches = re.findall(pattern, text_lower)
        count += len(matches)
        # Xóa các từ đã đếm để tránh đếm chồng (nếu có overlap hiếm gặp)
        text_lower = re.sub(pattern, '', text_lower)
    
    return count