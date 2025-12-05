from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.edge.options import Options  # Import Options
import os
import json
import logging
import time

# IMPORT HÀM TỪ DATA EXTRACTOR
from utils.data_extractor import extract_hotel_data, extract_evaluation_categories
# IMPORT HÀM TỪ REVIEW EXTRACTOR
from utils.review_extractor import crawl_all_reviews


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def crawl_hotels_from_file(input_file_path, output_dir="data"):
    """
    Hàm chính để đọc URL, khởi tạo driver, duyệt qua từng khách sạn và lưu dữ liệu.
    Đã thêm cấu hình chống chặn (User-Agent) và tăng thời gian chờ.
    """
    province_name = os.path.basename(os.path.dirname(input_file_path))
    
    try:
        with open(input_file_path, "r", encoding="utf-8") as file:
            hotel_urls = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        logging.error(f"Input file not found: {input_file_path}")
        return

    driver = None
    
    try:
        # Cấu hình Chrome Options để giả lập trình duyệt thực
        options = Options()
        # options.add_argument("--headless")  # Tùy chọn: Chạy ẩn
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        # Additional options to suppress console errors and logs
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")  # Suppresses INFO and below
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins-discovery")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        # Suppress GPU/WebGL errors
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-software-rasterizer")
        
        # Khởi tạo driver với Options
        driver = webdriver.Edge(options=options)
        driver.implicitly_wait(5)
        # Execute script to hide webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Bước mới: Vào trang chủ Booking.com trước để lấy cookie/session
        logging.info("Navigating to Booking.com homepage to establish session...")
        driver.get("https://www.booking.com")
        time.sleep(5)  # Chờ load trang chủ và thiết lập session/cookie

        for url in hotel_urls:
            if not url.startswith('http'):
                logging.warning(f"Skipping invalid URL: {url}")
                continue
            
            try:
                logging.info(f"Processing URL: {url}")
                url = url+"?lang=vi"
                driver.get(url)
                
                # Tăng thời gian chờ tĩnh ban đầu
                time.sleep(3) 
                
                # Tăng thời gian chờ đợi lên 10 giây và sử dụng XPATH ổn định hơn (đã chỉnh từ 30s xuống 10s để nhanh hơn)
                WebDriverWait(driver, 5).until(
                    # Chờ khối đánh giá tổng thể (data-testid ổn định)
                    EC.presence_of_element_located((By.XPATH, '//*[@data-testid="review-score-component"]'))
                )
                
                # Thêm một thời gian chờ tĩnh ngắn để các script cuối cùng hoàn thành
                time.sleep(2)

                # Xử lý REDIRECT URL (kiểm tra nếu URL bị thay đổi sau khi tải)
                current_url = driver.current_url
                if current_url != url:
                    logging.warning(f"URL redirected: {url} -> {current_url}. Proceeding with new URL content.")

                html_content = driver.page_source
                name, address, description, rating, number_rating = extract_hotel_data(html_content)
                evaluation_categories = extract_evaluation_categories(html_content)
                
                # Crawl reviews
                nameHotel, reviews = crawl_all_reviews(driver, url, province_name)
                
                if name:
                    name = nameHotel
                    
                # Cấu trúc JSON
                hotel_data = {
                    "name": name,
                    "address": address,
                    "description": description,
                    "rating": rating,
                    "total_rating": number_rating,
                    "evaluation_categories": evaluation_categories,
                    "reviews": reviews,
                }

                # Lưu vào file JSON
                output_folder_path = os.path.join(output_dir, province_name)
                os.makedirs(output_folder_path, exist_ok=True)
                
                hotel_name_from_url = url.split('/')[-1].split('.')[0].replace('-', '_') 
                filename = os.path.join(output_folder_path, f"{hotel_name_from_url}.json")
                
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(hotel_data, f, ensure_ascii=False, indent=4)
                logging.info(f"Processed and saved: {name} -> {filename}")

            except TimeoutException:
                logging.error(f"Timeout (10s) while loading key element on {url}. Skipping this hotel.")
            except Exception as e:
                logging.error(f"Error processing {url}: {str(e)}")
                continue

    except Exception as e:
        logging.error(f"Setup or main loop error: {str(e)}")
    finally:
        if driver:
            driver.quit()

def crawl_all_provinces(input_dir, output_dir="data"):
    """
    Hàm mới để duyệt qua tất cả các thư mục tỉnh trong input_dir.
    Giả sử mỗi thư mục tỉnh chứa file 'hotels_list.txt' với danh sách link hotel.
    """
    if not os.path.exists(input_dir):
        logging.error(f"Input directory not found: {input_dir}")
        return

    # Duyệt qua tất cả thư mục con (các tỉnh)
    for province_name in os.listdir(input_dir):
        province_path = os.path.join(input_dir, province_name)
        
        if os.path.isdir(province_path):
            logging.info(f"Starting crawl for province: {province_name}")
            
            # Tìm tất cả file .txt trong thư mục tỉnh
            txt_files = [f for f in os.listdir(province_path) if f.lower().endswith('.txt')]
            
            if txt_files:
                for txt_file in txt_files:
                    input_file_path = os.path.join(province_path, txt_file)
                    logging.info(f"Found and processing: {input_file_path}")
                    crawl_hotels_from_file(input_file_path, output_dir)
                logging.info(f"Finished crawl for province: {province_name}")
            else:
                logging.warning(f"No .txt files found in {province_path}. Skipping province: {province_name}")
        else:
            logging.warning(f"{province_path} is not a directory. Skipping.")

# Usage example
if __name__ == "__main__":
    # CHỈNH SỬA ĐƯỜNG DẪN NÀY
    input_dir = r"D:\private\crawler-booking-2025\src\crawler_province\hotel_links"  # Thư mục chứa các thư mục tỉnh
    output_dir = "data_test"  # Thư mục output (sẽ tạo thư mục con cho từng tỉnh)
    crawl_all_provinces(input_dir, output_dir) 