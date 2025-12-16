import os
import json
from pathlib import Path
from collections import Counter
from typing import Dict
import pandas as pd
import logging
from typing import Dict, List, Any
from config.config import BASE_FOLDER
from utils.processing import is_vietnamese_improved, normalize_stay_duration, is_vietnamese

def load_json_files():
    rows = []

    # Thống kê
    total_reviews = 0
    vietnamese_reviews = 0
    null_reviews = 0
    non_vietnamese_reviews = 0
    low_score_reviews = 0

    # Số thứ tự sẽ tăng dần qua các file
    stt = 1

    # Kiểm tra thư mục DATA tồn tại
    if not os.path.exists(BASE_FOLDER):
        print(f"Thư mục {BASE_FOLDER} không tồn tại! Vui lòng kiểm tra lại đường dẫn.")
        return [], {}  # Trả về rỗng nếu lỗi

    # In ra danh sách các thư mục con để kiểm tra
    print(f"Danh sách các thư mục con trong {BASE_FOLDER}:")
    for item in os.listdir(BASE_FOLDER):
        if os.path.isdir(os.path.join(BASE_FOLDER, item)):
            print(f" - {item}")

    # Đếm tổng số file JSON để theo dõi tiến trình
    total_json_files = 0
    for root, dirs, files in os.walk(BASE_FOLDER):
        for file in files:
            if file.endswith(".json"):
                total_json_files += 1
    print(f"Tìm thấy tổng cộng {total_json_files} file JSON")

    # Load và xử lý từng file JSON
    for root, dirs, files in os.walk(BASE_FOLDER):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        hotel_name = data.get('name', 'Unknown')
                        reviews = data.get('reviews', [])  # Giả sử có key 'reviews'
                        
                        for review in reviews:
                            total_reviews += 1
                            
                            # Lấy các trường chính
                            rating = review.get('rating')
                            positive = review.get('positive')
                            negative = review.get('negative')
                            score = review.get('score')
                            country = review.get('country')
                            room_type = review.get('room_type')  # Nếu có
                            stay_duration = review.get('stay_duration')  # Nếu có
                            group_type = review.get('group_type')  # Nếu có
                            
                            # Kiểm tra null review (nếu cả positive và negative đều rỗng)
                            if not positive and not negative:
                                null_reviews += 1
                                continue
                            
                            # Kết hợp text để kiểm tra ngôn ngữ
                            text = (positive or '') + ' ' + (negative or '')
                            if is_vietnamese(text, country):
                                vietnamese_reviews += 1
                                # Append row như dict cho DataFrame sau
                                rows.append({
                                    'stt': stt,
                                    'hotel_name': hotel_name,
                                    'rating': rating,
                                    'positive': positive,
                                    'negative': negative,
                                    'score': score,
                                    'country': country,
                                    'room_type': room_type,
                                    'stay_duration': stay_duration,
                                    'group_type': group_type
                                    # Thêm các trường khác nếu cần từ notebook
                                })
                                stt += 1
                            else:
                                non_vietnamese_reviews += 1
                            
                            # Kiểm tra low score (giả sử <5 là low)
                            if score is not None and score < 5:
                                low_score_reviews += 1
                                
                except Exception as e:
                    print(f"Lỗi khi đọc file {file_path}: {e}")

    # Tạo dict stats
    stats = {
        'total_reviews': total_reviews,
        'vietnamese_reviews': vietnamese_reviews,
        'null_reviews': null_reviews,
        'non_vietnamese_reviews': non_vietnamese_reviews,
        'low_score_reviews': low_score_reviews,
        'total_json_files': total_json_files
    }
    
    return rows, stats

def collect_full_stats() -> Dict:
    
    stats = {
        "total_files": 0,
        "total_reviews": 0,
        "kept_vietnamese": 0,
        "null_empty": 0,
        "non_vietnamese": 0,
        "low_score": 0,

        "total_hotels": set(),
        "hotel_review_count": Counter(),
        "scores": [],
        "countries": Counter(),
        "room_types": Counter(),
        "group_types": Counter(),
        "stay_durations": Counter(),
        "review_dates": [],
        "positive_vn_texts": [],
        "negative_vn_texts": [],
        "has_positive": 0,
        "has_negative": 0,
    }

    json_files = list(Path(BASE_FOLDER).rglob("*.json"))
    stats["total_files"] = len(json_files)

    for fp in json_files:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                data = json.load(f)

            hotel_name = data.get("name", "Không tên")
            stats["total_hotels"].add(hotel_name)
            stats["hotel_review_count"][hotel_name] += len(data.get("reviews", []))

            for rev in data.get("reviews", []):
                stats["total_reviews"] += 1

                reviewer = rev.get("reviewer", {})
                country = reviewer.get("country", "")

                r = rev.get("review", {})
                score = r.get("score")
                rating_text = r.get("rating", "")
                positive = r.get("comment_positive")
                negative = r.get("comment_negative")
                room_type = r.get("room_type", "")
                group_type = r.get("group_type", "")
                stay_duration = r.get("stay_duration", "")
                date_str = r.get("date", "")

                # === CŨ ===
                full_text = " ".join(filter(None, [str(rating_text), positive, negative]))
                if not full_text.strip():
                    stats["null_empty"] += 1
                    continue
                if score is not None and score < 5.0:
                    stats["low_score"] += 1
                if not is_vietnamese_improved(full_text, country):
                    stats["non_vietnamese"] += 1
                    continue
                stats["kept_vietnamese"] += 1

                # === MỚI ===
                if score is not None:
                    stats["scores"].append(float(score))
                stats["countries"][country] += 1
                stats["room_types"][room_type] += 1
                stats["group_types"][group_type] += 1
                stats["stay_durations"][normalize_stay_duration(stay_duration)] += 1

                # Ngày tháng (nếu có)
                try:
                    parts = date_str.split()
                    if len(parts) >= 3 and parts[-1].isdigit():
                        month_year = f"{parts[-1]}-{str(parts[-2]).zfill(2)}"
                        stats["review_dates"].append(month_year)
                except:
                    pass

                # Comment tiếng Việt
                if positive:
                    stats["has_positive"] += 1
                    stats["positive_vn_texts"].append(positive.strip())
                if negative:
                    stats["has_negative"] += 1
                    stats["negative_vn_texts"].append(negative.strip())

        except Exception as e:
            print(f"Lỗi đọc file {fp.name}: {e}")

    return stats
# src/data_processing/utils/master_stats_collector.py
import json
import re
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

from config.config import BASE_FOLDER, PROVINCE_MAPPING
from utils.processing import is_vietnamese_improved, normalize_stay_duration


def _extract_province_from_path(file_path: Path, base_folder: Path) -> str:
    """Trích xuất tên tỉnh/thành đã chuẩn hóa (ưu tiên điểm du lịch nổi tiếng)."""
    relative = file_path.relative_to(base_folder)
    if len(relative.parts) < 2:
        return "Khác"

    folder_name = relative.parts[0].lower()

    key = folder_name.replace("_", "-")
    return PROVINCE_MAPPING.get(key, folder_name.replace("-", " ").replace("_", " ").title())


def _safe_strip(text: Any) -> str:
    """An toàn strip chuỗi, tránh lỗi khi text là None."""
    return (text or "").strip()


def _parse_month_year(date_str: str) -> str | None:
    """Parse tháng năm từ chuỗi ngày (hỗ trợ nhiều định dạng)."""
    if not date_str or not isinstance(date_str, str):
        return None

    # Tìm năm
    years = re.findall(r'\b(20\d{2})\b', date_str)
    if not years:
        return None
    year = years[-1]

    # Tìm tháng
    month_match = re.search(r'(0?[1-9]|1[0-2]|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|tháng\s*\d{1,2})', date_str, re.I)
    month = "01"
    if month_match:
        txt = month_match.group().lower().replace("tháng", "").strip()
        if txt.isdigit():
            month = txt.zfill(2)
        else:
            month_map = {"jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
                         "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"}
            month = month_map.get(txt[:3], "01")

    return f"{year}-{month}"


def _process_single_review(review_data: dict, hotel_name: str, hotel_avg: float | None, province: str) -> List[dict]:
    """Xử lý từng review → trả về list record."""
    records = []
    reviewer = review_data.get("reviewer", {})
    country = reviewer.get("country", "Không rõ")

    r = review_data.get("review", {})

    # Safe extract score
    score = None
    try:
        score_val = r.get("score")
        score = float(score_val) if score_val is not None else None
    except (ValueError, TypeError):
        pass

    # Ghép full text
    full_text_parts = [
        r.get("rating"),
        r.get("comment_positive"),
        r.get("comment_negative")
    ]
    full_text = " ".join(filter(None, [_safe_strip(part) for part in full_text_parts]))
    text_length = len(full_text.split()) if full_text else 0
    is_vn = is_vietnamese_improved(full_text, country) if full_text else False

    deviation = score - hotel_avg if score is not None and hotel_avg is not None else None

    records.append({
        "hotel_name": hotel_name,
        "province_raw": province,
        "country": country,
        "score": score,
        "hotel_avg_score": hotel_avg,
        "deviation": deviation,
        "full_text": full_text,
        "positive_text": _safe_strip(r.get("comment_positive")),
        "negative_text": _safe_strip(r.get("comment_negative")),
        "text_length": text_length,
        "is_vietnamese": is_vn,
        "room_type": r.get("room_type") or "Không rõ",
        "group_type": r.get("group_type") or "Không rõ",
        "stay_duration": normalize_stay_duration(r.get("stay_duration", "")),
        "date_str": r.get("date", ""),
        "month_year": None,  # sẽ fill sau
    })
    return records


def collect_master_stats(top_provinces: int = 15) -> Dict[str, Any]:
    """Hàm chính: thu thập và tổng hợp toàn bộ dữ liệu review."""
    base_folder = Path(BASE_FOLDER)
    print(f"Đang đọc dữ liệu từ: {base_folder}")

    json_files = list(base_folder.rglob("*.json"))
    print(f"Phát hiện {len(json_files):,} file JSON\n")

    all_records = []

    for fp in json_files:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                data = json.load(f)

            province = _extract_province_from_path(fp, base_folder)
            hotel_name = data.get("name", "Không tên")

            # Hotel rating
            hotel_avg = None
            try:
                rating = data.get("rating")
                hotel_avg = float(rating) if rating else None
            except (ValueError, TypeError):
                pass

            reviews = data.get("reviews", [])
            for rev in reviews:
                all_records.extend(_process_single_review(rev, hotel_name, hotel_avg, province))

        except Exception as e:
            print(f"Lỗi khi đọc {fp}: {e}")
            continue  # tiếp tục với file khác

    if not all_records:
        print("Không có dữ liệu review nào!")
        return {"df": pd.DataFrame(), "top_provinces": [], "total_reviews": 0}

    df = pd.DataFrame(all_records)

    # Parse tháng năm
    df["month_year"] = df["date_str"].apply(_parse_month_year)

    # Xác định top tỉnh
    province_counts = df["province_raw"].value_counts()
    top_provinces_list = province_counts.head(top_provinces).index.tolist()
    df["province"] = df["province_raw"].apply(lambda x: x if x in top_provinces_list else "Khác")

    # In báo cáo
    print("\nHOÀN TẤT XỬ LÝ DỮ LIỆU")
    print("=" * 80)
    print(f"Tổng review                 : {len(df):,}")
    print(f"Số tỉnh/thành phát hiện     : {df['province_raw'].nunique()}")
    print(f"Top {top_provinces} địa điểm nhiều review nhất:")
    for p, c in province_counts.head(top_provinces).items():
        print(f"   → {p:<20}: {c:,} review")
    print(f"Khác                        : {len(df[df['province'] == 'Khác']):,} review")
    print(f"Tỷ lệ review tiếng Việt     : {df['is_vietnamese'].mean()*100:.2f}%")
    print(f"Điểm trung bình             : {df['score'].mean():.2f}" if df['score'].notna().any() else "Điểm trung bình             : N/A")
    print("=" * 80)

    return {
        "df": df,
        "top_provinces": top_provinces_list,
        "province_counts": province_counts,
        "total_reviews": len(df),
        "vietnamese_ratio": df['is_vietnamese'].mean()
    }

def load_data_from_csv(csv_path: str = 'du_lieu.csv') -> Dict[str, Any]:
    logging.info(f"Đang tải dữ liệu từ file CSV: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        logging.info(f"Đã tải thành công {len(df):,} bản ghi")
    except Exception as e:
        logging.error(f"Lỗi khi đọc CSV: {e}")
        raise

    # FIX quan trọng: Đảm bảo score là số
    if 'score' in df.columns:
        df['score'] = pd.to_numeric(df['score'], errors='coerce')

    # Tính top provinces (dùng để vẽ biểu đồ 04, 05)
    top_n = 15  # hoặc 10 tùy bạn
    province_value_counts = df['province'].value_counts()
    top_provinces_list = province_value_counts.head(top_n).index.tolist()

    # Các stats cần cho biểu đồ 10 (pie chart lọc dữ liệu)
    # Nếu file CSV của bạn KHÔNG có các cột này từ trước, thì mình sẽ để mặc định = 0
    # Nhưng nếu bạn muốn chính xác, hãy thêm chúng khi lưu CSV lần đầu
    stats_for_pie = {
        "kept_count_vn": len(df[df['is_vietnamese'] == True]),  # giả sử chỉ giữ TV
        "non_vietnamese": len(df[df['is_vietnamese'] == False]),
        "low_score": 0,  # nếu không có lọc thì để 0
        "null_empty": 0,
        "total_reviews": len(df)
    }

    load_stats = {
        "df": df,
        "top_provinces": top_provinces_list,  # quan trọng cho biểu đồ 04 & 05
        "province_counts": province_value_counts.to_dict(),
        "total_reviews": len(df),
        "vietnamese_ratio": df['is_vietnamese'].mean() if 'is_vietnamese' in df.columns else None,
        # Thêm các key giả lập để pie chart chạy được (nếu không có thật thì để 0)
        "kept_count_vn": stats_for_pie["kept_count_vn"],
        "non_vietnamese": stats_for_pie["non_vietnamese"],
        "low_score": stats_for_pie["low_score"],
        "null_empty": stats_for_pie["null_empty"],
    }

    return load_stats