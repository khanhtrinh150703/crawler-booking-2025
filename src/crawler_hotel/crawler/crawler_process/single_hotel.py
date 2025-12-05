# src/crawler/province_worker.py
import os
import time
import random
import logging
from utils.driver_utils import create_driver
from crawler_process.single_hotel import crawl_single_hotel
from config.settings import logger, MAX_WORKERS

def crawl_province_task(args):
    province_path, output_dir, max_workers, stop_event, worker_index = args
    province_name = os.path.basename(province_path)
    logger = logging.getLogger(f"Worker-{worker_index}-{province_name}")
    logger.info(f"Starting province: {province_name}")

    if stop_event.is_set():
        return province_name, 0, 0

    txt_files = [f for f in os.listdir(province_path) if f.lower().endswith('.txt')]
    if not txt_files:
        logger.warning("No .txt files found.")
        return province_name, 0, 0

    driver = None
    total_hotels = 0
    success_count = 0

    try:
        driver = create_driver(worker_index, max_workers)

        for txt_file in txt_files:
            if stop_event.is_set():
                break
            file_path = os.path.join(province_path, txt_file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    urls = [line.strip() for line in f if line.strip().startswith("http")]
            except Exception as e:
                logger.error(f"Read error {file_path}: {e}")
                continue

            for url in urls:
                if stop_event.is_set():
                    break
                total_hotels += 1
                if total_hotels > 1:
                    time.sleep(random.uniform(1.5, 3.5))
                if crawl_single_hotel(driver, url, province_name, output_dir, stop_event):
                    success_count += 1

    except Exception as e:
        logger.error(f"Crash: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    return province_name, total_hotels, success_count