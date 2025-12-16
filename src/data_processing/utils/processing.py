# src/data_processing/utils/processing.py

import re
import unicodedata
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Callable
from pathlib import Path
from langdetect import detect, LangDetectException
from underthesea import word_tokenize
from sklearn.preprocessing import LabelEncoder

from config.config import (
    EMOJI_PATTERN,
    VIETNAMESE_CHARS,
    VIETNAMESE_WORDS,
    NON_VIETNAMESE_LANGS,
    FOREIGN_WORDS
)


def contains_emoji(text: str) -> bool:
    return bool(EMOJI_PATTERN.search(text or ""))


def contains_foreign_words(text: str) -> bool:
    if not text or not text.strip():
        return False
    words = re.findall(r'\b\w+\b', text.lower())
    foreign_count = sum(w in FOREIGN_WORDS for w in words)
    return foreign_count > 0 and (foreign_count / len(words) > 0.2)


def normalize_stay_duration(duration: str) -> str:
    if not duration or not isinstance(duration, str):
        return ""
    match = re.search(r'(\d+)\s*đêm', duration.lower())
    return f"{match.group(1)} đêm" if match else duration.strip()


def is_vietnamese_improved(text: str, country: str = None) -> bool:
    if not text or not text.strip():
        return False

    is_vn_country = country and "vietnam" in str(country).lower()

    if is_vn_country and len(text.strip()) >= 5:
        if any(c.lower() in VIETNAMESE_CHARS.lower() for c in text):
            return True

    if len(text.strip()) < 15:
        return False
    if contains_foreign_words(text):
        return False

    cleaned = EMOJI_PATTERN.sub('', text)
    cleaned = re.sub(r'[^\w\sàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóọỏõôồốộổỗơờớợởỡùúủũụưừứựửữỳýỷỹỵđ]', ' ', cleaned)

    if len(cleaned.strip()) < 15:
        return False

    text_lower = text.lower()
    vn_word_hits = sum(word in text_lower for word in VIETNAMESE_WORDS)
    if vn_word_hits >= 2:
        return True

    vn_char_count = sum(c.lower() in VIETNAMESE_CHARS.lower() for c in text_lower)
    if vn_char_count >= 6:
        return True
    if vn_char_count / len(text.replace(" ", "")) > 0.15:
        return True

    try:
        lang = detect(text)
        if lang == 'vi' and vn_char_count == 0:
            return False
        if lang in NON_VIETNAMESE_LANGS and vn_char_count <= 5:
            return False
        return lang == 'vi'
    except:
        return vn_char_count >= 6


def normalize_vietnamese_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize('NFC', text)
    text = EMOJI_PATTERN.sub('', text)
    text = re.sub(r'[^\w\s\.\,\;\:\?\!àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóọỏõôồốộổỗơờớợởỡùúủũụưừứựửữỳýỷỹỵđ]', ' ', text)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^\s*-\s*', '', text)
    return text


def check_repetitive(text: str) -> bool:
    if not text or len(text) < 5:
        return True
    return any(text.count(c) > len(text) * 0.7 for c in set(text))


def create_combined_text(df: pd.DataFrame, cols=['rating', 'positive_comment']) -> pd.DataFrame:
    df = df.copy()
    df['combined_text'] = df[cols].fillna('').agg(' '.join, axis=1).str.strip()
    df['combined_text'] = df['combined_text'].replace('', np.nan)
    return df


def filter_high_quality_reviews(df: pd.DataFrame, min_len: int = 5) -> pd.DataFrame:
    df = df.copy()

    # Loại bỏ hoàn toàn trống
    df = df.dropna(subset=['rating', 'positive_comment'], how='all')
    df = df[~((df['rating'].str.strip() == '') & (df['positive_comment'].str.strip() == ''))]

    df = df[~((df['rating'].str.len() < min_len) & (df['positive_comment'].str.len() < min_len))]

    df = df[df.apply(lambda r: is_vietnamese_improved(r['rating'], r.get('country')) or
                                 is_vietnamese_improved(r['positive_comment'], r.get('country')), axis=1)]

    df = df[~(df.apply(lambda r: contains_foreign_words(r['rating']) and
                                   contains_foreign_words(r['positive_comment']), axis=1))]

    df = df[~(df.apply(lambda r: check_repetitive(r['rating']) and
                                   check_repetitive(r['positive_comment']), axis=1))]

    print(f"→ Sau lọc chất lượng cao: {len(df):,} bản ghi")
    return df.reset_index(drop=True)


def encode_metadata_columns(df: pd.DataFrame) -> Tuple[Dict, pd.DataFrame]:
    df = df.copy()
    encodings = {}

    le =LabelEncoder()
    df['room_type_id'] = le.fit_transform(df['room_type'].fillna('Unknown'))
    encodings['room_type'] = {k: int(v) for k, v in zip(le.classes_, le.transform(le.classes_))}

    le = LabelEncoder()
    df['group_type_id'] = le.fit_transform(df['group_type'].fillna('Unknown'))
    encodings['group_type'] = {k: int(v) for k, v in zip(le.classes_, le.transform(le.classes_))}

    def extract_nights(x):
        if pd.isna(x): return -1
        m = re.search(r'(\d+)\s*đêm', str(x).lower())
        return int(m.group(1)) if m else -1

    df['stay_duration_nights'] = df['stay_duration'].apply(extract_nights)
    unique = df[['stay_duration', 'stay_duration_nights']].drop_duplicates().sort_values('stay_duration_nights')
    mapping = {}
    for _, row in unique.iterrows():
        mapping[row['stay_duration']] = row['stay_duration_nights'] if row['stay_duration_nights'] >= 0 else len(mapping)
    df['stay_duration_id'] = df['stay_duration'].map(mapping)
    encodings['stay_duration'] = mapping

    return encodings, df


def process_reviews_dataframe(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict, Dict]:
    if df_raw.empty:
        raise ValueError("Không có dữ liệu đầu vào! DataFrame rỗng.")

    print(f"Nhận vào: {len(df_raw):,} đánh giá thô")

    df = df_raw.copy()
    df[['rating', 'positive_comment', 'room_type', 'stay_duration', 'group_type', 'country']] = df[
        ['rating', 'positive_comment', 'room_type', 'stay_duration', 'group_type', 'country']].fillna('')

    df = filter_high_quality_reviews(df)
    df = create_combined_text(df)
    encodings, df = encode_metadata_columns(df)

    stats = {
        "total_reviews": len(df_raw),
        "kept_count_vn": len(df),
        "filtered_out": len(df_raw) - len(df),
    }

    print(f"HOÀN TẤT XỬ LÝ → {len(df):,} đánh giá chất lượng cao")
    return df, stats, encodings

# ===================================================================
# CÁC HÀM TƯƠNG THÍCH CŨ – ĐỂ KHÔNG LỖI IMPORT Ở BẤT KỲ FILE NÀO
# ===================================================================

def is_vietnam(x):
    """Kiểm tra country có phải Việt Nam không – dùng cho filter cũ"""
    if not isinstance(x, str):
        return False
    x_clean = unicodedata.normalize('NFC', x.strip().lower())
    return x_clean in ['việt nam', 'vietnam', 'viet nam', 'vn']


def is_vietnamese(text, country=None):
    """Giữ tương thích hoàn toàn với code cũ"""
    return is_vietnamese_improved(text, country)


def preprocess_vietnamese_text(text: str) -> str:
    """Tiền xử lý cho wordcloud / embedding – fallback an toàn"""
    if not isinstance(text, str) or not text.strip():
        return ""
    try:
        from underthesea import word_tokenize
        tokens = word_tokenize(text.lower())
        stop_words = {'là', 'của', 'và', 'có', 'được', 'ở', 'tôi', 'mình', 'rất', 'khá',
                      'nhiều', 'với', 'từ', 'trong', 'này', 'đó', 'khi', 'thì', 'mà', 'nhưng'}
        tokens = [t for t in tokens if len(t) > 1 and t.isalpha() and t not in stop_words]
        return " ".join(tokens)
    except:
        import re
        text = re.sub(r'[^a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõôốồổỗơớờởỡùúủũụưừứựửữỳýỷỹỵđ\s]', ' ', text.lower())
        words = [w for w in text.split() if len(w) > 1]
        return " ".join(words)