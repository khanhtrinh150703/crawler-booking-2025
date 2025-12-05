# src/crawler/parallel_crawler.py
import os
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager
from crawler_process.province_worker import crawl_province_task
from config.settings import logger, MAX_WORKERS, MAX_RUNTIME_MINUTES

def crawl_all_provinces_parallel(input_dir, output_dir, max_workers=None, max_runtime_minutes=None):
    if not os.path.exists(input_dir):
        logger.error(f"Input not found: {input_dir}")
        return

    province_dirs = [os.path.join(input_dir, d) for d in os.listdir(input_dir)
                     if os.path.isdir(os.path.join(input_dir, d))]

    if not province_dirs:
        logger.warning("No provinces.")
        return

    max_workers = max_workers or min(len(province_dirs), MAX_WORKERS)
    os.makedirs(output_dir, exist_ok=True)
    manager = Manager()
    stop_event = manager.Event()

    # Auto stop
    if max_runtime_minutes:
        def auto_stop():
            import time
            time.sleep(max_runtime_minutes * 60)
            stop_event.set()
            logger.info(f"Auto-stop after {max_runtime_minutes} mins.")
        threading.Thread(target=auto_stop, daemon=True).start()

    # Enter to stop
    def wait_enter():
        print("\n" + "!"*60)
        print("     NHẤN ENTER ĐỂ DỪNG TOÀN BỘ")
        print("!"*60)
        input()
        stop_event.set()
        logger.info("ENTER pressed. Stopping...")
    threading.Thread(target=wait_enter, daemon=True).start()

    tasks = [(p, output_dir, max_workers, stop_event, i % max_workers) for i, p in enumerate(province_dirs)]

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(crawl_province_task, t): os.path.basename(t[0]) for t in tasks}
        for future in as_completed(futures):
            if stop_event.is_set():
                break
            prov, total, success = future.result()
            logger.info(f"Done {prov}: {success}/{total} hotels.")