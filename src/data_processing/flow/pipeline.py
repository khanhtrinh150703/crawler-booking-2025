import logging
import os
from loader.data_loader import load_json_files, collect_master_stats, load_data_from_csv
from process.data_processor import process_data
# from visualization.visualization import create_charts
from utils.processing import (
    process_reviews_dataframe,
    is_vietnam,
    preprocess_vietnamese_text
)
from utils.text_preparation import prepare_text_for_wordcloud

from config.config import CHARTS_DIR, OUTPUT_CSV, BASE_FOLDER, VIETNAMESE_STOPWORDS
from visualization.visualization import generate_all_advanced_charts

# Export
from export.export_data import export_final_dataset, export_metadata_mapping
from export.export_dataset_description import export_dataset_description_to_excel
from export.export_for_dl import export_for_deep_learning
from export.export_encode_to_excel import save_encodings_to_excel
from export.export_excel import save_to_excel

# Reporting
from reporting.summary import save_summary_report
from reporting.processing_report import save_processing_report
from reporting.dataset_description import describe_dataset


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)


def run_pipeline():
    logging.info("BẮT ĐẦU PIPELINE XỬ LÝ ĐÁNH GIÁ BOOKING.COM")

    # 1. Load dữ liệu JSON Hoặc CSV
    logging.info("Đang tải dữ liệu từ các file JSON...")
    # load_stats = collect_master_stats()
    
    # Chuyển dự liệu từ các file json thành 1 data frame và lưu lại vào file.csv
    # load_stats["df"].to_csv('du_lieu.csv', index=False, encoding='utf-8')
    
    load_stats = load_data_from_csv('du_lieu.csv')
    
    generate_all_advanced_charts(load_stats)
    
    
    # # 2. Xử lý và lọc dữ liệu (chỉ giữ tiếng Việt, loại null, điểm thấp...)
    # logging.info("Đang xử lý và lọc dữ liệu...")
    
    # logging.info("Bắt đầu xử lý data...")
    # df_raw, stats_raw, stats_display = process_data(BASE_FOLDER)
    
    # base_stats = stats_raw
    
    # if df_raw.empty:
    #     print("Không tìm thấy đánh giá tiếng Việt nào hợp lệ!")
    #     return
    
    # df_raw, stats_raw, encodings = process_reviews_dataframe(df_raw)

    # # 3. Báo cáo & lưu encodings
    # logging.info("Tạo báo cáo và lưu mã hóa...")
    # save_processing_report(
    #     total_reviews=load_stats.get("total_reviews", len(rows)),
    #     total_json_files=load_stats.get("total_files", 0),
    #     null_reviews=stats_raw.get("null_empty_count", 0),
    #     non_vietnamese_reviews=stats_raw.get("non_vietnamese_count", 0),
    #     low_score_reviews=stats_raw.get("low_score_count", 0),
    #     df=df_raw,
    #     room_type_encoding=encodings.get("room_type", {}),
    #     stay_duration_mapping=encodings.get("stay_duration", {}),
    #     group_type_encoding=encodings.get("group_type", {}),
    #     charts_dir=OUTPUT_CSV
    # )

    # save_summary_report(
    #     df=df_raw,
    #     total_reviews=load_stats.get("total_reviews", len(rows)),
    #     vietnamese_reviews=stats_raw.get("kept_count_vn", len(df_raw)),
    #     null_reviews=stats_raw.get("null_empty_count", 0),
    #     non_vietnamese_reviews=stats_raw.get("non_vietnamese_count", 0),
    #     low_score_reviews=stats_raw.get("low_score_count", 0),
    #     room_type_encoding=encodings.get("room_type", {}),
    #     stay_duration_mapping=encodings.get("stay_duration", {}),
    #     group_type_encoding=encodings.get("group_type", {}),
    #     charts_dir=OUTPUT_CSV,
    #     filename="summary_stats.json"
    # )

    # save_encodings_to_excel(
    #     encodings=encodings,
    #     stay_duration_mapping=encodings.get("stay_duration", {}),
    #     output_folder=OUTPUT_CSV,
    #     filename="Mã_hóa_dữ_liệu.xlsx"
    # )

    # # 4. Xuất dataset sạch + mapping
    # export_final_dataset(
    #     df=df_raw,
    #     output_folder=OUTPUT_CSV,
    #     filename="booking_reviews_vietnamese_final.csv"
    # )

    # export_metadata_mapping(
    #     room_type_mapping=encodings["room_type"],
    #     group_type_mapping=encodings["group_type"],
    #     stay_duration_mapping=encodings["stay_duration"],
    #     output_folder=OUTPUT_CSV,
    #     filename="metadata_mapping.json"
    # )

    # # 5. Phân tích riêng cho khách Việt Nam
    # df_vn = df_raw[df_raw['country'].apply(is_vietnam)].copy()
    # print(f"\nSố đánh giá của khách Việt Nam: {len(df_vn):,} ({len(df_vn)/len(df_raw)*100:.2f}%)")

    # describe_dataset(df_raw)
    # export_dataset_description_to_excel(df_raw, OUTPUT_CSV)
    # check_class_imbalance(
    #     df=df_raw,
    #     columns=['room_type', 'group_type', 'stay_duration', 'score'],
    #     output_folder=CHARTS_DIR
    # )

    # # 6. Tạo biểu đồ tổng quan
    # logging.info("Đang tạo biểu đồ phân tích...")
    # create_charts(df=df_raw, charts_dir=CHARTS_DIR, stats=load_stats)

    # # 7. Chuẩn bị dữ liệu cho WordCloud + Deep Learning
    # df_final, _ = prepare_text_for_wordcloud(
    #     df=df_raw,
    #     text_column="combined_text",
    #     positive_comment_column="positive_comment",
    #     preprocess_func=preprocess_vietnamese_text,
    #     vietnamese_stopwords=VIETNAMESE_STOPWORDS
    # )

    # export_for_deep_learning(
    #     df=df_final,
    #     text_column="processed_text",
    #     label_column="score",
    #     output_dir=OUTPUT_CSV,
    #     prefix="booking_review_vn"
    # )


    
    
    # # Hoàn tất
    # logging.info("HOÀN TẤT TOÀN BỘ PIPELINE!")
    # print("\n" + "="*60)
    # print("Tất cả file đã được lưu tại:")
    # print(f"   → {os.path.abspath(CHARTS_DIR)}")
    # print("   ├── Biểu đồ (.png)")
    # print("   ├── Mã_hóa_dữ_liệu.xlsx")
    # print("   ├── processing_report.html / .json")
    # print("   ├── summary_stats.json")
    # print("   ├── booking_reviews_vietnamese_final.csv")
    # print("   └── Dữ liệu sẵn cho DL (train/val/test)")
    # print("="*60 + "\n")


if __name__ == "__main__":
    run_pipeline()