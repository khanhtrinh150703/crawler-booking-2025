# core/processor.py
import os
from error.check_json import process_json_file
from config.config import ROOT_DIR, MODE, PROCESS_BY
from core.file_handler import copy_error_file
from utils.helpers import is_valid_range_folder

# core/processor.py

def process_range_folder(range_folder, range_path, main_error_dir, error_dir_created):
    error_count = review_count = viet_positive_total = 0
    log_lines = []

    for province_folder in os.listdir(range_path):
        province_path = os.path.join(range_path, province_folder)
        if not os.path.isdir(province_path):
            continue

        for json_file in os.listdir(province_path):
            if not json_file.endswith(".json"):
                continue

            file_path = os.path.join(province_path, json_file)
            has_error, reason, reviews, _, _, _, viet_pos = process_json_file(file_path)
            review_count += reviews
            viet_positive_total += viet_pos  # ← CỘNG DỒN

            if has_error:
                error_count += 1
                rel_path = f"{range_folder}/{province_folder}/{json_file}"
                log_lines.append(f"{rel_path}  [{reason}] (reviews: {reviews})")

                if MODE == "copy":
                    error_dir_created = copy_error_file(
                        file_path, main_error_dir, range_folder, province_folder
                    ) or error_dir_created

    return error_count, review_count, viet_positive_total, log_lines, error_dir_created


def process_province_folder(province_folder, province_path, main_error_dir, error_dir_created):
    error_count = review_count = viet_positive_total = 0
    log_lines = []

    for json_file in os.listdir(province_path):
        if not json_file.endswith(".json"):
            continue

        file_path = os.path.join(province_path, json_file)
        has_error, reason, reviews, _, _, _, viet_pos = process_json_file(file_path)
        review_count += reviews
        viet_positive_total += viet_pos  # ← CỘNG DỒN

        if has_error:
            error_count += 1
            rel_path = f"{province_folder}/{json_file}"
            log_lines.append(f"{rel_path}  [{reason}] (reviews: {reviews})")

            if MODE == "copy":
                error_dir_created = copy_error_file(
                    file_path, main_error_dir, province_folder
                ) or error_dir_created

    return error_count, review_count, viet_positive_total, log_lines, error_dir_created

def get_folders_to_process():
    folders = []
    for item in os.listdir(ROOT_DIR):
        item_path = os.path.join(ROOT_DIR, item)
        if not os.path.isdir(item_path):
            continue
        if PROCESS_BY == "range" and not is_valid_range_folder(item):
            continue
        folders.append((item, item_path))
    return sorted(folders)