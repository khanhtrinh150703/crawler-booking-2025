from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import os
import time
import urllib.parse

# === TẮT LOG ===
logging.getLogger('selenium').setLevel(logging.CRITICAL + 1)
os.environ['WDM_LOG_LEVEL'] = '0'

# === FILE & THƯ MỤC ===
URLS_FILE = "provinces_2.txt"
MAIN_FOLDER = "hotel_links_city"

if not os.path.exists(URLS_FILE):
    print(f"KHÔNG TÌM THẤY: {URLS_FILE}")
    input("Nhấn Enter để thoát...")
    exit()

# Đọc danh sách URLs
urls_list = []
with open(URLS_FILE, "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if not line or line.startswith("#"): 
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3: 
            print(f"Lỗi dòng {line_num}: {line}")
            continue
        raw_url, display_name, folder_name = parts
        if not raw_url.startswith("http"): 
            continue

        # === TỐI ƯU URL ĐỂ CÓ NÚT "LOAD MORE" ===
        parsed = urllib.parse.urlparse(raw_url)
        query = urllib.parse.parse_qs(parsed.query)

        new_query = {}
        if 'ss' in query:
            new_query['ss'] = query['ss']
        new_query['order'] = 'bayesian_review_score'

        for key in ['checkin', 'checkout', 'group_adults', 'group_children', 'no_rooms']:
            query.pop(key, None)

        new_query.update({k: v for k, v in query.items() if k not in ['label', 'aid', 'sid']})

        optimized_url = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urllib.parse.urlencode(new_query, doseq=True),
            parsed.fragment
        ))

        urls_list.append((optimized_url, display_name, folder_name))

if not urls_list:
    print("Không có URL hợp lệ!")
    exit()

os.makedirs(MAIN_FOLDER, exist_ok=True)

# === CẤU HÌNH DRIVER ===
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-logging")
options.add_argument("--log-level=3")
options.add_argument("--silent")
options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
options.add_experimental_option('useAutomationExtension', False)

service = Service(log_path=os.devnull)

# === XỬ LÝ TỪNG TỈNH ===
for search_url, display_name, folder_name in urls_list:
    print(f"\n{'='*60}")
    print(f"ĐANG XỬ LÝ: {display_name.upper()}")
    print(f"URL: {search_url}")
    print(f"{'='*60}")

    folder_path = os.path.join(MAIN_FOLDER, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    driver = webdriver.Edge(options=options, service=service)
    wait = WebDriverWait(driver, 15)
    
    try:
        # Bước 1: Mở trang
        search_url = search_url + "&lang=en-us"
        driver.get(search_url)
        time.sleep(4)

        # Bước 2: Tắt popup
        try:
            close = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Dismiss sign-in info.']")))
            close.click()
            time.sleep(1)
        except:
            pass
        
        
        # Bước 3: Load hết kết quả – NHƯNG KHÔNG VƯỢT QUÁ max_properties
        last_height = driver.execute_script("return document.body.scrollHeight")
        load_more_clicked = 0
        collected_links = 0
                # === BƯỚC MỚI: LẤY SỐ LƯỢNG TỪ <h1> ===
        max_properties = None
        try:
            h1 = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "h1[aria-live='assertive']")
            ))
            h1_text = h1.text.strip()
            print(f"Tiêu đề tìm kiếm: {h1_text}")

            # Trích xuất số: hỗ trợ cả "1,133 properties found" và "209 properties found"
            import re
            match = re.search(r'([\d,]+)\s+properties?\s+found', h1_text, re.IGNORECASE)
            if match:
                count_str = match.group(1).replace(',', '')  # Loại bỏ dấu phẩy
                max_properties = int(count_str)
                print(f"Số lượng tối đa: {max_properties}")
            else:
                print("Không tìm thấy số lượng trong tiêu đề.")
                max_properties = None

        except Exception as e:
            print(f"Không đọc được <h1>: {e}")
            max_properties = None
            
        while True:
            # Kiểm tra số link đã thu thập (từ soup tạm thời)
            soup_temp = BeautifulSoup(driver.page_source, 'html.parser')
            current_links = len([
                h3.find("a", class_="bd77474a8e") for h3 in soup_temp.find_all("h3", class_="a97d37cded")
                if h3.find("a", class_="bd77474a8e") and h3.find("a", class_="bd77474a8e").get("href")
            ])

            print(f"Đã thu thập tạm: {current_links} link", end="\r")

            # DỪNG nếu đã đủ (hoặc vượt nhẹ do load batch)
            if max_properties and current_links >= max_properties:
                print(f"\nĐÃ ĐỦ {max_properties} → Dừng load more.")
                break

            # Scroll xuống
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            # Click "Load more" nếu có
            try:
                load_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Load more results') or contains(text(), 'Tải thêm kết quả')]]"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_btn)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", load_btn)
                load_more_clicked += 1
                print(f"\nĐã click 'Load more' ({load_more_clicked})")
                time.sleep(3)
            except:
                # Không có nút → kiểm tra có thay đổi chiều cao không
                current_height = driver.execute_script("return document.body.scrollHeight")
                if current_height == last_height:
                    print("\nKhông còn kết quả mới → Dừng.")
                    break
                last_height = current_height
                time.sleep(1)

        # Bước 4: LẤY CHỈ LINK SẠCH TỪ <h3 class="a97d37cded">
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        hotel_links = set()  # Dùng set để tránh trùng

        for h3 in soup.find_all("h3", class_="a97d37cded"):
            a_tag = h3.find("a", class_="bd77474a8e")
            if not a_tag or not a_tag.get("href"):
                continue

            href = a_tag["href"].split("?")[0]  # Lấy phần trước dấu ?

            # XỬ LÝ LINK SẠCH: tránh dư https://www.booking.com
            if href.startswith("http"):
                clean_url = href
            else:
                clean_url = "https://www.booking.com" + href if href.startswith("/") else "https://www.booking.com/" + href

            hotel_links.add(clean_url)

                # Bước 5: LƯU FILE – CHỈ GIỚI HẠN KHI CÀO, FILE TXT THÌ GIỮ HẾT MÃI MÃI
        filename = f"{folder_name}_hotel_links.txt"
        filepath = os.path.join(folder_path, filename)

        # 1. Đọc toàn bộ link cũ (nếu có)
        old_links = set()
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f_old:
                for line in f_old:
                    ln = line.strip()
                    if ln.startswith("http"):
                        old_links.add(ln)
            print(f"Đã tìm thấy file cũ → {len(old_links)} link hiện có")
        else:
            print("Chưa có file cũ → tạo mới")

        # 2. Thêm tất cả link mới thu thập được (loại trùng tự động)
        before = len(old_links)
        old_links.update(hotel_links)  # set → tự loại trùng
        new_added = len(old_links) - before

        # 3. GHI LẠI TOÀN BỘ – KHÔNG BAO GIỜ CẮT, KHÔNG BAO GIỜ GIỚI HẠN
        final_links = sorted(old_links)  # sắp xếp lại cho đẹp (tùy chọn)

        with open(filepath, "w", encoding="utf-8") as f:
            for link in final_links:
                f.write(link + "\n")

        print(f"HOÀN TẤT! → Đã thêm {new_added} link mới")
        print(f"Tổng cộng hiện tại: {len(final_links)} link (không giới hạn)")
        print(f"File: {filepath}")

        if new_added == 0:
            print("→ Không có link mới (đã cào hết từ trước hoặc Booking.com đang hiển thị ít hơn thực tế)")
    except Exception as e:
        print(f"LỖI KHI XỬ LÝ {display_name}: {e}")
    finally:
        driver.quit()

# === HOÀN TẤT ===
print(f"\n{'='*60}")
print("TẤT CẢ TỈNH ĐÃ XỬ LÝ XONG!")
print(f"{'='*60}")
input("Nhấn Enter để thoát...")
