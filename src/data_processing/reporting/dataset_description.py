# src/reporting/dataset_description.py
import pandas as pd
from pathlib import Path


def describe_dataset(
    df: pd.DataFrame,
    output_folder: str = "outputs/analysis_results",
    excel_filename: str = "Mô_tả_Dataset_2.xlsx"
) -> Path:
    """
    In toàn bộ phần mô tả dataset ra console (đẹp như notebook)
    và lưu tất cả thống kê vào file Excel (5 sheet dễ đọc).
    
    Returns:
        Đường dẫn file Excel đã lưu
    """
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    excel_path = Path(output_folder) / excel_filename

    # Tạo các DataFrame để lưu Excel
    sheets = {}

    print("\n" + "="*70)
    print("        3. MÔ TẢ VÀ ĐÁNH GIÁ DATASET")
    print("="*70)

    # 1. Thông tin chung
    print("\nThông tin chung về dataset:")
    df.info()
    sheets["Thông tin chung"] = pd.DataFrame({"Description": [
        f"Số mẫu: {len(df):,}",
        f"Số cột: {len(df.columns)}",
        f"Cột có giá trị thiếu: {df.isna().any().sum()} cột",
        f"Bộ nhớ sử dụng: ~{df.memory_usage(deep=True).sum() / 1024**2:.1f} MB"
    ]})

    # 2. Thống kê số
    print("\nThống kê mô tả cho các trường số:")
    desc_num = df.describe()
    print(desc_num)
    sheets["Thống kê số"] = desc_num

    # 3. Phân bố điểm số
    print("\nPhân bố điểm số:")
    score_counts = df['score'].value_counts().sort_index()
    score_data = []
    for score, count in score_counts.items():
        pct = count / len(df) * 100
        print(f"Điểm {score}: {count:,} đánh giá ({pct:.2f}%)")
        score_data.append({"Điểm số": score, "Số lượng": count, "Tỷ lệ (%)": round(pct, 2)})
    sheets["Phân bố điểm số"] = pd.DataFrame(score_data)

    # 4. Top 10 loại phòng
    print("\nTop 10 loại phòng phổ biến:")
    room_counts = df['room_type'].value_counts().head(10)
    room_data = []
    for room, count in room_counts.items():
        pct = count / len(df) * 100
        print(f"{room}: {count:,} đánh giá ({pct:.2f}%)")
        room_data.append({"Loại phòng": room, "Số lượng": count, "Tỷ lệ (%)": round(pct, 2)})
    sheets["Top 10 loại phòng"] = pd.DataFrame(room_data)

    # 5. Loại nhóm
    print("\nPhân bố loại nhóm:")
    group_counts = df['group_type'].value_counts()
    group_data = []
    for group, count in group_counts.items():
        pct = count / len(df) * 100
        print(f"{group}: {count:,} đánh giá ({pct:.2f}%)")
        group_data.append({"Loại nhóm": group, "Số lượng": count, "Tỷ lệ (%)": round(pct, 2)})
    sheets["Phân bố loại nhóm"] = pd.DataFrame(group_data)

    # 6. Thời gian lưu trú (top 10)
    print("\nThống kê thời gian lưu trú (Top 10):")
    stay_counts = df['stay_duration'].value_counts().head(10)
    stay_data = []
    for stay, count in stay_counts.items():
        pct = count / len(df) * 100
        print(f"{stay}: {count:,} đánh giá ({pct:.2f}%)")
        stay_data.append({"Thời gian lưu trú": stay, "Số lượng": count, "Tỷ lệ (%)": round(pct, 2)})
    sheets["Top 10 thời gian lưu trú"] = pd.DataFrame(stay_data)

    # 7. Độ dài văn bản
    df_temp = df.copy()
    df_temp['rating_length'] = df_temp['rating'].str.len()
    df_temp['positive_length'] = df_temp['positive_comment'].str.len()
    df_temp['combined_length'] = df_temp['combined_text'].str.len()

    avg_rating = df_temp['rating_length'].mean()
    avg_positive = df_temp['positive_length'].mean()
    avg_combined = df_temp['combined_length'].mean()

    # print("\nThống kê độ dài văn bản:")
    # print(f"Độ dài trung bình đánh giá tổng quan: {avg_rating:.2f} ký tự")
    # print(f"Độ dài trung bình bình luận tích cực: {avg_positive:.2f} ký tự")
    # print(f"Độ dài trung bình văn bản kết hợp: {avg_combined:.2f} ký tự")

    sheets["Độ dài văn bản"] = pd.DataFrame({
        "Mô tả": [
            "Đánh giá tổng quan (rating)",
            "Bình luận tích cực",
            "Văn bản kết hợp (combined_text)"
        ],
        "Độ dài trung bình (ký tự)": [round(avg_rating, 2), round(avg_positive, 2), round(avg_combined, 2)]
    })

    # LƯU EXCEL (5 sheet đẹp, tự động điều chỉnh độ rộng cột)
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for sheet_name, data in sheets.items():
            data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Auto resize cột
            worksheet = writer.sheets[sheet_name]
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 50)

    # print("\n" + "="*70)
    # print(f"HOÀN TẤT! Đã lưu toàn bộ mô tả dataset vào:")
    # print(f"   📊 Excel: {excel_path}")
    # print(f"   Sheets: Thông tin chung • Thống kê số • Phân bố điểm số • Top 10 loại phòng")
    # print(f"           Phân bố loại nhóm • Top 10 thời gian lưu trú • Độ dài văn bản")
    # print("="*70)

    return excel_path