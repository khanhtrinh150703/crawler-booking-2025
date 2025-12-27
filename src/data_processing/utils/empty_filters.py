# utils/empty_filters.py

import pandas as pd
from typing import List, Dict, Tuple

def is_empty_value(value: any) -> bool:
    """
    Kiểm tra một giá trị có phải là 'rỗng' hoặc 'vô nghĩa' không.

    Trả về True nếu nên coi giá trị này là rỗng (cần loại bỏ row khi áp dụng filter_empty_reviews):
        - None hoặc NaN
        - Chuỗi rỗng sau khi strip()
        - Chuỗi chỉ chứa khoảng trắng
        - Chuỗi quá ngắn (< 5 ký tự) sau khi strip()
        - Chuỗi không chứa bất kỳ ký tự chữ cái/số nào (chỉ dấu câu, ký tự đặc biệt)

    Args:
        value: Giá trị cần kiểm tra (thường là str hoặc float/None từ pandas).

    Returns:
        bool: True nếu giá trị rỗng/vô nghĩa, False nếu có nội dung hợp lệ.
    """
    # Trường hợp None hoặc NaN
    if pd.isna(value):
        return True
    
    # Chuyển về string và làm sạch
    if not isinstance(value, str):
        text = str(value).strip()
    else:
        text = value.strip()
    
    # Chuỗi rỗng sau strip
    if text == "":
        return True
    
    # Quá ngắn: dưới 5 ký tự
    if len(text) < 5:
        return True
    
    # Không chứa chữ cái hoặc số nào → chỉ dấu câu, emoji đã clean, hoặc ký tự lạ → coi như spam/rỗng
    if not any(c.isalnum() for c in text):
        return True
    
    # Nếu qua hết các kiểm tra → có nội dung hợp lệ
    return False


def filter_empty_reviews(
    df: pd.DataFrame,
    columns: str | List[str]
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Lọc bỏ các row có nội dung rỗng/null theo logic:
        - Nếu chỉ định 1 cột: loại bỏ row nếu cột đó rỗng/vô nghĩa.
        - Nếu chỉ định nhiều cột: loại bỏ row chỉ khi TẤT CẢ các cột đều rỗng/vô nghĩa.
        - Nếu không chỉ định columns: áp dụng cho toàn bộ DataFrame
          (loại bỏ row mà tất cả các cột đều null/rỗng).

    "Rỗng/vô nghĩa" được xác định bởi hàm is_empty_or_meaningless (đã định nghĩa trước).

    Args:
        df: DataFrame đầu vào.
        columns: Danh sách tên cột cần kiểm tra. Nếu None, kiểm tra toàn bộ DataFrame.

    Returns:
        Tuple[pd.DataFrame, Dict[str, int]]:
            - DataFrame đã lọc.
            - Thống kê: {'original_rows': int, 'removed_rows': int, 'kept_rows': int}
    """
    df_clean = df.copy()
    total_before = len(df_clean)
    
    # Chuẩn hóa thành list
    columns_list = [columns] if isinstance(columns, str) else columns
    
    # Kiểm tra cột tồn tại
    missing_cols = [col for col in columns_list if col not in df_clean.columns]
    if missing_cols:
        return df_clean, {
            "Loại bỏ do nội dung rỗng": f"0 (thiếu cột: {', '.join(missing_cols)})",
            "Giữ lại sau lọc rỗng": f"{total_before:,}"
        }
    
    if not columns_list:
        return df_clean, {
            "Loại bỏ do nội dung rỗng": "0",
            "Giữ lại sau lọc rỗng": f"{total_before:,}"
        }
    
    # Tạo mask cho các giá trị rỗng ở từng cột
    empty_masks = [df_clean[col].apply(is_empty_value) for col in columns_list]
    
    if len(columns_list) == 1:
        # Trường hợp 1 cột: loại nếu cột đó rỗng
        mask_empty = empty_masks[0]
    else:
        # Trường hợp nhiều cột: loại chỉ khi TẤT CẢ đều rỗng
        mask_empty = pd.DataFrame(empty_masks).T.all(axis=1)
    
    # Lọc: giữ lại những row KHÔNG rỗng theo điều kiện
    df_filtered = df_clean[~mask_empty].copy()
    
    removed_count = total_before - len(df_filtered)
    
    if total_before > 0:
            percent = f"{removed_count / total_before:.2%}"
    else:
        percent = "0%"

    stats = {
        "Loại bỏ do nội dung rỗng": f"{removed_count:,} ({percent})",
        "Giữ lại sau lọc rỗng": f"{len(df_filtered):,}"
    }
    
    return df_filtered, stats