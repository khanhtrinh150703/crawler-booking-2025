# data_extractor.py

from bs4 import BeautifulSoup
import re
import logging
import time

# Setup logging (có thể setup lại trong main program)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_hotel_data(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    name, address, description, rating, number_rating = (
        "Not found", "Not found", "Not found", "Not found", "Not found"
    )
    try:
        # ==================================================================
        # 1. ƯU TIÊN CAO NHẤT: data-capla-component-boundary (CHUẨN MỚI 2025)
        # ==================================================================
        capla_div = soup.find(
            "div",
            attrs={"data-capla-component-boundary": "b-property-web-property-page/PropertyHeaderName"}
        )
        if capla_div:
            h2_tag = capla_div.find("h2", class_="pp-header__title")
            if h2_tag:
                name = h2_tag.get_text(strip=True)
                # Giải mã HTML entities (ví dụ: &amp; → &)
                name = re.sub(r'&amp;', '&', name)
                logging.info(f"[Priority 1] Tên khách sạn từ capla: '{name}'")

        # ==================================================================
        # 2. Fallback 1: id="hp_hotel_name" (cũ)
        # ==================================================================
        if not name or name == "Not found":
            hp_name_div = soup.find(id="hp_hotel_name")
            if hp_name_div:
                name_tag = hp_name_div.find("h2")
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    logging.info(f"[Fallback 1] Tên từ hp_hotel_name: '{name}'")

        # ==================================================================
        # 3. Fallback 2: <a id="hp_hotel_name_reviews">
        # ==================================================================
        if not name or name == "Not found":
            name_tag = soup.find("a", id="hp_hotel_name_reviews")
            if name_tag:
                name = name_tag.get_text(strip=True)
                logging.info(f"[Fallback 2] Tên từ hp_hotel_name_reviews: '{name}'")

        # ==================================================================
        # 4. Fallback 3: Từ phần "Các tiện nghi của ..." (div cha → div con)
        # ==================================================================
        if not name or name == "Not found":
            parent_div = soup.find("div", class_=lambda c: c and "aa225776f2" in c.split())
            if parent_div:
                amenities_div = parent_div.find(
                    "div",
                    class_=lambda c: c and all(cls in c.split() for cls in ["a4ac75716e", "f546354b44", "cc045b173b"])
                )
                if amenities_div:
                    header_text = amenities_div.get_text(strip=True)
                    match = re.search(r'của\s+(.+)', header_text, re.IGNORECASE)
                    if match:
                        extracted_name = match.group(1).strip()
                        extracted_name = re.sub(r'[.,\s]+$', '', extracted_name)
                        name = extracted_name
                        logging.info(f"[Fallback 3] Tên từ tiện nghi header: '{name}'")

        # ==================================================================
        # ĐỊA CHỈ, MÔ TẢ, ĐÁNH GIÁ (giữ nguyên như cũ)
        # ==================================================================
        # Địa chỉ
        address_div = soup.find("div", class_="b99b6ef58f cb4b7a25d9 b06461926f")
        if address_div:
            full_address_text = address_div.get_text(separator=' ', strip=True)
            parts = re.split(r'\s{2,}|(?=\sVị trí)', full_address_text, 1)
            address = parts[0].strip() if parts else full_address_text.strip()
            if 'Việt Nam' in address:
                address = address.rsplit('Việt Nam', 1)[0].strip() + ' Việt Nam'

        # Mô tả
        description_tag = soup.find("p", attrs={"data-testid": "property-description"})
        if description_tag:
            description = description_tag.get_text(separator='\n', strip=True)
            description = re.sub(r'\n\s*\n', '\n\n', description).strip()

        # Đánh giá tổng + số lượng
        rating_block = soup.find(attrs={"data-testid": "review-score-component"})
        if rating_block:
            score_container = rating_block.find("div", class_=lambda c: c and "dff2e52086" in c)
            if score_container:
                full_text = score_container.get_text(strip=True)
                match = re.search(r'([\d.,]+)', full_text)
                if match:
                    rating = match.group(1).replace(',', '.')

            number_rating_span = rating_block.find("span", class_=lambda c: c and "eaa8455879" in c)
            if number_rating_span:
                text = number_rating_span.get_text()
                match = re.search(r'([\d\.,]+)', text)
                if match:
                    number_rating = re.sub(r'[.,]', '', match.group(1))

    except Exception as e:
        logging.error(f"Error in extract_hotel_data: {e}")
    
    return name, address, description, rating, number_rating

def extract_evaluation_categories(html_content):
    """
    Trích xuất điểm số chi tiết theo từng hạng mục đánh giá.
    Cập nhật mapping với text chính xác từ log (bao gồm biến thể dấu) và thêm normalize để fuzzy match robust hơn.
    Thêm hỗ trợ ID mapping cho trường hợp cụ thể (nhưng ID có thể không stable).
    """
    import unicodedata  # Để normalize text (xử lý dấu tiếng Việt)
    
    def normalize_text(text):
        """Normalize Unicode text: NFC + remove diacritics cho match fuzzy."""
        # Normalize NFC (kết hợp dấu)
        text = unicodedata.normalize('NFC', text)
        # Option: Remove diacritics nếu cần (unidecode-like, nhưng dùng unicodedata)
        # Để giữ dấu, chỉ NFC là đủ; nếu vẫn fail, uncomment dưới
        # text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        return text.strip().lower()
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Mapping text-to-category (cập nhật từ log: thêm biến thể chính xác)
    category_mapping = {
        # Exact từ log
        "Nhân viên phục vụ": "service_staff",  # 'Nhân viên phục vụ' sau normalize
        "Tiện nghi": "amenities",
        "Sạch sẽ": "cleanliness",  # 'Sạch sẽ' sau NFC
        "Thoải mái": "comfort",
        "Đáng giá tiền": "value_for_money",  # 'Đáng giá tiền'
        "Địa điểm": "location",  # 'Địa điểm'
        "WiFi miễn phí": "free_wifi",
        
        # Fallback cho biến thể phổ biến (nếu log khác)
        "Nhân viên": "service_staff",
        "Giá trị tiền bạc": "value_for_money",
        "Vị trí": "location",
    }
    
    # Mapping ID-to-category (hardcode từ inspect cụ thể, ví dụ cho test)
    # Lưu ý: ID như ":r6t:" thường thay đổi, chỉ dùng cho trang cụ thể
    id_mapping = {
        ":r6t:": "amenities",  # Ví dụ: ID này cho Tiện nghi
        # Thêm ID khác nếu inspect: ":r7u:": "service_staff", etc.
    }
    
    evaluation_categories = {value: None for value in category_mapping.values() if value in ["service_staff", "amenities", "cleanliness", "comfort", "value_for_money", "location", "free_wifi"]}

    # Phần mới: Tìm bằng ID nếu có (cho trường hợp cụ thể)
    for block_id, eng_key in id_mapping.items():
        div_with_id = soup.find("div", id=block_id)
        if div_with_id:
            # Tìm parent block để lấy score (giả sử structure giống review-subscore)
            review_block = div_with_id.find_parent(attrs={"data-testid": "review-subscore"})
            if review_block:
                score = review_block.find("div", class_=lambda c: c and "f87e152973" in c)
                if score:
                    score_text = score.get_text(strip=True).replace(",", ".").strip()
                    score_text = re.sub(r'[^\d.]', '', score_text)
                    try:
                        score_value = float(score_text)
                        evaluation_categories[eng_key] = score_value
                    except ValueError:
                        pass
            # Xác nhận text để debug
            category_name = div_with_id.find("span", class_=lambda c: c and "d96a4619c0" in c)
            if category_name:
                logging.info(f"ID {block_id} -> Text: '{category_name.get_text(strip=True)}' -> Mapped to {eng_key}")

    # Phần chính: Loop qua các block review-subscore (fallback ổn định nhất)
    score_blocks = soup.find_all("div", attrs={"data-testid": "review-subscore"}) 

    for block in score_blocks:
        # Tên hạng mục: class d96a4619c0
        category_name = block.find("span", class_=lambda c: c and "d96a4619c0" in c)
        
        # Điểm số: class f87e152973
        score = block.find("div", class_=lambda c: c and "f87e152973" in c)

        if category_name and score:
            category_name_text_raw = category_name.get_text(strip=True)
            category_name_text = normalize_text(category_name_text_raw)  # Normalize cho match
            
            score_text = score.get_text(strip=True) 
            score_text = score_text.replace(",", ".").strip()
            score_text = re.sub(r'[^\d.]', '', score_text)

            try:
                score_value = float(score_text)
            except ValueError:
                score_value = None

            if score_value is not None:
                matched = False
                # Exact match trước (sau normalize)
                for vn_key, eng_key in category_mapping.items():
                    normalized_key = normalize_text(vn_key)
                    if category_name_text == normalized_key:
                        evaluation_categories[eng_key] = score_value
                        matched = True
                        break
                
                if not matched:
                    # Fuzzy match: Kiểm tra chứa từ khóa chính (sau normalize)
                    for vn_key, eng_key in category_mapping.items():
                        normalized_key = normalize_text(vn_key)
                        if normalized_key in category_name_text:  # Ví dụ: "nhân viên" in "nhân viên phục vụ"
                            evaluation_categories[eng_key] = score_value
                            matched = True
                            break
                
                # Debug: Log text thực tế (raw và normalized) để kiểm tra
                # logging.info(f"Found category: '{category_name_text_raw}' (norm: '{category_name_text}') -> Score: {score_value} -> Matched: {matched}")

    return evaluation_categories