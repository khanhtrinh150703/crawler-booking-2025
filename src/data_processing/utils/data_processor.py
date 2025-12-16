import pandas as pd
import numpy as np
import os
import json
from data_processing.utils.processing import normalize_vietnamese_text, label_encode, normalize_stay_duration, is_vietnamese_improved  # Assuming other functions are imported here

def process_data(base_folder, rows=None):
    if rows is None:
        rows = []
    
    # Initialize counters
    stt = 1
    total_reviews = 0
    vietnamese_reviews = 0
    null_reviews = 0
    non_vietnamese_reviews = 0
    low_score_reviews = 0
    
    # Count total JSON files first
    total_json_files = sum(1 for root, dirs, files in os.walk(base_folder) for file in files if file.endswith(".json"))
    
    file_counter = 0
    for root, dirs, files in os.walk(base_folder):
        for filename in files:
            if filename.endswith(".json"):
                file_counter += 1
                file_path = os.path.join(root, filename)
                print(f"[{file_counter}/{total_json_files}] Đang xử lý file: {file_path}")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Kiểm tra cấu trúc dữ liệu
                    if "reviews" not in data:
                        print(f" - Bỏ qua: File không có trường 'reviews'")
                        continue
                    reviews_in_file = len(data['reviews'])
                    print(f" - Số lượng đánh giá trong file: {reviews_in_file}")
                    total_reviews += reviews_in_file
                    file_vietnamese = 0
                    file_null = 0
                    file_non_vietnamese = 0
                    file_low_score = 0
                    hotel_name = data.get('name', 'N/A')
                    for review in data.get("reviews", []):
                        # Lấy thông tin cần thiết
                        try:
                            reviewer_data = review.get("reviewer", {})
                            review_data = review.get("review", {})
                            # Các trường cần lấy theo yêu cầu
                            rating = review_data.get("rating")
                            positive_comment = review_data.get("comment_positive")
                            score = review_data.get("score")
                            room_type = review_data.get("room_type")
                            stay_duration = review_data.get("stay_duration")
                            group_type = review_data.get("group_type")
                            # Lấy thêm thông tin quốc gia của người review
                            country = reviewer_data.get("country", "")
                            # Kiểm tra null hoặc empty
                            if (rating is None or rating == "") and (positive_comment is None or positive_comment == ""):
                                null_reviews += 1
                                file_null += 1
                                continue
                            # Chỉ lấy các đánh giá có điểm >= 5
                            if not score or score < 5:
                                low_score_reviews += 1
                                file_low_score += 1
                                continue
                            # Chuẩn hóa stay_duration chỉ lấy số đêm
                            normalized_stay_duration = normalize_stay_duration(stay_duration) if stay_duration else ""
                            # Kiểm tra xem có phải tiếng Việt không (đánh giá tổng quan hoặc bình luận tích cực),
                            # có thêm thông tin quốc gia để tăng độ chính xác
                            is_vietnamese_rating = is_vietnamese_improved(rating, country) if rating else False
                            is_vietnamese_positive = is_vietnamese_improved(positive_comment, country) if positive_comment else False
                            if is_vietnamese_rating or is_vietnamese_positive:
                                # Chuẩn hóa văn bản
                                normalized_rating = normalize_vietnamese_text(rating) if rating else ""
                                normalized_positive = normalize_vietnamese_text(positive_comment) if positive_comment else ""
                                # Kiểm tra lại một lần nữa sau khi chuẩn hóa
                                if not normalized_rating and not normalized_positive:
                                    null_reviews += 1
                                    file_null += 1
                                    continue
                                # Kiểm tra có vẫn là tiếng Việt sau khi chuẩn hóa không
                                # (đặc biệt quan trọng với những văn bản sau khi loại bỏ ký tự)
                                is_still_vietnamese = is_vietnamese_improved(normalized_rating, country) or is_vietnamese_improved(normalized_positive, country)
                                if not is_still_vietnamese:
                                    non_vietnamese_reviews += 1
                                    file_non_vietnamese += 1
                                    continue
                                # Chỉ lưu nếu có nội dung sau khi chuẩn hóa
                                if normalized_rating or normalized_positive:
                                    rows.append({
                                        "stt": stt,
                                        "hotel_name": hotel_name,
                                        "rating": normalized_rating,  # Đánh giá tổng quan
                                        "positive_comment": normalized_positive,  # Bình luận tích cực
                                        "score": score,
                                        "room_type": room_type if room_type else "",
                                        "stay_duration": normalized_stay_duration,  # Đã chuẩn hóa số đêm
                                        "group_type": group_type if group_type else "",
                                        "country": country  # Thêm trường country để phân tích sau này
                                    })
                                    stt += 1
                                    file_vietnamese += 1
                                    vietnamese_reviews += 1
                            else:
                                file_non_vietnamese += 1
                                non_vietnamese_reviews += 1
                        except Exception as e:
                            print(f" - Lỗi khi xử lý bản ghi: {str(e)}")
                            continue
                    print(f" - Kết quả xử lý file:")
                    print(f" + Số đánh giá tiếng Việt đã lưu: {file_vietnamese}")
                    print(f" + Số đánh giá bị loại (Null/Empty): {file_null}")
                    print(f" + Số đánh giá bị loại (Không phải tiếng Việt): {file_non_vietnamese}")
                    print(f" + Số đánh giá bị loại (Điểm < 5): {file_low_score}")
                except Exception as e:
                    print(f" - Lỗi khi đọc file {file_path}: {str(e)}")
                    continue
    
    # Thống kê tổng quát
    print("\n=== THỐNG KÊ TỔNG QUÁT ===")
    print(f"Tổng số đánh giá đã quét: {total_reviews}")
    print(f"Số đánh giá tiếng Việt hợp lệ: {vietnamese_reviews} ({vietnamese_reviews / total_reviews * 100:.2f}% if total_reviews > 0 else 0)")
    print(f"Số đánh giá bị loại do null/empty: {null_reviews} ({null_reviews / total_reviews * 100:.2f}% if total_reviews > 0 else 0)")
    print(f"Số đánh giá bị loại do không phải tiếng Việt: {non_vietnamese_reviews} ({non_vietnamese_reviews / total_reviews * 100:.2f}% if total_reviews > 0 else 0)")
    print(f"Số đánh giá bị loại do điểm < 5: {low_score_reviews} ({low_score_reviews / total_reviews * 100:.2f}% if total_reviews > 0 else 0)")
        
    # 1. Tạo dict chứa số thô (raw numbers) – dùng để vẽ biểu đồ, tính toán
    stats_raw = {
        "total_reviews": total_reviews,
        "kept_count_vn": vietnamese_reviews,
        "null_empty_count": null_reviews,
        "non_vietnamese_count": non_vietnamese_reviews,
        "low_score_count": low_score_reviews,
    }

    # 2. Tạo dict hiển thị đẹp (chỉ để in log, không dùng tính toán)
    def safe_pct(num, total):
        if total == 0:
            return "0.00%"
        return f"{num/total*100:.2f}%"

    stats_display = {
        "Tổng số đánh giá đã quét": f"{total_reviews:,}",
        "Số đánh giá tiếng Việt hợp lệ": f"{vietnamese_reviews:,} ({safe_pct(vietnamese_reviews, total_reviews)})",
        "Số đánh giá bị loại do null/empty": f"{null_reviews:,} ({safe_pct(null_reviews, total_reviews)})",
        "Số đánh giá bị loại do không phải tiếng Việt": f"{non_vietnamese_reviews:,} ({safe_pct(non_vietnamese_reviews, total_reviews)})",
        "Số đánh giá bị loại do điểm < 5": f"{low_score_reviews:,} ({safe_pct(low_score_reviews, total_reviews)})",
    }

    # In log đẹp
    print("\n=== THỐNG KÊ TỔNG QUÁT ===")
    for label, value in stats_display.items():
        print(f"{label}: {value}")

    # Tạo DataFrame
    df_processed = pd.DataFrame(rows)

    # Trả về cả 2 (hoặc trả về cả df + 2 dict nếu trong hàm)
    return df_processed, stats_raw, stats_display