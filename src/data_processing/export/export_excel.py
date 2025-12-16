import json
import pandas as pd

def save_to_excel(df, top_provinces_list, province_counts, filename="ket_qua_phan_tich.xlsx"):
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Sheet 1: Dữ liệu gốc
        df.to_excel(writer, sheet_name='Data', index=False)
        
        # Sheet 2: Top tỉnh/thành
        pd.DataFrame(top_provinces_list, columns=['province', 'count']).to_excel(
            writer, sheet_name='Top_Provinces', index=False
        )
        
        # Sheet 3: Tất cả tỉnh/thành
        pd.DataFrame(list(province_counts.items()), columns=['province', 'count']).to_excel(
            writer, sheet_name='All_Provinces', index=False
        )
        
        # Sheet 4: Thống kê tổng hợp
        summary_df = pd.DataFrame([
            ["Tổng số review", len(df)],
            ["Tỷ lệ tiếng Việt", f"{df['is_vietnamese'].mean():.2%}"],
            ["Thời gian xử lý", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")]
        ], columns=["Chỉ số", "Giá trị"])
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"Đã lưu tất cả vào file Excel: {filename}")