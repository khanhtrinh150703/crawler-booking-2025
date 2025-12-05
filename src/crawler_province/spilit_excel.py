import pandas as pd
import os

# 1. Định nghĩa tên file và sheet
file_excel = r'D:\private\crawler-booking-2025\src\crawler_hotel\crawler\So_Sanh_Khach_San_Final.xlsx' # Thay thế bằng tên file Excel thực tế
sheet_name = '2. KS Khác Tên' 

# Tên cột trong file Excel
cot_nguon = 'Nguồn'
cot_file_path = 'File Path'

# Cấu hình xử lý chuỗi
nguon_can_loc = r"REPORT_HOTELS_FULL.xlsx"
url_booking_base = 'https://www.booking.com/hotel/vn/'
url_booking_suffix = '.vi.html'
file_path_delimiter = '/'

# 🆕 THƯ MỤC CHỨA KẾT QUẢ
output_directory = 'D:\private\crawler-booking-2025\src\crawler_province\links_hotel_temp' 
# Tất cả các file/folder sẽ được tạo bên trong thư mục này (ví dụ: links_hotel_tam/ha-noi/link.txt)

try:
    # 2. Đọc, lọc và xử lý dữ liệu (giữ nguyên logic cũ)
    df = pd.read_excel(file_excel, sheet_name=sheet_name)
    df_filtered = df[df[cot_nguon] == nguon_can_loc].copy()

    # Tạo cột 'Thư mục' (Tên tỉnh/thành phố)
    df_filtered['Thư mục'] = df_filtered[cot_file_path].apply(
        lambda x: x.split(file_path_delimiter)[0] if pd.notna(x) and file_path_delimiter in x else 'khong_xac_dinh'
    )

    # Tạo cột 'URL Booking'
    def create_booking_url(file_path):
        if pd.notna(file_path) and file_path_delimiter in file_path:
            file_name_with_ext = file_path.split(file_path_delimiter)[-1]
            hotel_slug = os.path.splitext(file_name_with_ext)[0]
            return f"{url_booking_base}{hotel_slug}{url_booking_suffix}"
        return None 

    df_filtered['URL Booking'] = df_filtered[cot_file_path].apply(create_booking_url)
    df_result = df_filtered.dropna(subset=['URL Booking']).copy()
    print(f"Số dòng hợp lệ sau khi lọc và xử lý URL: {len(df_result)}")

    # 3. NHÓM DỮ LIỆU VÀ TẠO FOLDER + FILE link.txt
    
    # Tạo thư mục cha nếu nó chưa tồn tại
    os.makedirs(output_directory, exist_ok=True)
    print(f"Đã tạo thư mục cha: {output_directory}")
    
    # Nhóm URL theo tên tỉnh/thành phố (cột 'Thư mục')
    grouped_urls = df_result.groupby('Thư mục')['URL Booking'].apply(list).reset_index()

    # Lặp qua từng nhóm và tạo folder + file link.txt
    for index, row in grouped_urls.iterrows():
        folder_name = row['Thư mục']
        urls = row['URL Booking']
        
        # ⚠️ TẠO ĐƯỜNG DẪN THƯ MỤC CON BÊN TRONG THƯ MỤC CHỦ
        # Ví dụ: links_hotel_tam/ha-noi
        sub_folder_path = os.path.join(output_directory, folder_name)
        
        # Tạo thư mục con (ví dụ: links_hotel_tam/ha-noi)
        os.makedirs(sub_folder_path, exist_ok=True) 
        
        # Tạo đường dẫn file: 'links_hotel_tam/ha-noi/link.txt'
        output_filepath = os.path.join(sub_folder_path, 'link.txt')
        
        # Ghi các URL vào file link.txt
        with open(output_filepath, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(f"{url}\n")
        
        print(f"✅ Đã tạo file: {output_filepath} ({len(urls)} links)")
        
    print("\nQuá trình tạo thư mục và file link.txt hoàn tất.")

except FileNotFoundError:
    print(f"❌ Lỗi: Không tìm thấy file Excel '{file_excel}'. Vui lòng kiểm tra lại tên file.")
except KeyError as e:
    print(f"❌ Lỗi: Không tìm thấy cột {e} trong file Excel. Vui lòng kiểm tra lại tên cột.")
except Exception as e:
    print(f"❌ Đã xảy ra lỗi: {e}")