import os
import re

# Đường dẫn (local, chỉnh sửa theo máy bạn)
BASE_FOLDER = r"D:\private\data"
OUTPUT_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs', 'analysis_results')
CHARTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs', 'charts')
os.makedirs(CHARTS_DIR, exist_ok=True)

ANALYSIS_RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs', 'analysis_results')
os.makedirs(ANALYSIS_RESULTS_DIR, exist_ok=True)

DEFAULT_SCORE = 5

# Regex và lists từ notebook
EMOJI_PATTERN = re.compile(
    "["
    u"\U0001F600-\U0001F64F"  # faces
    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
    u"\U0001F680-\U0001F6FF"  # transport & map symbols
    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
    u"\U00002500-\U00002BEF"  # chinese char
    u"\U00002702-\U000027B0"
    u"\U000024C2-\U0001F251"
    u"\U0001f926-\U0001f937"
    u'\U00010000-\U0010ffff'
    "]+", flags=re.UNICODE
)

VIETNAMESE_CHARS = "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỷỹỵđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỈĨỊÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỶỸỴĐ"

VIETNAMESE_WORDS = [
    "và", "hoặc", "nhưng", "vì", "nên", "thì", "mà", "là", "có", "không",
    "rất", "tốt", "đẹp", "sạch sẽ", "tiện nghi", "thoải mái", "phòng", "khách sạn",
    "nhân viên", "dịch vụ", "vị trí", "gần", "xa", "trung tâm", "giá cả", "hợp lý",
    "thân thiện", "tuyệt vời", "kém", "tệ", "bẩn", "ồn ào", "yên tĩnh", "ngon", "dở",
    "đồ ăn", "bữa sáng", "bữa trưa", "bữa tối", "hồ bơi", "bãi biển", "phục vụ",
    "đặt phòng", "trả phòng", "nhận phòng", "wifi", "internet", "máy lạnh", "điều hòa",
    "thang máy", "cửa sổ", "giường", "chăn", "gối", "nệm", "tắm", "vòi sen"
]

VIETNAMESE_STOPWORDS = [
    "là", "và", "của", "có", "không", "được", "trong", "đã", "cho", "với", "này", "đó",
    "các", "để", "những", "một", "rất", "cũng", "khi", "như", "về", "từ", "tại", "tới",
    "thì", "vì", "nên", "lúc", "mà", "còn", "bởi", "theo", "vào", "ra", "lên", "xuống",
    "tôi", "tầm", "tạm", "nơi", "thư", "mọi", "đâu", "mình", "ai", "khi", "sẽ", "đều",
    "chỉ", "mới", "thật", "quá", "đến", "nhất", "đủ", "chỉ", "đang", "trước", "sau",
    "đây", "đấy", "thì", "đó", "này", "nhiều", "ít", "hơn", "thôi", "tuy", "hay", "bởi",
    "ở", "đi", "làm", "nếu", "tuy", "hoặc", "đều", "cứ", "đã", "rồi", "xong", "phòng", "khách",
    "tam", "nhung", "nhieu", "duoc", "minh", "khong", "ngay", "cac", "nha", "rat", "co",
    "khach san", "can", "tai", "cua", "tot", "nay", "chi", "tren", "day", "hon"
]

NON_VIETNAMESE_LANGS = ['en', 'fr', 'es', 'de', 'it', 'pt', 'nl', 'ru', 'ja', 'ko', 'zh-cn', 'zh-tw', 'ar', 'hi', 'id', 'ms', 'th', 'tr']

FOREIGN_WORDS = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'in', 'on', 'at',
        'de', 'le', 'la', 'les', 'du', 'des', 'un', 'une', 'et', 'en',
        'el', 'los', 'las', 'es', 'muy', 'bien', 'con', 'por', 'para',
        'je', 'tu', 'il', 'nous', 'vous', 'ils', 'elle', 'elles',
        'das', 'der', 'die', 'ein', 'eine', 'mit', 'für', 'ist', 'und'
    }

# Mapping: thư mục → tên hiển thị (ưu tiên địa danh du lịch)
PROVINCE_MAPPING = {
        # Tỉnh thành chính thức
        "an-giang": "An Giang", "bac-lieu": "Bạc Liêu", "bac-giang": "Bắc Giang",
        "bac-kan": "Bắc Kạn", "bac-ninh": "Bắc Ninh", "ben-tre": "Bến Tre",
        "binh-dinh": "Bình Định", "binh-duong": "Bình Dương", "binh-phuoc": "Bình Phước",
        "binh-thuan": "Bình Thuận", "ca-mau": "Cà Mau", "can-tho": "Cần Thơ",
        "cao-bang": "Cao Bằng", "da-nang": "Đà Nẵng", "dak-lak": "Đắk Lắk",
        "dak-nong": "Đắk Nông", "dien-bien": "Điện Biên", "dong-nai": "Đồng Nai",
        "dong-thap": "Đồng Tháp", "gia-lai": "Gia Lai", "ha-giang": "Hà Giang",
        "ha-nam": "Hà Nam", "ha-noi": "Hà Nội", "ha-tinh": "Hà Tĩnh",
        "hai-duong": "Hải Dương", "hai-phong": "Hải Phòng", "hau-giang": "Hậu Giang",
        "hoa-binh": "Hòa Bình", "hung-yen": "Hưng Yên", "khanh-hoa": "Nha Trang",
        "kien-giang": "Phú Quốc", "kon-tum": "Kon Tum", "lai-chau": "Lai Châu",
        "lam-dong": "Đà Lạt", "lang-son": "Lạng Sơn", "lao-cai": "Sapa",
        "long-an": "Long An", "nam-dinh": "Nam Định", "nghe-an": "Nghệ An",
        "ninh-binh": "Ninh Bình", "ninh-thuan": "Ninh Thuận", "phu-tho": "Phú Thọ",
        "phu-yen": "Phú Yên", "quang-binh": "Quảng Bình", "quang-nam": "Hội An",
        "quang-ngai": "Quảng Ngãi", "quang-ninh": "Hạ Long", "quang-tri": "Quảng Trị",
        "soc-trang": "Sóc Trăng", "son-la": "Sơn La", "tay-ninh": "Tây Ninh",
        "thai-binh": "Thái Bình", "thai-nguyen": "Thái Nguyên", "thanh-hoa": "Thanh Hóa",
        "thua-thien-hue": "Huế", "tien-giang": "Tiền Giang", "tra-vinh": "Trà Vinh",
        "tuyen-quang": "Tuyên Quang", "vinh-long": "Vĩnh Long", "vinh-phuc": "Vĩnh Phúc",
        "yen-bai": "Yên Bái",

        # Tên viết tắt / biến thể
        "hanoi": "Hà Nội", "ha-noi": "Hà Nội",
        "ho-chi-minh": "TP.HCM", "hcm": "TP.HCM", "tphcm": "TP.HCM",
        "sai-gon": "TP.HCM", "saigon": "TP.HCM", "tphcm": "TP.HCM",
        "phu-quoc": "Phú Quốc", "phu_quoc": "Phú Quốc",
        "da-lat": "Đà Lạt", "dalat": "Đà Lạt",
        "ha-long": "Hạ Long", "vung-tau": "Vũng Tàu",
        "hoi-an": "Hội An", "nha-trang": "Nha Trang", "sapa": "Sapa",
        "mui-ne": "Phan Thiết", "phan-thiet": "Phan Thiết",
    }