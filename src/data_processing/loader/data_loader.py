# src/data_processing/loader/data_loader.py
import json
import re
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import logging
from config.config import BASE_FOLDER, PROVINCE_MAPPING, EXPECTED_COLUMNS
from utils.vietnamese_filter import is_vietnamese_improved
from utils.normalize_stay import normalize_stay_duration
import numpy as np
import re
from pathlib import Path
from typing import Any

def _extract_province_from_path(file_path: Path, base_folder: Path) -> str:
    """
    Trích xuất tên tỉnh/thành phố đã chuẩn hóa từ đường dẫn file.

    Ưu tiên sử dụng mapping để trả về tên chính thức (ví dụ: "ha-noi" → "Hà Nội").
    Nếu không có trong mapping thì chuẩn hóa tên thư mục (thay -/_ bằng khoảng trắng và title case).

    Args:
        file_path: Đường dẫn đầy đủ đến file.
        base_folder: Thư mục gốc chứa các thư mục tỉnh/thành.

    Returns:
        Tên tỉnh/thành đã chuẩn hóa, hoặc "Khác" nếu không xác định được.
    """
    try:
        relative = file_path.relative_to(base_folder)
    except ValueError:
        # Nếu file_path không nằm trong base_folder
        return "Khác"

    if len(relative.parts) < 2:
        return "Khác"

    folder_name = relative.parts[0].lower()
    key = folder_name.replace("_", "-")

    # Ưu tiên lấy từ mapping để có tên chuẩn (có dấu, đẹp)
    return PROVINCE_MAPPING.get(key, folder_name.replace("-", " ").replace("_", " ").title())


def _safe_strip(text: Any) -> str:
    """
    An toàn strip chuỗi, tránh lỗi khi text là None hoặc không phải string.

    Args:
        text: Giá trị bất kỳ (thường là str hoặc None).

    Returns:
        Chuỗi đã được strip, hoặc chuỗi rỗng nếu input là None.
    """
    return (str(text) if text is not None else "").strip()


def _parse_month_year(date_str: str | None) -> str | None:
    """
    Parse tháng và năm từ chuỗi ngày tháng dưới nhiều định dạng phổ biến.

    Hỗ trợ:
        - "Tháng 10 2024", "10/2024", "2024-10"
        - "October 2024", "Oct 2023"
        - "Reviewed 15 November 2023"

    Args:
        date_str: Chuỗi chứa thông tin ngày tháng.

    Returns:
        Chuỗi định dạng "YYYY-MM" hoặc None nếu không parse được.
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if not date_str:
        return None

    # Tìm năm (20xx)
    years = re.findall(r"\b(20\d{2})\b", date_str)
    if not years:
        return None
    year = years[-1]  # Lấy năm cuối cùng xuất hiện

    # Tìm tháng bằng số hoặc tên (tiếng Anh/Việt)
    month_match = re.search(
        r"(0?[1-9]|1[0-2]|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|tháng\s*[1-9][0-2]?)",
        date_str,
        re.IGNORECASE,
    )

    month = "01"  # Default nếu không tìm thấy
    if month_match:
        txt = month_match.group().lower().replace("tháng", "").strip(" .")
        if txt.isdigit():
            month_num = int(txt)
            month = f"{month_num:02d}"
        else:
            month_map = {
                "jan": "01", "feb": "02", "mar": "03", "apr": "04",
                "may": "05", "jun": "06", "jul": "07", "aug": "08",
                "sep": "09", "oct": "10", "nov": "11", "dec": "12",
            }
            month = month_map.get(txt[:3], "01")

    return f"{year}-{month}"

def _process_single_review(
    review_data: Dict[str, Any],
    hotel_name: str,
    hotel_avg: float,
    province: str,
) -> List[Dict[str, Any]]:
    """
    Xử lý một review duy nhất từ dữ liệu thô thành dict chuẩn hóa để đưa vào DataFrame.

    Args:
        review_data: Dictionary chứa thông tin review gốc (từ JSON scraped).
        hotel_name: Tên khách sạn (truyền từ ngoài vào).
        hotel_avg: Điểm trung bình của khách sạn (float, có thể là NaN).
        province: Tên tỉnh/thành phố đã chuẩn hóa.

    Returns:
        List chứa một dict duy nhất đại diện cho review đã được xử lý.
        (Trả về list để dễ extend sau này nếu cần xử lý nhiều record từ 1 review)
    """
    records: List[Dict[str, Any]] = []

    reviewer = review_data.get("reviewer", {})
    review = review_data.get("review", {})

    country = reviewer.get("country", "Không rõ")
    reviewer_name = reviewer.get("name", "Không rõ")
    score = review.get("score")

    # An toàn xử lý hotel_avg (trong trường hợp là NaN từ pandas)
    hotel_avg_score = float(hotel_avg) if pd.notna(hotel_avg) else np.nan

    # Tính độ lệch điểm so với trung bình khách sạn
    if pd.isna(score) or pd.isna(hotel_avg_score):
        deviation = np.nan
    else:
        deviation = round(float(score) - hotel_avg_score, 1)

    # Ghép full text từ các phần: rating (tiêu đề), positive, negative
    full_text_parts = [
        review.get("rating"),
        review.get("comment_positive"),
        review.get("comment_negative"),
    ]
    full_text = " ".join(
        _safe_strip(part) for part in full_text_parts if _safe_strip(part)
    )
    text_length = len(full_text.split()) if full_text else 0

    # Phát hiện có phải review tiếng Việt không
    is_vietnamese = (
        is_vietnamese_improved(full_text, country) if full_text else False
    )

    # Tạo record
    record = {
        "hotel_name": hotel_name,
        "country": country,
        "province_raw": province,
        "review_name": reviewer_name,
        "score": score,
        "hotel_avg_score": hotel_avg_score,
        "deviation": float(deviation) if not pd.isna(deviation) else None,

        "date_str": review.get("date", ""),
        "month_year": None,  # Sẽ được fill sau bằng hàm parse nếu cần

        "stay_duration": normalize_stay_duration(review.get("stay_duration", "")),
        "room_type": review.get("room_type") or "Không rõ",
        "group_type": review.get("group_type") or "Không rõ",

        "rating": review.get("rating"),
        "positive_comment": _safe_strip(review.get("comment_positive")),
        "negative_comment": _safe_strip(review.get("comment_negative")),
        "combined_text": full_text,

        "text_length": text_length,
        "is_vietnamese": is_vietnamese,
    }

    records.append(record)
    return records

def collect_master_stats(top_provinces: int = 15) -> Dict[str, Any]:
    """
    Hàm chính: Thu thập và xử lý toàn bộ dữ liệu review từ các file JSON trong thư mục.

    Đọc tất cả file JSON theo cấu trúc thư mục tỉnh → khách sạn → reviews,
    xử lý từng review, chuẩn hóa dữ liệu và tổng hợp thống kê.

    Args:
        top_provinces: Số lượng tỉnh/thành phổ biến nhất để giữ nguyên tên,
                       các tỉnh còn lại sẽ gộp vào "Khác" (mặc định 15).

    Returns:
        Dictionary chứa:
            - df: DataFrame đầy đủ đã xử lý
            - top_provinces: Danh sách tên các tỉnh top
            - province_counts: Series đếm số lượng review theo tỉnh gốc
            - total_reviews: Tổng số review
            - vietnamese_ratio: Tỷ lệ review tiếng Việt
    """
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
            hotel_avg_raw = data.get("rating", "0")
            hotel_avg = 0.0
            if isinstance(hotel_avg_raw, str):
                hotel_avg_raw = hotel_avg_raw.replace(',', '.')
            try:
                hotel_avg = float(hotel_avg_raw)
            except (ValueError, TypeError):
                hotel_avg = 0.0  # hoặc None nếu bạn muốn

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

def load_data_from_csv(csv_path: str = 'du_lieu_test.csv') -> Dict[str, Any]:
    logging.info(f"Đang tải dữ liệu từ file CSV: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')  # utf-8-sig tốt hơn cho file Excel xuất ra
        logging.info(f"Đã tải thành công {len(df):,} bản ghi từ file")
    except Exception as e:
        logging.error(f"Lỗi khi đọc CSV: {e}")
        raise

    # === FIX 1: Đảm bảo tất cả các cột mong muốn đều tồn tại ===
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            logging.warning(f"Cột thiếu: '{col}' - sẽ thêm cột trống")
            df[col] = None  # hoặc np.nan, hoặc giá trị mặc định phù hợp

    # === FIX 2: Sắp xếp lại thứ tự cột đúng như mong muốn ===
    df = df[EXPECTED_COLUMNS]

    # === FIX 3: Ép kiểu dữ liệu cần thiết ===
    if 'score' in df.columns:
        df['score'] = pd.to_numeric(df['score'], errors='coerce')

    if 'is_vietnamese' in df.columns:
        # Đảm bảo is_vietnamese là bool
        df['is_vietnamese'] = df['is_vietnamese'].astype(bool)

    # Tính top provinces (nếu có cột province)
    top_n = 15
    top_provinces_list = []
    province_counts_dict = {}
    if 'province' in df.columns:
        province_value_counts = df['province'].value_counts()
        top_provinces_list = province_value_counts.head(top_n).index.tolist()
        province_counts_dict = province_value_counts.to_dict()
    else:
        logging.warning("Không tìm thấy cột 'province' trong dữ liệu")

    # Stats cho pie chart
    kept_vn = len(df[df['is_vietnamese'] == True]) if 'is_vietnamese' in df.columns else 0
    non_vn = len(df[df['is_vietnamese'] == False]) if 'is_vietnamese' in df.columns else 0

    load_stats = {
        "df": df,
        "top_provinces": top_provinces_list,
        "province_counts": province_counts_dict,
        "total_reviews": len(df),
        "vietnamese_ratio": df['is_vietnamese'].mean() if 'is_vietnamese' in df.columns else None,
        "kept_count_vn": kept_vn,
        "non_vietnamese": non_vn,
        "low_score": 0,      # bạn có thể tính thật nếu có lọc
        "null_empty": 0,
    }

    logging.info("Load dữ liệu hoàn tất - thứ tự cột đã được chuẩn hóa")
    return load_stats