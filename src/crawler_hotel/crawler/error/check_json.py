import json

# ==============================================

def check_invalid_evaluation_categories(eval_cat):
    required_fields = ["service_staff", "amenities", "cleanliness", "comfort", "value_for_money", "location"]
    all_null = True
    any_null = False

    for field in required_fields:
        value = eval_cat.get(field)
        if value is None:
            any_null = True
        else:
            all_null = False

    return all_null, any_null

def is_invalid_reviews(reviews):
    if reviews is None:
        return True
    if isinstance(reviews, str) and reviews.strip().lower() in ["not found", ""]:
        return True
    if isinstance(reviews, list) and len(reviews) == 0:
        return True
    if isinstance(reviews, dict) and len(reviews) == 0:
        return True
    if not isinstance(reviews, (list, dict)):
        return True
    return False

def process_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 1. name null hoặc rỗng
        name = data.get("name")
        if name is None or (isinstance(name, str) and name.strip() == ""):
            return True, "name is null or empty"

        # 2. evaluation_categories
        eval_cat = data.get("evaluation_categories", {})
        if not isinstance(eval_cat, dict):
            return True, "evaluation_categories invalid"

        all_null, any_null = check_invalid_evaluation_categories(eval_cat)
        if all_null:
            return True, "all 6 eval fields are null"
        if any_null:
            return True, "at least one of 6 eval fields is null"

        # 3. reviews
        reviews = data.get("reviews")
        if is_invalid_reviews(reviews):
            return True, "reviews is null/empty/not found/invalid"

        return False, None  # Hợp lệ

    except Exception as e:
        return True, f"Error: {str(e)}"


