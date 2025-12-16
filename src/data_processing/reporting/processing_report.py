import json
import os
from datetime import datetime
import pandas as pd

def save_processing_report(
    total_reviews: int,
    total_json_files: int,
    null_reviews: int,
    non_vietnamese_reviews: int,
    low_score_reviews: int,
    df: pd.DataFrame,
    room_type_encoding: dict,
    stay_duration_mapping: dict,
    group_type_encoding: dict,
    charts_dir: str,
    extra_stats: dict | None = None
) -> str:
    """
    Lưu báo cáo tổng hợp quá trình xử lý dữ liệu dưới dạng JSON + in log đẹp.
    
    Returns:
        Đường dẫn file JSON đã lưu
    """
    os.makedirs(charts_dir, exist_ok=True)
    report_path = os.path.join(charts_dir, "processing_report.json")

    # Tính thêm một số thống kê hữu ích
    final_count = len(df)
    avg_score = float(df['score'].mean()) if 'score' in df.columns and not df['score'].isna().all() else 0.0
    avg_text_len = float(df['combined_text'].str.len().mean()) if 'combined_text' in df.columns else 0.0

    report = {
        "report_generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": {
            "total_reviews_scanned": total_reviews,
            "total_json_files_processed": total_json_files
        },
        "filtering_summary": {
            "removed_null_or_empty": null_reviews,
            "removed_non_vietnamese": non_vietnamese_reviews,
            "removed_low_score": low_score_reviews,
            "total_removed": null_reviews + non_vietnamese_reviews + low_score_reviews,
            "kept_reviews": final_count,
            "keep_ratio (%)": round(final_count / total_reviews * 100, 2) if total_reviews > 0 else 0
        },
        "final_dataset": {
            "total_valid_reviews": final_count,
            "unique_room_types": len(room_type_encoding),
            "unique_stay_durations": len(stay_duration_mapping),
            "unique_group_types": len(group_type_encoding),
            "average_score": round(avg_score, 2),
            "average_text_length": round(avg_text_len, 1)
        },
        "encodings_summary": {
            "room_type_count": len(room_type_encoding),
            "group_type_count": len(group_type_encoding),
            "stay_duration_count": len(stay_duration_mapping)
        }
    }

    # Nếu có thêm stats từ bạn (ví dụ: từ các bước lọc chi tiết)
    if extra_stats:
        report["extra_stats"] = extra_stats

    # Lưu file JSON
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=4)

    # # In log đẹp
    # print("\n" + "="*60)
    # print("               BÁO CÁO XỬ LÝ DỮ LIỆU HOÀN TẤT")
    # print("="*60)
    # print(f"Thời gian tạo báo cáo   : {report['report_generated_at']}")
    # print(f"Tổng file JSON đã quét  : {total_json_files:,}")
    # print(f"Tổng đánh giá thô       : {total_reviews:,}")
    # print(f"└─ Loại bỏ null/rỗng    : {null_reviews:,}")
    # print(f"└─ Loại bỏ không VN     : {non_vietnamese_reviews:,}")
    # print(f"└─ Loại bỏ điểm thấp    : {low_score_reviews:,}")
    # print(f"→ Đánh giá hợp lệ cuối  : {final_count:,} "
    #       f"({report['filtering_summary']['keep_ratio (%)']}%)")
    # print("-"*60)
    # print(f"Phân loại:")
    # print(f"  • Loại phòng           : {len(room_type_encoding):,} loại")
    # print(f"  • Thời gian lưu trú    : {len(stay_duration_mapping):,} giá trị")
    # print(f"  • Loại nhóm            : {len(group_type_encoding):,} loại")
    # print(f"Điểm trung bình         : {avg_score:.2f}/10")
    # print(f"Độ dài trung bình văn bản: {avg_text_len:.0f} ký tự")
    # print("-"*60)
    print(f"Đã lưu báo cáo chi tiết → {report_path}")
    # print("="*60)

    return report_path
