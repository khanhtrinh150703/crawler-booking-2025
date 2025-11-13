# modes/mode2.py
from concurrent.futures import ProcessPoolExecutor, as_completed
from core.crawler import BookingCrawler
from utils.file_utils import load_urls_from_province, chunk_urls
import logging
import os

def crawl_chunk_mode2(args):
    urls_chunk, province_name, output_dir, worker_index, stop_event = args
    if not urls_chunk:
        return worker_index, 0, 0

    crawler = BookingCrawler(worker_index, output_dir, province_name, stop_event)
    total, success = crawler.run(urls_chunk)
    return worker_index, total, success

def run_mode2(input_dir, output_dir, max_workers, max_runtime_minutes, stop_event):
    province_dirs = [os.path.join(input_dir, d) for d in os.listdir(input_dir)
                     if os.path.isdir(os.path.join(input_dir, d))]

    for province_path in province_dirs:
        if stop_event.is_set():
            break
        province_name = os.path.basename(province_path)
        logger = logging.getLogger(f"Mode2-Province-{province_name}")

        all_urls = load_urls_from_province(province_path)
        if not all_urls:
            logger.warning(f"No URLs in {province_name}")
            continue

        chunks = chunk_urls(all_urls, max_workers)
        tasks = [(chunks[i], province_name, output_dir, i, stop_event)
                 for i in range(max_workers) if chunks[i]]

        total_all = len(all_urls)
        success_all = 0

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(crawl_chunk_mode2, task): task[3] for task in tasks}
            for future in as_completed(futures):
                if stop_event.is_set():
                    break
                wid = futures[future]
                try:
                    _, total, success = future.result()
                    success_all += success
                    logger.info(f"Worker-{wid}: {success}/{total}")
                except Exception as e:
                    logger.error(f"Worker-{wid} error: {e}")

        logger.info(f"Province {province_name} DONE: {success_all}/{total_all}")