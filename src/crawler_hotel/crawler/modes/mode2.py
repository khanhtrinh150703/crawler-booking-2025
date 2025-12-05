# modes/mode2.py
from concurrent.futures import ProcessPoolExecutor, as_completed
from core.crawler import BookingCrawler
from utils.file_utils import load_urls_from_province
import logging
import os
import time
import random
from multiprocessing import Manager


def worker_dynamic_task(args):
    worker_id, province_name, output_dir, url_queue, stop_event, success_counter, counter_lock, total_urls, idle_timeout = args
    logger = logging.getLogger(f"Worker-{worker_id}-{province_name}")

    crawler = BookingCrawler(worker_id, output_dir, province_name, stop_event)
    local_success = 0
    last_activity = time.time()

    try:
        crawler._init_driver()
        crawler.driver.get("https://www.booking.com")
        time.sleep(random.uniform(2.0, 4.0))
        logger.info(f"Worker-{worker_id} ready.")

        while not stop_event.is_set():
            # KIỂM TRA HẾT URL
            with counter_lock:
                if success_counter.value >= total_urls:
                    logger.info(f"Worker-{worker_id}: HẾT URL → DỪNG")
                    break

            # CHỈ KIỂM TRA IDLE KHI QUEUE RỖNG
            if url_queue.empty():
                if time.time() - last_activity > idle_timeout:
                    logger.info(f"Worker-{worker_id}: QUEUE RỖNG + {idle_timeout}s KHÔNG HOẠT ĐỘNG → DỪNG")
                    break
            else:
                last_activity = time.time()  # Reset nếu còn URL

            try:
                url = url_queue.get(timeout=1.0)
                last_activity = time.time()
            except:
                time.sleep(0.5)
                continue

            if url is None:
                break

            total, success = crawler.run([url])
            local_success += success

            with counter_lock:
                success_counter.value += success

            logger.info(f"Worker-{worker_id}: +{success}/1 | Tổng: {success_counter.value}")

    except Exception as e:
        logger.error(f"Worker-{worker_id} error: {e}")
    finally:
        if crawler.driver:
            try:
                crawler.driver.quit()
                logger.info(f"Worker-{worker_id} WEB CLOSED.")
            except:
                pass

    return worker_id, local_success


def run_mode2(input_dir, output_dir, max_workers=3, max_runtime_minutes=None, stop_event=None, idle_timeout=60):
    if stop_event is None:
        manager = Manager()
        stop_event = manager.Event()

    province_dirs = [os.path.join(input_dir, d) for d in os.listdir(input_dir)
                     if os.path.isdir(os.path.join(input_dir, d))]

    total_success = 0
    total_urls_all = 0

    for province_path in province_dirs:
        if stop_event.is_set():
            break

        province_name = os.path.basename(province_path)
        logger = logging.getLogger(f"Mode2-Province-{province_name}")
        logger.info(f"Starting: {province_name}")

        all_urls = load_urls_from_province(province_path)
        if not all_urls:
            logger.warning(f"No URLs in {province_name}")
            continue

        total_urls = len(all_urls)
        total_urls_all += total_urls
        logger.info(f"Loaded {total_urls} URLs")

        manager = Manager()
        url_queue = manager.Queue()
        for url in all_urls:
            url_queue.put(url)

        success_counter = manager.Value('i', 0)
        counter_lock = manager.Lock()

        tasks = [
            (i, province_name, output_dir, url_queue, stop_event, success_counter, counter_lock, total_urls, idle_timeout)
            for i in range(max_workers)
        ]

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(worker_dynamic_task, task): i for i, task in enumerate(tasks)}

            completed = 0
            for future in as_completed(futures):
                if stop_event.is_set():
                    break
                try:
                    wid, success = future.result()
                    completed += 1

                    if completed == 1:
                        for _ in range(max_workers):
                            try:
                                url_queue.put_nowait(None)
                            except:
                                pass
                        logger.info("1 worker xong → GỬI DỪNG CHO TẤT CẢ")

                except Exception as e:
                    wid = futures[future]
                    logger.error(f"Worker-{wid} error: {e}")

        logger.info(f"Province {province_name} DONE: {success_counter.value}/{total_urls}")
        total_success += success_counter.value

    logger = logging.getLogger("Mode2-Summary")
    logger.info(f"MODE 2 COMPLETED: {total_success}/{total_urls_all}")
    stop_event.set()