import os
import re
from typing import Dict

# Thư mục data đầu vào
BASE_FOLDER = r"D:\private\data"
# Thư mục data đầu ra
DATA_DIR = r"D:\private\crawler-booking-2025\src\data_processing\data"

OUTPUT_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs', 'analysis_results')
CHARTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs', 'charts')
os.makedirs(CHARTS_DIR, exist_ok=True)

ANALYSIS_RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs', 'analysis_results')
os.makedirs(ANALYSIS_RESULTS_DIR, exist_ok=True)

# Điểm mặc định để loại bỏ
DEFAULT_SCORE = 5

# Thứ tự cột CHUẨN 
EXPECTED_COLUMNS = [
    "hotel_name",
    "country",
    "review_name",
    "province",          
    "score",
    "hotel_avg_score",
    "deviation",
    "date_str",
    "month_year",
    "stay_duration",
    "room_type",
    "group_type",
    "rating",
    "positive_comment",
    "negative_comment",
    "combined_text",
    "text_length",
    "is_vietnamese",
]

# Các cột chính chứa nội dung review: bình luận tích cực, điểm rating, bình luận tiêu cực.
CONTENT_COLUMNS = ['positive_comment', 'rating', 'negative_comment']

# Cột chứa điểm rating (có thể là số hoặc text cần xử lý thêm).
RATING_COLUMN = 'rating'             

# Cột mặc định chứa thông tin quốc gia của review/người dùng.
COUNTRY_COLUMN = 'country'

# Các tên cột có thể chứa quốc gia, dùng để tự động tìm cột phù hợp trong dataset khác nhau.
POSSIBLE_COUNTRY_COLUMNS = ['country', 'user_country', 'location', 'region']

# Các tên cột có thể chứa nội dung bình luận, giúp code linh hoạt với nhiều nguồn dữ liệu.
POSSIBLE_COMMENT_COLUMNS = ['positive_comment', 'review_text', 'comment', 'content', 'review']

# Pattern regex để phát hiện và loại bỏ emoji, biểu tượng cảm xúc, text smiley phổ biến
EMOJI_PATTERN = re.compile(  
    "["
    u"\U0001F600-\U0001F64F"  # emoticons (mặt cười, mặt buồn,...)
    u"\U0001F300-\U0001F5FF"  # symbols & pictographs (biểu tượng, hình vẽ)
    u"\U0001F680-\U0001F6FF"  # transport & map symbols (xe cộ, bản đồ)
    u"\U0001F1E0-\U0001F1FF"  # flags (cờ các nước)
    u"\U00002500-\U00002BEF"  # một số ký tự tiếng Trung
    u"\U00002702-\U000027B0"  # dingbats (ký tự trang trí)
    u"\U000024C2-\U0001F251"  # enclosed characters
    u"\U0001f926-\U0001f937"  # các emoji bổ sung (người nhún vai, mặt che miệng,...)
    u"\U00010000-\U0010ffff"  # vùng unicode bổ sung (bao quát hầu hết emoji khác)
    u"::-?D+"                  # :D, :-D, :DD,... (cười to)
    u"::-?\\)+"                # :), :-), :)),... (cười)
    u"=\\)+"                    # =) (cười)
    u":'-?\\)+"                 # :') (cười có nước mắt)
    u";-?\\)+"                  # ;) (nháy mắt)
    u":\\(+"                    # :( (buồn)
    u":/-?\\("                 # :/ (khó chịu)
    u"<3"                      # trái tim
    u"!"                       # dấu chấm than
    u"?"                       # dấu hỏi
    u"_"                       # dấu gạch dưới
    "]+",
    flags=re.UNICODE
)

# Các từ tiếng nước ngoài thông dụng
FOREIGN_INDICATORS = [
    'very', 'good', 'great', 'room', 'view', 'staff', 'clean', 'excellent', 'nice', 'perfect',
    'recommend', 'breakfast', 'location', 'comfortable', 'friendly',
    'très', 'tres', 'bon', 'chambre', 'vue', 'accueil', 'lit', 'balcon', 'spacieuse', 'agréable',
    'bien', 'décorée', 'confortable', 'douche', 'excellent', 'parfait', 'propre', 'personnel',
    'calme', 'coucher de soleil', 'établissement', 'recommandons', 'super', 'magnifique',
    'piscine', 'petit déjeuner', 'service', 'prix', 'dispo'
]

# Chuỗi chứa tất cả các ký tự tiếng Việt có dấu (nguyên âm + đ), dùng để kiểm tra/normalize text tiếng Việt
VIETNAMESE_CHARS = "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóọỏõôồốộổỗơờớợởỡùúủũụưừứựửữỳýỷỹỵđÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỦŨỤƯỪỨỰỬỮỲÝỶỸỴĐ"

# Test string ký tự Slav nguy hiểm (Czech/Slovak/Polish diacritics) - check Unicode/encoding bugs
CZECH_SLAVIC_DANGER = "čďěňřšťžůýáéíóúôľĺŕąęćłńóśźżČĎĚŇŘŠŤŽŮÝÁÉÍÓÚÔĽĹŔĄĘĆŁŃÓŚŹŻ"

# Ký tự tiếng Đức "nguy hiểm" (diacritics + ß) - dùng để test Unicode/encoding bugs với text Đức
GERMAN_DANGER_CHARS = "äöüßÄÖÜẞ"

# Các từ phổ biến trong review tiếng Pháp (thường gặp ở booking/hotel review từ khách Pháp)
FRENCH_COMMON_WORDS = [
    "très", "bien", "chambre", "propre", "accueil", "personnel", "bon", "excellent",
    "parfait", "confortable", "lit", "douche", "petit", "déjeuner", "merci", "hôtel",
    "séjour", "recommande", "calme", "propreté", "impeccable", "récent", "bâtiment",
    "familial", "gentillesse", "propriétaire", "attentionnée", "convivialité", "idéal",
    "étape", "disponible", "sympathique", "accueillant", "calme", "fenêtre", "ras",
    "personnel", "châssis", "obstacle", "sora", "pension", "villa", "moderne", "piscine"
]

# Các từ phổ biến trong review tiếng Ý (thường gặp ở khách du lịch Ý)
ITALIAN_COMMON_WORDS = [
    "ottima", "pulizia", "struttura", "moderna", "possibilità", "noleggio", "motorini",
    "disponibilità", "organizzare", "tour", "personale", "disponibile", "logistica",
    "trasferimento", "città", "difficoltà", "comunicazione", "lingua", "inglese",
    "buona", "bella", "posizione", "camera", "colazione", "gentile", "accogliente"
]


# Các từ phổ biến trong review tiếng Anh
ENGLISH_COMMON_WORDS = [
    "very", "clean", "helpful", "staff", "location", "room", "good", "great", "nice",
    "friendly", "recommend", "breakfast", "comfortable", "value", "money", "host",
    "family", "scooter", "border", "mosquito", "home", "away", "experience", "highly",
    "wonderful", "amazing", "best", "perfect", "lovely", "quiet", "central", "excellent",
    "super", "fantastic", "awesome", "beautiful", "delicious", "thank", "thanks",
    "choice", "and", "receptionists", "kind", "is", "this", "place", "the", "absolutely",
    "everything", "stay", "stayed", "night", "nights", "hotel", "homestay", "owner", "owners",
    "welcome", "welcoming", "made", "feel", "like", "house", "air", "conditioning",
    "bed", "shower", "hot", "water", "wifi", "strong", "fast", "free", "included",
    "fruit", "fruits", "tea", "coffee", "provided", "every", "day", "terrace", "view",
    "river", "market", "walking", "distance", "close", "near", "easy", "get", "to",
    "around", "motorbike", "bike", "rent", "rental", "tour", "boat", "trip", "bus",
    "ticket", "booked", "arranged", "help", "with", "transport", "taxi", "grab",
    "food", "restaurant", "nearby", "street", "local", "noodles",
    "rice", "fresh", "tasty", "cheap", "price", "reasonable", "worth", "it",
    "definitely", "will", "come", "back", "again", "return", "next", "time",
    "peaceful", "relaxing", "convenient", "spacious", "modern", "facilities",
    "service", "hospitality", "warm", "smile", "always", "ready", "assist",
    "nothing", "too", "much", "trouble", "top", "notch", "outstanding", "exceptional",
    "gem", "hidden", "spot", "must", "highly_recommend", "cannot", "say", "enough",
    "about", "how", "wonderful", "fantastic_place", "perfect_location", "lovely_host",
    "extremely", "kind", "generous", "attentive", "care", "details", "small", "touches",
    "fan", "balcony", "pool", "swimming", "garden", "quiet_area", "no", "noise",
    "sleep", "well", "comfortable_bed", "pillows", "towels", "toiletries", "shampoo",
    "soap", "laundry", "service", "motorbike_parking", "secure", "safe", "area",
    "english", "spoken", "communication", "easy", "no_problem", "thank_you", "thanks_again",
    "cheers", "all", "best_wishes", "see", "you", "soon", "hope", "visit", "again"
]

# Các từ phổ biến trong review tiếng Việt
VIETNAMESE_WORDS = [
    "và", "hoặc", "nhưng", "vì", "nên", "thì", "mà", "là", "có", "không",
    "rất", "tốt", "đẹp", "sạch sẽ", "tiện nghi", "thoải mái", "phòng", "khách sạn",
    "nhân viên", "dịch vụ", "vị trí", "gần", "xa", "trung tâm", "giá cả", "hợp lý",
    "thân thiện", "tuyệt vời", "kém", "tệ", "bẩn", "ồn ào", "yên tĩnh", "ngon", "dở",
    "đồ ăn", "bữa sáng", "bữa trưa", "bữa tối", "hồ bơi", "bãi biển", "phục vụ",
    "đặt phòng", "trả phòng", "nhận phòng", "wifi", "internet", "máy lạnh", "điều hòa",
    "thang máy", "cửa sổ", "giường", "chăn", "gối", "nệm", "tắm", "vòi sen"
]

# Stopwords tiếng Việt 
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

# Các ngôn ngữ KHÔNG phải tiếng Việt thường gặp trong review khách sạn/du lịch quốc tế
NON_VIETNAMESE_LANGS = [
    'en',    # English
    'fr',    # French
    'es',    # Spanish
    'de',    # German
    'it',    # Italian
    'pt',    # Portuguese (bao gồm Brazil pt-br)
    'nl',    # Dutch
    'ru',    # Russian
    'ja',    # Japanese
    'ko',    # Korean
    'zh-cn', # Simplified Chinese (Trung Quốc đại lục)
    'zh-tw', # Traditional Chinese (Đài Loan, Hồng Kông)
    'ar',    # Arabic
    'hi',    # Hindi
    'id',    # Indonesian
    'ms',    # Malay
    'th',    # Thai
    'tr',    # Turkish
]

# Tập hợp các từ cực kỳ phổ biến (stopwords cơ bản) của một số ngôn ngữ châu Âu chính
FOREIGN_WORDS = {
    # English
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'in', 'on', 'at',
    'and', 'of', 'for', 'with', 'that', 'this', 'it', 'you', 'i', 'we',
    
    # French
    'de', 'le', 'la', 'les', 'du', 'des', 'un', 'une', 'et', 'en',
    'je', 'tu', 'il', 'nous', 'vous', 'ils', 'elle', 'elles', 'que', 'dans',
    
    # Spanish
    'el', 'los', 'las', 'es', 'muy', 'bien', 'con', 'por', 'para', 'del',
    'un', 'una', 'y', 'en', 'se', 'lo', 'al', 'de', 'su', 'me',
    
    # German
    'das', 'der', 'die', 'ein', 'eine', 'mit', 'für', 'ist', 'und', 'zu',
    'den', 'dem', 'im', 'am', 'auf', 'aus', 'nach', 'bei', 'von', 'ich',
    
    # Italian (thêm để tăng độ bao phủ)
    'il', 'la', 'di', 'e', 'in', 'un', 'una', 'per', 'che', 'del',
    'lo', 'gli', 'le', 'si', 'da', 'con', 'su', 'non', 'ha', 'è'
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


# -----------------------------
# Cấu hình ánh xạ từ (có thể di chuyển ra config riêng sau)
# -----------------------------
DEFAULT_VIETNAMESE_ABBREVIATION_MAPPING: Dict[str, str] = {
    # Người xưng hô (thân mật)
    "a": "anh",
    "c": "chị",
    "e": "em",
    "vk": "vợ",
    "ck": "chồng",
    "host": "chủ nhà",
    "take care": "chăm sóc",
    "takecare": "chăm sóc",
    "anyways": "dù sao thì",
    "k": "không",
    "mn": "mọi người",
    "j" : "gì",
    "h" : "giờ",
    "tp" : "thành phố",
    "tb" : "trung bình",
    "đg" : "đang",
    "dg" : "đang",
    "đ" : "đáng", 
    
    "complai" : "khiếu nại",
    "complain" : "khiếu nại",
    "report" : "khiếu nại",
    "reject" : "từ chối",
    
    # Ăn uống
    "bufet": "tiệc tự chọn",
    "buffet": "tiệc tự chọn",
    "bfast": "bữa sáng",
    "breakfast": "bữa sáng",
    "lunch": "bữa trưa",
    "dinner": "bữa tối",
    "snack": "đồ ăn vặt",
    "food": "đồ ăn",
    "delicious": "ngon",
    "tasty": "ngon",
    "yummy": "ngon",
    "bf ngon": "bữa sáng ngon",

    # Khách sạn & loại hình lưu trú
    "ks": "khách sạn",
    "ksan": "khách sạn",
    "ksách": "khách sạn",
    "ksach": "khách sạn",
    "khach san": "khách sạn",
    "kháchsạn": "khách sạn",
    "hotel": "khách sạn",
    "home" : "nhà",
    "hostel": "nhà nghỉ giá rẻ",
    "homestay": "ở nhà địa phương",
    "resort": "khu nghỉ dưỡng",
    "motel": "nhà nghỉ ven đường",
    "villa": "biệt thự",
    "5*": "5 sao",

    # Đặt phòng
    "bok": "đặt",
    "book": "đặt",
    "booking": "đặt phòng",
    "boking": "đặt phòng",
    "checkin": "nhận phòng",
    "check in": "nhận phòng",
    "check-in": "nhận phòng",
    "checkout": "trả phòng",
    "check-out": "trả phòng",
    "check out": "trả phòng",
    "onl" : "trực tuyến",
    "online" : "trực tuyến",
    
    # Nhân viên & dịch vụ
    "tuỵt" : "tuyệt",
    "tỵt" : "tuyệt",
    "nv": "nhân viên",
    "nvien" : "nhân viên",
    "nviên" : "nhân viên",
    "nhan vien": "nhân viên",
    "nhânviên": "nhân viên",
    "nvs" : "nhà vệ sinh",
    "wc" : "nhà vệ sinh",
    "staff": "nhân viên",
    "reception": "lễ tân",
    "front desk": "lễ tân",
    "housekeeping": "dọn phòng",
    "security": "bảo vệ",
    "friendly": "thân thiện",
    "helpful": "hữu ích",
    "kind": "tốt bụng",
    "polite": "lịch sự",
    "attentive": "chu đáo",
    "staff friendly": "nhân viên thân thiện",
    "rude": "thô lỗ",
    "unfriendly": "không thân thiện",
    "casino" : "sòng bạc",
    "layout" : "bố cục",
    "pc" : "phòng cháy",
    "sofa" : "ghế dài",
    "vui vẽ" : "vui vẻ",
    "zui" : "vui",
    "zẽ" : "vẻ",
    "zẻ" : "vẻ",
        
    # Phòng ốc & tiện nghi trong phòng
    "p": "phòng",
    "phong": "phòng",
    "phòngó": "phòng",
    "room": "phòng",
    "bed": "giường",
    "bathroom": "phòng tắm",
    "toilet": "nhà vệ sinh",
    "wc": "nhà vệ sinh",
    "shower": "vòi sen",
    "ac": "máy lạnh",
    "aircon": "máy lạnh",
    "air cond": "máy lạnh",
    "wifi": "mạng wifi",
    "wi-fi": "mạng wifi",
    "tv": "ti vi",
    "fridge": "tủ lạnh",
    "minibar": "tủ lạnh mini",
    "balcony": "ban công",
    "view": "tầm nhìn",
    "sea view": "tầm nhìn biển",
    "city view": "tầm nhìn thành phố",
    "pool view": "tầm nhìn hồ bơi",
    "view dep": "tầm nhìn đẹp",
    "mini" : "nhỏ",
    
    # Tiện ích khách sạn
    "pool": "hồ bơi",
    "swimming pool": "hồ bơi",
    "infinity pool": "hồ bơi vô cực",
    "gym": "phòng tập gym",
    "fitness": "phòng tập gym",
    "spa": "khu spa",
    "sauna": "phòng xông hơi",
    "elevator": "thang máy",
    "lift": "thang máy",
    "parking": "bãi đỗ xe",
    "free parking": "bãi đỗ xe miễn phí",
    "beach": "bãi biển",
    "bien": "biển",
    "near beach": "gần bãi biển",
    "private beach": "bãi biển riêng",

    # Đánh giá chung - Tích cực
    "ok": "tốt",
    "oke": "tốt",
    "oki": "tốt",
    "được": "tốt",
    "okay": "tốt",
    "good": "tốt",
    "tot": "tốt",
    "nice": "đẹp",
    "clean": "sạch sẽ",
    "cover": "bao quát",
    "comfortable": "thoải mái",
    "comfy": "thoải mái",
    "thoai mai": "thoải mái",
    "spacious": "rộng rãi",
    "quiet": "yên tĩnh",
    "yen tinh": "yên tĩnh",
    "noisy": "ồn ào",
    "on ao": "ồn ào",
    "expensive": "đắt",
    "dat": "đắt",
    "cheap": "rẻ",
    "re": "rẻ",
    "value": "đáng giá",
    "worth": "đáng giá",
    "dang tien": "đáng tiền",
    "recommend": "khuyên",
    "recomend": "khuyên",
    "recoment": "khuyên",
    "recommended": "khuyên",
    "highly recommend": "rất khuyên",
    "will come back": "sẽ quay lại",
    "excellent": "xuất sắc",
    "amazing": "tuyệt vời",
    "awesome": "tuyệt vời",
    "wonderful": "tuyệt vời",
    "great": "tuyệt vời",
    "fantastic": "tuyệt vời",
    "perfect": "hoàn hảo",
    "beautiful": "đẹp",
    "dep": "đẹp",
    "lovely": "dễ thương",
    "best": "tốt nhất",
    "super": "siêu",
    "modern": "hiện đại",
    "luxury": "sang trọng",
    "luxurious": "sang trọng",
    "cozy": "ấm cúng",
    "relaxing": "thư giãn",
    "peaceful": "bình yên",
    "large": "lớn",
    "big": "lớn",
    "bua sáng" : "bữa sáng",
    
    # Đánh giá chung - Tiêu cực
    "bad": "xấu",
    "xau": "xấu",
    "poor": "kém",
    "terrible": "tồi tệ",
    "awful": "tệ hại",
    "dirty": "bẩn",
    "old": "cũ",
    "small": "nhỏ",
    "tiny": "bé xíu",
    "crowded": "đông đúc",
    "slow": "chậm",
    "overpriced": "quá đắt",
    "disappointing": "thất vọng",
    "not worth": "không đáng",
    "chil" : "thư giản",
    "chill" : "thư giản",

    # Vị trí
    "vt": "vị trí",
    "vitri": "vị trí",
    "location": "vị trí",
    "central": "trung tâm",
    "convenient": "tiện lợi",
    "walking distance": "cách đi bộ",

    # Dịch vụ khác
    "dv": "dịch vụ",
    "dịchvu": "dịch vụ",
    "service": "dịch vụ",
    "free": "miễn phí",
    "fre": "miễn phí",

    # Sạch sẽ
    "sạch": "sạch sẽ",
    "sach se": "sạch sẽ",
    "sạchsẽ": "sạch sẽ",
    "sach": "sạch",

    # Giá cả
    "gc": "giá cả",
    "gia ca": "giá cả",
    "price": "giá cả",
    "reasonable": "hợp lý",
    "bill" : "hóa đơn", 
    "bil" : "hóa đơn",
    "smart" : "thông minh",
    "decor" : "trang trí",
    "style" : "phong cách",
    
    # Teencode & từ phổ biến khác
    "bt": "bình thường",
    "dc": "được",
    "cx": "cũng",
    "rat": "rất",
    "r": "rất",
    "nhanh": "nhanh chóng",
    "sp": "sản phẩm",
    "bh": "bảo hành",
    "ship": "giao hàng",
    "oto": "xe hơi",
    "ô tô": "xe hơi",
    "ôtô": "xe hơi",
    "car": "xe hơi",
    "cf": "cà phê",
    "coffee": "cà phê",
    "royal": "hoàng gia",
    "fancy": "sang trọng",
    "vilage": "làng",
    "village": "làng",
    "ni long": "nhựa",
    "nilong" : "nhựa",
    "grab" : "xe ôm công nghệ",
    "xanh sm" : "xe ôm công nghệ",
    "tien nghi" :  "tiện nghi",
    "an uong" : "ăn uống",
    "plaza" : "quảng trường",
    "double" : "đôi",
}