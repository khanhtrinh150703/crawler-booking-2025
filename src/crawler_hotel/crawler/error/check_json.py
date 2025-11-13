import json
import os
# ==============================================

def check_invalid_evaluation_categories(eval_cat):
    required_fields = ["service_staff", "amenities", "cleanliness",
                       "comfort", "value_for_money", "location"]
    all_null = True
    any_null = False

    for field in required_fields:
        value = eval_cat.get(field)
        if value is None:
            any_null = True
        else:
            all_null = False

    return all_null, any_null


def is_invalid_reviews(reviews):
    if reviews is None:
        return True
    if isinstance(reviews, str) and reviews.strip().lower() in ["not found", ""]:
        return True
    if isinstance(reviews, list) and len(reviews) == 0:
        return True
    if isinstance(reviews, dict) and len(reviews) == 0:
        return True
    if not isinstance(reviews, (list, dict)):
        return True
    return False


def safe_float(value, default=None):
    """Chuyển đổi an toàn sang float, trả về default nếu lỗi"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(',', '.'))  # hỗ trợ cả dấu phẩy
        except ValueError:
            return default
    return default


def extract_review_summary(reviews, max_reviews=5):
    """
    Trích xuất tóm tắt reviews để hiển thị trong Excel.
    - Nếu là list: lấy tối đa `max_reviews` review đầu tiên (chỉ nội dung + rating nếu có)
    - Nếu là dict: lấy các key là ID, value là nội dung
    - Trả về chuỗi ngắn gọn
    """
    if isinstance(reviews, list):
        summary = []
        for i, rev in enumerate(reviews[:max_reviews]):
            if isinstance(rev, dict):
                content = rev.get("content", rev.get("text", "")).strip()
                rating = rev.get("rating")
                rating_str = f" ({rating}/5)" if rating is not None else ""
                summary.append(f"[{i+1}] {content[:100]}{'...' if len(content) > 100 else ''}{rating_str}")
            else:
                summary.append(f"[{i+1}] {str(rev)[:100]}...")
        return "\n".join(summary) + (f"\n... (+{len(reviews) - max_reviews} more)" if len(reviews) > max_reviews else "")
    
    elif isinstance(reviews, dict):
        summary = []
        for i, (key, value) in enumerate(list(reviews.items())[:max_reviews]):
            if isinstance(value, dict):
                content = value.get("content", value.get("text", "")).strip()
                rating = value.get("rating")
                rating_str = f" ({rating}/5)" if rating is not None else ""
            else:
                content = str(value)
                rating_str = ""
            summary.append(f"[{key}] {content[:100]}{'...' if len(content) > 100 else ''}{rating_str}")
        return "\n".join(summary) + (f"\n... (+{len(reviews) - max_reviews} more)" if len(reviews) > max_reviews else "")
    
    else:
        return str(reviews)[:500]


# error/check_json.py

def process_json_file(file_path):
    file_name = os.path.basename(file_path)
    hotel_name = "Unknown"
    review_count = 0
    total_rating = None  # ← MỚI: Lấy total_rating

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # === TÊN KHÁCH SẠN ===
        hotel_name = data.get("name", "Unknown")
        if isinstance(hotel_name, str):
            hotel_name = hotel_name.strip() or "Unknown"

        # === SỐ LƯỢNG REVIEWS ===
        reviews = data.get("reviews", [])
        if isinstance(reviews, list):
            review_count = len(reviews)
        elif isinstance(reviews, dict):
            review_count = len(reviews)

        # === LẤY total_rating (chuẩn hóa) ===
        total_rating_raw = data.get("total_rating")
        if total_rating_raw is not None:
            if isinstance(total_rating_raw, str):
                cleaned = total_rating_raw.strip()
                try:
                    total_rating = float(cleaned)
                except ValueError:
                    total_rating = None
            elif isinstance(total_rating_raw, (int, float)):
                total_rating = float(total_rating_raw)
            else:
                total_rating = None

        # === KIỂM TRA LỖI ===
        if not hotel_name or hotel_name == "Unknown":
            return True, "name is null or empty", review_count, hotel_name, file_name, total_rating

        eval_cat = data.get("evaluation_categories", {})
        if not isinstance(eval_cat, dict):
            return True, "evaluation_categories invalid", review_count, hotel_name, file_name, total_rating

        all_null, any_null = check_invalid_evaluation_categories(eval_cat)
        if all_null:
            return True, "all 6 eval fields are null", review_count, hotel_name, file_name, total_rating
        if any_null:
            return True, "at least one of 6 eval fields is null", review_count, hotel_name, file_name, total_rating

        if is_invalid_reviews(reviews):
            return True, "reviews is null/empty/not found/invalid", review_count, hotel_name, file_name, total_rating

        # ===  KIỂM TRA total_rating ===
        total_rating_raw = data.get("total_rating")
        if total_rating_raw is not None:
            if not isinstance(total_rating_raw, str):
                return True, f"total_rating must be string, got {type(total_rating_raw)}", review_count, hotel_name, file_name, total_rating

            cleaned = total_rating_raw.strip()
            try:
                total_rating = float(cleaned)
            except ValueError:
                return True, f"total_rating invalid string: '{total_rating_raw}'", review_count, hotel_name, file_name, total_rating

            if total_rating < 0:
                return True, f"total_rating cannot be negative: {total_rating}", review_count, hotel_name, file_name, total_rating

            if total_rating == int(total_rating):
                total_rating_int = int(total_rating)
                if total_rating_int > review_count:
                    return True, f"total_rating ({total_rating_int}) > review count ({review_count})", review_count, hotel_name, file_name, total_rating

        return False, None, review_count, hotel_name, file_name, total_rating

    except Exception as e:
        return True, f"Error: {str(e)}", 0, "Unknown", file_name, None
    
    