# export/export_for_dl.py
import numpy as np
from pathlib import Path
import pandas as pd

def export_for_deep_learning(
    df: pd.DataFrame,
    text_column: str = "processed_text",
    label_column: str = "score",
    output_dir: str | Path = "outputs/dl_ready",
    prefix: str = "booking_review"
) -> dict:
    """
    Xuất dữ liệu đã xử lý sạch thành 2 file .txt chuẩn cho Deep Learning:
    - {prefix}_labels.txt → nhãn (score)
    - {prefix}_texts.txt  → văn bản đã tiền xử lý
    
    Parameters:
    - df: DataFrame đã được lọc và xử lý (có processed_text)
    - text_column: cột chứa văn bản đã xử lý
    - label_column: cột chứa điểm số (nhãn)
    - output_dir: thư mục lưu
    - prefix: tiền tố tên file
    
    Returns:
        dict chứa đường dẫn 2 file đã xuất
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    labels_path = output_dir / f"{prefix}_labels.txt"
    texts_path = output_dir / f"{prefix}_texts.txt"
    
    # print("\n" + "═" * 65)
    # print("      XUẤT DỮ LIỆU CHO MÔ HÌNH DEEP LEARNING")
    # print("═" * 65)
    
    if text_column not in df.columns:
        raise ValueError(f"Cột '{text_column}' không tồn tại trong DataFrame!")
    if label_column not in df.columns:
        raise ValueError(f"Cột '{label_column}' không tồn tại trong DataFrame!")
    
    # Làm sạch dữ liệu lần cuối
    df_clean = df[[text_column, label_column]].dropna().copy()
    df_clean = df_clean[df_clean[text_column].str.strip() != ""]
    
    if len(df_clean) == 0:
        raise ValueError("Không còn dữ liệu sau khi làm sạch! Kiểm tra processed_text.")
    
    total = len(df_clean)
    print(f"   • Số mẫu cuối cùng: {total:,} đánh giá")
    
    # Xuất file labels (score)
    try:
        np.savetxt(labels_path, df_clean[label_column].values, fmt='%g')
        print(f"   NHÃN: {labels_path.name}")
        print(f"         → {total:,} nhãn (điểm từ 1-10)")
    except Exception as e:
        raise RuntimeError(f"Lỗi khi xuất file nhãn: {e}")
    
    # Xuất file texts (processed_text)
    try:
        # Dùng np.savetxt nhưng đảm bảo mỗi dòng là 1 văn bản
        texts = df_clean[text_column].astype(str).values
        np.savetxt(texts_path, texts, fmt='%s', encoding='utf-8')
        print(f"   VĂN BẢN: {texts_path.name}")
        print(f"         → {total:,} câu đã tiền xử lý")
    except Exception as e:
        raise RuntimeError(f"Lỗi khi xuất file văn bản: {e}")
    
    # In tóm tắt
    score_dist = df_clean[label_column].value_counts().sort_index()
    print(f"   Phân bố điểm số:")
    for score, count in score_dist.items():
        print(f"      • Điểm {score}: {count:,} ({count/total*100:.1f}%)")
    
    print("═" * 65)
    print(f"HOÀN TẤT! Dữ liệu đã sẵn sàng cho BERT, PhoBERT, vGPT...")
    print(f"Thư mục: {output_dir.resolve()}")
    print("═" * 65)
    
    return {
        "labels_file": str(labels_path),
        "texts_file": str(texts_path),
        "total_samples": total,
        "output_dir": str(output_dir)
    }