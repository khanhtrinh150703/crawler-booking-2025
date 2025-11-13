# core/driver.py
from selenium import webdriver
from selenium.webdriver.edge.options import Options

def create_driver(screen_width=1920, screen_height=1080, cols=3, worker_index=0):
    options = Options()
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

    # Căn cửa sổ
    cell_w = screen_width // cols
    cell_h = screen_height
    x = (worker_index % cols) * cell_w
    y = 0
    driver.set_window_rect(x=x, y=y, width=cell_w, height=cell_h)

    return driver