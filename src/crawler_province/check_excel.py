import pandas as pd
import os

def xu_ly_du_lieu_khach_san(file_excel_1, file_excel_2, ten_cot_khach_san='Tên Khách Sạn', ten_file_dau_ra='Ket_Qua_So_Sanh_Khach_San.xlsx'):
    """
    Đọc hai tệp Excel, so sánh dựa trên cột tên khách sạn, 
    và lưu kết quả vào một tệp Excel mới với hai sheet:
    1. Khách sạn chung tên (có trong cả 2 file).
    2. Khách sạn khác tên (chỉ có trong 1 trong 2 file).

    Args:
        file_excel_1 (str): Đường dẫn đến tệp Excel thứ nhất.
        file_excel_2 (str): Đường dẫn đến tệp Excel thứ hai.
        ten_cot_khach_san (str): Tên cột chứa tên khách sạn.
        ten_file_dau_ra (str): Tên của tệp Excel đầu ra.
    """
    
    # --- 1. Đọc Dữ Liệu ---
    try:
        df1 = pd.read_excel(file_excel_1)
        df2 = pd.read_excel(file_excel_2)
    except FileNotFoundError as e:
        print(f"Lỗi: Không tìm thấy tệp {e.filename}. Vui lòng kiểm tra lại đường dẫn.")
        return
    except Exception as e:
        print(f"Lỗi khi đọc tệp Excel: {e}")
        return

    # Chuẩn hóa tên cột để tránh lỗi so sánh (ví dụ: loại bỏ khoảng trắng thừa)
    cot_chuan_hoa = ten_cot_khach_san.strip()
    
    # Kiểm tra cột bắt buộc
    if cot_chuan_hoa not in df1.columns or cot_chuan_hoa not in df2.columns:
        print(f"Lỗi: Một trong hai tệp không có cột '{ten_cot_khach_san}'.")
        return

    # --- 2. Xử Lý và So Sánh Dữ Liệu ---
    
    # Lấy danh sách tên khách sạn từ mỗi DataFrame, chuẩn hóa tên (chuyển về chữ thường, loại bỏ khoảng trắng) 
    # để đảm bảo so sánh chính xác ngay cả khi có lỗi chính tả nhỏ về chữ hoa/thường.
    df1['KEY'] = df1[cot_chuan_hoa].astype(str).str.lower().str.strip()
    df2['KEY'] = df2[cot_chuan_hoa].astype(str).str.lower().str.strip()

    # Tên khách sạn chỉ có trong file 1
    ten_chi_file_1 = set(df1['KEY']) - set(df2['KEY'])
    # Tên khách sạn chỉ có trong file 2
    ten_chi_file_2 = set(df2['KEY']) - set(df1['KEY'])
    # Tên khách sạn có trong cả 2 file
    ten_chung = set(df1['KEY']) & set(df2['KEY'])

    # --- 3. Tạo DataFrames Kết Quả ---

    # 3.1. Khách Sạn Chung Tên (Sheet 1)
    
    # Lọc các hàng có tên khách sạn chung trong cả 2 file gốc
    df_chung_1 = df1[df1['KEY'].isin(ten_chung)].copy()
    df_chung_2 = df2[df2['KEY'].isin(ten_chung)].copy()
    
    # Đổi tên cột để dễ phân biệt nguồn gốc
    df_chung_1 = df_chung_1.rename(columns={'Tổng Reviews Cao Được': 'Tổng Reviews Cao Được (File 1)'})
    df_chung_2 = df_chung_2.rename(columns={'Tổng Reviews Cao Được': 'Tổng Reviews Cao Được (File 2)'})

    # Ghép dữ liệu chung lại với nhau
    df_chung = pd.merge(
        df_chung_1.drop(columns=['File Path', 'Tên File']), 
        df_chung_2.drop(columns=['File Path', 'Tên File']), 
        on=['KEY', cot_chuan_hoa], 
        how='outer'
    )
    df_chung = df_chung.drop(columns=['KEY'])
    
    # Sắp xếp theo tên khách sạn
    df_chung = df_chung.sort_values(by=cot_chuan_hoa)

    # 3.2. Khách Sạn Khác Tên (Sheet 2)

    # Lọc các hàng chỉ có trong File 1 hoặc File 2
    df_khac_1 = df1[df1['KEY'].isin(ten_chi_file_1)].copy()
    df_khac_2 = df2[df2['KEY'].isin(ten_chi_file_2)].copy()

    # Thêm cột nguồn gốc
    df_khac_1['Nguồn'] = os.path.basename(file_excel_1)
    df_khac_2['Nguồn'] = os.path.basename(file_excel_2)

    # Ghép 2 DataFrame lại
    df_khac = pd.concat([df_khac_1, df_khac_2], ignore_index=True)
    df_khac = df_khac.drop(columns=['KEY'])
    
    # Sắp xếp theo tên khách sạn và nguồn
    df_khac = df_khac.sort_values(by=['Nguồn', cot_chuan_hoa])

    # --- 4. Ghi Kết Quả vào Tệp Excel Mới ---

    print(f"Đang ghi kết quả vào tệp: {ten_file_dau_ra}...")

    try:
        # Sử dụng pd.ExcelWriter để ghi nhiều DataFrame vào các sheet khác nhau
        with pd.ExcelWriter(ten_file_dau_ra, engine='openpyxl') as writer:
            # Sheet 1: Khách sạn có chung tên
            df_chung.to_excel(writer, sheet_name='1. KS Chung Tên', index=False)
            
            # Sheet 2: Khách sạn có khác tên (chỉ có trong 1 file)
            df_khac.to_excel(writer, sheet_name='2. KS Khác Tên', index=False)

        print("✅ Xử lý hoàn tất!")
        print(f"Kết quả đã được lưu tại: {os.path.abspath(ten_file_dau_ra)}")
        print(f" - Sheet '1. KS Chung Tên': Có {len(df_chung)} khách sạn chung tên.")
        print(f" - Sheet '2. KS Khác Tên': Có {len(df_khac)} khách sạn khác tên.")

    except Exception as e:
        print(f"Lỗi khi ghi tệp Excel đầu ra: {e}")

# --- 5. Ví dụ Sử Dụng (Bạn cần thay đổi tên file này) ---

# Giả sử tên 2 file excel của bạn là 'data_file_1.xlsx' và 'data_file_2.xlsx'
FILE_1 = r'D:\private\crawler-booking-2025\src\crawler_hotel\crawler\output_2023\excel\REPORT_HOTELS_FULL.xlsx' 
FILE_2 = r"D:\private\crawler-booking-2025\src\crawler_hotel\crawler\output_2025\excel\REPORT_HOTELS_FULL_2025.xlsx"
OUTPUT_FILE = r'D:\private\crawler-booking-2025\src\crawler_hotel\crawler\So_Sanh_Khach_San_Final.xlsx'

# Gọi hàm để thực thi
# Lưu ý: Trước khi chạy, bạn phải đảm bảo đã cài đặt thư viện 'pandas' và 'openpyxl':
# pip install pandas openpyxl
# và hai file Excel ('data_file_1.xlsx', 'data_file_2.xlsx') nằm cùng thư mục với script này
# hoặc bạn phải cung cấp đường dẫn đầy đủ.
xu_ly_du_lieu_khach_san(FILE_1, FILE_2, ten_file_dau_ra=OUTPUT_FILE)

