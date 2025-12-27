# utils/word_segmentation.py

from __future__ import annotations

import pandas as pd
from typing import Any

from underthesea import word_tokenize


def add_word_segmented_column(
    df: pd.DataFrame,
    input_column: str = "normalized_text",
    output_column: str = "word_segmented",
) -> pd.DataFrame:
    """
    Thêm cột chứa văn bản đã được tách từ tiếng Việt bằng underthesea.

    underthesea là thư viện tách từ tiếng Việt nhanh, chính xác cao và không cần Java.
    Sử dụng format="text" để trả về dạng phù hợp với PhoBERT/VinBERT:
        "khách sạn rất đẹp" → "khách_sạn rất đẹp"

    Args:
        df: DataFrame đầu vào.
        input_column: Tên cột chứa văn bản đã chuẩn hóa (mặc định "normalized_text").
        output_column: Tên cột mới sẽ được tạo (mặc định "word_segmented").

    Returns:
        DataFrame gốc với cột mới đã được thêm.

    Raises:
        ValueError: Nếu cột input_column không tồn tại trong DataFrame.
    """
    if input_column not in df.columns:
        raise ValueError(f"Cột '{input_column}' không tồn tại trong DataFrame.")

    print(
        f"Đang tách từ tiếng Việt bằng underthesea cho cột '{input_column}' → '{output_column}'..."
    )

    def segment_text(text: Any) -> str:
        """Tách từ an toàn cho một giá trị đơn lẻ."""
        if pd.isna(text) or text is None:
            return ""

        text_str = str(text).strip()
        if not text_str:
            return ""

        return word_tokenize(text_str, format="text")

    # Áp dụng tách từ
    df[output_column] = df[input_column].apply(segment_text)

    total_rows = len(df)
    empty_after = (df[output_column] == "").sum()

    print(f"Tách từ hoàn tất: {total_rows:,} dòng xử lý.")
    if empty_after > 0:
        print(f"   → {empty_after:,} dòng rỗng sau tách từ (do input rỗng hoặc NaN).")
    else:
        print("   → Không có dòng rỗng sau tách từ.")

    return df