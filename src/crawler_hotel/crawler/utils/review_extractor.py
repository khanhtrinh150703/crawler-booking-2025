# review_extractor.py
# Module for extracting reviews from Booking.com with robust pagination & language filtering

import re
import time
import logging
from typing import List, Dict, Optional, Tuple

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException

from config.config import SELECT_LANGUAGE  # Giữ nguyên tên biến bạn đang dùng


# =============================================================================
# UTILS
# =============================================================================

def convert_vietnamese_date_to_standard(date_str: Optional[str]) -> Optional[str]:
    """Convert 'Đánh giá ngày 15 tháng 10 2023' → '15/10/2023'"""
    if not date_str:
        return None

    vietnamese_months = {
        "tháng 1": "01", "tháng 2": "02", "tháng 3": "03", "tháng 4": "04",
        "tháng 5": "05", "tháng 6": "06", "tháng 7": "07", "tháng 8": "08",
        "tháng 9": "09", "tháng 10": "10", "tháng 11": "11", "tháng 12": "12",
    }

    text = date_str.lower()
    for vn, num in vietnamese_months.items():
        text = text.replace(vn, num)

    # Extract day/month/year by keywords
    match = re.search(r"ngày\D*(\d{1,2})\D*(\d{1,2})\D*(\d{4})", text)
    if match:
        day, month, year = match.groups()
        return f"{int(day):02d}/{month}/{year}"
    return None


# =============================================================================
# EXTRACT HOTEL NAME
# =============================================================================

def extract_hotel_name_dynamic(driver, timeout: int = 20) -> Optional[str]:
    """Extract hotel name from dynamic h2[id$='-title'] in reviews tab."""
    try:
        logging.info("Đang chờ tiêu đề khách sạn trong tab đánh giá...")

        h2 = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h2[id$='-title']"))
        )
        full_text = h2.text.strip()
        logging.info(f"Tiêu đề tìm thấy: '{full_text}'")

        match = re.search(r"về\s+([^–\-]+)", full_text)
        if match:
            name = match.group(1).strip()
            name = re.sub(r"[.,\s]+$", "", name)
            logging.info(f"→ Tên khách sạn: {name}")
            return name

        logging.warning("Không tìm thấy tên khách sạn (không có 'về ')")
        return None

    except Exception as e:
        logging.error(f"Lỗi khi lấy tên khách sạn: {e}")
        driver.save_screenshot("error_hotel_name.png")
        return None


# =============================================================================
# FILTERS: Language + Sorter
# =============================================================================

def _select_review_language(driver) -> None:
    """Select Vietnamese reviews (value = 'vi')"""
    try:
        dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select[data-testid='languages']"))
        )
        Select(dropdown).select_by_value(SELECT_LANGUAGE)
        time.sleep(2)
        logging.info(f"Đã chọn ngôn ngữ đánh giá: {SELECT_LANGUAGE.upper()}")
    except Exception as e:
        logging.warning(f"Không thể chọn ngôn ngữ đánh giá: {e}")


def _select_newest_first(driver) -> None:
    """Sort reviews by newest first"""
    try:
        sorter = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "reviewListSorters"))
        )
        Select(sorter).select_by_value("NEWEST_FIRST")
        time.sleep(2)
        logging.info("Đã sắp xếp theo 'Mới nhất'")
    except Exception as e:
        logging.warning(f"Không thể thay đổi bộ lọc sắp xếp: {e}")


def apply_review_filters(driver) -> None:
    """Apply both language and sorting filters"""
    _select_review_language(driver)
    _select_newest_first(driver)


# =============================================================================
# EXTRACT ONE PAGE
# =============================================================================

def extract_reviews_from_page(soup: BeautifulSoup) -> List[Dict]:
    """Extract all review cards from current page source"""
    reviews = []
    cards = soup.find_all("div", {"data-testid": "review-card"})

    for card in cards:
        review = _extract_single_review(card)
        if review:
            reviews.append(review)

    return reviews


def _extract_single_review(card) -> Optional[Dict]:
    # Reviewer
    avatar_div = card.find("div", {"data-testid": "review-avatar"})
    if not avatar_div:
        return None
    reviewer_info = avatar_div.parent

    name = reviewer_info.find("div", class_= "b08850ce41 f546354b44")
    country = reviewer_info.find("span", class_="d838fb5f41 aea5eccb71")
    avatar_img = reviewer_info.find("img", {"role": "presentation"})

    # Stay info
    stay_info = card.find("div", {"data-testid": "review-stay-info"})
    if not stay_info:
        return None

    room = stay_info.find("span", {"data-testid": "review-room-name"})
    nights = stay_info.find("span", {"data-testid": "review-num-nights"})
    stay_date = stay_info.find("span", {"data-testid": "review-stay-date"})
    traveler_type = stay_info.find("span", {"data-testid": "review-traveler-type"})

    # Content
    content = card.find("div", {"role": "group", "aria-label": "Nội dung đánh giá"})
    if not content:
        return None

    date_elem = content.find("span", {"data-testid": "review-date"})
    title_elem = content.find("h4", {"data-testid": "review-title"})
    score_elem = content.find("div", {"data-testid": "review-score"})
    pos_elem = content.find("div", {"data-testid": "review-positive-text"})
    neg_elem = content.find("div", {"data-testid": "review-negative-text"})

    # Extract score (prefer hidden clean value)
    score = None
    if score_elem:
        hidden = score_elem.find("div", {"aria-hidden": "true"})
        score_text = hidden.get_text(strip=True) if hidden else score_elem.get_text(strip=True)
        score_match = re.search(r"\d+[.,]?\d*", score_text)
        if score_match:
            score = float(score_match.group(0).replace(",", "."))

    return {
        "reviewer": {
            "name": name.get_text(strip=True) if name else None,
            "country": country.get_text(strip=True) if country else None,
            "avatar": avatar_img["src"] if avatar_img and avatar_img.get("src") else None,
        },
        "review": {
            "date": convert_vietnamese_date_to_standard(date_elem.get_text(strip=True)) if date_elem else None,
            "rating": title_elem.get_text(strip=True) if title_elem else None,
            "score": score,
            "room_type": room.get_text(strip=True) if room else None,
            "stay_duration": f"{nights.get_text(strip=True) if nights else ''} {stay_date.get_text(strip=True) if stay_date else ''}".strip(),
            "group_type": traveler_type.get_text(strip=True) if traveler_type else None,
            "comment_positive": pos_elem.get_text(strip=True) if pos_elem else None,
            "comment_negative": neg_elem.get_text(strip=True) if neg_elem else None,
        }
    }


# =============================================================================
# PAGINATION
# =============================================================================

def _click_next_page(driver) -> bool:
    """Return True if successfully moved to next page, False if no more pages"""
    try:
        next_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Trang sau']"))
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
        time.sleep(0.8)

        if not next_btn.is_enabled():
            logging.info("Nút 'Trang sau' bị disable → hết trang")
            return False

        try:
            next_btn.click()
        except ElementNotInteractableException:
            driver.execute_script("arguments[0].click();", next_btn)

        time.sleep(2)
        return True

    except TimeoutException:
        logging.info("Không tìm thấy nút 'Trang sau' → kết thúc phân trang")
        return False


# =============================================================================
# MAIN CRAWL FUNCTION
# =============================================================================

def crawl_all_reviews(
    driver,
    base_url: str,
    province: str,
    max_pages: Optional[int] = None
) -> Tuple[Optional[str], List[Dict]]:
    """
    Main function: crawl all Vietnamese newest reviews of a hotel.
    Returns (hotel_name, list_of_reviews)
    """
    all_reviews = []
    driver.get(f"{base_url}#tab-reviews")
    time.sleep(3)

    hotel_name = extract_hotel_name_dynamic(driver)
    apply_review_filters(driver)

    page_count = 0
    while True:
        page_count += 1
        logging.info(f"Đang crawl trang {page_count}...")

        soup = BeautifulSoup(driver.page_source, "html.parser")
        page_reviews = extract_reviews_from_page(soup)
        all_reviews.extend(page_reviews)
        logging.info(f"Trang {page_count}: {len(page_reviews)} reviews → Tổng: {len(all_reviews)}")

        if max_pages and page_count >= max_pages:
            logging.info(f"Đã đạt giới hạn max_pages = {max_pages}")
            break

        if not _click_next_page(driver):
            break

        # Optional: small break to be gentle
        time.sleep(1)

    logging.info(f"HOÀN TẤT! Tổng cộng thu thập được {len(all_reviews)} đánh giá.")
    return hotel_name, all_reviews