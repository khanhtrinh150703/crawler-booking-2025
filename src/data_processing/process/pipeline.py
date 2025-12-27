# process/pipeline.py

from typing import Dict, Any, Tuple
import pandas as pd

from config.config import CONTENT_COLUMNS, POSSIBLE_COMMENT_COLUMNS, POSSIBLE_COUNTRY_COLUMNS

from utils.filter_by_score import filter_by_score_only
from utils.aux_filters import clean_emoji_from_column
from utils.repetitive_filters import clean_repetitive_in_columns
from utils.empty_filters import filter_empty_reviews
from utils.vietnamese_filter import is_vietnamese_improved
from utils.normalize_vietnamese_text import normalize_vietnamese_text
from utils.text_mapping import apply_text_mapping
from utils.word_segmentation import add_word_segmented_column
from utils.remove_duplicate_words import remove_consecutive_duplicates_in_column
from utils.vietnamese_money_reader import read_money_amount, remove_phone_numbers, is_vietnamese_phone_number
from utils.deduplicate_reviews_by_user_time import deduplicate_reviews_by_user_and_time


def print_columns(df: pd.DataFrame, stage: str):
    """Hàm phụ để in ra các cột hiện có trong DataFrame tại mỗi giai đoạn."""
    print(f"\n=== {stage} ===")
    print(f"Số lượng đánh giá: {len(df):,}")
    print("Các cột hiện có:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2}. {col}")
    print("=" * 50)


def process_csv_pipeline(load_stats: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, str]]:
    df_raw = load_stats["df"]
    total_reviews = load_stats["total_reviews"]

    # In cột ban đầu
    print_columns(df_raw, "1. DỮ LIỆU GỐC (RAW)")

    # Bước 1: Lọc điểm số thấp
    df_after_score, score_stats = filter_by_score_only(df_raw)

    # Lấy các cột nội dung thực tế
    actual_columns = [col for col in CONTENT_COLUMNS if col in df_after_score.columns]
    if not actual_columns:
        raise ValueError(f"Không tìm thấy bất kỳ cột nội dung nào trong {CONTENT_COLUMNS}")

    # Bước 2: Làm sạch emoji
    df_step2, emoji_stats = clean_emoji_from_column(df_after_score, actual_columns)

    # Bước 3: Làm sạch repetitive
    df_step3, repetitive_stats = clean_repetitive_in_columns(df_step2, actual_columns)

    # Bước 4: Lọc row rỗng sau khi đã clean
    df_clean, empty_stats = filter_empty_reviews(df_step3, actual_columns)

    # Bước 5: Xác định cột chính để xử lý
    COMMENT_COLUMN = next((col for col in POSSIBLE_COMMENT_COLUMNS if col in df_clean.columns), actual_columns[0])
    COUNTRY_COLUMN = next((col for col in POSSIBLE_COUNTRY_COLUMNS if col in df_clean.columns), None)

    print(f"\nCột nội dung chính được chọn: {COMMENT_COLUMN}")
    if COUNTRY_COLUMN:
        print(f"Cột quốc gia được chọn: {COUNTRY_COLUMN}")
    else:
        print("Không tìm thấy cột quốc gia.")

    # Bước 6: Chuẩn hóa văn bản chính
    df_clean['normalized_text'] = df_clean[COMMENT_COLUMN].apply(normalize_vietnamese_text)

    # Bước 7-8: Phát hiện tiếng Việt
    df_clean['is_vietnamese_raw'] = df_clean.apply(
        lambda row: is_vietnamese_improved(
            row[COMMENT_COLUMN],
            row[COUNTRY_COLUMN] if COUNTRY_COLUMN else None
        ),
        axis=1
    )
    df_clean['is_vietnamese'] = df_clean.apply(
        lambda row: is_vietnamese_improved(
            row['normalized_text'],
            row[COUNTRY_COLUMN] if COUNTRY_COLUMN else None
        ),
        axis=1
    )

    # Bước 9: Áp dụng mở rộng từ viết tắt + loại bỏ từ lặp liên tiếp
    df_clean['normalized_text'] = df_clean['normalized_text'].apply(apply_text_mapping)
    df_clean = remove_consecutive_duplicates_in_column(
        df=df_clean,
        column="normalized_text",
        new_column="normalized_text"
    )

    # ==================== BƯỚC XỬ LÝ TIỀN & SỐ ĐIỆN THOẠI (ĐÃ SỬA) ====================
    print("Đang xử lý tiền và loại bỏ số điện thoại trong đánh giá...")

    # 1. Xử lý biểu diễn tiền (500k, 1tr, ...)
    df_clean['money_text'] = df_clean['normalized_text'].apply(read_money_amount)
    money_mask = df_clean['money_text'] != ""
    df_clean.loc[money_mask, 'normalized_text'] = df_clean.loc[money_mask, 'money_text']
    money_converted = money_mask.sum()

    # 2. LOẠI BỎ SỐ ĐIỆN THOẠI - QUAN TRỌNG: LÀM SAU KHI XỬ LÝ TIỀN
    df_clean['normalized_text'] = df_clean['normalized_text'].apply(remove_phone_numbers)

    # 3. Lọc các đánh giá trở thành rỗng sau khi xử lý tiền + xóa SDT
    before_final_filter = len(df_clean)
    df_clean = df_clean[df_clean['normalized_text'].str.strip() != ""].copy()
    after_final_filter = len(df_clean)
    removed_after_processing = before_final_filter - after_final_filter

    print(f"✓ Đã chuyển {money_converted:,} đánh giá chứa tiền thành chữ")
    print(f"✓ Đã loại bỏ {removed_after_processing:,} đánh giá trở thành rỗng (chủ yếu là chỉ chứa SDT hoặc vô nghĩa sau xử lý)")

    # ==================== BƯỚC LOẠI TRÙNG USER + TIME ====================
    print("Đang loại bỏ đánh giá trùng lặp từ cùng người dùng trong thời gian gần...")

    USER_COLUMN = "review_name"        # Thay nếu tên cột khác
    TIME_COLUMN = "month_year"        # Thay nếu tên cột khác

    if USER_COLUMN in df_clean.columns and TIME_COLUMN in df_clean.columns:
        print(f"Tìm thấy cột user ('{USER_COLUMN}') và time ('{TIME_COLUMN}') → Thực hiện loại trùng")
        df_clean, dedup_stats = deduplicate_reviews_by_user_and_time(
            df=df_clean,
            user_column=USER_COLUMN,
            text_column="normalized_text",   # đã clean tiền + remove SDT, chưa segment
            time_column=TIME_COLUMN,
            time_window_days=30,
            keep="first"
        )
    else:
        missing = [col for col in [USER_COLUMN, TIME_COLUMN] if col not in df_clean.columns]
        print(f"Không tìm thấy cột: {', '.join(missing)} → BỎ QUA bước loại trùng theo user")
        dedup_stats = {
            "Trước khi loại trùng theo user + thời gian": f"{len(df_clean):,}",
            "Sau khi loại trùng": f"{len(df_clean):,}",
            "Số đánh giá bị loại do trùng lặp nội dung từ cùng người dùng trong 30 ngày": "0 (không có cột cần thiết)"
        }

    # Bước 10: Tách từ (word segmentation)
    df_clean = add_word_segmented_column(
        df=df_clean,
        input_column="normalized_text",
        output_column="word_segmented"
    )

    # Bước 11: Lọc chỉ giữ tiếng Việt
    before_vn_filter = len(df_clean)
    df_clean = df_clean[df_clean['is_vietnamese']].copy()
    after_vn_filter = len(df_clean)
    non_vietnamese_removed = before_vn_filter - after_vn_filter

    # Thêm STT
    df_clean = df_clean.reset_index(drop=True)
    df_clean.insert(0, 'stt', range(1, len(df_clean) + 1))

    # ==================== TỔNG HỢP THỐNG KÊ ====================
    final_count = len(df_clean)
    vietnamese_count = final_count

    display_stats = {
        "Tổng đánh giá trong dữ liệu": f"{total_reviews:,}",
        "Sau lọc điểm thấp": score_stats["Giữ lại sau lọc score"],
        "Loại bỏ do điểm thấp": score_stats["Loại bỏ do điểm thấp"],
        "Số đánh giá chứa emoji (đã làm sạch)": emoji_stats["Số đánh giá chứa emoji (đã làm sạch)"],
        "Số đánh giá được làm sạch repetitive": repetitive_stats["Số đánh giá được làm sạch repetitive"],
        "Loại bỏ do nội dung rỗng (sau clean ban đầu)": empty_stats["Loại bỏ do nội dung rỗng"],
        "Đánh giá được chuyển đổi từ biểu diễn tiền (500k → ... đồng)": f"{money_converted:,}",
        "Đánh giá bị loại vì chỉ chứa SDT hoặc trở thành rỗng sau xử lý": f"{removed_after_processing:,}",
        "Đánh giá tiếng Việt được phát hiện": f"{vietnamese_count:,} ({vietnamese_count/final_count:.2%} trong data sạch)",
        "Đánh giá cuối cùng (sau tất cả bước)": f"{final_count:,} ({final_count/total_reviews:.2%})",
    }

    # Thêm thống kê dedup
    display_stats.update(dedup_stats)

    print("\n" + "="*60)
    print("HOÀN THÀNH PIPELINE - THỐNG KÊ TỔNG QUÁT")
    print("="*60)
    for key, value in display_stats.items():
        print(f"{key}: {value}")
    print("="*60)

    return df_clean, display_stats