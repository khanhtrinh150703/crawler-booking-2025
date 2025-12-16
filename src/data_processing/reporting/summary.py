import json
import os
from datetime import datetime
from typing import Dict, Any
import pandas as pd

def save_summary_report(
    df: pd.DataFrame,
    total_reviews: int,
    vietnamese_reviews: int,
    null_reviews: int = 0,
    non_vietnamese_reviews: int = 0,
    low_score_reviews: int = 0,
    room_type_encoding: dict | None = None,
    stay_duration_mapping: dict | None = None,
    group_type_encoding: dict | None = None,
    charts_dir: str = "outputs/charts",
    filename: str = "summary_stats.json"
) -> str:
    """
    Lưu báo cáo tổng quan (summary) dưới dạng JSON + in log đẹp.
    
    Returns:
        Đường dẫn file đã lưu
    """
    os.makedirs(charts_dir, exist_ok=True)
    file_path = os.path.join(charts_dir, filename)

    # Tính toán an toàn các giá trị thống kê
    final_count = len(df)
    
    avg_score = round(float(df['score'].mean()), 2) if 'score' in df.columns and not df['score'].isna().all() else None
    min_score = float(df['score'].min()) if avg_score is not None else None
    max_score = float(df['score'].max()) if avg_score is not None else None

    # Tìm cột độ dài bình luận (linh hoạt)
    length_col = None
    for col in ['positive_length', 'combined_length', 'comment_length']:
        if col in df.columns:
            length_col = col
            break
    if length_col and not df[length_col].isna().all():
        avg_comment_length = round(float(df[length_col].mean()), 1)
    else:
        avg_comment_length = None

    # Đếm unique an toàn
    unique_rooms = len(room_type_encoding) if room_type_encoding else 0
    unique_durations = len(stay_duration_mapping) if stay_duration_mapping else 0
    unique_groups = len(group_type_encoding) if group_type_encoding else 0

    # Tạo báo cáo
    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": "Booking.com Reviews (Vietnamese only)",
        "processing_summary": {
            "total_reviews_scanned": total_reviews,
            "total_vietnamese_reviews": vietnamese_reviews,
            "final_reviews_in_dataset": final_count,
            "keep_ratio_percent": round(final_count / total_reviews * 100, 2) if total_reviews > 0 else 0.0
        },
        "rejection_breakdown": {
            "rejected_null_or_empty": null_reviews,
            "rejected_non_vietnamese": non_vietnamese_reviews,
            "rejected_low_score": low_score_reviews,
            "total_rejected": null_reviews + non_vietnamese_reviews + low_score_reviews
        },
        "dataset_statistics": {
            "unique_room_types": unique_rooms,
            "unique_stay_durations": unique_durations,
            "unique_group_types": unique_groups,
            "average_score": avg_score,
            "min_score": min_score,
            "max_score": max_score,
            "average_comment_length_chars": avg_comment_length
        },
        "file_info": {
            "dataset_size_records": final_count,
            "saved_charts_directory": os.path.abspath(charts_dir),
            "summary_file": file_path
        }
    }

    # Lưu file JSON
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=4)

    # In log đẹp như báo cáo chính thức
    # print("\n" + "═" * 70)
    # print("                   TỔNG QUAN XỬ LÝ DỮ LIỆU")
    # print("═" * 70)
    # print(f"Ngày tạo báo cáo        : {summary['generated_at']}")
    # print(f"Tổng đánh giá đã quét   : {total_reviews:,}")
    # print(f"→ Tiếng Việt hợp lệ     : {vietnamese_reviews:,}")
    # print(f"→ Loại bỏ null/rỗng     : {null_reviews:,}")
    # print(f"→ Loại bỏ không VN      : {non_vietnamese_reviews:,}")
    # print(f"→ Loại bỏ điểm thấp     : {low_score_reviews:,}")
    # print(f"→ Dữ liệu cuối cùng     : {final_count:,} "
    #       f"({summary['processing_summary']['keep_ratio_percent']}%)")
    # print("─" * 70)
    # print(f"Phân loại:")
    # print(f"   • Loại phòng          : {unique_rooms:,} loại")
    # print(f"   • Thời gian lưu trú   : {unique_durations:,} giá trị")
    # print(f"   • Loại nhóm           : {unique_groups:,} loại")
    # if avg_score is not None:
    #     print(f"Điểm trung bình         : {avg_score}/10")
    # if avg_comment_length is not None:
    #     print(f"Độ dài bình luận TB     : {avg_comment_length:.0f} ký tự")
    # print("─" * 70)
    print(f"Đã lưu báo cáo tổng quan → {file_path}")
    # print("═" * 70 + "\n")

    return file_path