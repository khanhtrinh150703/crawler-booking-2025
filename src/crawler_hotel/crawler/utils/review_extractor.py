# review_extractor.py
# Module for extracting reviews with pagination handling and error fixes

from bs4 import BeautifulSoup
import re
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException

def convert_vietnamese_date_to_standard(date_str):
    """
    Convert Vietnamese date format to standard DD/MM/YYYY.
    Handles formats like "Đánh giá ngày 15 tháng 10 2023."
    """
    if not date_str:
        return None

    # Convert Vietnamese month names to numbers
    vietnamese_months = {
        "tháng 1": "01", "tháng 2": "02", "tháng 3": "03", "tháng 4": "04",
        "tháng 5": "05", "tháng 6": "06", "tháng 7": "07", "tháng 8": "08",
        "tháng 9": "09", "tháng 10": "10", "tháng 11": "11", "tháng 12": "12",
    }
    for vn_month, num_month in vietnamese_months.items():
        date_str = date_str.replace(vn_month, num_month)

    # Extract day, month, year (flexible parsing)
    parts = date_str.split()
    if len(parts) >= 8 and "ngày" in date_str:
        # Full format: "Đánh giá ngày [day] [month] [year]."
        day_idx = parts.index('ngày') + 1
        day = parts[day_idx]
        month = parts[day_idx + 1]
        year = parts[day_idx + 3] if len(parts) > day_idx + 3 else parts[-1]
    else:
        # Shorter format fallback
        day = next((p for p in parts if p.isdigit() and 1 <= int(p) <= 31), parts[0])
        month = next((p for p in parts if p in vietnamese_months.values()), parts[2])
        year = next((p for p in parts if len(p) == 4 and p.isdigit()), parts[-1])

    try:
        formatted_date = f"{int(day):02d}/{month}/{year}"
        return formatted_date
    except:
        return None

def extract_hotel_name_dynamic(driver, timeout=20):
    """
    TÌM CHÍNH XÁC thẻ <h2 id="...:title"> trong tab #tab-reviews
    → CHỜ JS RENDER XONG → TRÍCH XUẤT TÊN
    """
    try:
        logging.info("Đang chờ tiêu đề đánh giá hiện ra...")

        # BƯỚC 1: Đợi thẻ <h2> có id kết thúc bằng "-title"
        h2_elem = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "h2[id$='-title']")
            )
        )

        # BƯỚC 2: Lấy text
        full_text = h2_elem.text.strip()
        logging.info(f"Tiêu đề tìm thấy: '{full_text}'")

        # BƯỚC 3: Regex lấy tên sau "về "
        match = re.search(r'về\s+([^–\-]+)', full_text)
        if match:
            name = match.group(1).strip()
            name = re.sub(r'[.,\s]+$', '', name)  # Xóa dấu chấm, phẩy cuối
            print(f"\nTÊN KHÁCH SẠN: {name}\n")
            return name
        else:
            print("TÊN KHÁCH SẠN: Not found (không có 'về ')")
            return None

    except Exception as e:
        logging.error(f"Lỗi: {e}")
        driver.save_screenshot("error_hotel_name.png")  # Debug
        print("TÊN KHÁCH SẠN: Error (xem ảnh lỗi)")
        return None

def extract_reviews(soup):
    """
    Extract review data from the current page's soup.
    Returns list of review dicts.
    """
    reviews = []
    review_cards = soup.find_all("div", {"data-testid": "review-card"})
    
    for review in review_cards:
        # Reviewer info
        reviewer_avatar_elem = review.find("div", {"data-testid": "review-avatar"})
        if not reviewer_avatar_elem:
            continue
        reviewer_info = reviewer_avatar_elem.parent
        
        reviewer_name_elem = reviewer_info.find("div", class_="b08850ce41 f546354b44")
        reviewer_name = reviewer_name_elem.get_text(strip=True) if reviewer_name_elem else None
        
        reviewer_country_elem = reviewer_info.find("span", class_="d838fb5f41 aea5eccb71")
        reviewer_country = reviewer_country_elem.get_text(strip=True) if reviewer_country_elem else None
        
        reviewer_avatar_img = reviewer_info.find("img", {"role": "presentation"})
        reviewer_avatar = reviewer_avatar_img["src"] if reviewer_avatar_img else None

        # Stay info
        stay_info_elem = review.find("div", {"data-testid": "review-stay-info"})
        if not stay_info_elem:
            continue
        
        room_type_elem = stay_info_elem.find("span", {"data-testid": "review-room-name"})
        room_type = room_type_elem.get_text(strip=True) if room_type_elem else None
        
        nights_elem = stay_info_elem.find("span", {"data-testid": "review-num-nights"})
        date_elem = stay_info_elem.find("span", {"data-testid": "review-stay-date"})
        stay_duration = f"{nights_elem.get_text(strip=True)} {date_elem.get_text(strip=True)}" if nights_elem and date_elem else None
        
        traveler_type_elem = stay_info_elem.find("span", {"data-testid": "review-traveler-type"})
        group_type = traveler_type_elem.get_text(strip=True) if traveler_type_elem else None

        # Content
        content_group = review.find("div", {"role": "group", "aria-label": "Nội dung đánh giá"})
        if not content_group:
            continue
        
        date_elem = content_group.find("span", {"data-testid": "review-date"})
        review_date = convert_vietnamese_date_to_standard(date_elem.get_text(strip=True)) if date_elem else None
        
        title_elem = content_group.find("h4", {"data-testid": "review-title"})
        review_title = title_elem.get_text(strip=True) if title_elem else None
        
        score_elem = content_group.find("div", {"data-testid": "review-score"})
        review_score = None
        if score_elem:
            # Prefer the hidden div with clean numeric score
            hidden_score_div = score_elem.find("div", {"aria-hidden": "true"})
            if hidden_score_div:
                score_text = hidden_score_div.get_text(strip=True)
            else:
                # Fallback to full text extraction
                score_text = score_elem.get_text(strip=True)
            
            match = re.search(r"\d+", score_text)
            if match:
                review_score = float(match.group(0))
        
        positive_elem = content_group.find("div", {"data-testid": "review-positive-text"})
        positive_text = positive_elem.get_text(strip=True) if positive_elem else None
        
        negative_elem = content_group.find("div", {"data-testid": "review-negative-text"})
        negative_text = negative_elem.get_text(strip=True) if negative_elem else None

        reviews.append({
            "reviewer": {
                "name": reviewer_name,
                "avatar": reviewer_avatar,
                "country": reviewer_country,
            },
            "review": {
                "date": review_date,
                "rating": review_title,  # Title as qualitative rating
                "score": review_score,
                "room_type": room_type,
                "stay_duration": stay_duration,
                "group_type": group_type,
                "comment_positive": positive_text,
                "comment_negative": negative_text,
            },
        })
    
    # logging.info(f"Extracted {len(reviews)} reviews from current page.")
    return reviews

def crawl_all_reviews(driver, base_url,province, max_pages=None):
    """
    Crawl all reviews: navigate to #tab-reviews, paginate, extract.
    Handles ElementNotInteractableException with waits and JS click.
    """
    all_reviews = []
    
    # Navigate to reviews tab
    reviews_url = f"{base_url}#tab-reviews"
    driver.get(reviews_url)
    time.sleep(3)  # Initial load
    
    hotel_name = extract_hotel_name_dynamic(driver)
    
    # Select sorter to "NEWEST_FIRST" (Mới nhất)
    try:
        sorter_select = Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "reviewListSorters"))
        ))
        sorter_select.select_by_value("NEWEST_FIRST")
        time.sleep(2)  # Wait for page to reload with new sorting
        logging.info("Sorter changed to 'NEWEST_FIRST' (Mới nhất).")
    except Exception as e:
        logging.warning(f"Failed to change sorter: {str(e)}")
    
    page_count = 0
    while True:
        try:
            # Extract current page
            soup = BeautifulSoup(driver.page_source, "html.parser")
            current_reviews = extract_reviews(soup)
            all_reviews.extend(current_reviews)
            
            page_count += 1
            if max_pages and page_count >= max_pages:
                logging.info(f"Reached max_pages ({max_pages}). Stopping.")
                break
            
            # Wait for and interact with next button
            next_selector = "button[aria-label='Trang sau']"
            try:
                # Wait for clickable
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, next_selector))
                )
                
                # Scroll into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                time.sleep(1)
                
                # Check enabled
                if not next_button.is_enabled():
                    logging.info("Next button disabled - no more pages.")
                    break
                
                # Click (try normal, fallback to JS)
                try:
                    next_button.click()
                except ElementNotInteractableException:
                    logging.warning("Normal click failed, using JS click.")
                    driver.execute_script("arguments[0].click();", next_button)
                
                time.sleep(2)  # Page load
                
            except TimeoutException:
                logging.info("Next button not clickable/visible - ending pagination.")
                break
                
        except Exception as e:
            logging.error(f"Pagination error: {str(e)}")
            # Save screenshot for debug
            driver.save_screenshot(f"pagination_error_page_{page_count}_{province}.png")
            break
    
    logging.info(f"Total reviews crawled: {len(all_reviews)}")
    return hotel_name, all_reviews