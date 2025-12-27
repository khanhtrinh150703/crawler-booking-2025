# File: src/data_processing/utils/filter_by_score.py

import pandas as pd
from typing import Tuple, Dict, Any
from config.config import DEFAULT_SCORE

def filter_by_score_only(
    df: pd.DataFrame,
    min_score: float = DEFAULT_SCORE
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Hàm độc lập: Chỉ lọc DataFrame theo điểm số (score >= min_score).
    Không tạo cột mới, không xử lý text, không lọc ngôn ngữ/spam.
    
    Args:
        df: DataFrame đầu vào (phải có cột 'score')
        min_score: Ngưỡng điểm tối thiểu (mặc định lấy từ DEFAULT_SCORE)
    
    Returns:
        df_clean: DataFrame đã lọc
        stats: Dict thống kê ngắn gọn
    """
    # Copy để không ảnh hưởng df gốc
    df_work = df.copy()
    
    total_reviews = len(df_work)
    
    # Đảm bảo score là số
    if 'score' in df_work.columns:
        df_work['score'] = pd.to_numeric(df_work['score'], errors='coerce')
    
    # Đếm số lượng bị loại do điểm thấp
    if 'score' in df_work.columns:
        low_score_count = (df_work['score'] < min_score).sum()
        df_clean = df_work[df_work['score'] >= min_score].copy()
    else:
        low_score_count = 0
        df_clean = df_work.copy()
    
    kept_count = len(df_clean)
        
    # Thống kê
    stats = {
        "Tổng đánh giá đầu vào": f"{total_reviews:,}",
        "Giữ lại sau lọc score": f"{kept_count:,} ({kept_count/total_reviews:.2%})",   # <--- Key cố định
        "Loại bỏ do điểm thấp": f"{low_score_count:,} ({low_score_count/total_reviews:.2%})",
    }
    
    return df_clean, stats