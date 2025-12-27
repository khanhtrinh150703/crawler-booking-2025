import logging
import os
from typing import Dict, Any, Tuple

from config.config import DATA_DIR, EXPECTED_COLUMNS, RATING_COLUMN, COUNTRY_COLUMN
from loader.data_loader import collect_master_stats, load_data_from_csv
from process.pipeline import process_csv_pipeline
# from visualization.visualization import create_charts

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

    # ------------------------------------------------------------------
    # 1. Tải dữ liệu thô từ file CSV (dùng cho biểu đồ, phân tích nhanh, dashboard...)
    # ------------------------------------------------------------------
    
    # logging.info("Đang tải dữ liệu từ các file JSON...")
    # load_stats = collect_master_stats()

    # df = load_stats["df"]

    # # # Xuất TOÀN BỘ df 
    # test_csv_file = os.path.join(DATA_DIR, "du_lieu_test_full.csv")
    # df.to_csv(test_csv_file, index=False, encoding='utf-8-sig')
    # logging.info(f"Đã xuất file kiểm tra đầy đủ: {test_csv_file}")

    clean_csv_file = os.path.join(DATA_DIR, "du_lieu_test_full.csv")
    
    # Dùng file sạch này để vẽ biểu đồ
    load_stats_final = load_data_from_csv(clean_csv_file)
    # generate_all_advanced_charts(load_stats_final)

    df_raw = load_stats_final["df"]
    logging.info(f"Đã tải {len(df_raw):,} bản ghi thô (chưa lọc)")

    print(f"\nTổng số đánh giá thô: {len(df_raw):,}")
    print(f"Top provinces đã được tính sẵn: {load_stats_final['top_provinces'][:10]} ...\n")

    # ------------------------------------------------------------------
    # 2. Xử lý và lọc dữ liệu sạch (chỉ giữ tiếng Việt hợp lệ, loại null, điểm thấp, spam...)
    #    → Dùng cho training model, topic modeling, phân tích sentiment sâu...
    # ------------------------------------------------------------------

    logging.info("Đang chạy pipeline lọc dữ liệu sạch từ dữ liệu đã tải...")
    df_clean, filter_stats = process_csv_pipeline(load_stats_final)
    process_csv_file = os.path.join(DATA_DIR, 'du_lieu_processing.csv')
    df_clean.to_csv(process_csv_file, index=False, encoding='utf-8-sig')
    # df_clean: DataFrame đã được lọc chất lượng cao, có thêm cột stt, positive_comment, v.v.
    # filter_stats: dict thống kê chi tiết quá trình lọc

    logging.info(f"Hoàn tất lọc: giữ lại {len(df_clean):,} / {len(df_raw):,} đánh giá chất lượng cao")

    print("\n" + "="*60)
    print(" THỐNG KÊ LỌC DỮ LIỆU")
    print("="*60)
    for key, value in filter_stats.items():
        print(f"{key:>40}: {value}")
    print("="*60)


if __name__ == "__main__":
    run_pipeline()