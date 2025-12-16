# utils/text_preparation.py hoặc visualization/text_utils.py
import pandas as pd
import re
from typing import Callable, List

def prepare_text_for_wordcloud(
    df: pd.DataFrame,
    text_column: str = "combined_text",
    positive_comment_column: str = "positive_comment",
    preprocess_func: Callable[[str], str] | None = None,
    min_positive_length: int = 5,
    min_processed_length: int = 1,
    vietnamese_stopwords: List[str] | None = None
) -> tuple[pd.DataFrame, str]:
    """
    Tiền xử lý văn bản tiếng Việt để tạo Word Cloud.
    
    Parameters:
    - df: DataFrame đầu vào
    - text_column: cột chứa văn bản gốc (combined_text)
    - positive_comment_column: cột bình luận tích cực (dùng để lọc chất lượng)
    - preprocess_func: hàm tiền xử lý (word_tokenize + loại stopword)
    - min_positive_length: độ dài tối thiểu của positive_comment (sau khi strip)
    - min_processed_length: độ dài tối thiểu của văn bản sau xử lý
    - vietnamese_stopwords: danh sách stopwords (nếu không dùng preprocess_func)
    
    Returns:
    - df_filtered: DataFrame đã lọc sạch
    - all_text: chuỗi văn bản đã xử lý để tạo word cloud
    """
    df = df.copy()
    
    print("\nBắt đầu tiền xử lý văn bản cho Word Cloud...")
    print(f"   • Dữ liệu ban đầu: {len(df):,} bản ghi")

    # 1. Tiền xử lý văn bản
    if preprocess_func is not None:
        df['processed_text'] = df[text_column].apply(preprocess_func)
    else:
        # Fallback đơn giản nếu không có hàm preprocess
        def simple_preprocess(text):
            if not isinstance(text, str):
                return ""
            text = text.lower()
            if vietnamese_stopwords:
                pattern = r'\b(' + '|'.join(map(re.escape, vietnamese_stopwords)) + r')\b'
                text = re.sub(pattern, '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        df['processed_text'] = df[text_column].apply(simple_preprocess)

    # 2. Lọc dữ liệu chất lượng cao
    mask1 = (
        df[positive_comment_column].notna() & 
        (df[positive_comment_column].str.strip().str.len() > min_positive_length)
    )
    
    mask2 = (
        df['processed_text'].notna() & 
        (df['processed_text'].str.strip().str.len() > min_processed_length)
    )
    
    df_filtered = df[mask1 & mask2].copy()
    df_filtered.reset_index(drop=True, inplace=True)

    before = len(df)
    after = len(df_filtered)
    removed = before - after

    print(f"   • Sau khi lọc chất lượng: {after:,} bản ghi (loại bỏ {removed:,} ~ {removed/before*100:.1f}%)")

    # 3. Ghép văn bản
    all_text = " ".join(df_filtered['processed_text'].dropna())

    # 4. Fallback nếu rỗng
    if not all_text.strip():
        print("   Cảnh báo: Văn bản sau xử lý bị rỗng → dùng fallback đơn giản...")
        raw_text = " ".join(df[text_column].dropna().astype(str))
        if vietnamese_stopwords:
            pattern = r'\b(' + '|'.join(map(re.escape, vietnamese_stopwords)) + r')\b'
            raw_text = re.sub(pattern, ' ', raw_text)
        all_text = re.sub(r'\s+', ' ', raw_text).strip()

    if all_text.strip():
        print(f"   Thành công: Đã chuẩn bị {len(all_text.split()):,} từ cho Word Cloud")
    else:
        print("   Lỗi: Không thể tạo văn bản cho Word Cloud!")

    return df_filtered, all_text