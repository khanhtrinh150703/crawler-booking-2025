import os
import json
from typing import Tuple, Dict, List
import pandas as pd

from utils.processing import (
    normalize_vietnamese_text,
    normalize_stay_duration,
    is_vietnamese_improved,
)
from config.config import DEFAULT_SCORE


def process_data(base_folder: str) -> Tuple[pd.DataFrame, Dict, Dict]:
    rows = []
    stats = {
        "total_reviews": 0,
        "kept_vn": 0,
        "null_empty": 0,
        "non_vietnamese": 0,
        "low_score": 0,
    }

    json_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(base_folder)
        for f in files if f.endswith(".json")
    ]
    total_files = len(json_files)

    print(f"Phát hiện {total_files} file JSON. Bắt đầu xử lý...\n")

    stt = 1

    for idx, file_path in enumerate(json_files, 1):
        print(f"[{idx}/{total_files}] Đang xử lý: {os.path.basename(file_path)}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"   Lỗi đọc file: {e}")
            continue

        if "reviews" not in data:
            print("   Bỏ qua: Không có trường 'reviews'")
            continue

        hotel_name = data.get("name", "N/A")
        reviews = data.get("reviews", [])
        stats["total_reviews"] += len(reviews)

        for review in reviews:
            try:
                reviewer = review.get("reviewer", {})
                rev = review.get("review", {})

                country = reviewer.get("country", "")
                rating = rev.get("rating")
                positive_comment = rev.get("comment_positive")
                score = rev.get("score")
                room_type = rev.get("room_type", "")
                stay_duration = rev.get("stay_duration")
                group_type = rev.get("group_type", "")

                # 1. Loại null/empty
                if not rating and not positive_comment:
                    stats["null_empty"] += 1
                    continue

                # 2. Loại điểm thấp
                if not score or score < DEFAULT_SCORE:
                    stats["low_score"] += 1
                    continue

                # 3. Kiểm tra tiếng Việt (trước và sau normalize)
                is_vn_before = is_vietnamese_improved(rating, country) or is_vietnamese_improved(positive_comment, country)
                if not is_vn_before:
                    stats["non_vietnamese"] += 1
                    continue

                # Normalize văn bản
                norm_rating = normalize_vietnamese_text(rating) if rating else ""
                norm_positive = normalize_vietnamese_text(positive_comment) if positive_comment else ""

                # Sau normalize vẫn rỗng → bỏ
                if not norm_rating and not norm_positive:
                    stats["null_empty"] += 1
                    continue

                # Kiểm tra lại lần cuối có còn tiếng Việt không
                if not (is_vietnamese_improved(norm_rating, country) or is_vietnamese_improved(norm_positive, country)):
                    stats["non_vietnamese"] += 1
                    continue

                # Chuẩn hóa số đêm
                norm_stay = normalize_stay_duration(stay_duration) if stay_duration else ""

                # Lưu kết quả hợp lệ
                rows.append({
                    "stt": stt,
                    "hotel_name": hotel_name,
                    "rating": norm_rating,
                    "positive_comment": norm_positive,
                    "score": score,
                    "room_type": room_type,
                    "stay_duration": norm_stay,
                    "group_type": group_type,
                    "country": country,
                })
                stt += 1
                stats["kept_vn"] += 1

            except Exception as e:
                print(f"   Lỗi xử lý một review: {e}")
                continue

        print(f"   Đã xử lý xong {len(reviews)} reviews\n")

    # Tạo DataFrame
    df = pd.DataFrame(rows)

    # Tính phần trăm an toàn
    total = stats["total_reviews"] or 1  # tránh chia 0
    display_stats = {
        "Tổng số đánh giá đã quét": f"{stats['total_reviews']:,}",
        "Số đánh giá tiếng Việt hợp lệ": f"{stats['kept_vn']:,} ({stats['kept_vn']/total:.2%})",
        "Bị loại do null/empty": f"{stats['null_empty']:,} ({stats['null_empty']/total:.2%})",
        "Bị loại do không phải tiếng Việt": f"{stats['non_vietnamese']:,} ({stats['non_vietnamese']/total:.2%})",
        "Bị loại do điểm < {DEFAULT_SCORE}": f"{stats['low_score']:,} ({stats['low_score']/total:.2%})",
    }

    print("\n" + "="*50)
    print("                HOÀN TẤT XỬ LÝ")
    print("="*50)
    for k, v in display_stats.items():
        print(f"{k:>40}: {v}")
    print("="*50)

    return df, stats, display_stats