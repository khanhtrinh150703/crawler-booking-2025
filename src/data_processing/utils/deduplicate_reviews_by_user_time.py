# utils/deduplicate_reviews_by_user_time.py
import pandas as pd
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

def deduplicate_reviews_by_user_and_time(
    df: pd.DataFrame,
    user_column: str = "review_name",          # Cột tên người dùng
    text_column: str = "normalized_text",      # Cột nội dung đã chuẩn hóa
    time_column: str = "review_date",          # Cột ngày giờ đánh giá (nên là datetime)
    time_window_days: int = 30,                 # Khoảng thời gian coi là "gần nhau" (mặc định 30 ngày)
    keep: str = "first"                         # Giữ lại bản ghi nào: 'first' hoặc 'last'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Loại bỏ các đánh giá trùng nội dung từ cùng một người dùng trong khoảng thời gian gần nhau.
    
    Logic:
    - Với mỗi người dùng (review_name)
    - Sắp xếp theo thời gian (review_date)
    - Nếu 2 đánh giá có normalized_text giống nhau và cách nhau <= time_window_days ngày
      → chỉ giữ lại 1 (theo tham số keep)
    
    Args:
        df: DataFrame đầu vào
        user_column: Tên cột chứa tên/id người dùng
        text_column: Tên cột chứa nội dung đã chuẩn hóa
        time_column: Tên cột chứa thời gian đánh giá (phải là datetime)
        time_window_days: Ngưỡng thời gian (ngày) để coi là trùng lặp gần
        keep: 'first' (giữ đánh giá đầu tiên) hoặc 'last' (giữ đánh giá mới nhất)
    
    Returns:
        df_dedup: DataFrame sau khi loại trùng
        stats: Thống kê số lượng bị loại
    """
    if user_column not in df.columns:
        raise ValueError(f"Cột người dùng '{user_column}' không tồn tại trong DataFrame")
    if text_column not in df.columns:
        raise ValueError(f"Cột nội dung '{text_column}' không tồn tại trong DataFrame")
    if time_column not in df.columns:
        raise ValueError(f"Cột thời gian '{time_column}' không tồn tại trong DataFrame")

    # Đảm bảo cột thời gian là datetime
    df = df.copy()
    df[time_column] = pd.to_datetime(df[time_column], errors='coerce')

    # Loại bỏ các row có thời gian NaT (không hợp lệ)
    invalid_time = df[time_column].isna()
    if invalid_time.sum() > 0:
        print(f"Cảnh báo: {invalid_time.sum()} đánh giá có thời gian không hợp lệ → sẽ bị loại bỏ")
        df = df[~invalid_time].copy()

    before_count = len(df)

    # Sắp xếp để xử lý theo thứ tự thời gian
    df = df.sort_values([user_column, time_column]).reset_index(drop=True)

    # Tạo cột tạm để đánh dấu trùng lặp
    df['text_lower'] = df[text_column].str.strip().str.lower()  # So sánh không phân biệt hoa thường và khoảng trắng
    df['prev_user'] = df[user_column].shift(1)
    df['prev_text'] = df['text_lower'].shift(1)
    df['prev_time'] = df[time_column].shift(1)

    # Điều kiện trùng: cùng user + cùng nội dung + thời gian cách <= time_window_days
    time_diff = (df[time_column] - df['prev_time']).dt.days
    is_duplicate = (
        (df[user_column] == df['prev_user']) &
        (df['text_lower'] == df['prev_text']) &
        (time_diff <= time_window_days) &
        (time_diff >= 0)  # Đảm bảo không âm (do sort)
    )

    # Đánh dấu các bản ghi cần loại (trừ cái đầu tiên nếu keep='first')
    if keep == "first":
        # Giữ cái đầu → loại các cái sau nếu trùng với cái trước
        df['is_duplicated'] = is_duplicate
    elif keep == "last":
        # Giữ cái cuối → cần đánh dấu ngược lại (loại các cái cũ nếu trùng với cái mới hơn)
        # Cách đơn giản hơn: dùng groupby và giữ last
        df = df.drop(columns=['text_lower', 'prev_user', 'prev_text', 'prev_time'], errors='ignore')
        df = df.drop_duplicates(
            subset=[user_column, 'text_lower'],
            keep='last'
        )
        # Nhưng cách này không xét thời gian → không chính xác hoàn toàn
        # → Tốt hơn nên dùng cách shift như trên và đảo logic
        df['is_duplicated'] = is_duplicate[::-1].cumsum()[::-1] > 0  # phức tạp, nên dùng groupby
        # → Dùng cách groupby an toàn hơn cho keep='last'
        raise NotImplementedError("keep='last' với điều kiện thời gian cần xử lý phức tạp hơn, hiện chỉ hỗ trợ 'first'")
    else:
        raise ValueError("keep phải là 'first' hoặc 'last'")

    # Loại bỏ các bản ghi trùng
    df_dedup = df[~df['is_duplicated']].copy()

    # Dọn dẹp cột tạm
    df_dedup = df_dedup.drop(columns=[
        'text_lower', 'prev_user', 'prev_text', 'prev_time', 'is_duplicated'
    ], errors='ignore')

    after_count = len(df_dedup)
    removed_count = before_count - after_count

    stats = {
        "Trước khi loại trùng theo user + thời gian": f"{before_count:,}",
        "Sau khi loại trùng": f"{after_count:,}",
        "Số đánh giá bị loại do trùng lặp nội dung từ cùng người dùng trong {time_window_days} ngày": f"{removed_count:,}"
    }

    return df_dedup, stats