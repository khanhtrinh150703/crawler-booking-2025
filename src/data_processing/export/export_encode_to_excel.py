# export/export_encode_to_excel.py
import pandas as pd
from pathlib import Path
from typing import Dict, Any


def save_encodings_to_excel(
    encodings: Dict[str, Any],
    output_folder: str = "outputs",
    stay_duration_mapping: Dict[str, Any] | None = None,
    filename: str = "Mã_hóa_dữ_liệu.xlsx"
) -> Path:
    """
    Lưu 3 bảng mã hóa vào 1 file Excel với 3 sheet riêng biệt (có tiếng Việt, auto resize cột).

    Parameters:
    - encodings: dict từ encode_metadata_columns() → có 'room_type', 'group_type', 'stay_duration'
    - output_folder: thư mục lưu
    - stay_duration_mapping: nếu truyền riêng thì dùng cái này (tùy chọn)
    - filename: tên file Excel

    Returns:
        Path: đường dẫn file đã lưu
    """
    output_path = Path(output_folder) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Nếu không truyền stay_duration_mapping → lấy từ encodings
    if stay_duration_mapping is None:
        stay_duration_mapping = encodings.get("stay_duration", {})

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # ── Sheet 1: Loại phòng ──
        room_df = pd.DataFrame([
            {"ID": idx, "Loại phòng": label}
            for label, idx in sorted(encodings.get("room_type", {}).items(), key=lambda x: x[1])
        ])
        room_df.to_excel(writer, sheet_name="Loại phòng", index=False)

        # ── Sheet 2: Loại nhóm ──
        group_df = pd.DataFrame([
            {"ID": idx, "Loại nhóm": label}
            for label, idx in sorted(encodings.get("group_type", {}).items(), key=lambda x: x[1])
        ])
        group_df.to_excel(writer, sheet_name="Loại nhóm", index=False)

        # ── Sheet 3: Thời gian lưu trú ──
        stay_df = pd.DataFrame([
            {"ID": nid, "Thời gian lưu trú": duration}
            for duration, nid in sorted(stay_duration_mapping.items(), key=lambda x: x[1])
        ])
        stay_df.to_excel(writer, sheet_name="Thời gian lưu trú", index=False)

        # Auto resize cột cho đẹp khi mở Excel
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column_cells in worksheet.columns:
                max_length = 0
                column_letter = column_cells[0].column_letter
                for cell in column_cells:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # giới hạn tối đa 50
                worksheet.column_dimensions[column_letter].width = adjusted_width

    # # In log đẹp như báo cáo
    # print(f"\nĐã lưu bảng mã hóa dữ liệu thành công!")
    # print(f"   File: {output_path}")
    # print(f"   Sheet: Loại phòng | Loại nhóm | Thời gian lưu trú")
    # print(f"   Tổng: {len(room_df)} phòng • {len(group_df)} nhóm • {len(stay_df)} thời gian")

    return output_path