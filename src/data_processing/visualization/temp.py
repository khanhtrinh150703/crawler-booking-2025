import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import Counter
from config.config import VIETNAMESE_STOPWORDS , ANALYSIS_RESULTS_DIR
import pandas as pd
from wordcloud import WordCloud
import unicodedata
from pathlib import Path
from underthesea import word_tokenize
from utils.processing import preprocess_vietnamese_text
from typing import List

def plot_country_distribution_chart(df, charts_dir):
    """
    Hàm vẽ biểu đồ phân bố top 10 quốc gia có nhiều đánh giá tiếng Việt nhất.
    
    Parameters:
    - df: DataFrame chứa dữ liệu với cột 'country'
    - charts_dir: Thư mục để lưu biểu đồ
    """
    if 'country' in df.columns and not df['country'].isnull().all():
        plt.figure(figsize=(10, 6))
        country_counts = df['country'].value_counts().head(10)  # Top 10 quốc gia

        ax = sns.barplot(x=country_counts.index, y=country_counts.values)
        plt.title('Top 10 quốc gia có nhiều đánh giá tiếng Việt nhất')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # Thêm số lượng lên thanh
        for i, v in enumerate(country_counts.values):
            ax.text(i, v + 0.1, str(v), ha='center')

        os.makedirs(charts_dir, exist_ok=True)
        plt.savefig(os.path.join(charts_dir, 'country_distribution.png'))
        plt.close()  # Đóng figure để tránh xung đột
        print("Đã lưu biểu đồ phân bố quốc gia")
    else:
        print("Không có dữ liệu quốc gia để vẽ biểu đồ")

def plot_top_common_words_chart(df, charts_dir, sample_size=500, top_n=20):
    """
    Hàm vẽ biểu đồ top từ phổ biến trong đánh giá, sử dụng underthesea để tách từ.
    
    Parameters:
    - df: DataFrame chứa dữ liệu với cột 'combined_text'
    - charts_dir: Thư mục để lưu biểu đồ
    - sample_size: Số lượng mẫu đánh giá để phân tích (mặc định 500)
    - top_n: Số lượng từ top để hiển thị (mặc định 20)
    """
    try:
        from underthesea import word_tokenize
        
        # Lấy mẫu các đánh giá để phân tích từ vựng
        sample_size = min(sample_size, len(df))
        sample_indices = np.random.choice(df.index, sample_size, replace=False)

        all_words = []
        for idx in sample_indices:
            text = df.loc[idx, 'combined_text']
            if isinstance(text, str) and text.strip():
                tokens = word_tokenize(text)
                # Loại bỏ stopwords và các từ quá ngắn
                filtered_tokens = [w.lower() for w in tokens if len(w) > 1 and w.lower() not in VIETNAMESE_STOPWORDS]
                all_words.extend(filtered_tokens)

        # Đếm tần suất từ
        word_freq = Counter(all_words)
        top_words = word_freq.most_common(top_n)

        # print(f"\nTop {top_n} từ xuất hiện nhiều nhất:")
        # for word, count in top_words:
        #     print(f"  {word}: {count}")

        # Vẽ biểu đồ top từ
        plt.figure(figsize=(12, 8))
        words = [word for word, _ in top_words]
        counts = [count for _, count in top_words]

        ax = sns.barplot(x=counts, y=words)
        plt.title(f'Top {top_n} từ xuất hiện nhiều nhất trong đánh giá')
        plt.xlabel('Số lần xuất hiện')
        plt.ylabel('Từ')

        # Thêm số lượng lên thanh
        for i, v in enumerate(counts):
            ax.text(v + 0.5, i, str(v), va='center')

        plt.tight_layout()
        os.makedirs(charts_dir, exist_ok=True)
        plt.savefig(os.path.join(charts_dir, 'top_words.png'))
        plt.close()  # Đóng figure để tránh xung đột
        print("Đã lưu biểu đồ top từ phổ biến")
    
    except ImportError:
        print("Không thể thực hiện thống kê từ vựng do thiếu thư viện underthesea")
    except Exception as e:
        print(f"Lỗi khi vẽ biểu đồ top từ: {str(e)}")


def plot_processing_ratio_chart(stats: dict, charts_dir: str):
    from pathlib import Path
    import matplotlib.pyplot as plt

    total = int(stats.get("total_reviews", 0))
    kept = int(stats.get("kept_count_vn", stats.get("kept_vn", 0)))
    non_vn = int(stats.get("non_vietnamese", 0))
    low_score = int(stats.get("low_score", 0))
    null_c = int(stats.get("null_empty", 0))

    actual_total = kept + non_vn + low_score + null_c

    if actual_total == 0:
        print("DỮ LIỆU RỖNG → KHÔNG VẼ PIE")
        return

    # VẼ PIE CHART – BÂY GIỜ EM ĐÃ THẤY SỐ RỒI, KHÔNG CÒN NGHI NGỜ GÌ NỮA!!!
    labels = ['Tiếng Việt hợp lệ', 'Không phải tiếng Việt', 'Điểm < 5', 'Null / Rỗng']
    sizes = [kept, non_vn, low_score, null_c]
    colors = ['#27ae60', '#3498db', '#e74c3c', '#95a5a6']
    explode = (0.15, 0.05, 0.05, 0.1)

    plt.figure(figsize=(12, 9))

    def autopct(pct):
        if pct < 2:
            return ''
        val = int(round(pct / 100 * actual_total))
        return f'{pct:.1f}%\n{val:,}'

    plt.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct=autopct, startangle=90,
            textprops={'fontsize': 13, 'color': 'white', 'weight': 'bold'},
            wedgeprops={'edgecolor': 'black', 'linewidth': 2.5})

    plt.title(f'TỶ LỆ LỌC ĐÁNH GIÁ BOOKING.COM\n',
              fontsize=20, fontweight='bold', color='#2c3e50', pad=40)
    plt.axis('equal')

    Path(charts_dir).mkdir(parents=True, exist_ok=True)
    save_path = Path(charts_dir) / "01_data_processing_ratio_pie.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"ĐÃ LƯU BIỂU ĐỒ → {save_path}")
    print("="*60 + "\n")
        
def perform_eda_and_save_charts(df: pd.DataFrame, charts_dir: str, top_n: int = 10):
    """
    Thực hiện phân tích thăm dò (EDA) và lưu toàn bộ biểu đồ cần thiết.
    
    Parameters:
    - df: DataFrame đã xử lý
    - charts_dir: Thư mục lưu biểu đồ
    - top_n: Số lượng top loại phòng phổ biến nhất để hiển thị
    """
    os.makedirs(charts_dir, exist_ok=True)
    sns.set_style("whitegrid")
    plt.rcParams['font.family'] = 'DejaVu Sans'  # hoặc 'Arial' nếu có font tiếng Việt

    print("\n" + "="*60)
    print("           PHÂN TÍCH DỮ LIỆU THĂM DÒ (EDA)")
    print("="*60)

    # ------------------------------------------------------------------
    # 1. Top loại phòng phổ biến
    # ------------------------------------------------------------------
    if 'room_type' in df.columns and not df['room_type'].isna().all():
        plt.figure(figsize=(12, 6))
        top_rooms = df['room_type'].value_counts().head(top_n)
        
        ax = sns.barplot(
            data=top_rooms.reset_index(),
            x='room_type', 
            y='count', 
            hue='room_type',
            palette="viridis",
            legend=False
        )
        plt.title(f'Top {top_n} Loại Phòng Phổ Biến Nhất', fontsize=14, fontweight='bold', pad=20)
        plt.xlabel('Loại phòng')
        plt.ylabel('Số lượng đánh giá')
        plt.xticks(rotation=45, ha='right')

        for i, v in enumerate(top_rooms.values):
            ax.text(i, v + v*0.01, f"{v:,}", ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        path1 = os.path.join(charts_dir, 'top_room_types.png')
        plt.savefig(path1, dpi=200, bbox_inches='tight')
        plt.close()
        print(f"→ Đã lưu: Top {top_n} loại phòng → {path1}")
    else:
        print("→ Bỏ qua biểu đồ loại phòng (không có dữ liệu)")

    # ------------------------------------------------------------------
    # 2. Phân bố loại nhóm
    # ------------------------------------------------------------------
    if 'group_type' in df.columns and not df['group_type'].isna().all():
        plt.figure(figsize=(10, 6))
        group_counts = df['group_type'].value_counts()
        
        # Mới – sạch warning
        ax = sns.barplot(
            data=group_counts.reset_index(),
            x='group_type',
            y='count',
            hue='group_type',
            palette="mako",
            legend=False
        )
        plt.title('Phân Bố Theo Loại Nhóm Khách', fontsize=14, fontweight='bold', pad=20)
        plt.xlabel('Loại nhóm')
        plt.ylabel('Số lượng')
        plt.xticks(rotation=30, ha='right')

        for i, v in enumerate(group_counts.values):
            ax.text(i, v + v*0.01, f"{v:,}", ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        path2 = os.path.join(charts_dir, 'group_type_distribution.png')
        plt.savefig(path2, dpi=200, bbox_inches='tight')
        plt.close()
        print(f"→ Đã lưu: Phân bố loại nhóm → {path2}")
    else:
        print("→ Bỏ qua biểu đồ nhóm khách (không có dữ liệu)")

    # ------------------------------------------------------------------
    # 3. Phân bố điểm số
    # ------------------------------------------------------------------
    if 'score' in df.columns:
        plt.figure(figsize=(10, 6))
        ax = sns.histplot(data=df, x='score', bins=10, kde=True, color='#4CAF50', alpha=0.7)
        plt.title('Phân Bố Điểm Đánh Giá', fontsize=14, fontweight='bold', pad=20)
        plt.xlabel('Điểm số (trên 10)')
        plt.ylabel('Số lượng đánh giá')

        # Thêm số lượng lên từng cột
        for rect in ax.patches:
            height = rect.get_height()
            if height > 0:
                ax.text(rect.get_x() + rect.get_width()/2., height + height*0.01,
                        f'{int(height)}', ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        path3 = os.path.join(charts_dir, 'score_distribution.png')
        plt.savefig(path3, dpi=200, bbox_inches='tight')
        plt.close()
        print(f"→ Đã lưu: Phân bố điểm số → {path3}")
    else:
        print("→ Bỏ qua biểu đồ điểm số (không có cột 'score')")

    # ------------------------------------------------------------------
    # 4. Độ dài bình luận (dùng combined_text hoặc positive_comment)
    # ------------------------------------------------------------------
    text_col = None
    for col in ['combined_text', 'positive_comment', 'rating']:
        if col in df.columns and df[col].dtype == 'object':
            text_col = col
            break

    if text_col:
        lengths = df[text_col].astype(str).str.len()
        if not lengths.isna().all():
            plt.figure(figsize=(10, 6))
            ax = sns.histplot(lengths.dropna(), bins=30, kde=True, color='#2196F3', alpha=0.8)
            plt.title(f'Phân Bố Độ Dài Bình Luận (cột: {text_col})', fontsize=14, fontweight='bold', pad=20)
            plt.xlabel('Số ký tự')
            plt.ylabel('Số lượng bình luận')

            plt.axvline(lengths.mean(), color='red', linestyle='--', linewidth=2, 
                        label=f'Trung bình: {lengths.mean():.0f} ký tự')
            plt.legend()

            plt.tight_layout()
            path4 = os.path.join(charts_dir, 'comment_length_distribution.png')
            plt.savefig(path4, dpi=200, bbox_inches='tight')
            plt.close()
            print(f"→ Đã lưu: Độ dài bình luận → {path4}")
        else:
            print("→ Bỏ qua biểu đồ độ dài bình luận (dữ liệu rỗng)")
    else:
        print("→ Bỏ qua biểu đồ độ dài bình luận (không tìm thấy cột văn bản)")

    print("="*60)
    print("HOÀN TẤT PHÂN TÍCH EDA – Tất cả biểu đồ đã được lưu!")
    print("="*60)


def generate_vietnamese_wordcloud(
    df: pd.DataFrame,
    text_column: str = "combined_text",
    output_dir: str = "outputs/analysis_results",
    min_text_length: int = 10
) -> dict:
    """
    Tạo Word Cloud + Top words + N-grams cho tiếng Việt (chuẩn 2025)
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print("\n" + "═" * 70)
    print("             TẠO WORD CLOUD & PHÂN TÍCH TỪ KHÓA TIẾNG VIỆT")
    print("═" * 70)

    # Tiền xử lý
    print("Đang tiền xử lý văn bản...")
    df = df.copy()
    df['processed_text'] = df[text_column].apply(preprocess_vietnamese_text)
    
    # Lọc dữ liệu chất lượng cao
    mask = (
        df['processed_text'].str.len() > min_text_length
    )
    df_filtered = df[mask].copy()
    print(f"   • Dữ liệu đầu vào: {len(df):,} → Sau lọc: {len(df_filtered):,} bản ghi")

    if len(df_filtered) == 0:
        print("   Cảnh báo: Không còn dữ liệu sau khi lọc!")
        return {}

    all_text = " ".join(df_filtered['processed_text'])

    # Tạo Word Cloud
    print("   • Đang tạo Word Cloud...")
    font_path = None
    possible_fonts = [
        "fonts/times-new-roman.ttf",
        "fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        None
    ]
    for fp in possible_fonts:
        if fp and os.path.exists(fp):
            font_path = fp
            break

    wc = WordCloud(
        width=1600, height=900,
        background_color='white',
        max_words=300,
        contour_width=3,
        contour_color='#1f77b4',
        font_path=font_path,
        colormap='viridis',
        random_state=42
    ).generate(all_text)

    plt.figure(figsize=(16, 10))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.title('WORD CLOUD ĐÁNH GIÁ KHÁCH SẠN - NGƯỜI VIỆT NAM', fontsize=20, pad=30, fontweight='bold')
    wc_path = Path(output_dir) / "vietnam_reviews_wordcloud.png"
    plt.savefig(wc_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"   • Đã lưu Word Cloud → {wc_path}")

    # Top words
    words = [w for text in df_filtered['processed_text'] for w in text.split()]
    word_counter = Counter(words)
    top_words = word_counter.most_common(100)

    # N-grams
    def get_ngrams(texts, n=2):
        ngrams = []
        for text in texts:
            tokens = text.split()
            if len(tokens) >= n:
                ngrams.extend([" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)])
        return Counter(ngrams).most_common(20)

    bigrams = get_ngrams(df_filtered['processed_text'], 2)
    trigrams = get_ngrams(df_filtered['processed_text'], 3)

    # In kết quả
    print(f"\n   TOP 15 TỪ PHỔ BIẾN:")
    for w, c in top_words[:15]:
        print(f"      {w}: {c:,}")

    print(f"\n   TOP 10 CỤM TỪ 2 TỪ (BIGRAMS):")
    for bg, c in bigrams[:10]:
        print(f"      {bg}: {c:,}")

    print(f"\n   TOP 10 CỤM TỪ 3 TỪ (TRIGRAMS):")
    for tg, c in trigrams[:10]:
        print(f"      {tg}: {c:,}")

    # Lưu file
    # Trong hàm generate_vietnamese_wordcloud hoặc nơi lưu file:
    pd.DataFrame(top_words, columns=['Từ', 'Số lần xuất hiện']).to_csv(
        Path(ANALYSIS_RESULTS_DIR) / "top_words.csv", 
        index=False, encoding='utf-8-sig'
    )
    pd.DataFrame(bigrams, columns=['Cụm 2 từ', 'Số lần']).to_csv(
        Path(ANALYSIS_RESULTS_DIR) / "top_bigrams.csv", 
        index=False, encoding='utf-8-sig'
    )
    pd.DataFrame(trigrams, columns=['Cụm 3 từ', 'Số lần']).to_csv(
        Path(ANALYSIS_RESULTS_DIR) / "top_trigrams.csv", 
        index=False, encoding='utf-8-sig'
    )

    print(f"\n   Đã lưu tất cả file phân tích từ khóa vào:")
    print(f"      {Path(output_dir).resolve()}")

    print("═" * 70)
    return {
        "wordcloud_path": str(wc_path),
        "top_words": top_words[:50],
        "bigrams": bigrams,
        "trigrams": trigrams,
        "final_count": len(df_filtered)
    }
    
def check_class_imbalance(
    df: pd.DataFrame,
    columns: List[str],
    output_folder: str = "outputs/charts"
) -> pd.DataFrame:
    from pathlib import Path
    import seaborn as sns
    import matplotlib.pyplot as plt

    Path(output_folder).mkdir(parents=True, exist_ok=True)
    results = []

    print("\n" + "═" * 80)
    print("          KIỂM TRA MẤT CÂN BẰNG LỚP (CLASS IMBALANCE)")
    print("═" * 80)

    for col in columns:
        if col not in df.columns:
            print(f"Cảnh báo: Không tìm thấy cột '{col}'")
            continue

        series = df[col].dropna()
        if series.empty:
            continue

        # Ép kiểu score
        if col == "score":
            series = pd.to_numeric(series, errors='coerce').dropna()

        counts = series.value_counts()
        total = len(series)

        # Tính chỉ số mất cân bằng
        max_prop = counts.max() / total
        min_prop = counts.min() / total if len(counts) > 1 else 0
        imbalance_ratio = max_prop / min_prop if min_prop > 0 else float('inf')

        severity = "CÂN BẰNG"
        if imbalance_ratio > 20: severity = "NGHIÊM TRỌNG"
        elif imbalance_ratio > 10: severity = "TRUNG BÌNH"
        elif imbalance_ratio > 3: severity = "NHẸ"

        results.append({
            'Cột': col,
            'Số lớp': len(counts),
            'Max (%)': round(max_prop * 100, 2),
            'Tỷ lệ mất cân bằng': f"{imbalance_ratio:.1f}x" if imbalance_ratio != float('inf') else "∞",
            'Mức độ': severity
        })

        # VẼ BIỂU ĐỒ ĐÚNG KIỂU
        plt.figure(figsize=(14, 8))

        if col == "score":
            # Chỉ score mới dùng histogram
            sns.histplot(series, bins=20, kde=True, color="#e74c3c", alpha=0.8, edgecolor="black")
            plt.title(f'Phân phối điểm đánh giá (score)', fontsize=18, fontweight='bold', pad=20)
            plt.xlabel('Điểm')
            plt.ylabel('Số lượng đánh giá')
        else:
            # Tất cả các cột phân loại khác: countplot nằm ngang, hiện tên rõ ràng
            top_n = 20  # hiện top 20 loại phòng phổ biến nhất
            top_counts = counts.head(top_n)

            sns.barplot(
                x=top_counts.values,
                y=top_counts.index.astype(str),
                hue=top_counts.index.astype(str),
                palette="viridis",
                legend=False,
                edgecolor="black",
                linewidth=1.3
            )
            plt.title(f'Top {top_n} loại {col.replace("_", " ").title()} phổ biến nhất', 
                      fontsize=18, fontweight='bold', pad=20)
            plt.xlabel('Số lượng đánh giá')
            plt.ylabel(col.replace('_', ' ').title())

            # Ghi số lên thanh
            for i, v in enumerate(top_counts.values):
                plt.text(v + total*0.001, i, f'{v:,}', va='center', fontweight='bold', color='black')

        plt.tight_layout()
        plt.savefig(Path(output_folder) / f"imbalance_{col}.png", dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()

    # Lưu Excel
    result_df = pd.DataFrame(results)
    excel_path = Path("outputs/analysis_results/Báo_cáo_mất_cân_bằng.xlsx")
    excel_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_excel(excel_path, index=False)
    print(f"\nĐÃ LƯU báo cáo mất cân bằng → {excel_path}")

    return result_df
    
def create_charts(df, charts_dir, stats: dict):
    """
    Tạo toàn bộ biểu đồ, chỉ cần truyền 1 dict stats thay vì 4 biến rời.
    """
    plot_country_distribution_chart(df, charts_dir)
    plot_top_common_words_chart(df, charts_dir)
    plot_processing_ratio_chart(stats, charts_dir) 
    perform_eda_and_save_charts(df, charts_dir, 10)
    generate_vietnamese_wordcloud(df, text_column="combined_text", output_dir=charts_dir)
    
    
# src/visualization/advanced_charts.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
import numpy as np
from wordcloud import WordCloud
from typing import Dict

plt.style.use("seaborn-v0_8-whitegrid")
sns.set_palette("husl")

# Thiết lập font tiếng Việt (nếu cần)
plt.rcParams["font.family"] = "DejaVu Sans"  # hoặc "Arial Unicode MS", "Times New Roman"


def save_fig(fig: plt.Figure, filename: str, output_dir: str):
    """Helper để lưu ảnh đẹp"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    fig.savefig(f"{output_dir}/{filename}", dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_score_distribution(df: pd.DataFrame, output_dir: str):
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(df["score"].dropna(), bins=20, kde=True, color="#e74c3c", ax=ax)
    ax.set_title("Phân phối điểm đánh giá", fontsize=16, pad=20)
    ax.set_xlabel("Điểm số")
    ax.set_ylabel("Số lượng")
    save_fig(fig, "01_score_distribution.png", output_dir)


def plot_missing_values(df: pd.DataFrame, output_dir: str):
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(df.isnull(), cbar=True, yticklabels=False, cmap="viridis", ax=ax)
    ax.set_title("Ma trận dữ liệu thiếu (Missing Values)", fontsize=16)
    save_fig(fig, "02_missing_values.png", output_dir)


def plot_boxplot_score_by_province(df: pd.DataFrame, output_dir: str):
    df_plot = df[df["province"] != "Khác"].copy()
    if df_plot.empty:
        return

    order = df_plot.groupby("province")["score"].median().sort_values(ascending=False).index

    fig, ax = plt.subplots(figsize=(12, 8))
    # ĐÃ SỬA: dùng hue + legend=False thay vì palette
    sns.boxplot(data=df_plot, x="score", y="province", order=order,
                hue="province", dodge=False, palette="coolwarm", legend=False, ax=ax)
    ax.set_title("Boxplot điểm đánh giá theo Tỉnh/Thành (Top)", fontsize=16)
    ax.set_xlabel("Điểm số")
    ax.set_ylabel("")
    save_fig(fig, "03_boxplot_score_by_province.png", output_dir)


def plot_score_distribution_top15(df: pd.DataFrame, top_provinces: list, output_dir: str):
    df_plot = df[df["province"].isin(top_provinces)]
    if df_plot.empty:
        return

    g = sns.FacetGrid(df_plot, col="province", col_wrap=3, height=3.5, aspect=1.4, sharex=True, sharey=True)
    g.map(sns.histplot, "score", bins=10, kde=True, color="#3498db")
    g.set_titles("{col_name}")
    g.fig.suptitle("Phổ điểm đánh giá của các thành phố nhiều review nhất", fontsize=18, y=1.02)
    save_fig(g.fig, "04_score_distribution_top15_cities.png", output_dir)


def plot_time_series_reviews(df: pd.DataFrame, top_provinces: list, output_dir: str):
    if "month_year" not in df.columns or df["month_year"].isna().all():
        return

    # LỌC + CHUẨN HÓA THỜI GIAN ĐÚNG CÁCH → KHÔNG CÒN WARNING!
    df_plot = df[df["province"].isin(top_provinces + ["Khác"])].copy()
    df_plot = df_plot.dropna(subset=["month_year"])
    
    # ÉP KIỂU CHUẨN: datetime → tránh cảnh báo categorical units
    df_plot["month_year_dt"] = pd.to_datetime(df_plot["month_year"], format="%Y-%m", errors="coerce")
    df_plot = df_plot.dropna(subset=["month_year_dt"])

    if df_plot.empty:
        return

    # Tính số lượng review theo tháng và tỉnh
    trend = (df_plot
             .groupby([pd.Grouper(key="month_year_dt", freq="MS"), "province"])
             .size()
             .unstack(fill_value=0))

    if trend.empty:
        return

    # Tạo trục thời gian đầy đủ
    full_range = pd.date_range(start=trend.index.min(), end=trend.index.max(), freq="MS")
    trend = trend.reindex(full_range, fill_value=0)

    # Dùng datetime làm index → matplotlib/seaborn hiểu đúng là time series
    fig, ax = plt.subplots(figsize=(16, 10))
    for prov in top_provinces[:8]:
        if prov in trend.columns:
            ax.plot(trend.index, trend[prov], label=prov, linewidth=2.7, marker='o', markersize=4)

    ax.set_title("Xu hướng số lượng review theo thời gian – Top 8 thành phố", fontsize=18, pad=20)
    ax.set_xlabel("Thời gian", fontsize=14)
    ax.set_ylabel("Số lượng review", fontsize=14)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=12)
    ax.grid(True, alpha=0.3, linestyle="--")

    # Định dạng trục X đẹp: chỉ hiện tháng/năm, xoay 45 độ
    ax.xaxis.set_major_locator(plt.MaxNLocator(20))  # tối đa 20 nhãn
    ax.xaxis.set_major_formatter(plt.FixedFormatter(trend.index.strftime("%m/%Y")))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    plt.tight_layout()
    save_fig(fig, "05_time_series_top_cities.png", output_dir)


def plot_reviewer_deviation(df: pd.DataFrame, output_dir: str):
    if "deviation" not in df.columns or df["deviation"].isna().all():
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(df["deviation"].dropna(), bins=30, kde=True, color="#9b59b6", ax=ax)
    ax.set_title("Phân phối độ lệch điểm so với trung bình khách sạn", fontsize=16)
    ax.set_xlabel("Độ lệch (Score - Hotel Avg)")
    ax.axvline(0, color='red', linestyle='--', linewidth=1.5)
    save_fig(fig, "06_reviewer_deviation.png", output_dir)


def plot_text_length_vs_score(df: pd.DataFrame, output_dir: str):
    sample_df = df.sample(n=min(10000, len(df)), random_state=42)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(data=sample_df, x="text_length", y="score",
                    hue="is_vietnamese", alpha=0.6, palette="deep", ax=ax)
    ax.set_title("Độ dài comment vs Điểm số", fontsize=16)
    ax.set_xlabel("Số từ trong comment")
    max_x = df["text_length"].quantile(0.95)
    ax.set_xlim(0, max_x)
    ax.legend(title="Tiếng Việt")
    save_fig(fig, "07_text_length_vs_score.png", output_dir)


def plot_violin_room_type(df: pd.DataFrame, output_dir: str):
    top_rooms = df["room_type"].value_counts().head(15).index
    df_plot = df[df["room_type"].isin(top_rooms)]
    if df_plot.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 8))
    # ĐÃ SỬA: dùng hue + legend=False
    sns.violinplot(data=df_plot, x="score", y="room_type",
                   hue="room_type", dodge=False, palette="Set2", legend=False, ax=ax)
    ax.set_title("Phân phối điểm theo loại phòng (Top 15)", fontsize=16)
    save_fig(fig, "08_violin_room_type.png", output_dir)


def plot_correlation_heatmap(df: pd.DataFrame, output_dir: str):
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) < 2:
        return

    corr = df[numeric_cols].corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, square=True,
                linewidths=.5, cbar_kws={"shrink": .8}, ax=ax)
    ax.set_title("Ma trận tương quan các biến số", fontsize=16)
    save_fig(fig, "09_correlation_heatmap.png", output_dir)


def plot_wordcloud_positive(df: pd.DataFrame, output_dir: str):
    pos_text = df[df["is_vietnamese"] & (df["positive_text"].str.strip() != "")]["positive_text"]
    if pos_text.empty:
        return

    text = " ".join(pos_text)
    wc = WordCloud(width=1200, height=600, background_color='white', max_words=200,
                   colormap="Greens", contour_width=1, contour_color='green').generate(text)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    ax.set_title("Từ khóa tích cực – Tiếng Việt", fontsize=18, pad=20)
    save_fig(fig, "10_wordcloud_positive.png", output_dir)


def plot_wordcloud_negative(df: pd.DataFrame, output_dir: str):
    neg_text = df[df["is_vietnamese"] & (df["negative_text"].str.strip() != "")]["negative_text"]
    if neg_text.empty:
        return

    text = " ".join(neg_text)
    wc = WordCloud(width=1200, height=600, background_color='black', max_words=200,
                   colormap="Reds", contour_width=1, contour_color='darkred').generate(text)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    ax.set_title("Từ khóa tiêu cực – Tiếng Việt", fontsize=18, pad=20)
    save_fig(fig, "11_wordcloud_negative.png", output_dir)


# ====================== HÀM CHÍNH – GỌI TẤT CẢ ======================
def generate_all_advanced_charts(data: Dict, output_dir: str = "outputs/advanced_analysis"):
    """
    CHẠY 1 LẦN → RA 11 BIỂU ĐỒ ĐẸP LUNG LINH, KHÔNG WARNING!
    """
    df = data["df"]
    top_provinces = data["top_provinces"]

    print("Bắt đầu vẽ biểu đồ nâng cao...")

    plot_score_distribution(df, output_dir)
    plot_missing_values(df, output_dir)
    plot_boxplot_score_by_province(df, output_dir)
    plot_score_distribution_top15(df, top_provinces, output_dir)
    plot_time_series_reviews(df, top_provinces, output_dir)
    plot_reviewer_deviation(df, output_dir)
    plot_text_length_vs_score(df, output_dir)
    plot_violin_room_type(df, output_dir)
    plot_correlation_heatmap(df, output_dir)
    plot_wordcloud_positive(df, output_dir)
    plot_wordcloud_negative(df, output_dir)

    print(f"\nHOÀN TẤT! Đã lưu tất cả biểu đồ tại:")
    print(f"→ {Path(output_dir).resolve()}")