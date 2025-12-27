from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Sequence, Dict


def save_to_excel(
    df: pd.DataFrame,
    top_provinces_list: Sequence[tuple[str, int]],
    province_counts: Dict[str, int],
    filename: str | Path = "ket_qua_phan_tich.xlsx",
) -> None:
    """
    Xuất kết quả phân tích tỉnh/thành phố từ dữ liệu review ra file Excel đa sheet.

    Các sheet được tạo:
    - 'Data': Dữ liệu gốc đầy đủ (df)
    - 'Top_Provinces': Danh sách các tỉnh/thành có số lượng review cao nhất
    - 'All_Provinces': Toàn bộ tỉnh/thành và số lượng review (kể cả ít)
    - 'Summary': Thống kê tổng hợp (tổng review, tỷ lệ tiếng Việt, thời gian xuất file)

    Args:
        df: DataFrame chứa dữ liệu review đã xử lý (phải có cột 'is_vietnamese')
        top_provinces_list: Danh sách các tuple (province, count) đã được sắp xếp giảm dần
        province_counts: Dictionary {province: count} chứa số lượng review theo tỉnh
        filename: Tên hoặc đường dẫn file Excel đầu ra (mặc định "ket_qua_phan_tich.xlsx")

    Returns:
        None (chỉ lưu file và in thông báo)
    """
    filename = Path(filename)

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        # Sheet 1: Dữ liệu gốc
        df.to_excel(writer, sheet_name="Data", index=False)

        # Sheet 2: Top tỉnh/thành phố
        pd.DataFrame(
            top_provinces_list, columns=["province", "count"]
        ).to_excel(writer, sheet_name="Top_Provinces", index=False)

        # Sheet 3: Tất cả tỉnh/thành phố
        all_provinces_df = pd.DataFrame(
            list(province_counts.items()), columns=["province", "count"]
        )
        all_provinces_df.to_excel(writer, sheet_name="All_Provinces", index=False)

        # Sheet 4: Thống kê tổng hợp
        summary_data = [
            ["Tổng số review", len(df)],
            ["Số tỉnh/thành có review", len(province_counts)],
            ["Tỷ lệ review tiếng Việt", f"{df['is_vietnamese'].mean():.2%}"],
            ["Thời gian xuất file", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")],
        ]
        summary_df = pd.DataFrame(summary_data, columns=["Chỉ số", "Giá trị"])
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        # Tự động điều chỉnh độ rộng cột cho tất cả sheet (tùy chọn, giúp đọc dễ hơn)
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                    except Exception:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Giới hạn tối đa 50
                worksheet.column_dimensions[column_letter].width = adjusted_width

    print(f"Đã lưu kết quả phân tích tỉnh/thành phố vào file Excel: {filename}")