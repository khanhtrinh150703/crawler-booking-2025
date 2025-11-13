# modes/mode1.py
from concurrent.futures import ProcessPoolExecutor, as_completed
from core.crawler import BookingCrawler
from utils.file_utils import load_urls_from_province
import os
import logging

def crawl_province_mode1(args):
    province_path, output_dir, max_workers, stop_event, worker_index = args
    province_name = os.path.basename(province_path)
    logger = logging.getLogger(f"Mode1-{province_name}")

    all_urls = load_urls_from_province(province_path)
    if not all_urls:
        logger.warning(f"No URLs in {province_path}")
        return province_name, 0, 0

    crawler = BookingCrawler(worker_index, output_dir, province_name, stop_event)
    total, success = crawler.run(all_urls)
    return province_name, total, success

def run_mode1(input_dir, output_dir, max_workers, max_runtime_minutes, stop_event):
    province_dirs = [os.path.join(input_dir, d) for d in os.listdir(input_dir)
                     if os.path.isdir(os.path.join(input_dir, d))]

    tasks = [(p, output_dir, max_workers, stop_event, i % max_workers)
             for i, p in enumerate(province_dirs)]

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(crawl_province_mode1, task): os.path.basename(task[0]) for task in tasks}
        for future in as_completed(futures):
            if stop_event.is_set():
                break
            prov_name = futures[future]
            try:
                prov, total, success = future.result()
                logging.info(f"[MODE1] {prov}: {success}/{total} hotels.")
            except Exception as e:
                logging.error(f"[MODE1] {prov_name} error: {e}")