# core/crawler.py
import os
import json
import time
import random
import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from core.driver import create_driver
from utils.data_extractor import extract_hotel_data, extract_evaluation_categories
from utils.review_extractor import crawl_all_reviews
from utils.helpers import delay

class BookingCrawler:
    def __init__(self, worker_index, output_dir, province_name, stop_event, screen_width=1920, screen_height=1080, cols=3):
        self.worker_index = worker_index
        self.output_dir = output_dir
        self.province_name = province_name
        self.stop_event = stop_event
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.cols = cols
        self.driver = None
        self.logger = logging.getLogger(f"Worker-{worker_index}-{province_name}")

    def _init_driver(self):
        self.driver = create_driver(self.screen_width, self.screen_height, self.cols, self.worker_index)
        self.logger.info(f"Window [{self.worker_index}] initialized.")

    def _save_hotel(self, hotel_data, url):
        output_folder = os.path.join(self.output_dir, self.province_name)
        os.makedirs(output_folder, exist_ok=True)
        hotel_key = url.split('/')[-1].split('.')[0].replace('-', '_')
        filename = os.path.join(output_folder, f"{hotel_key}.json")

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(hotel_data, f, ensure_ascii=False, indent=4)
        self.logger.info(f"Saved: {hotel_data.get('name', 'Unknown')}")

    def crawl_hotel(self, url):
        if self.stop_event.is_set():
            return False

        full_url = url + "?lang=vi"
        retry_count = 0
        max_retries = 2

        while retry_count <= max_retries and not self.stop_event.is_set():
            try:
                self.driver.get(full_url)
                time.sleep(random.uniform(0.5, 1.5))

                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@data-testid="review-score-component"]'))
                )
                time.sleep(random.uniform(0.8, 1.8))

                html = self.driver.page_source
                name, address, description, rating, number_rating = extract_hotel_data(html)
                evaluation_categories = extract_evaluation_categories(html)
                name_from_reviews, reviews = crawl_all_reviews(self.driver, full_url, self.province_name)

                if name_from_reviews:
                    name = name_from_reviews

                hotel_data = {
                    "name": name,
                    "address": address,
                    "description": description,
                    "rating": rating,
                    "total_rating": number_rating,
                    "evaluation_categories": evaluation_categories,
                    "reviews": reviews,
                }

                self._save_hotel(hotel_data, full_url)
                return True

            except TimeoutException:
                retry_count += 1
                if retry_count <= max_retries:
                    self.logger.warning(f"Timeout (retry {retry_count}/{max_retries}): {url}")
                    time.sleep(random.uniform(3.0, 6.0))
                else:
                    self.logger.error(f"Timeout failed after {max_retries} retries: {url}")
                    return False
            except Exception as e:
                self.logger.error(f"Error on {url}: {str(e)}")
                return False

        return False

    def run(self, urls):
        if not urls:
            return 0, 0

        self._init_driver()
        self.driver.get("https://www.booking.com")
        time.sleep(random.uniform(2.0, 4.0))

        success = 0
        total = len(urls)

        for idx, url in enumerate(urls):
            if self.stop_event.is_set():
                break
            if idx > 0:
                delay(1.5, 3.5)
            if self.crawl_hotel(url):
                success += 1
            self.logger.info(f"[{success}/{total}] Processed.")

        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Driver quit.")
            except:
                pass

        return total, success