# src/utils/driver_utils.py
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from config.settings import USER_AGENT, HEADLESS, IMPLICIT_WAIT, SCREEN_WIDTH, SCREEN_HEIGHT
import time
import random

def create_driver(worker_index, max_workers):
    options = Options()
    if HEADLESS:
        options.add_argument("--headless")
    options.add_argument(f"user-agent={USER_AGENT}")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Edge(options=options)
    driver.implicitly_wait(IMPLICIT_WAIT)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # === CHIA MÀN HÌNH ===
    cols = min(3, max_workers)
    rows = (max_workers + cols - 1) // cols
    cell_w = SCREEN_WIDTH // cols
    cell_h = SCREEN_HEIGHT // rows

    col = worker_index % cols
    row = worker_index // cols
    x = col * cell_w
    y = row * cell_h

    driver.set_window_rect(x=x, y=y, width=cell_w, height=cell_h)

    # === VÀO TRANG CHỦ ===
    driver.get("https://www.booking.com")
    time.sleep(random.uniform(2.0, 4.0))

    return driver