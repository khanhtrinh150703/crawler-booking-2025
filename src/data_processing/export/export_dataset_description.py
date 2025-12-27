from pathlib import Path
import pandas as pd

def export_dataset_description_to_excel(
    df: pd.DataFrame,
    output_folder: str = "output/analysis_results",
    filename: str = "Mô_tả_dataset_1.xlsx"
):
    """
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame đã được tiền xử lý, phải chứa ít nhất các cột:
        - 'score' hoặc 'rating' (điểm số)
        - 'positive_comment'
        - 'combined_text'
        - 'room_type'
        - 'group_type'
        - 'stay_duration'
    output_folder : str, default "output/analysis_results"
        Thư mục lưu file Excel kết quả
    filename : str, default "Mô_tả_dataset_1.xlsx"
        Tên file Excel đầu ra (nên giữ đuôi .xlsx)

    Returns
    -------
    None
        Chỉ tạo file Excel tại đường dẫn chỉ định.
    """
    output_path = Path(output_folder) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total = len(df)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # ─────────────────────── Sheet 1: Tổng quan ───────────────────────
        overview_data = {
            "Tiêu chí": [
                "Tổng số đánh giá (sau lọc tiếng Việt)",
                "Số lượng cột",
                "Điểm trung bình",
                "Độ dài trung bình đánh giá tổng quan",
                "Độ dài trung bình bình luận tích cực",
                "Độ dài trung bình văn bản kết hợp (dùng cho DL)"
            ],
            "Giá trị": [
                f"{total:,}",
                len(df.columns),
                f"{df['score'].mean():.2f}/10",
                f"{df['rating'].str.len().mean():.1f} ký tự",
                f"{df['positive_comment'].str.len().mean():.1f} ký tự",
                f"{df['combined_text'].str.len().mean():.1f} ký tự"
            ]
        }
        pd.DataFrame(overview_data).to_excel(writer, sheet_name='Tổng quan', index=False)

        # ─────────────────────── Sheet 2: Thông tin chung  ───────────────────────
        info_lines = [
            ["Dataset sau khi lọc tiếng Việt và làm sạch"],
            [""],
            ["Số lượng bản ghi:", f"{total:,}"],
            ["Số lượng cột:", len(df.columns)],
            [""],
            ["Các cột hiện có:"],
        ]
        info_lines.extend([f"• {col} ({dtype})" for col, dtype in df.dtypes.items()])

        # Tạo DataFrame đúng cách (1 cột duy nhất)
        info_df = pd.DataFrame({"Mô tả": info_lines})
        info_df.to_excel(writer, sheet_name='Thông tin chung', index=False)

        # ─────────────────────── Sheet 3: Thống kê số ───────────────────────
        df.describe().round(2).to_excel(writer, sheet_name='Thống kê số')

        # ─────────────────────── Sheet 4: Phân bố điểm số ───────────────────────
        score_dist = df['score'].value_counts().sort_index()
        score_df = pd.DataFrame({
            'Điểm số': score_dist.index,
            'Số lượng': score_dist.values,
            'Tỷ lệ (%)': (score_dist.values / total * 100).round(2)
        })
        score_df.to_excel(writer, sheet_name='Phân bố điểm số', index=False)

        # ─────────────────────── Sheet 5: Loại phòng (Top 20) ───────────────────────
        room_top = df['room_type'].value_counts().head(20)
        room_df = pd.DataFrame({
            'Loại phòng': room_top.index,
            'Số lượng': room_top.values,
            'Tỷ lệ (%)': (room_top.values / total * 100).round(2)
        })
        room_df.to_excel(writer, sheet_name='Loại phòng (Top 20)', index=False)

        # ─────────────────────── Sheet 6: Nhóm & Lưu trú ───────────────────────
        group_dist = df['group_type'].value_counts()
        stay_dist = df['stay_duration'].value_counts().head(15)

        max_rows = max(len(group_dist), len(stay_dist))
        summary = pd.DataFrame({
            'Loại nhóm': list(group_dist.index) + [""] * (max_rows - len(group_dist)),
            'Số lượng (nhóm)': [f"{val:,} ({val/total*100:.2f}%)" for val in group_dist.values] + [""] * (max_rows - len(group_dist)),
            'Thời gian lưu trú': list(stay_dist.index) + [""] * (max_rows - len(stay_dist)),
            'Số lượng (lưu trú)': [f"{val:,} ({val/total*100:.2f}%)" for val in stay_dist.values] + [""] * (max_rows - len(stay_dist))
        })
        summary.to_excel(writer, sheet_name='Nhóm & Lưu trú', index=False)

        # Auto-resize tất cả các sheet
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value or "")) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 60)
                ws.column_dimensions[column_letter].width = adjusted_width
