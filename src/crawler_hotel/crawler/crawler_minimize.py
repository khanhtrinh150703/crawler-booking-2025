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
from data_extractor import extract_hotel_data, extract_evaluation_categories
# IMPORT HÀM TỪ REVIEW EXTRACTOR
from crawler_hotel.utils.review_extractor import crawl_all_reviews



# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def crawl_hotels_from_file(input_file_path, output_dir="data"):
    """
    Hàm chính để đọc URL, khởi tạo driver, duyệt qua từng khách sạn và lưu dữ liệu.
    Sử dụng headless + force load để ẩn trình duyệt nhưng vẫn crawl đầy đủ.
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
        # Cấu hình Edge Options để giả lập trình duyệt thực (headless)
        options = Options()
        options.add_argument("--headless")  # Ẩn hoàn toàn, nhưng fix detection
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins-discovery")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-software-rasterizer")
        
        # Fix detection nâng cao cho headless
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-default-apps")
        options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
        # THÊM MỚI: Chống headless detection thêm
        options.add_argument("--disable-features=site-per-process")
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--disable-ipc-flooding-protection")
        
        # Khởi tạo driver
        driver = webdriver.Edge(options=options)
        driver.implicitly_wait(10)  # Tăng implicit wait
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # OPTIONAL: Nếu muốn minimize thay vì headless, uncomment dưới và comment --headless
        # driver.minimize_window()
        # logging.info("Browser window minimized.")

        # Vào trang chủ Booking.com để lấy cookie/session
        logging.info("Navigating to Booking.com homepage to establish session...")
        driver.get("https://www.booking.com")
        time.sleep(5)

        for url in hotel_urls:
            if not url.startswith('http'):
                logging.warning(f"Skipping invalid URL: {url}")
                continue
            
            try:
                logging.info(f"Processing URL: {url}")
                
                driver.get(url)
                
                # Tăng thời gian chờ tĩnh ban đầu để JS load
                time.sleep(7)  # Tăng từ 5s lên 7s
                
                # Chờ element chính
                WebDriverWait(driver, 15).until(  # Tăng từ 10s lên 15s
                    EC.presence_of_element_located((By.XPATH, '//*[@data-testid="review-score-component"]'))
                )
                time.sleep(3)  # Chờ thêm script

                # THÊM MỚI: Multiple scrolls để trigger lazy load đầy đủ
                for _ in range(3):  # Scroll 3 lần
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)

                # THÊM MỚI: JS force expand all sections (cho reviews, categories trên Booking)
                driver.execute_script("""
                    // Expand all review tabs/accordions
                    document.querySelectorAll('[data-testid="reviews-tab"]').forEach(el => el.click());
                    // Click to load more reviews if available
                    document.querySelectorAll('[data-testid="reviews-load-more-button"]').forEach(el => el.click());
                    // Expand description if collapsed
                    document.querySelectorAll('.hp_desc_section__more').forEach(el => el.click());
                """)
                time.sleep(3)  # Chờ expand

                # Kiểm tra redirect
                current_url = driver.current_url
                logging.info(f"Loaded URL: {current_url}")
                if current_url != url:
                    logging.warning(f"URL redirected: {url} -> {current_url}")

                html_content = driver.page_source
                logging.info(f"HTML length for {url}: {len(html_content)} characters")  # Debug: Check data đầy không
                
                name, address, description, rating, number_rating = extract_hotel_data(html_content)
                evaluation_categories = extract_evaluation_categories(html_content)
                
                # Crawl reviews (giả sử hàm này cũng dùng driver, nên đã load đầy)
                reviews = crawl_all_reviews(driver, url)
                
                hotel_data = {
                    "name": name,
                    "address": address,
                    "description": description,
                    "rating": rating,
                    "total_rating": number_rating,
                    "evaluation_categories": evaluation_categories,
                    "reviews": reviews,
                }

                # Lưu JSON
                output_folder_path = os.path.join(output_dir, province_name)
                os.makedirs(output_folder_path, exist_ok=True)
                
                hotel_name_from_url = url.split('/')[-1].split('.')[0].replace('-', '_')
                filename = os.path.join(output_folder_path, f"{hotel_name_from_url}.json")
                
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(hotel_data, f, ensure_ascii=False, indent=4)
                logging.info(f"Processed and saved: {name} -> {filename}")

            except TimeoutException:
                logging.error(f"Timeout (15s) while loading key element on {url}. Skipping.")
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
    """
    if not os.path.exists(input_dir):
        logging.error(f"Input directory not found: {input_dir}")
        return
    
    for province_name in os.listdir(input_dir):
        province_path = os.path.join(input_dir, province_name)
        if os.path.isdir(province_path):
            input_file_path = os.path.join(province_path, "hotels_list.txt")
            if os.path.exists(input_file_path):
                logging.info(f"Starting crawl for province: {province_name}")
                crawl_hotels_from_file(input_file_path, output_dir)
                logging.info(f"Finished crawl for province: {province_name}")
            else:
                logging.warning(f"hotels_list.txt not found in {province_path}. Skipping.")
        else:
            logging.warning(f"{province_path} is not a directory. Skipping.")

# Usage example
if __name__ == "__main__":
    # CHỈNH SỬA ĐƯỜNG DẪN NÀY
    input_dir = r"D:\private\crawler-booking-2025\src\test"  # Thư mục chứa các thư mục tỉnh
    output_dir = "data"  # Thư mục output
    crawl_all_provinces(input_dir, output_dir)    