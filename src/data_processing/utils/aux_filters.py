# utils/aux_filters.py

import pandas as pd
from typing import List, Dict, Tuple
from config.config import EMOJI_PATTERN

def remove_emoji(text: str) -> str:
    """
    Loại bỏ toàn bộ emoji, emoticon text (:D, :(, <3, ...) và một số ký tự spam khỏi chuỗi.

    Sử dụng EMOJI_PATTERN (regex đã định nghĩa trước đó) để thay thế bằng chuỗi rỗng.
    Xử lý an toàn với None, NaN (từ pandas), hoặc các kiểu dữ liệu khác.

    Args:
        text: Văn bản đầu vào (str, None, NaN, hoặc bất kỳ kiểu nào).

    Returns:
        Chuỗi đã được loại bỏ emoji và strip khoảng trắng thừa. Trả về "" nếu input rỗng/NaN.
    """
    # Kiểm tra NaN từ pandas hoặc None
    if pd.isna(text) or text is None:
        return ""

    # Chuyển về str để tránh lỗi với số, bool,...
    clean_text = str(text)

    # Loại bỏ emoji bằng regex pattern đã định nghĩa
    clean_text = EMOJI_PATTERN.sub(r"", clean_text)

    # Strip khoảng trắng thừa ở đầu/cuối
    return clean_text.strip()

def clean_emoji_from_column(
    df: pd.DataFrame,
    columns: str | List[str]
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Làm sạch emoji khỏi một hoặc nhiều cột nội dung.
    
    Args:
        df: DataFrame đầu vào
        columns: Tên cột (str) hoặc list các cột cần xử lý
    
    Returns:
        df_clean, stats
    """
    df_clean = df.copy()
    columns_list = [columns] if isinstance(columns, str) else columns
    
    total_rows = len(df_clean)
    total_with_emoji = 0
    
    # Kiểm tra cột tồn tại
    missing_cols = [col for col in columns_list if col not in df_clean.columns]
    if missing_cols:
        return df_clean, {
            "Số đánh giá chứa emoji (đã làm sạch)": f"0 (thiếu cột: {', '.join(missing_cols)})"
        }
    
    for col in columns_list:
        # Đếm số row có emoji trước khi xóa (chỉ đếm lần đầu để tránh đúp)
        if total_with_emoji == 0:  # chỉ đếm ở cột đầu tiên để tránh tính trùng
            has_emoji_mask = df_clean[col].apply(
                lambda x: bool(EMOJI_PATTERN.search(str(x))) if pd.notna(x) else False
            )
            total_with_emoji = has_emoji_mask.sum()
        
        # Xóa emoji
        df_clean[col] = df_clean[col].apply(remove_emoji)
    
    stats = {
        "Số đánh giá chứa emoji (đã làm sạch)": f"{total_with_emoji:,} ({total_with_emoji/total_rows:.2%})",
        "Số đánh giá không có emoji": f"{total_rows - total_with_emoji:,}",
    }
    
    return df_clean, stats