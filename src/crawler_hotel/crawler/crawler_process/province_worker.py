# crawler/parallel_by_province.py
import os
import json
import logging
import time
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager, freeze_support
from utils.driver_utils import create_driver
from utils.data_extractor import extract_hotel_data, extract_evaluation_categories
from utils.review_extractor import crawl_all_reviews
from config.settings import OUTPUT_DIR
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/crawler.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def crawl_province_task(args):
    province_path, output_dir, max_workers, stop_event, worker_index = args
    province_name = os.path.basename(province_path)
    logger = logging.getLogger(f"Prov-{worker_index}-{province_name}")
    logger.info(f"Bắt đầu tỉnh: {province_name}")

    if stop_event.is_set():
        return province_name, 0, 0

    txt_files = [f for f in os.listdir(province_path) if f.lower().endswith('.txt')]
    if not txt_files:
        return province_name, 0, 0

    driver = create_driver(worker_index)
    total_hotels = 0
    success_count = 0

    try:
        driver.get("https://www.booking.com")
        time.sleep(random.uniform(2, 4))

        for txt_file in txt_files:
            if stop_event.is_set(): break
            file_path = os.path.join(province_path, txt_file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    urls = [line.strip() for line in f if line.strip().startswith('http')]
            except: continue

            for url in urls:
                if stop_event.is_set(): break
                total_hotels += 1
                if total_hotels > 1:
                    time.sleep(random.uniform(1.5, 3.5))

                retry = 0
                while retry <= 1 and not stop_event.is_set():
                    try:
                        driver.get(url + "?lang=vi")
                        time.sleep(1)
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.XPATH, '//*[@data-testid="review-score-component"]'))
                        )
                        time.sleep(1.5)

                        html = driver.page_source
                        name, addr, desc, rating, total = extract_hotel_data(html)
                        cats = extract_evaluation_categories(html)
                        name_h, reviews = crawl_all_reviews(driver, url, province_name)
                        if name_h: name = name_h

                        data = {"name": name, "address": addr, "description": desc, "rating": rating, "total_rating": total, "evaluation_categories": cats, "reviews": reviews}
                        out_dir = os.path.join(output_dir, province_name)
                        os.makedirs(out_dir, exist_ok=True)
                        key = url.split('/')[-1].split('.')[0].replace('-', '_')
                        with open(os.path.join(out_dir, f"{key}.json"), "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)

                        success_count += 1
                        logger.info(f"Đã lưu: {name}")
                        break
                    except TimeoutException:
                        retry += 1
                        time.sleep(random.uniform(3, 6))
                    except Exception as e:
                        logger.error(f"Lỗi: {url} | {e}")
                        break
    finally:
        driver.quit()

    return province_name, total_hotels, success_count

def crawl_all_provinces_parallel(input_dir, output_dir=OUTPUT_DIR, max_workers=3, max_runtime_minutes=None):
    if not os.path.exists(input_dir): return
    provinces = [os.path.join(input_dir, d) for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
    if not provinces: return

    manager = Manager()
    stop_event = manager.Event()

    if max_runtime_minutes:
        def auto_stop():
            time.sleep(max_runtime_minutes * 60)
            stop_event.set()
        import threading
        threading.Thread(target=auto_stop, daemon=True).start()

    def wait_enter():
        input("\nNHẤN ENTER ĐỂ DỪNG...\n")
        stop_event.set()
    import threading
    threading.Thread(target=wait_enter, daemon=True).start()

    tasks = [(p, output_dir, max_workers, stop_event, i % max_workers) for i, p in enumerate(provinces)]

    with ProcessPoolExecutor(max_workers=max_workers) as exec:
        futures = {exec.submit(crawl_province_task, t): os.path.basename(t[0]) for t in tasks}
        for f in as_completed(futures):
            if stop_event.is_set(): break
            prov, total, success = f.result()
            logging.info(f"Hoàn thành {prov}: {success}/{total}")

    logging.info("=== HOÀN TẤT ===")