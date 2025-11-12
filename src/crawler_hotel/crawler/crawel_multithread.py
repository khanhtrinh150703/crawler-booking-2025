# main.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.edge.options import Options
import os
import json
import logging
import time
import random
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import freeze_support, Manager

# IMPORT HÀM TỪ DATA EXTRACTOR
from utils.data_extractor import extract_hotel_data, extract_evaluation_categories
# IMPORT HÀM TỪ REVIEW EXTRACTOR
from utils.review_extractor import crawl_all_reviews

# ================================
# CẤU HÌNH LOGGING
# ================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# ================================
# HÀM CHẠY CHO MỘT PHẦN URL (trong process riêng)
# ================================
def crawl_hotel_chunk(args):
    urls_chunk, province_name, output_dir, worker_index, stop_event = args
    logger = logging.getLogger(f"Worker-{worker_index}-{province_name}")
    logger.info(f"Worker-{worker_index} started with {len(urls_chunk)} hotels")

    driver = None
    success_count = 0
    total_hotels = len(urls_chunk)

    try:
        # === CẤU HÌNH EDGE DRIVER ===
        options = Options()
        # options.add_argument("--headless")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Edge(options=options)
        driver.implicitly_wait(5)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # === CHIA MÀN HÌNH ĐỀU (3 workers) ===
        screen_width = 1920
        screen_height = 1080
        cols = 3
        cell_w = screen_width // cols
        cell_h = screen_height

        x = (worker_index % cols) * cell_w
        y = 0

        driver.set_window_rect(x=x, y=y, width=cell_w, height=cell_h)
        logger.info(f"Window [{worker_index}] → ({x}, {y}) | {cell_w}x{cell_h}")

        # === VÀO TRANG CHỦ (một lần) ===
        logger.info("Opening Booking.com...")
        driver.get("https://www.booking.com")
        time.sleep(random.uniform(2.0, 4.0))

        for idx, url in enumerate(urls_chunk):
            if stop_event.is_set():
                logger.info("Stop signal received.")
                break

            # Delay giữa các hotel
            if idx > 0:
                delay = random.uniform(1.5, 3.5)
                logger.info(f"Delay {delay:.1f}s before next hotel...")
                time.sleep(delay)

            retry_count = 0
            max_retries = 2

            while retry_count <= max_retries and not stop_event.is_set():
                try:
                    full_url = url + "?lang=vi"
                    driver.get(full_url)
                    time.sleep(random.uniform(0.5, 1.5))

                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@data-testid="review-score-component"]'))
                    )
                    time.sleep(random.uniform(0.8, 1.8))

                    html = driver.page_source
                    name, address, description, rating, number_rating = extract_hotel_data(html)
                    evaluation_categories = extract_evaluation_categories(html)
                    nameHotel, reviews = crawl_all_reviews(driver, full_url, province_name)

                    if nameHotel:
                        name = nameHotel

                    hotel_data = {
                        "name": name,
                        "address": address,
                        "description": description,
                        "rating": rating,
                        "total_rating": number_rating,
                        "evaluation_categories": evaluation_categories,
                        "reviews": reviews,
                    }

                    output_folder = os.path.join(output_dir, province_name)
                    os.makedirs(output_folder, exist_ok=True)
                    hotel_key = full_url.split('/')[-1].split('.')[0].replace('-', '_')
                    filename = os.path.join(output_folder, f"{hotel_key}.json")

                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(hotel_data, f, ensure_ascii=False, indent=4)

                    success_count += 1
                    logger.info(f"[{success_count}/{total_hotels}] Saved: {name}")
                    break

                except TimeoutException:
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.warning(f"Timeout (retry {retry_count}/{max_retries}): {url}")
                        time.sleep(random.uniform(3.0, 6.0))
                    else:
                        logger.error(f"Timeout failed: {url}")
                except Exception as e:
                    logger.error(f"Error on {url}: {str(e)}")
                    break

    except Exception as e:
        logger.error(f"Worker-{worker_index} crashed: {e}")
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Driver quit.")
            except:
                pass

    return worker_index, total_hotels, success_count


# ================================
# HÀM CHẠY MỘT TỈNH VỚI NHIỀU PROCESS
# ================================
def crawl_province_with_workers(province_path, output_dir, max_workers=3, max_runtime_minutes=None):
    province_name = os.path.basename(province_path)
    logger = logging.getLogger(f"Province-{province_name}")
    logger.info(f"Starting province: {province_name} with {max_workers} workers")

    # === GOM TẤT CẢ URL TỪ CÁC FILE .TXT ===
    all_hotel_urls = []
    txt_files = [f for f in os.listdir(province_path) if f.lower().endswith('.txt')]

    if not txt_files:
        logger.warning(f"No .txt files in {province_path}")
        return 0, 0

    for txt_file in txt_files:
        file_path = os.path.join(province_path, txt_file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip().startswith('http')]
                all_hotel_urls.extend(urls)
        except Exception as e:
            logger.error(f"Cannot read {file_path}: {e}")

    if not all_hotel_urls:
        logger.warning(f"No valid URLs found in {province_name}")
        return 0, 0

    total_urls = len(all_hotel_urls)
    logger.info(f"Found {total_urls} hotel URLs in {province_name}")

    # === CHIA ĐỀU URL CHO CÁC WORKER ===
    chunk_size = (total_urls + max_workers - 1) // max_workers
    url_chunks = [
        all_hotel_urls[i:i + chunk_size]
        for i in range(0, total_urls, chunk_size)
    ]

    # Đảm bảo có đủ chunk cho từng worker
    while len(url_chunks) < max_workers:
        url_chunks.append([])

    # === CHUẨN BỊ STOP EVENT ===
    manager = Manager()
    stop_event = manager.Event()

    # === TỰ ĐỘNG DỪNG SAU X PHÚT ===
    if max_runtime_minutes:
        def auto_stop():
            time.sleep(max_runtime_minutes * 60)
            logger.info(f"Auto-stop after {max_runtime_minutes} minutes.")
            stop_event.set()
        threading.Thread(target=auto_stop, daemon=True).start()

    # === NHẤN ENTER ĐỂ DỪNG ===
    def wait_for_enter():
        print("\n" + "!"*60)
        print(f"     ĐANG CRAWL TỈNH: {province_name}")
        print("     NHẤN PHÍM ENTER ĐỂ DỪNG TOÀN BỘ")
        print("!"*60)
        input()
        stop_event.set()
        logger.info("ENTER pressed. Stopping all workers...")
    threading.Thread(target=wait_for_enter, daemon=True).start()

    # === CHẠY ĐA PROCESS ===
    province_output_dir = os.path.join(output_dir, province_name)
    os.makedirs(province_output_dir, exist_ok=True)

    tasks = [
        (url_chunks[i], province_name, output_dir, i, stop_event)
        for i in range(max_workers)
        if url_chunks[i]  # Chỉ tạo task nếu có URL
    ]

    total_success = 0
    total_processed = 0

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(crawl_hotel_chunk, task): task[3]  # worker_index
            for task in tasks
        }

        for future in as_completed(futures):
            if stop_event.is_set():
                break
            worker_idx = futures[future]
            try:
                wid, total, success = future.result()
                total_processed += total
                total_success += success
                logger.info(f"Worker-{wid} completed: {success}/{total} hotels")
            except Exception as e:
                logger.error(f"Worker-{worker_idx} error: {e}")

    logger.info(f"Province {province_name} DONE: {total_success}/{total_processed} hotels saved.")
    return total_processed, total_success


# ================================
# HÀM CHẠY TẤT CẢ CÁC TỈNH TUẦN TỰ
# ================================
def crawl_all_provinces_sequential(
    input_dir,
    output_dir="data",
    max_workers=3,
    max_runtime_minutes=None
):
    if not os.path.exists(input_dir):
        logging.error(f"Input directory not found: {input_dir}")
        return

    province_dirs = [
        os.path.join(input_dir, d) for d in os.listdir(input_dir)
        if os.path.isdir(os.path.join(input_dir, d))
    ]

    if not province_dirs:
        logging.warning("No province folders found.")
        return

    os.makedirs(output_dir, exist_ok=True)

    total_all = 0
    success_all = 0

    for province_path in province_dirs:
        processed, success = crawl_province_with_workers(
            province_path=province_path,
            output_dir=output_dir,
            max_workers=max_workers,
            max_runtime_minutes=max_runtime_minutes
        )
        total_all += processed
        success_all += success

    logging.info(f"ALL DONE: {success_all}/{total_all} hotels across all provinces.")


# ================================
# CHẠY CHÍNH - DUYỆT TỪNG RANGE THEO THỨ TỰ
# ================================
if __name__ == "__main__":
    freeze_support()

    # === CẤU HÌNH CHUNG ===
    base_input_dir = r"D:\private\crawler-booking-2025\src\crawler_province\hotel_test"
    output_dir = "data_test"

    MAX_WORKERS = 3
    MAX_RUNTIME_MINUTES = None  # None = chạy đến khi nhấn Enter

    # === LẤY DANH SÁCH RANGE THEO THỨ TỰ ===
    range_dirs = sorted(
        [d for d in os.listdir(base_input_dir)
         if os.path.isdir(os.path.join(base_input_dir, d)) and d.replace('-', '').isdigit()],
        key=lambda x: int(x.split('-')[0])
    )

    if not range_dirs:
        print("Không tìm thấy thư mục range nào trong:", base_input_dir)
        exit()

    print("\n" + "="*80)
    print("     BOOKING.COM CRAWLER - 1 TỈNH = 3 WORKERS (chia URL)")
    print("     → Nhấn ENTER để dừng toàn bộ")
    print("     → Duyệt từng range → từng tỉnh → chia URL cho 3 worker")
    print(f"     → Workers per province: {MAX_WORKERS}")
    print("="*80 + "\n")

    # === DUYỆT TỪNG RANGE ===
    for range_name in range_dirs:
        input_dir = os.path.join(base_input_dir, range_name)
        range_output_dir = os.path.join(output_dir, range_name)
        os.makedirs(range_output_dir, exist_ok=True)

        print(f"\n{'-'*60}")
        print(f" BẮT ĐẦU RANGE: {range_name}")
        print(f"   → Input : {input_dir}")
        print(f"   → Output: {range_output_dir}")
        print(f"{'-'*60}\n")

        # Gọi hàm crawl cho range này
        crawl_all_provinces_sequential(
            input_dir=input_dir,
            output_dir=range_output_dir,
            max_workers=MAX_WORKERS,
            max_runtime_minutes=MAX_RUNTIME_MINUTES
        )

        print(f"\nHOÀN THÀNH RANGE: {range_name}\n")
        print("="*80)

    print("\n" + "="*70)
    print("          ĐÃ HOÀN THÀNH TẤT CẢ CÁC RANGE!")
    print(f"          Dữ liệu được lưu theo từng range/tỉnh trong: {os.path.abspath(output_dir)}")
    print("          Log: crawler.log")
    print("="*70)
    print("          Thoát trong 5 giây...")
    time.sleep(5)