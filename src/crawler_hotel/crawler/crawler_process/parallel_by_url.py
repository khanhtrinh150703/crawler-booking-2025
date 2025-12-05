# crawler/parallel_by_url.py
import os
import json
import logging
import time
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager
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

def crawl_hotel_chunk(args):
    urls_chunk, province_name, output_dir, worker_index, stop_event = args
    logger = logging.getLogger(f"Worker-{worker_index}")
    driver = create_driver(worker_index)
    success = 0

    try:
        driver.get("https://www.booking.com")
        time.sleep(random.uniform(2, 4))

        for i, url in enumerate(urls_chunk):
            if stop_event.is_set(): break
            if i > 0: time.sleep(random.uniform(1.5, 3.5))

            retry = 0
            while retry <= 2 and not stop_event.is_set():
                try:
                    driver.get(url + "?lang=vi")
                    time.sleep(1)
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@data-testid="review-score-component"]')))
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

                    success += 1
                    logger.info(f"[{success}/{len(urls_chunk)}] Đã lưu: {name}")
                    break
                except TimeoutException:
                    retry += 1
                    time.sleep(random.uniform(3, 6))
                except Exception as e:
                    logger.error(f"Lỗi: {url} | {e}")
                    break
    finally:
        driver.quit()

    return worker_index, len(urls_chunk), success

def crawl_province_with_workers(province_path, output_dir, max_workers=3):
    province_name = os.path.basename(province_path)
    all_urls = []
    for f in os.listdir(province_path):
        if f.lower().endswith('.txt'):
            try:
                with open(os.path.join(province_path, f), "r", encoding="utf-8") as file:
                    all_urls.extend([line.strip() for line in file if line.strip().startswith('http')])
            except: pass

    if not all_urls: return 0, 0

    chunk_size = (len(all_urls) + max_workers - 1) // max_workers
    chunks = [all_urls[i:i + chunk_size] for i in range(0, len(all_urls), chunk_size)]
    while len(chunks) < max_workers:
        chunks.append([])

    manager = Manager()
    stop_event = manager.Event()

    def wait_enter():
        input(f"\nĐANG CRAWL {province_name} - NHẤN ENTER ĐỂ DỪNG...\n")
        stop_event.set()
    import threading
    threading.Thread(target=wait_enter, daemon=True).start()

    tasks = [(chunks[i], province_name, output_dir, i, stop_event) for i in range(max_workers) if chunks[i]]
    total, success = 0, 0

    with ProcessPoolExecutor(max_workers=max_workers) as exec:
        for f in as_completed([exec.submit(crawl_hotel_chunk, t) for t in tasks]):
            if stop_event.is_set(): break
            _, t, s = f.result()
            total += t
            success += s

    return total, success

def crawl_all_provinces_sequential(input_dir, output_dir=OUTPUT_DIR, max_workers=3):
    if not os.path.exists(input_dir): return
    provinces = [os.path.join(input_dir, d) for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]

    for prov in provinces:
        p, s = crawl_province_with_workers(prov, output_dir, max_workers)
        logging.info(f"Hoàn thành {os.path.basename(prov)}: {s}/{p}")