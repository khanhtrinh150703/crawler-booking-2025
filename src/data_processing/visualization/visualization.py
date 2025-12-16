# src/visualization/advanced_charts.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from wordcloud import WordCloud
from typing import Dict, List
from matplotlib.dates import DateFormatter, MonthLocator

import matplotlib.pyplot as plt

# FIX FONT: Hỗ trợ đầy đủ tiếng Việt + tiếng Nhật (Katakana, Kanji...) mà không cần cài thêm
# Ưu tiên Yu Gothic (đẹp, hiện đại), fallback Meiryo, rồi Arial (hỗ trợ VN tốt)
plt.rcParams["font.family"] = "Meiryo"          # Font chính - đẹp nhất cho Japanese + Vietnamese
plt.rcParams["font.sans-serif"] = ["Yu Gothic", "Meiryo", "Arial", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False       # Fix dấu trừ bị thành ô vuông

plt.style.use("seaborn-v0_8-whitegrid")
sns.set_palette("husl")
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.formatter.useoffset"] = False

DEFAULT_OUTPUT = "outputs/advanced_analysis"
Path(DEFAULT_OUTPUT).mkdir(parents=True, exist_ok=True)

# HÀM ĐỊNH DẠNG SỐ – CHUẨN HÓA 4500 → 4.5K, 1234567 → 1.23M
def format_count(x):
    """Chuyển 4500 → 4.5K, 1234567 → 1.23M – siêu đẹp cho luận văn"""
    if x >= 1_000_000:
        return f'{x/1_000_000:.1f}M'.replace('.0M', 'M')
    elif x >= 1_000:
        return f'{x/1_000:.1f}K'.replace('.0K', 'K')
    else:
        return f'{int(x):,}'

def save_fig(fig: plt.Figure, filename: str, output_dir: str = DEFAULT_OUTPUT):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = Path(output_dir) / filename
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"   → Đã lưu: {filename}")

# 01. Phân phối điểm – ĐẸP HOÀN HẢO, SỐ CHÍNH GIỮA CỘT, CHỈ HIỆN 1→10
def plot_score_distribution(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ biểu đồ histogram phân phối điểm đánh giá từ 1 đến 10,
    hiển thị số lượng chính xác trên đầu mỗi cột và lưu file ảnh.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa cột 'score' với điểm đánh giá.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    # Tạo figure và axis với kích thước phù hợp
    fig, ax = plt.subplots(figsize=(12, 7.5))

    # Chuẩn bị dữ liệu: loại bỏ NaN và chuyển sang float
    scores = df["score"].dropna().astype(float)

    # Định nghĩa bins để các cột nằm chính giữa số nguyên từ 1 đến 10
    bins = np.arange(0.5, 11.6, 1)

    # Vẽ histogram
    n, _, patches = ax.hist(
        scores,
        bins=bins,
        color="#e74c3c",
        alpha=0.85,
        edgecolor="black",
        linewidth=1.3,
        rwidth=0.88,
    )

    # Thiết lập tiêu đề và nhãn trục
    ax.set_title("01. Phân phối điểm đánh giá", fontsize=20, fontweight="bold", pad=25)
    ax.set_xlabel("Điểm số", fontsize=14)
    ax.set_ylabel("Số lượng đánh giá", fontsize=14)

    # Chỉ hiển thị tick từ 1 đến 10, giới hạn trục x
    ax.set_xticks(range(1, 11))
    ax.set_xlim(0.5, 10.5)

    # Thêm lưới ngang nhẹ để dễ đọc
    ax.grid(axis="y", alpha=0.3)

    # Thêm text hiển thị số lượng chính giữa trên đầu mỗi cột có dữ liệu
    max_n = max(n)
    for i, patch in enumerate(patches):
        count = n[i]
        if count > 0:
            ax.text(
                patch.get_x() + patch.get_width() / 2,
                patch.get_height() + max_n * 0.03,
                format_count(count),
                ha="center",
                va="bottom",
                fontweight="bold",
                fontsize=11,
                color="#2c3e50",
            )

    # Lưu biểu đồ vào file
    save_fig(fig, "01_score_distribution.png", output_dir)
    
# 02. Missing values
def plot_missing_values(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ heatmap hiển thị ma trận dữ liệu thiếu (missing values) trong DataFrame,
    giúp nhận diện nhanh các cột và hàng có giá trị bị thiếu.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame cần kiểm tra dữ liệu thiếu.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    # Tạo figure với kích thước phù hợp để hiển thị toàn bộ các cột
    fig, ax = plt.subplots(figsize=(14, 10))

    # Vẽ heatmap: ô vàng (True) đại diện cho giá trị thiếu, ô tím (False) là giá trị tồn tại
    sns.heatmap(
        df.isnull(),          # Ma trận boolean: True nếu giá trị thiếu
        cbar=True,            # Hiển thị thanh màu bên phải
        yticklabels=False,    # Ẩn nhãn trục y để tránh rối (vì thường có quá nhiều hàng)
        cmap="viridis",       # Bảng màu viridis giúp phân biệt rõ ràng
        ax=ax,
    )

    # Đặt tiêu đề cho biểu đồ
    ax.set_title("02. Ma trận dữ liệu thiếu", fontsize=18, fontweight="bold")

    # Lưu biểu đồ vào file
    save_fig(fig, "02_missing_values.png", output_dir)

# 03. Boxplot tỉnh
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from your_module import save_fig  # Giả sử save_fig được định nghĩa ở nơi khác


def plot_boxplot_by_province(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ boxplot phân phối điểm đánh giá theo từng tỉnh/thành phố,
    sắp xếp theo median điểm giảm dần, loại bỏ tỉnh 'Khác'.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa ít nhất các cột 'province' và 'score'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    # Lọc bỏ tỉnh "Khác" (thường là dữ liệu không xác định hoặc ngoài phạm vi)
    df_plot = df[df["province"] != "Khác"]

    # Nếu không còn dữ liệu sau khi lọc thì không vẽ biểu đồ
    if df_plot.empty:
        return

    # Sắp xếp tỉnh/thành theo median điểm giảm dần để dễ so sánh
    order = (
        df_plot.groupby("province")["score"]
        .median()
        .sort_values(ascending=False)
        .index
    )

    # Tạo figure với kích thước phù hợp
    fig, ax = plt.subplots(figsize=(12, 9))

    # Vẽ boxplot ngang: trục y là tỉnh/thành, trục x là điểm số
    sns.boxplot(
        data=df_plot,
        x="score",
        y="province",
        order=order,              # Thứ tự tỉnh đã sắp xếp
        hue="province",           # Màu theo tỉnh (cần để palette hoạt động)
        dodge=False,              # Không dịch chuyển các box (vì chỉ 1 box mỗi tỉnh)
        palette="coolwarm",       # Bảng màu nóng-lạnh để phân biệt cao-thấp
        legend=False,             # Ẩn legend vì đã có nhãn trục y
        ax=ax,
    )

    # Thiết lập tiêu đề và nhãn trục
    ax.set_title("03. Boxplot điểm theo tỉnh/thành", fontsize=18, fontweight="bold")
    ax.set_xlabel("Điểm số")
    ax.set_ylabel("")  # Có thể để trống vì nhãn tỉnh đã hiển thị trên trục y

    # Lưu biểu đồ vào file
    save_fig(fig, "03_boxplot_by_province.png", output_dir)

# 04. Phổ điểm Top 15 – FIX 100%: LUÔN HIỆN ĐỦ 1 2 3 4 5 6 7 8 9 10 + SỐ CHÍNH GIỮA
def plot_score_facet_top15(df: pd.DataFrame, top_provinces: List[str], output_dir: str):
    df_plot = df[df["province"].isin(top_provinces)].copy()
    if df_plot.empty or "score" not in df_plot.columns or df_plot["score"].isna().all():
        print("   → Bỏ qua biểu đồ 04: Không có dữ liệu score")
        return

    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    df_plot = df_plot.dropna(subset=["score"])
    bins = np.arange(0.5, 11.6, 1)

    g = sns.FacetGrid(df_plot, col="province", col_wrap=3, height=4.4, aspect=1.5,
                      sharex=True, sharey=False)

    def hist_with_kde(x, **kwargs):
        ax = plt.gca()
        counts, _, _ = ax.hist(x, bins=bins, color="#3498db", alpha=0.82,
                               edgecolor="black", linewidth=1.1, rwidth=0.9)
        sns.kdeplot(x, color="#2c3e50", linewidth=2.2, ax=ax)
        
        max_count = max(counts) if counts.size > 0 else 1
        for i, count in enumerate(counts):
            if count > 0:
                center = bins[i] + 0.5
                ax.text(center, count + max_count * 0.08,
                        format_count(int(count)),
                        ha='center', va='bottom', fontweight='bold',
                        fontsize=10, color='#2c3e50')

    g.map(hist_with_kde, "score")

    for ax in g.axes.flat:
        ax.set_xlim(0.5, 10.5)
        ax.set_xticks(range(1, 11))
        ax.set_xticklabels(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        ax.set_xlabel("Điểm số", fontsize=11)
        ax.grid(axis='y', alpha=0.3)

    g.set_axis_labels("", "Số lượng đánh giá")
    g.fig.suptitle("04. Phổ điểm đánh giá – Top 15 địa điểm",
                   fontsize=22, fontweight='bold', y=1.01)
    plt.subplots_adjust(bottom=0.18, top=0.92, hspace=0.5, wspace=0.25)
    save_fig(g.fig, "04_score_facet_top15.png", output_dir)

# 05. Time series
def plot_time_series_top8(df: pd.DataFrame, top_provinces: List[str], output_dir: str):
    if "month_year" not in df.columns or df["month_year"].isna().all(): return
    df_plot = df[df["province"].isin(top_provinces)].copy()
    df_plot["date"] = pd.to_datetime(df_plot["month_year"], format="%Y-%m", errors="coerce")
    df_plot = df_plot.dropna(subset=["date"])

    if df_plot.empty: return
    trend = df_plot.groupby([pd.Grouper(key="date", freq="MS"), "province"]).size().unstack(fill_value=0)
    full_range = pd.date_range(trend.index.min(), trend.index.max(), freq="MS")
    trend = trend.reindex(full_range, fill_value=0)

    fig, ax = plt.subplots(figsize=(18, 10))
    
    # 8 màu được chọn lọc: rõ ràng, khác biệt, đẹp mắt
    custom_colors = [
        '#1f77b4',  # Xanh dương đậm
        '#ff7f0e',  # Cam rực
        '#2ca02c',  # Xanh lá đậm  
        '#d62728',  # Đỏ tươi
        '#9467bd',  # Tím đẹp
        '#8c564b',  # Nâu đỏ
        '#e377c2',  # Hồng tím
        '#17becf'   # Xanh ngọc
    ]
    
    # Đặt cycle màu tùy chỉnh
    ax.set_prop_cycle('color', custom_colors)
    
    for prov in top_provinces[:8]:
        if prov in trend.columns:
            ax.plot(trend.index, trend[prov], label=prov, linewidth=3.5, marker='o', markersize=8)
    
    ax.set_title("05. Xu hướng số lượng review – Top 8 địa điểm", fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel("Thời gian"); ax.set_ylabel("Số review")
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(MonthLocator(interval=max(1, len(trend)//18)))
    ax.xaxis.set_major_formatter(DateFormatter("%m/%Y"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    save_fig(fig, "05_time_series_top8.png", output_dir)

# 06. Độ lệch reviewer – ĐẸP HƠN, CHUẨN KHOA HỌC
def plot_reviewer_deviation(df: pd.DataFrame, output_dir: str):
    if "deviation" not in df.columns or df["deviation"].isna().all():
        print("   → Bỏ qua biểu đồ 06: Không có deviation")
        return

    fig, ax = plt.subplots(figsize=(13, 8))
    dev = df["deviation"].dropna()
    n, bins, patches = ax.hist(dev, bins=80, color="#9b59b6", alpha=0.85,
                               edgecolor='white', linewidth=0.8)

    mean_dev = dev.mean()
    ax.axvline(mean_dev, color='red', linestyle='--', linewidth=4, label=f'Trung bình = {mean_dev:.3f}')
    ax.axvline(0, color='black', linestyle='-', linewidth=2, alpha=0.6, label='Không thiên vị (0)')

    ax.set_title("06. Phân phối độ lệch điểm của reviewer so với trung bình khách sạn",
                 fontsize=19, fontweight='bold', pad=25)
    ax.set_xlabel("Độ lệch = Score cá nhân − Điểm trung bình khách sạn", fontsize=13)
    ax.set_ylabel("Số lượng reviewer")
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3)

    for i, patch in enumerate(patches):
        if n[i] > max(n)*0.1:  # Chỉ hiện cột cao >10%
            ax.text(patch.get_x() + patch.get_width()/2,
                    patch.get_height() + max(n)*0.02,
                    format_count(int(n[i])),
                    ha='center', va='bottom', fontweight='bold', fontsize=9)

    save_fig(fig, "06_reviewer_deviation.png", output_dir)

# 07. Mối liên hệ độ dài bình luận vs điểm số
def plot_text_length_vs_score(df: pd.DataFrame, output_dir: str):
    sample = df.sample(min(10000, len(df)), random_state=42)
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.scatterplot(data=sample, x="text_length", y="score", hue="is_vietnamese", 
                    alpha=0.6, palette="deep", ax=ax, s=50)
    ax.set_title("07. Độ dài bình luận vs Điểm số", fontsize=18, fontweight='bold')
    ax.set_xlabel("Số từ", fontsize=14)
    ax.set_ylabel("Điểm số", fontsize=14)
    ax.set_xlim(0, df["text_length"].quantile(0.97))
    ax.legend(title="Tiếng Việt", title_fontsize=12, fontsize=10)
    save_fig(fig, "07_text_length_vs_score.png", output_dir)

# 08. Top loại phòng phổ biến
def plot_top_room_types(df: pd.DataFrame, output_dir: str, top_n: int = 15):
    counts = df["room_type"].value_counts().head(top_n)
    if counts.empty: return
    fig, ax = plt.subplots(figsize=(12, max(6, len(counts)*0.5)))
    bars = ax.barh(counts.index, counts.values, color=sns.color_palette("viridis", len(counts)))
    ax.set_title(f"08. Top {len(counts)} loại phòng phổ biến nhất", fontsize=18, fontweight='bold')
    ax.set_xlabel("Số lượng đánh giá", fontsize=14)
    ax.invert_yaxis()
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(width + width*0.01, bar.get_y() + bar.get_height()/2,
                format_count(int(width)),
                va='center', fontweight='bold', fontsize=10)
    plt.tight_layout()
    save_fig(fig, "08_top_room_types.png", output_dir)

# 09. Phân bố theo loại nhóm khách
def plot_group_type_distribution(df: pd.DataFrame, output_dir: str):
    if "group_type" not in df.columns: return
    counts = df["group_type"].value_counts()
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(counts.index, counts.values, color=sns.color_palette("mako", len(counts)))
    ax.set_title("09. Phân bố theo loại nhóm khách", fontsize=18, fontweight='bold')
    ax.set_ylabel("Số lượng", fontsize=14)
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + height*0.02,
                format_count(int(height)),
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    save_fig(fig, "09_group_type_distribution.png", output_dir)

# 10. Pie chart lọc dữ liệu
def plot_processing_ratio_pie(stats: dict, output_dir: str):
    total = stats.get("total_reviews", 0)
    kept = stats.get("kept_count_vn", 0)
    non_vn = stats.get("non_vietnamese", 0)
    low_score = stats.get("low_score", 0)
    null_c = stats.get("null_empty", 0)
    actual = kept + non_vn + low_score + null_c
    if actual == 0: return

    labels = ['Tiếng Việt hợp lệ', 'Không phải TV', 'Điểm < 5', 'Rỗng/Null']
    sizes = [kept, non_vn, low_score, null_c]
    colors = ['#27ae60', '#3498db', '#e74c3c', '#95a5a6']
    explode = (0.15, 0.05, 0.05, 0.1)

    fig, ax = plt.subplots(figsize=(12, 9))
    def autopct(pct):
        if pct < 3: return ''
        val = int(round(pct/100*actual))
        return f'{pct:.1f}%\n{format_count(val)}'
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct=autopct,
           startangle=90, textprops={'fontsize': 13, 'color': 'white', 'weight': 'bold'},
           wedgeprops={'edgecolor': 'black', 'linewidth': 3})
    ax.set_title("10. TỶ LỆ LỌC DỮ LIỆU BOOKING.COM", fontsize=22, fontweight='bold', pad=40)
    save_fig(fig, "10_data_processing_ratio.png", output_dir)

# 11. Top quốc gia có nhiều đánh giá nhất
def plot_country_distribution(df: pd.DataFrame, output_dir: str):
    if "country" not in df.columns: return
    top = df["country"].value_counts().head(12)
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(top.index, top.values, color=sns.color_palette("Set2", len(top)))
    ax.set_title("11. Top quốc gia có nhiều đánh giá nhất", fontsize=18, fontweight='bold')
    ax.set_ylabel("Số lượng", fontsize=14)
    plt.xticks(rotation=45, ha='right')
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + h*0.02,
                format_count(int(h)),
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    save_fig(fig, "11_top_countries.png", output_dir)

# 12. Wordcloud tiếng Việt
def plot_vietnamese_wordcloud(df: pd.DataFrame, output_dir: str):
    text_col = "full_text" if "full_text" in df.columns else "combined_text"
    if text_col not in df.columns: return
    text = " ".join(df[df["is_vietnamese"]][text_col].dropna().astype(str))
    if not text.strip(): return

    wc = WordCloud(
        width=1800, height=1000, background_color='white', max_words=300,
        colormap='viridis', contour_width=3, contour_color='#1f77b4',
        min_font_size=10, max_font_size=150
    ).generate(text)

    fig, ax = plt.subplots(figsize=(18, 11))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    ax.set_title("12. WORDCLOUD ĐÁNH GIÁ TIẾNG VIỆT (Tất cả bình luận)", 
                 fontsize=24, fontweight='bold', pad=30)
    save_fig(fig, "12_vietnamese_wordcloud_full.png", output_dir)

# 13. Ma trận tương quan các biến số
def plot_correlation_heatmap(df: pd.DataFrame, output_dir: str):
    num_cols = df.select_dtypes(include=[np.number]).columns
    if len(num_cols) < 2: return
    corr = df[num_cols].corr()
    fig, ax = plt.subplots(figsize=(11, 9))
    sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, square=True,
                linewidths=.8, cbar_kws={"shrink": .8}, ax=ax, fmt=".2f")
    ax.set_title("13. Ma trận tương quan các biến số", fontsize=18, fontweight='bold')
    save_fig(fig, "13_correlation_heatmap.png", output_dir)

# 14. Xu hướng tổng số lượng review theo thời gian (toàn bộ dữ liệu)
def plot_review_trend_over_time(df: pd.DataFrame, output_dir: str):
    if "month_year" not in df.columns:
        return
    df_plot = df.copy()
    df_plot["date"] = pd.to_datetime(df_plot["month_year"], format="%Y-%m", errors="coerce")
    df_plot = df_plot.dropna(subset=["date"])
    if df_plot.empty:
        return

    trend = df_plot.groupby(pd.Grouper(key="date", freq="MS")).size()
    trend = trend.reindex(pd.date_range(trend.index.min(), trend.index.max(), freq="MS"), fill_value=0)

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(trend.index, trend.values, linewidth=4, color="#2ecc71", marker='o', markersize=6)
    ax.fill_between(trend.index, trend.values, alpha=0.3, color="#2ecc71")
    
    ax.set_title("14. Xu hướng tổng số lượng đánh giá theo thời gian", fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel("Thời gian", fontsize=14)
    ax.set_ylabel("Số lượng đánh giá", fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(MonthLocator(interval=max(1, len(trend)//15)))
    ax.xaxis.set_major_formatter(DateFormatter("%m/%Y"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    
    # Annotate đỉnh cao
    peak_idx = trend.idxmax()
    peak_val = trend.max()
    ax.annotate(f'Đỉnh: {format_count(peak_val)}\n{peak_idx.strftime("%m/%Y")}',
                xy=(peak_idx, peak_val), xytext=(10, 10), textcoords='offset points',
                fontsize=12, fontweight='bold', color='#e74c3c',
                arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2))
    
    save_fig(fig, "14_review_trend_over_time.png", output_dir)

# 15. Điểm trung bình theo thời gian (rolling 3 tháng)
def plot_average_score_over_time(df: pd.DataFrame, output_dir: str):
    if "month_year" not in df.columns or "score" not in df.columns:
        return
    df_plot = df.copy()
    df_plot["date"] = pd.to_datetime(df_plot["month_year"], format="%Y-%m", errors="coerce")
    df_plot = df_plot.dropna(subset=["date", "score"])
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    if df_plot.empty:
        return

    monthly = df_plot.groupby(pd.Grouper(key="date", freq="MS"))["score"].mean()
    monthly = monthly.reindex(pd.date_range(monthly.index.min(), monthly.index.max(), freq="MS"))
    rolling = monthly.rolling(window=3, center=True).mean()

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(monthly.index, monthly.values, alpha=0.4, color="#3498db", label="Trung bình tháng")
    ax.plot(rolling.index, rolling.values, linewidth=4, color="#e74c3c", label="Trung bình trượt 3 tháng")
    
    ax.set_title("15. Điểm trung bình đánh giá theo thời gian", fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel("Thời gian", fontsize=14)
    ax.set_ylabel("Điểm trung bình", fontsize=14)
    ax.set_ylim(7.5, 9.5)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(MonthLocator(interval=max(1, len(monthly)//15)))
    ax.xaxis.set_major_formatter(DateFormatter("%m/%Y"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    
    save_fig(fig, "15_average_score_over_time.png", output_dir)

# 16. Điểm trung bình theo nhóm khách
def plot_score_by_group_type(df: pd.DataFrame, output_dir: str):
    if "group_type" not in df.columns or "score" not in df.columns:
        return
    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    order = df_plot.groupby("group_type")["score"].median().sort_values(ascending=False).index
    
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.boxplot(data=df_plot, x="score", y="group_type", order=order,
                palette="Set3", hue="group_type", dodge=False, legend=False, ax=ax)
    ax.set_title("16. Điểm đánh giá theo loại nhóm khách", fontsize=20, fontweight='bold')
    ax.set_xlabel("Điểm số", fontsize=14)
    ax.set_ylabel("Nhóm khách", fontsize=14)
    save_fig(fig, "16_score_by_group_type.png", output_dir)

# 17. Violin plot điểm theo tỉnh (top 10 - đẹp hơn boxplot)
def plot_violin_score_by_province(df: pd.DataFrame, output_dir: str):
    df_plot = df[df["province"] != "Khác"]
    top_provinces = df_plot["province"].value_counts().head(10).index
    df_plot = df_plot[df_plot["province"].isin(top_provinces)]
    if df_plot.empty:
        return
    
    order = df_plot.groupby("province")["score"].median().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(12, 9))
    sns.violinplot(data=df_plot, x="score", y="province", order=order,
                   palette="coolwarm", hue="province", dodge=False, legend=False, ax=ax, inner="quartile")
    ax.set_title("17. Phân phối điểm theo tỉnh/thành (Top 10) - Violin Plot", fontsize=20, fontweight='bold')
    ax.set_xlabel("Điểm số", fontsize=14)
    save_fig(fig, "17_violin_score_by_province.png", output_dir)

# 18. Wordcloud: Điểm cao (9-10) vs Điểm thấp (≤7)
def plot_wordcloud_high_vs_low(df: pd.DataFrame, output_dir: str):
    text_col = "full_text"
    if text_col not in df.columns or "score" not in df.columns or "is_vietnamese" not in df.columns:
        return
    
    df_vn = df[df["is_vietnamese"]].copy()
    df_vn["score"] = pd.to_numeric(df_vn["score"], errors="coerce")
    high = df_vn[df_vn["score"] >= 9]
    low = df_vn[df_vn["score"] <= 7]
    
    if high.empty or low.empty:
        return
    
    text_high = " ".join(high[text_col].dropna().astype(str))
    text_low = " ".join(low[text_col].dropna().astype(str))
    
    wc_high = WordCloud(width=900, height=600, background_color='white', colormap='Greens', max_words=150).generate(text_high)
    wc_low = WordCloud(width=900, height=600, background_color='white', colormap='Reds', max_words=150).generate(text_low)
    
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))
    axes[0].imshow(wc_high, interpolation='bilinear')
    axes[0].set_title("18. Từ khóa phổ biến - Điểm cao (9-10)", fontsize=20, fontweight='bold', color='#27ae60')
    axes[0].axis("off")
    
    axes[1].imshow(wc_low, interpolation='bilinear')
    axes[1].set_title("18. Từ khóa phổ biến - Điểm thấp (≤7)", fontsize=20, fontweight='bold', color='#e74c3c')
    axes[1].axis("off")
    
    plt.tight_layout()
    save_fig(fig, "18_wordcloud_high_vs_low_score.png", output_dir)

# 19. Tỷ lệ đánh giá tiếng Việt theo tỉnh (top 15)
def plot_vietnamese_ratio_by_province(df: pd.DataFrame, output_dir: str):
    if "province" not in df.columns or "is_vietnamese" not in df.columns:
        return
    df_plot = df[df["province"] != "Khác"]
    ratio = df_plot.groupby("province")["is_vietnamese"].mean().sort_values(ascending=False)
    top = ratio.head(15)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(top.index, top.values * 100, color=sns.color_palette("Blues_r", len(top)))
    ax.set_title("19. Tỷ lệ đánh giá tiếng Việt theo tỉnh/thành (Top 15)", fontsize=20, fontweight='bold')
    ax.set_xlabel("Tỷ lệ (%)", fontsize=14)
    ax.invert_yaxis()
    
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2,
                f'{width:.1f}%', va='center', fontweight='bold', fontsize=11)
    
    save_fig(fig, "19_vietnamese_ratio_by_province.png", output_dir)

# 20. Điểm trung bình theo thời gian lưu trú (stay_duration) – ĐÃ FIX "X đêm" → số
def plot_score_by_stay_duration(df: pd.DataFrame, output_dir: str):
    if "stay_duration" not in df.columns or "score" not in df.columns:
        return
    
    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    
    # FIX CHÍNH: Extract số từ chuỗi kiểu "1 đêm", "2 đêm",...
    df_plot["stay_duration_num"] = df_plot["stay_duration"].str.extract(r'(\d+)').astype(float)
    
    # Kiểm tra xem có giá trị hợp lệ không
    df_plot = df_plot.dropna(subset=["stay_duration_num", "score"])
    if df_plot.empty:
        print("   → Bỏ qua biểu đồ 20: Không có dữ liệu stay_duration hợp lệ sau khi extract")
        return
    
    # Group thành bin hợp lý
    bins = [0, 1, 3, 7, np.inf]
    labels = ["1 đêm", "2-3 đêm", "4-7 đêm", "8+ đêm"]
    df_plot["duration_group"] = pd.cut(df_plot["stay_duration_num"], bins=bins, labels=labels, include_lowest=True)
    
    # Sắp xếp thứ tự
    order = ["1 đêm", "2-3 đêm", "4-7 đêm", "8+ đêm"]
    
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.boxplot(data=df_plot, x="duration_group", y="score", order=order,
                palette="Oranges_r", hue="duration_group", dodge=False, legend=False, ax=ax)
    
    ax.set_title("20. Điểm đánh giá theo thời gian lưu trú", 
                 fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel("Thời gian lưu trú", fontsize=14)
    ax.set_ylabel("Điểm số", fontsize=14)
    
    # Thêm số lượng mẫu trên mỗi box (nice touch)
    counts = df_plot["duration_group"].value_counts().reindex(order)
    for i, count in enumerate(counts):
        ax.text(i, df_plot["score"].max() + 0.1, f'n={format_count(count)}', 
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    save_fig(fig, "20_score_by_stay_duration.png", output_dir)

# 21. Heatmap số lượng review theo tháng & tỉnh (top 8 tỉnh)
def plot_review_heatmap_by_province(df: pd.DataFrame, top_provinces: List[str], output_dir: str):
    if "month_year" not in df.columns or df.empty:
        return
    df_plot = df[df["province"].isin(top_provinces[:8])].copy()
    df_plot["date"] = pd.to_datetime(df_plot["month_year"], format="%Y-%m", errors="coerce")
    df_plot = df_plot.dropna(subset=["date"])
    
    df_plot["year_month"] = df_plot["date"].dt.strftime("%Y-%m")
    df_plot["month"] = df_plot["date"].dt.month
    pivot = df_plot.pivot_table(values="score", index="province", columns="month", 
                                aggfunc="count", fill_value=0)
    
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(pivot, annot=True, fmt="d", cmap="YlOrRd", linewidths=.5, ax=ax,
                cbar_kws={"label": "Số lượng review"})
    ax.set_title("21. Heatmap số lượng review theo tháng – Top 8 tỉnh ", 
                 fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel("Tháng", fontsize=14)
    ax.set_ylabel("Tỉnh/thành", fontsize=14)
    save_fig(fig, "21_review_heatmap_by_province.png", output_dir)

# 22. Scatter: Số review của hotel vs Điểm trung bình hotel
def plot_hotel_popularity_vs_score(df: pd.DataFrame, output_dir: str):
    if "hotel_name" not in df.columns or "score" not in df.columns:
        return
    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    
    hotel_stats = df_plot.groupby("hotel_name").agg(
        review_count=("score", "count"),
        avg_score=("score", "mean")
    ).reset_index()
    hotel_stats = hotel_stats[hotel_stats["review_count"] >= 5]  # Lọc hotel ít review
    
    fig, ax = plt.subplots(figsize=(14, 9))
    sns.scatterplot(data=hotel_stats, x="review_count", y="avg_score", 
                    alpha=0.6, size="review_count", sizes=(20, 200), hue="review_count",
                    palette="Blues_d", legend=False, ax=ax)
    ax.set_title("22. Số lượng review vs Điểm trung bình của khách sạn ", 
                 fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel("Số lượng review (log scale)", fontsize=14)
    ax.set_ylabel("Điểm trung bình", fontsize=14)
    ax.set_xscale("log")
    save_fig(fig, "22_hotel_popularity_vs_score.png", output_dir)

# 23. So sánh điểm số: Khách Việt vs Khách quốc tế (top 10 tỉnh)
def plot_score_vietnamese_vs_international(df: pd.DataFrame, output_dir: str):
    if "is_vietnamese" not in df.columns or "province" not in df.columns:
        return
    df_plot = df[df["province"] != "Khác"].copy()
    top_provinces = df_plot["province"].value_counts().head(10).index
    df_plot = df_plot[df_plot["province"].isin(top_provinces)]
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    
    summary = df_plot.groupby(["province", "is_vietnamese"])["score"].mean().unstack()
    summary.columns = ["Khách quốc tế", "Khách Việt Nam"]
    
    fig, ax = plt.subplots(figsize=(12, 8))
    summary.plot(kind="barh", ax=ax, color=["#3498db", "#e74c3c"])
    ax.set_title("23. Điểm trung bình: Khách Việt vs Quốc tế – Top 10 tỉnh (CULTURAL BIAS?)", 
                 fontsize=20, fontweight='bold')
    ax.set_xlabel("Điểm trung bình", fontsize=14)
    ax.invert_yaxis()
    save_fig(fig, "23_score_vn_vs_international.png", output_dir)

# 24. Top bigrams (cụm 2 từ) theo điểm cao/thấp – TIẾT LỘ TỪ KHÓA THỰC TẾ
def plot_top_bigrams_high_low(df: pd.DataFrame, output_dir: str):
    from collections import Counter
    from sklearn.feature_extraction.text import CountVectorizer
    
    if "full_text" not in df.columns or "score" not in df.columns or "is_vietnamese" not in df.columns:
        return
    
    df_vn = df[df["is_vietnamese"]].copy()
    df_vn["score"] = pd.to_numeric(df_vn["score"], errors="coerce")
    high = df_vn[df_vn["score"] >= 8]["full_text"].dropna()
    low = df_vn[df_vn["score"] <= 7]["full_text"].dropna()
    
    vec = CountVectorizer(ngram_range=(2,2), stop_words=None, max_features=20)
    
    high_bigrams = vec.fit_transform(high.astype(str))
    low_bigrams = vec.fit_transform(low.astype(str))
    
    high_counts = Counter(dict(zip(vec.get_feature_names_out(), high_bigrams.sum(axis=0).A1)))
    low_counts = Counter(dict(zip(vec.get_feature_names_out(), low_bigrams.sum(axis=0).A1)))
    
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))
    pd.Series(dict(high_counts.most_common(20))).sort_values().plot(kind="barh", ax=axes[0], color="#27ae60")
    axes[0].set_title("24. Top bigrams – Điểm cao (8-10)", fontsize=18, fontweight='bold')
    
    pd.Series(dict(low_counts.most_common(20))).sort_values().plot(kind="barh", ax=axes[1], color="#e74c3c")
    axes[1].set_title("24. Top bigrams – Điểm thấp (≤7)", fontsize=18, fontweight='bold')
    
    plt.tight_layout()
    save_fig(fig, "24_top_bigrams_high_vs_low.png", output_dir)
    
# 25. Điểm trung bình theo loại phòng (Top 15 phổ biến nhất) – MÀU SẮC SIÊU RÕ RÀNG, DỄ PHÂN BIỆT
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

def plot_score_by_room_type(df: pd.DataFrame, output_dir: str, top_n: int = 15):
    if "room_type" not in df.columns or "score" not in df.columns:
        return
    
    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    df_plot = df_plot.dropna(subset=["score"])
    
    # Top room_type theo số lượng review
    top_rooms = df_plot["room_type"].value_counts().head(top_n).index
    df_plot = df_plot[df_plot["room_type"].isin(top_rooms)]
    if df_plot.empty:
        return
    
    # Tính mean score và sắp xếp từ cao xuống thấp
    mean_scores = df_plot.groupby("room_type")["score"].mean().sort_values(ascending=False)
    
    # Tự động height
    fig_height = max(8, len(mean_scores) * 0.55)
    fig, ax = plt.subplots(figsize=(16, fig_height))
    
    # Palette màu ĐẸP + RÕ RÀNG NHẤT (gradient rực rỡ, phân biệt tốt)
    colors = sns.color_palette("Spectral_r", len(mean_scores))  # Spectral_r: từ đỏ (cao) đến xanh (thấp) – siêu đẹp!
    # Hoặc thử "viridis" nếu muốn hiện đại hơn: colors = sns.color_palette("viridis", len(mean_scores))
    
    # Vẽ barh
    bars = ax.barh(mean_scores.index, mean_scores.values, color=colors, height=0.8)
    
    # Thêm giá trị mean ở cuối thanh (nhưng cách ra, sạch sẽ)
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(width + 0.05, bar.get_y() + bar.get_height()/2, 
                f'{width:.2f}', va='center', ha='left', fontweight='bold', fontsize=12)
    
    ax.set_title(f"25. Điểm đánh giá trung bình theo loại phòng (Top {top_n} phổ biến nhất)", 
                 fontsize=22, fontweight='bold', pad=25)
    ax.set_xlabel("Điểm trung bình", fontsize=15)
    ax.set_ylabel("Loại phòng", fontsize=15)
    ax.grid(axis='x', alpha=0.3)
    ax.invert_yaxis()  # Cao nhất ở trên
    
    plt.tight_layout()
    save_fig(fig, "25_score_by_room_type_bar_clean.png", output_dir)

# 26. Độ lệch điểm (deviation) theo nhóm khách – AI THIÊN VỊ NHẤT?
def plot_deviation_by_group_type(df: pd.DataFrame, output_dir: str):
    if "deviation" not in df.columns or "group_type" not in df.columns:
        return
    
    df_plot = df.copy()
    df_plot["deviation"] = pd.to_numeric(df_plot["deviation"], errors="coerce")
    df_plot = df_plot.dropna(subset=["deviation"])
    
    order = df_plot.groupby("group_type")["deviation"].median().sort_values(ascending=False).index
    
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.boxplot(data=df_plot, x="deviation", y="group_type", order=order,
                palette="Set3", hue="group_type", dodge=False, legend=False, ax=ax)
    
    ax.axvline(0, color='black', linestyle='--', linewidth=2, label='Không thiên vị')
    ax.set_title("26. Độ lệch điểm đánh giá theo nhóm khách – Nhóm nào thiên vị nhất?", 
                 fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel("Độ lệch (Score cá nhân − Trung bình khách sạn)", fontsize=14)
    ax.set_ylabel("Nhóm khách", fontsize=14)
    ax.legend(fontsize=12)
    
    plt.tight_layout()
    save_fig(fig, "26_deviation_by_group_type.png", output_dir)

# 27. Phân bố điểm theo khách sạn (Top 20 hotel nhiều review nhất) – CHẤT LƯỢNG ỔN ĐỊNH?
def plot_score_by_top_hotels(df: pd.DataFrame, output_dir: str, top_n: int = 20):
    if "hotel_name" not in df.columns or "score" not in df.columns:
        return
    
    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    
    # Lấy top hotel theo số lượng review
    top_hotels = df_plot["hotel_name"].value_counts().head(top_n).index
    df_plot = df_plot[df_plot["hotel_name"].isin(top_hotels)]
    if df_plot.empty:
        return
    
    # Sắp xếp theo median score
    order = df_plot.groupby("hotel_name")["score"].median().sort_values(ascending=False).index
    
    # Tự động tăng height
    fig_height = max(10, len(top_hotels) * 0.65)
    fig, ax = plt.subplots(figsize=(15, fig_height))
    
    sns.violinplot(data=df_plot, x="score", y="hotel_name", order=order,
                   palette="coolwarm", hue="hotel_name", dodge=False, legend=False, ax=ax, inner="quartile")
    
    ax.set_title(f"27. Phân phối điểm theo khách sạn (Top {top_n} nhiều review nhất)", 
                 fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel("Điểm số", fontsize=14)
    ax.set_ylabel("Tên khách sạn", fontsize=14)
    ax.tick_params(axis='y', labelsize=10)
    
    plt.tight_layout(pad=3.0)
    save_fig(fig, "27_score_by_top_hotels.png", output_dir)


def plot_pairplot_numeric_features(df: pd.DataFrame, output_dir: str):
    cols = ['score', 'text_length', 'deviation', 'hotel_avg_score']
    if 'stay_duration_num' in df.columns:
        cols.append('stay_duration_num')
    
    df_plot = df[cols].dropna()
    if len(df_plot) < 100:
        return
    
    df_sample = df_plot.sample(min(5000, len(df_plot)), random_state=42)
    
    g = sns.pairplot(
        df_sample,
        diag_kind='kde',
        plot_kws={'alpha': 0.5, 's': 20},
        diag_kws={'fill': True},
        corner=True  # Gọn hơn, tránh lặp
    )
    
    g.figure.suptitle("28. Pairplot các đặc trưng số – Mối quan hệ pairwise & phân bố", 
                   fontsize=22, fontweight='bold', y=1.02)
    
    # DÙNG g.tight_layout() THAY VÌ plt.tight_layout()
    g.tight_layout()
    
    save_fig(g.figure, "28_pairplot_numeric_features.png", output_dir)
    
# 29. Score vs Text Length theo nhóm khách
def plot_score_vs_text_length_faceted_vertical(df: pd.DataFrame, output_dir: str):
    if "text_length" not in df.columns or "score" not in df.columns or "group_type" not in df.columns:
        return
    
    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    df_plot = df_plot.dropna(subset=["score", "text_length", "group_type"])
    
    if df_plot.empty:
        return
    
    # Sort nhóm để thứ tự ổn định và đẹp
    df_plot["group_type"] = df_plot["group_type"].astype("category")
    unique_groups = df_plot["group_type"].cat.categories
    df_plot["group_type"] = df_plot["group_type"].cat.reorder_categories(sorted(unique_groups))
    
    # Tạo figure thủ công với GridSpec để kiểm soát layout hoàn toàn
    n_groups = len(unique_groups)
    fig = plt.figure(figsize=(14, 4 * n_groups))  # Chiều ngang rộng, mỗi nhóm cao 4 inch
    
    # GridSpec: 1 cột cho các plot + 1 cột nhỏ cho colorbar chung
    from matplotlib.gridspec import GridSpec
    gs = GridSpec(n_groups, 2, width_ratios=[50, 1], wspace=0.05, hspace=0.3)
    
    # Giới hạn x chung
    xlim_max = df_plot["text_length"].quantile(0.98)
    
    # Colorbar sẽ thêm sau, lấy từ hexbin đầu tiên
    cax = None
    hex_obj = None
    
    for i, group in enumerate(unique_groups):
        row = i
        sub = df_plot[df_plot["group_type"] == group]
        
        ax = fig.add_subplot(gs[row, 0])
        
        # Vẽ hexbin
        hexbin = ax.hexbin(sub["text_length"], sub["score"], gridsize=60, 
                           cmap="YlOrRd", mincnt=1, linewidths=0.2)
        
        ax.set_xlim(0, xlim_max)
        ax.set_ylim(df_plot["score"].min() - 0.5, df_plot["score"].max() + 0.5)
        
        # Tiêu đề mỗi nhóm
        ax.set_title(group, fontsize=16, fontweight='bold', pad=15)
        
        # Chỉ hiện xlabel ở hàng dưới cùng
        if i == n_groups - 1:
            ax.set_xlabel("Độ dài bình luận (số từ)", fontsize=14)
        else:
            ax.set_xlabel("")
        
        # Chỉ hiện ylabel ở tất cả (vì dọc), nhưng có thể bỏ nếu muốn sạch hơn
        ax.set_ylabel("Điểm số", fontsize=14)
        
        ax.grid(alpha=0.3)
        
        # Lưu hexbin đầu tiên để làm colorbar
        if i == 0:
            hex_obj = hexbin
    
    # Thêm colorbar chung bên phải
    cax = fig.add_subplot(gs[:, 1])  # Chiếm toàn bộ chiều dọc bên phải
    cb = plt.colorbar(hex_obj, cax=cax)
    cb.set_label('Số lượng bình luận', fontsize=14, rotation=270, labelpad=20)
    cb.ax.tick_params(labelsize=12)
    
    # Tiêu đề tổng
    fig.suptitle("29. Score vs Độ dài bình luận – Hexbin Density",
                 fontsize=22, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    # Điều chỉnh để suptitle không bị đè
    plt.subplots_adjust(top=0.9)
    
    save_fig(fig, "29_score_vs_text_length_vertical_hexbin.png", output_dir)
    
# 30. 

def plot_score_vs_text_length_stacked_bar(df: pd.DataFrame, output_dir: str, bins: int = 10):
    if "text_length" not in df.columns or "score" not in df.columns or "group_type" not in df.columns:
        return
    
    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    df_plot = df_plot.dropna(subset=["score", "text_length", "group_type"])
    
    if df_plot.empty:
        return
    
    # Chia độ dài bình luận thành bins bằng quantile (đảm bảo mỗi bin có số lượng tương đối đều)
    df_plot['length_bin'] = pd.qcut(df_plot["text_length"], q=bins, duplicates='drop')
    
    # Tính count tuyệt đối
    crosstab_count = pd.crosstab(df_plot['length_bin'], df_plot['group_type'])
    
    # Sắp xếp bin từ dài nhất xuống ngắn nhất (giống biểu đồ mẫu)
    crosstab_count = crosstab_count.sort_index(ascending=False)
    
    # Tính % để vẽ 100% stacked bar
    crosstab_pct = crosstab_count.div(crosstab_count.sum(axis=1), axis=0) * 100
    
    # Palette màu đẹp, rõ ràng (xanh lá, cam, xanh dương... giống biểu đồ FB/Twitter/Instagram)
    unique_groups = crosstab_count.columns
    custom_colors = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3']
    colors = custom_colors[:len(unique_groups)]
    if len(unique_groups) > len(custom_colors):
        colors += sns.color_palette("husl", len(unique_groups) - len(custom_colors)).tolist()
    
    # Tăng kích thước figure để có chỗ cho label dài
    fig, ax = plt.subplots(figsize=(18, max(9, len(crosstab_count) * 0.9)))
    
    # Vẽ 100% stacked bar horizontal
    crosstab_pct.plot(kind='barh', stacked=True, color=colors, ax=ax, width=0.8)
    
    ax.set_title("30. Tỷ lệ và số lượng nhóm khách theo độ dài bình luận",
                 fontsize=22, fontweight='bold', pad=30)
    ax.set_xlabel("Tỷ lệ phần trăm (%)", fontsize=15)
    ax.set_ylabel("Khoảng độ dài bình luận (số từ)", fontsize=15)
    ax.grid(axis='x', alpha=0.3)
    
    # Dual label: XX.X% (YYYY) — chỉ hiện khi >= 5% để tránh chồng chéo
    rects = ax.patches  # Các segment
    count_flat = crosstab_count.to_numpy().flatten('F')  # Flatten theo thứ tự stacked
    pct_flat = crosstab_pct.to_numpy().flatten('F')
    
    for rect, count, pct in zip(rects, count_flat, pct_flat):
        if pct >= 5:  # Ngưỡng hiển thị — có thể giảm xuống 3 nếu muốn hiện nhiều hơn
            label = f"{pct:.1f}% ({int(count)})"
            ax.text(
                rect.get_x() + rect.get_width() / 2,
                rect.get_y() + rect.get_height() / 2,
                label,
                ha='center',
                va='center',
                fontsize=11,
                fontweight='bold',
                color='white' 
            )
    
    # Legend bên phải
    ax.legend(title="Nhóm khách", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=12, title_fontsize=13)
    
    plt.tight_layout()
    save_fig(fig, "30_score_vs_text_length_100percent_stacked_dual_label.png", output_dir)

#31
def plot_sentiment_ratio_by_group(df: pd.DataFrame, output_dir: str):
    if "score" not in df.columns or "group_type" not in df.columns:
        return
    
    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    df_plot = df_plot.dropna(subset=["score", "group_type"])
    
    if df_plot.empty:
        return
    
    # Định nghĩa sentiment (có thể chỉnh threshold)
    def get_sentiment(s):
        if s >= 8:
            return "Positive"
        elif s <= 4:
            return "Negative"
        else:
            return None  # Neutral, bỏ qua để chỉ tính pos/neg
    
    df_plot['sentiment'] = df_plot["score"].apply(get_sentiment)
    df_sent = df_plot.dropna(subset=['sentiment'])  # Chỉ giữ pos/neg
    
    if df_sent.empty:
        return
    
    # Crosstab count pos/neg theo group
    crosstab_count = pd.crosstab(df_sent['group_type'], df_sent['sentiment'])
    
    # Sắp xếp theo tổng count giảm dần để nhóm lớn ở trên
    crosstab_count['total'] = crosstab_count.sum(axis=1)
    crosstab_count = crosstab_count.sort_values('total', ascending=True)  # Nhỏ ở trên để đẹp
    crosstab_count = crosstab_count.drop(columns='total')
    
    # Nếu nhóm nào thiếu Positive hoặc Negative, fill 0
    for col in ['Positive', 'Negative']:
        if col not in crosstab_count.columns:
            crosstab_count[col] = 0
    crosstab_count = crosstab_count[['Positive', 'Negative']]  # Thứ tự cố định
    
    # Tính % cho 100% stacked
    crosstab_pct = crosstab_count.div(crosstab_count.sum(axis=1), axis=0) * 100
    
    # Màu: Xanh lá cho Positive, Đỏ cho Negative
    colors = ['#66c2a5', '#fc8d62']  # Xanh lá positive, Cam/đỏ negative
    
    fig, ax = plt.subplots(figsize=(14, max(6, len(crosstab_count) * 0.7)))
    
    # Vẽ 100% stacked horizontal
    crosstab_pct.plot(kind='barh', stacked=True, color=colors, ax=ax, width=0.8)
    
    ax.set_title("31. Tỷ lệ đánh giá Tích cực & Tiêu cực theo nhóm khách",
                 fontsize=22, fontweight='bold', pad=30)
    ax.set_xlabel("Tỷ lệ phần trăm (%)", fontsize=15)
    ax.set_ylabel("Nhóm khách", fontsize=15)
    ax.grid(axis='x', alpha=0.3)
    
    # Dual label XX.X% (YYYY)
    rects = ax.patches
    count_flat = crosstab_count.to_numpy().flatten('F')  # Theo thứ tự stacked
    pct_flat = crosstab_pct.to_numpy().flatten('F')
    
    for rect, count, pct in zip(rects, count_flat, pct_flat):
        if pct >= 5:  # Ngưỡng hiển thị
            label = f"{pct:.1f}% ({int(count)})"
            ax.text(
                rect.get_x() + rect.get_width() / 2,
                rect.get_y() + rect.get_height() / 2,
                label,
                ha='center',
                va='center',
                fontsize=11,
                fontweight='bold',
                color='white' if pct > 40 else 'black'
            )
    
    # Legend
    ax.legend(title="Sentiment", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=12)
    
    plt.tight_layout()
    save_fig(fig, "31_sentiment_ratio_by_group.png", output_dir)

#32
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.gridspec import GridSpec

def plot_sentiment_count_from_text_columns(df: pd.DataFrame, output_dir: str):
    required_cols = ['positive_text', 'negative_text']
    if not all(col in df.columns for col in required_cols):
        print("Thiếu cột positive_text hoặc negative_text – Skip biểu đồ này.")
        return
    
    df_plot = df[required_cols].copy()
    total_rows = len(df_plot)
    
    if total_rows == 0:
        return
    
    # Kiểm tra có nội dung
    pos_has_content = df_plot['positive_text'].notna() & (df_plot['positive_text'].astype(str).str.strip() != '')
    neg_has_content = df_plot['negative_text'].notna() & (df_plot['negative_text'].astype(str).str.strip() != '')
    
    # Đếm riêng từng loại
    has_positive_count = pos_has_content.sum()
    has_negative_count = neg_has_content.sum()
    no_positive_count = (~pos_has_content).sum()   # positive_text trống
    no_negative_count = (~neg_has_content).sum()   # negative_text trống
    
    # Tính %
    has_positive_pct = round(has_positive_count / total_rows * 100, 1)
    has_negative_pct = round(has_negative_count / total_rows * 100, 1)
    no_positive_pct = round(no_positive_count / total_rows * 100, 1)
    no_negative_pct = round(no_negative_count / total_rows * 100, 1)
    
    # Data cho pie
    counts = [has_positive_count, has_negative_count, no_positive_count, no_negative_count]
    labels = [
        'Có nội dung tích cực',
        'Có nội dung tiêu cực',
        'Không có review tích cực',
        'Không có review tiêu cực'
    ]
    
    # MÀU NHẸ NHÀNG, THANH LỊCH, ĐỦ NỔI BẬT
    colors = ['#a8e6cf', '#ffcccb', '#d0e1f9', '#e6e6fa']  # Mint, Soft pink, Soft blue, Soft lavender
    
    # Figure layout
    fig = plt.figure(figsize=(18, 11))
    gs = GridSpec(1, 2, width_ratios=[1.6, 1], wspace=0.4)
    
    # Pie chart bên trái
    ax_pie = fig.add_subplot(gs[0, 0])
    wedges, texts, autotexts = ax_pie.pie(
        counts,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        textprops={'fontsize': 12, 'fontweight': 'bold'},
        wedgeprops={'linewidth': 3, 'edgecolor': 'white'}
    )
    
    # Phần trăm trên pie đẹp
    for autotext in autotexts:
        autotext.set_color('black' if autotext.get_text() == '' else 'white')
        autotext.set_fontsize(16)
        autotext.set_fontweight('bold')
    
    ax_pie.set_title("Tỷ lệ có/không nội dung theo từng loại review", fontsize=18, fontweight='bold', pad=20)
    
    # Ghi chú hoàn toàn bên phải
    ax_text = fig.add_subplot(gs[0, 1])
    ax_text.axis('off')
    
    info_text = (
        f"Tổng số bình luận: {total_rows:,}\n\n"
        f"• Có nội dung tích cực\n   (positive_text): {has_positive_count:,} ({has_positive_pct}%)\n\n"
        f"• Có nội dung tiêu cực\n   (negative_text): {has_negative_count:,} ({has_negative_pct}%)\n\n"
        f"• Không có review tích cực\n   (positive_text trống): {no_positive_count:,} ({no_positive_pct}%)\n\n"
        f"• Không có review tiêu cực\n   (negative_text trống): {no_negative_count:,} ({no_negative_pct}%)"
    )
    
    ax_text.text(0.05, 0.5, info_text, fontsize=16, verticalalignment='center', linespacing=1.8,
                 bbox=dict(boxstyle="round,pad=1.5", facecolor="white", edgecolor="#95a5a6", linewidth=2, alpha=0.95))
    
    # Tiêu đề tổng
    fig.suptitle("32. Phân tích chi tiết nội dung positive_text & negative_text\n ", 
                 fontsize=24, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    save_fig(fig, "32_sentiment_count_split_pos_neg_missing.png", output_dir)
    
def generate_all_advanced_charts(data: Dict, stats: Dict = None, output_dir: str = DEFAULT_OUTPUT):
    """
    Hàm chính tạo ĐỦ 32 BIỂU ĐỒ phân tích nâng cao
    Đã fix hết lỗi: trục 0-10, tên tỉnh dài, wordcloud, pie chart, deviation,...
    """
    df = data["df"]
    top_provinces = data.get("top_provinces", [])
    stats = stats or {}

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("\n" + "═" * 90)
    print("        ĐANG TẠO ĐỦ 32 BIỂU ĐỒ ")
    print("═" * 90)

    # 01. Phân phối điểm số
    # plot_score_distribution(df, output_dir)

    # # 02. Ma trận dữ liệu thiếu
    # plot_missing_values(df, output_dir)

    # # 03. Boxplot điểm theo tỉnh/thành
    # plot_boxplot_by_province(df, output_dir)

    # # 04. Phổ điểm Top 15 tỉnh – ĐÃ FIX trục 0-10 dù tên dài cỡ nào
    # plot_score_facet_top15(df, top_provinces, output_dir)

    # # 05. Xu hướng review theo thời gian – Top 8 tỉnh
    # plot_time_series_top8(df, top_provinces, output_dir)

    # # 06. Độ lệch điểm của reviewer so với trung bình khách sạn
    # plot_reviewer_deviation(df, output_dir)

    # # 07. Mối liên hệ độ dài bình luận vs điểm số
    # plot_text_length_vs_score(df, output_dir)

    # # 08. Top loại phòng phổ biến
    # plot_top_room_types(df, output_dir, top_n=15)

    # # 09. Phân bố theo nhóm khách (cặp đôi, gia đình, một mình,...)
    # plot_group_type_distribution(df, output_dir)

    # # 10. Tỷ lệ lọc dữ liệu (Pie chart) – RẤT QUAN TRỌNG CHO LUẬN VĂN
    # if stats:
    #     plot_processing_ratio_pie(stats, output_dir)
    # else:
    #     print("   → Bỏ qua biểu đồ 10: Không có stats để vẽ pie chart lọc dữ liệu")

    # # 11. Top quốc gia có nhiều đánh giá nhất
    # plot_country_distribution(df, output_dir)

    # # 12. Wordcloud tiếng Việt (to đẹp, chuyên nghiệp)
    # plot_vietnamese_wordcloud(df, output_dir)

    # # 13. Ma trận tương quan các biến số
    # plot_correlation_heatmap(df, output_dir)

    # # 14. Xu hướng tổng số lượng đánh giá theo thời gian 
    # plot_review_trend_over_time(df, output_dir)

    # # 15. Điểm trung bình đánh giá theo thời gian 
    # plot_average_score_over_time(df, output_dir)

    # # 16. Điểm đánh giá theo loại nhóm khách
    # plot_score_by_group_type(df, output_dir)

    # # 17. Phân phối điểm theo tỉnh/thành (Top 10) 
    # plot_violin_score_by_province(df, output_dir)

    # # 18. Wordcloud so sánh điểm cao (9-10) vs điểm thấp (≤7) –
    # plot_wordcloud_high_vs_low(df, output_dir)

    # # 19. Tỷ lệ đánh giá tiếng Việt theo tỉnh/thành (Top 15)
    # plot_vietnamese_ratio_by_province(df, output_dir)

    # # 20. Điểm trung bình theo thời gian lưu trú – Ở lâu có hài lòng hơn?
    # plot_score_by_stay_duration(df, output_dir)

    # # 21. Heatmap số lượng review theo tháng & tỉnh – Mùa vụ từng nơi rõ rệt
    # plot_review_heatmap_by_province(df, top_provinces, output_dir)

    # # 22. Scatter: Số review vs Điểm trung bình khách sạn – Nổi tiếng = chất lượng?
    # plot_hotel_popularity_vs_score(df, output_dir)

    # # 23. So sánh điểm số Khách Việt vs Quốc tế – Cultural bias thú vị
    # plot_score_vietnamese_vs_international(df, output_dir)

    # # 24. Top bigrams điểm cao vs thấp – Từ khóa thực tế khách dùng
    # plot_top_bigrams_high_low(df, output_dir)

    # # 25. Điểm đánh giá theo loại phòng – Phòng cao cấp có thật sự tốt hơn?
    # plot_score_by_room_type(df, output_dir)

    # # 26. Độ lệch điểm theo nhóm khách – Phát hiện thiên vị theo loại khách
    # plot_deviation_by_group_type(df, output_dir)

    # # 27. Phân phối điểm theo top 20 khách sạn – Chất lượng ổn định hay biến động?
    # plot_score_by_top_hotels(df, output_dir, top_n=20)
    
    # # 28. Pairplot các đặc trưng số – Correlation pairwise siêu rõ
    # plot_pairplot_numeric_features(df, output_dir)

    # # 29. Score vs Text Length theo group_type – Tương tác 3 feature
    # plot_score_vs_text_length_faceted_vertical(df, output_dir)

    # # 30. Jointplot Score vs Text Length với regression – Hay nhất để thấy mối quan hệ tuyến tính
    # plot_score_vs_text_length_stacked_bar(df, output_dir)
    
    # #31
    # plot_sentiment_ratio_by_group(df, output_dir)
    
    #32
    plot_sentiment_count_from_text_columns(df, output_dir)
    
    print("\n" + "═" * 90)
    print("        HOÀN TẤT THÀNH CÔNG!")
    print(f"        Đã tạo ĐỦ 31 biểu đồ")
    print(f"        Thư mục lưu: {Path(output_dir).resolve()}")
    # print("\n        Giờ thì in ra, nộp sếp, bảo vệ xuất sắc, crush phải đổ!")
    # print("        Chúc bạn 10 ĐIỂM LUẬN VĂN & THĂNG CHỨC NHANH!")
    print("═" * 90 + "\n")