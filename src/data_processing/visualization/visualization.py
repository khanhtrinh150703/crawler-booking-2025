# src/visualization/advanced_charts.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from wordcloud import WordCloud
from typing import Dict, List
from matplotlib.dates import DateFormatter, MonthLocator
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
from matplotlib.gridspec import GridSpec

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
def plot_time_series_top8(df: pd.DataFrame, top_provinces: List[str], output_dir: str) -> None:
    """
    Vẽ biểu đồ đường thể hiện xu hướng số lượng review theo thời gian (theo tháng)
    cho 8 tỉnh/thành có nhiều dữ liệu nhất trong top_provinces.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'month_year' (dạng YYYY-MM) và 'province'.
    top_provinces : List[str]
        Danh sách các tỉnh/thành được xếp hạng top (theo số lượng review hoặc tiêu chí khác).
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    # Kiểm tra sự tồn tại của cột month_year và dữ liệu hợp lệ
    if "month_year" not in df.columns or df["month_year"].isna().all():
        return

    # Lọc dữ liệu chỉ giữ các tỉnh thuộc top
    df_plot = df[df["province"].isin(top_provinces)].copy()

    # Chuyển đổi month_year thành datetime (đầu tháng)
    df_plot["date"] = pd.to_datetime(df_plot["month_year"], format="%Y-%m", errors="coerce")
    df_plot = df_plot.dropna(subset=["date"])

    # Nếu không còn dữ liệu hợp lệ thì bỏ qua
    if df_plot.empty:
        return

    # Tính số lượng review theo tháng và tỉnh
    trend = (
        df_plot.groupby([pd.Grouper(key="date", freq="MS"), "province"])
        .size()
        .unstack(fill_value=0)
    )

    # Tạo dãy thời gian đầy đủ để tránh khoảng trống trên đồ thị
    full_range = pd.date_range(trend.index.min(), trend.index.max(), freq="MS")
    trend = trend.reindex(full_range, fill_value=0)

    # Tạo figure với kích thước lớn để hiển thị rõ ràng
    fig, ax = plt.subplots(figsize=(18, 10))

    # Bộ 8 màu được chọn thủ công: phân biệt rõ, đẹp mắt, phù hợp in ấn và màn hình
    custom_colors = [
        "#1f77b4",  # Xanh dương đậm
        "#ff7f0e",  # Cam rực
        "#2ca02c",  # Xanh lá đậm
        "#d62728",  # Đỏ tươi
        "#9467bd",  # Tím
        "#8c564b",  # Nâu đỏ
        "#e377c2",  # Hồng tím
        "#17becf",  # Xanh ngọc
    ]

    # Áp dụng chu kỳ màu tùy chỉnh
    ax.set_prop_cycle("color", custom_colors)

    # Vẽ đường cho tối đa 8 tỉnh đầu tiên trong top
    for prov in top_provinces[:8]:
        if prov in trend.columns:
            ax.plot(
                trend.index,
                trend[prov],
                label=prov,
                linewidth=3.5,
                marker="o",
                markersize=8,
            )

    # Thiết lập tiêu đề và nhãn trục
    ax.set_title(
        "05. Xu hướng số lượng review – Top 8 địa điểm",
        fontsize=20,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Thời gian")
    ax.set_ylabel("Số review")

    # Đặt legend bên ngoài để tránh che khuất đồ thị
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=12)

    # Thêm lưới nhẹ để dễ theo dõi giá trị
    ax.grid(True, alpha=0.3)

    # Tự động điều chỉnh khoảng cách nhãn trục x để tránh chồng lấn
    ax.xaxis.set_major_locator(MonthLocator(interval=max(1, len(trend) // 18)))
    ax.xaxis.set_major_formatter(DateFormatter("%m/%Y"))

    # Xoay nhãn trục x để dễ đọc
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    # Lưu biểu đồ
    save_fig(fig, "05_time_series_top8.png", output_dir)

# 06. Độ lệch reviewer 
def plot_reviewer_deviation(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ histogram phân phối độ lệch điểm đánh giá của từng reviewer 
    so với điểm trung bình của khách sạn mà họ đánh giá.

    Độ lệch (deviation) = Score cá nhân − Điểm trung bình khách sạn.
    Giá trị dương: reviewer đánh giá cao hơn trung bình.
    Giá trị âm: reviewer đánh giá thấp hơn trung bình.
    Giá trị gần 0: reviewer đánh giá gần với mức trung bình chung.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame phải chứa cột 'deviation' đã được tính sẵn.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    # Kiểm tra sự tồn tại và tính hợp lệ của cột deviation
    if "deviation" not in df.columns or df["deviation"].isna().all():
        print("   → Bỏ qua biểu đồ 06: Không có deviation")
        return

    # Tạo figure với kích thước phù hợp
    fig, ax = plt.subplots(figsize=(13, 8))

    # Lấy dữ liệu deviation hợp lệ
    dev = df["deviation"].dropna()

    # Vẽ histogram với nhiều bins để thấy rõ phân phối
    n, bins, patches = ax.hist(
        dev,
        bins=80,
        color="#9b59b6",      # Màu tím đẹp, nổi bật
        alpha=0.85,
        edgecolor="white",
        linewidth=0.8,
    )

    # Tính và vẽ đường trung bình của độ lệch
    mean_dev = dev.mean()
    ax.axvline(
        mean_dev,
        color="red",
        linestyle="--",
        linewidth=4,
        label=f"Trung bình = {mean_dev:.3f}",
    )

    # Vẽ đường tham chiếu tại 0 (không thiên vị)
    ax.axvline(
        0,
        color="black",
        linestyle="-",
        linewidth=2,
        alpha=0.6,
        label="Không thiên vị (0)",
    )

    # Thiết lập tiêu đề và nhãn trục
    ax.set_title(
        "06. Phân phối độ lệch điểm của reviewer so với trung bình khách sạn",
        fontsize=19,
        fontweight="bold",
        pad=25,
    )
    ax.set_xlabel(
        "Độ lệch = Score cá nhân − Điểm trung bình khách sạn",
        fontsize=13,
    )
    ax.set_ylabel("Số lượng reviewer")

    # Hiển thị legend
    ax.legend(fontsize=12)

    # Thêm lưới ngang nhẹ để dễ đọc
    ax.grid(axis="y", alpha=0.3)

    # Chỉ hiển thị số lượng trên các cột có chiều cao đáng kể (>10% cột cao nhất)
    # để tránh làm rối biểu đồ
    max_count = max(n)
    for i, patch in enumerate(patches):
        if n[i] > max_count * 0.1:
            ax.text(
                patch.get_x() + patch.get_width() / 2,
                patch.get_height() + max_count * 0.02,
                format_count(int(n[i])),
                ha="center",
                va="bottom",
                fontweight="bold",
                fontsize=9,
            )

    # Lưu biểu đồ
    save_fig(fig, "06_reviewer_deviation.png", output_dir)
    
# 07. Mối liên hệ độ dài bình luận vs điểm số
def plot_text_length_vs_score(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ biểu đồ phân tán (scatter plot) thể hiện mối quan hệ giữa độ dài bình luận
    (số từ) và điểm số đánh giá, phân biệt theo ngôn ngữ (Tiếng Việt hay không).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'text_length' (số từ), 'score' (điểm số),
        và 'is_vietnamese' (boolean chỉ định ngôn ngữ).
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    # Lấy mẫu ngẫu nhiên tối đa 10,000 dòng để giảm tải tính toán và tránh biểu đồ quá dày
    sample = df.sample(min(10000, len(df)), random_state=42)

    # Tạo figure với kích thước phù hợp
    fig, ax = plt.subplots(figsize=(12, 7))

    # Vẽ scatter plot với màu phân biệt theo is_vietnamese
    sns.scatterplot(
        data=sample,
        x="text_length",
        y="score",
        hue="is_vietnamese",
        alpha=0.6,              # Độ trong suốt để thấy rõ khi điểm chồng lấn
        palette="deep",         # Bảng màu sâu, dễ nhìn
        ax=ax,
        s=50,                   # Kích thước điểm
    )

    # Thiết lập tiêu đề và nhãn trục
    ax.set_title("07. Độ dài bình luận vs Điểm số", fontsize=18, fontweight="bold")
    ax.set_xlabel("Số từ", fontsize=14)
    ax.set_ylabel("Điểm số", fontsize=14)

    # Giới hạn trục x đến phân vị 97% để loại bỏ các giá trị ngoại lai cực đại
    ax.set_xlim(0, df["text_length"].quantile(0.97))

    # Tùy chỉnh legend
    ax.legend(title="Tiếng Việt", title_fontsize=12, fontsize=10)

    # Lưu biểu đồ
    save_fig(fig, "07_text_length_vs_score.png", output_dir)
    
# 08. Top loại phòng phổ biến
def plot_top_room_types(df: pd.DataFrame, output_dir: str, top_n: int = 15) -> None:
    """
    Vẽ biểu đồ thanh ngang (horizontal bar chart) hiển thị top các loại phòng
    phổ biến nhất dựa trên số lượng đánh giá (review).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa cột 'room_type' (chuỗi mô tả loại phòng).
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    top_n : int, default 15
        Số lượng loại phòng hàng đầu muốn hiển thị.
    """
    # Đếm số lượng đánh giá theo từng loại phòng và lấy top_n
    counts = df["room_type"].value_counts().head(top_n)

    # Nếu không có dữ liệu thì bỏ qua việc vẽ
    if counts.empty:
        return

    # Tính kích thước figure động: cao hơn nếu có nhiều loại phòng
    fig, ax = plt.subplots(figsize=(12, max(6, len(counts) * 0.5)))

    # Vẽ thanh ngang với bảng màu viridis (đẹp, phân biệt tốt)
    bars = ax.barh(
        counts.index,
        counts.values,
        color=sns.color_palette("viridis", len(counts)),
    )

    # Thiết lập tiêu đề và nhãn trục
    ax.set_title(
        f"08. Top {len(counts)} loại phòng phổ biến nhất",
        fontsize=18,
        fontweight="bold",
    )
    ax.set_xlabel("Số lượng đánh giá", fontsize=14)

    # Đảo ngược trục y để loại phòng phổ biến nhất nằm trên cùng
    ax.invert_yaxis()

    # Hiển thị số lượng chính xác bên phải mỗi thanh
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax.text(
            width + width * 0.01,                  # Vị trí hơi lệch ra ngoài thanh
            bar.get_y() + bar.get_height() / 2,     # Căn giữa theo chiều dọc
            format_count(int(width)),
            va="center",
            fontweight="bold",
            fontsize=10,
        )

    # Tự động điều chỉnh layout để tránh cắt nhãn
    plt.tight_layout()

    # Lưu biểu đồ
    save_fig(fig, "08_top_room_types.png", output_dir)

# 09. Phân bố theo loại nhóm khách
def plot_group_type_distribution(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ biểu đồ cột hiển thị phân bố số lượng đánh giá theo loại nhóm khách
    (ví dụ: Cá nhân, Cặp đôi, Gia đình, Nhóm bạn, Doanh nghiệp...).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa cột 'group_type' (chuỗi mô tả loại nhóm khách).
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    # Kiểm tra sự tồn tại của cột group_type
    if "group_type" not in df.columns:
        return

    # Đếm số lượng theo từng loại nhóm khách
    counts = df["group_type"].value_counts()

    # Nếu không có dữ liệu thì bỏ qua (tránh lỗi khi counts rỗng)
    if counts.empty:
        return

    # Tạo figure với kích thước phù hợp
    fig, ax = plt.subplots(figsize=(10, 6))

    # Vẽ biểu đồ cột với bảng màu mako (xanh lá - xanh dương, đẹp và chuyên nghiệp)
    bars = ax.bar(
        counts.index,
        counts.values,
        color=sns.color_palette("mako", len(counts)),
    )

    # Thiết lập tiêu đề và nhãn trục
    ax.set_title("09. Phân bố theo loại nhóm khách", fontsize=18, fontweight="bold")
    ax.set_ylabel("Số lượng", fontsize=14)

    # Xoay nhãn trục x nếu cần (tùy thuộc vào độ dài tên nhóm)
    plt.xticks(rotation=15, ha="right")

    # Hiển thị số lượng chính xác trên đầu mỗi cột
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + height * 0.02,                  # Đặt hơi cao hơn đầu cột
            format_count(int(height)),
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=10,
        )

    # Tự động điều chỉnh layout để tránh cắt nhãn
    plt.tight_layout()

    # Lưu biểu đồ
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
def plot_country_distribution(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ biểu đồ cột hiển thị top 12 quốc gia có số lượng đánh giá (review) nhiều nhất.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa cột 'country' (tên quốc gia của reviewer hoặc khách hàng).
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    # Kiểm tra sự tồn tại của cột country
    if "country" not in df.columns:
        return

    # Lấy top 12 quốc gia có nhiều đánh giá nhất
    top = df["country"].value_counts().head(12)

    # Nếu không có dữ liệu thì bỏ qua
    if top.empty:
        return

    # Tạo figure với kích thước phù hợp
    fig, ax = plt.subplots(figsize=(12, 7))

    # Vẽ biểu đồ cột với bảng màu Set2 (phân biệt tốt, thân thiện với màu mù)
    bars = ax.bar(
        top.index,
        top.values,
        color=sns.color_palette("Set2", len(top)),
    )

    # Thiết lập tiêu đề và nhãn trục
    ax.set_title("11. Top quốc gia có nhiều đánh giá nhất", fontsize=18, fontweight="bold")
    ax.set_ylabel("Số lượng", fontsize=14)

    # Xoay nhãn trục x để tránh chồng lấn khi tên quốc gia dài
    plt.xticks(rotation=45, ha="right")

    # Hiển thị số lượng chính xác trên đầu mỗi cột
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + height * 0.02,                  # Đặt hơi cao hơn đầu cột
            format_count(int(height)),
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=10,
        )

    # Tự động điều chỉnh layout để tránh cắt nhãn
    plt.tight_layout()

    # Lưu biểu đồ
    save_fig(fig, "11_top_countries.png", output_dir)

# 12. Wordcloud tiếng Việt
def plot_vietnamese_wordcloud(df: pd.DataFrame, output_dir: str) -> None:
    """
    Tạo và lưu wordcloud từ toàn bộ bình luận tiếng Việt trong dữ liệu.
    Chỉ sử dụng các bình luận được xác định là tiếng Việt (cột is_vietnamese == True).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa ít nhất một trong các cột 'full_text' hoặc 'combined_text',
        cùng với cột 'is_vietnamese' (boolean).
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    # Xác định cột văn bản cần sử dụng (ưu tiên full_text)
    text_col = "full_text" if "full_text" in df.columns else "combined_text"

    # Kiểm tra sự tồn tại của cột văn bản cần thiết
    if text_col not in df.columns:
        return

    # Lọc chỉ bình luận tiếng Việt, loại bỏ NaN, chuyển về chuỗi và nối lại
    vietnamese_texts = (
        df[df["is_vietnamese"]][text_col]
        .dropna()
        .astype(str)
    )

    text = " ".join(vietnamese_texts)

    # Nếu không có nội dung tiếng Việt thì bỏ qua
    if not text.strip():
        return

    # Tạo WordCloud với thiết kế đẹp, chuyên nghiệp
    wc = WordCloud(
        width=1800,
        height=1000,
        background_color="white",
        max_words=300,
        colormap="viridis",              # Màu sắc hiện đại, dễ nhìn
        contour_width=3,                 # Viền nhẹ để từ nổi bật hơn
        contour_color="#1f77b4",         # Màu xanh dương đậm làm viền
        min_font_size=10,
        max_font_size=150,
        random_state=42,                 # Đảm bảo tái lập được kết quả
    ).generate(text)

    # Vẽ wordcloud
    fig, ax = plt.subplots(figsize=(18, 11))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")  # Tắt trục để chỉ hiển thị đám mây từ

    # Tiêu đề lớn, nổi bật
    ax.set_title(
        "12. WORDCLOUD ĐÁNH GIÁ TIẾNG VIỆT (Tất cả bình luận)",
        fontsize=24,
        fontweight="bold",
        pad=30,
    )

    # Lưu hình ảnh chất lượng cao
    save_fig(fig, "12_vietnamese_wordcloud_full.png", output_dir)
    
# 13. Ma trận tương quan các biến số
def plot_correlation_heatmap(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ heatmap ma trận tương quan (correlation matrix) giữa các biến số
    trong DataFrame, giúp phát hiện nhanh mối liên hệ tuyến tính giữa chúng.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa dữ liệu cần phân tích.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    # Chỉ lấy các cột có kiểu dữ liệu số
    num_cols = df.select_dtypes(include=[np.number]).columns

    # Nếu ít hơn 2 cột số thì không thể tính tương quan
    if len(num_cols) < 2:
        return

    # Tính ma trận tương quan Pearson
    corr = df[num_cols].corr()

    # Tạo figure với kích thước phù hợp
    fig, ax = plt.subplots(figsize=(11, 9))

    # Vẽ heatmap với các thiết lập đẹp và dễ đọc
    sns.heatmap(
        corr,
        annot=True,              # Hiển thị giá trị tương quan trên từng ô
        cmap="coolwarm",         # Màu đỏ (dương), xanh (âm), trắng (gần 0)
        center=0,                # Trung tâm màu tại 0
        square=True,             # Ô vuông đều
        linewidths=0.8,          # Đường viền giữa các ô
        cbar_kws={"shrink": 0.8},  # Thanh màu nhỏ gọn
        ax=ax,
        fmt=".2f",               # Hiển thị 2 chữ số thập phân
    )

    # Thiết lập tiêu đề
    ax.set_title("13. Ma trận tương quan các biến số", fontsize=18, fontweight="bold")

    # Tự động xoay nhãn trục nếu tên cột dài (tránh chồng lấn)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)

    # Tối ưu layout
    plt.tight_layout()

    # Lưu biểu đồ
    save_fig(fig, "13_correlation_heatmap.png", output_dir)

# 14. Xu hướng tổng số lượng review theo thời gian (toàn bộ dữ liệu)
def plot_review_trend_over_time(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ biểu đồ đường thể hiện xu hướng tổng số lượng đánh giá theo thời gian (theo tháng),
    kèm vùng tô mờ và chú thích tự động cho tháng có số lượng đánh giá cao nhất (đỉnh).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa cột 'month_year' định dạng YYYY-MM.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    # Kiểm tra sự tồn tại của cột month_year
    if "month_year" not in df.columns:
        return

    # Sao chép dữ liệu và chuyển đổi sang datetime (đầu tháng)
    df_plot = df.copy()
    df_plot["date"] = pd.to_datetime(df_plot["month_year"], format="%Y-%m", errors="coerce")
    df_plot = df_plot.dropna(subset=["date"])

    # Nếu không còn dữ liệu hợp lệ thì bỏ qua
    if df_plot.empty:
        return

    # Tính số lượng đánh giá theo tháng
    trend = df_plot.groupby(pd.Grouper(key="date", freq="MS")).size()

    # Tạo dãy thời gian đầy đủ để tránh khoảng trống trên đồ thị
    full_range = pd.date_range(trend.index.min(), trend.index.max(), freq="MS")
    trend = trend.reindex(full_range, fill_value=0)

    # Tạo figure với kích thước lớn để hiển thị rõ xu hướng dài hạn
    fig, ax = plt.subplots(figsize=(16, 8))

    # Vẽ đường chính với marker và vùng tô mờ bên dưới
    ax.plot(
        trend.index,
        trend.values,
        linewidth=4,
        color="#2ecc71",       # Màu xanh lá tươi nổi bật
        marker="o",
        markersize=6,
    )
    ax.fill_between(trend.index, trend.values, alpha=0.3, color="#2ecc71")

    # Thiết lập tiêu đề và nhãn trục
    ax.set_title(
        "14. Xu hướng tổng số lượng đánh giá theo thời gian",
        fontsize=20,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Thời gian", fontsize=14)
    ax.set_ylabel("Số lượng đánh giá", fontsize=14)

    # Thêm lưới nhẹ để dễ theo dõi giá trị
    ax.grid(True, alpha=0.3)

    # Tự động điều chỉnh khoảng cách nhãn trục x để tránh chồng lấn
    ax.xaxis.set_major_locator(MonthLocator(interval=max(1, len(trend) // 15)))
    ax.xaxis.set_major_formatter(DateFormatter("%m/%Y"))

    # Xoay nhãn ngày tháng cho dễ đọc
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    # Chú thích tự động cho tháng đạt đỉnh cao nhất
    peak_idx = trend.idxmax()
    peak_val = trend.max()
    ax.annotate(
        f'Đỉnh: {format_count(peak_val)}\n{peak_idx.strftime("%m/%Y")}',
        xy=(peak_idx, peak_val),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=12,
        fontweight="bold",
        color="#e74c3c",       # Màu đỏ nổi bật
        arrowprops=dict(arrowstyle="->", color="#e74c3c", lw=2),
    )

    # Lưu biểu đồ
    save_fig(fig, "14_review_trend_over_time.png", output_dir)
    
# 15. Điểm trung bình theo thời gian (rolling 3 tháng)
def plot_average_score_over_time(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ biểu đồ đường thể hiện xu hướng điểm trung bình đánh giá theo thời gian (theo tháng),
    kết hợp đường trung bình tháng gốc (nhạt) và đường trung bình trượt 3 tháng (nổi bật)
    để làm mượt và dễ nhận diện xu hướng dài hạn.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'month_year' (định dạng YYYY-MM) và 'score' (điểm số).
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    # Kiểm tra sự tồn tại của các cột cần thiết
    if "month_year" not in df.columns or "score" not in df.columns:
        return

    # Sao chép dữ liệu và chuẩn bị
    df_plot = df.copy()
    df_plot["date"] = pd.to_datetime(df_plot["month_year"], format="%Y-%m", errors="coerce")
    df_plot = df_plot.dropna(subset=["date", "score"])

    # Chuyển score sang numeric để tính toán chính xác
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")

    # Nếu không còn dữ liệu hợp lệ thì bỏ qua
    if df_plot.empty:
        return

    # Tính điểm trung bình theo tháng
    monthly = df_plot.groupby(pd.Grouper(key="date", freq="MS"))["score"].mean()

    # Tạo dãy thời gian đầy đủ để tránh lỗ hổng trên đồ thị
    full_range = pd.date_range(monthly.index.min(), monthly.index.max(), freq="MS")
    monthly = monthly.reindex(full_range)

    # Tính trung bình trượt 3 tháng (căn giữa) để làm mượt xu hướng
    rolling = monthly.rolling(window=3, center=True).mean()

    # Tạo figure với kích thước lớn để hiển thị rõ xu hướng dài hạn
    fig, ax = plt.subplots(figsize=(16, 8))

    # Vẽ đường trung bình tháng gốc (mờ hơn để làm nền)
    ax.plot(
        monthly.index,
        monthly.values,
        alpha=0.4,
        color="#3498db",
        label="Trung bình tháng",
    )

    # Vẽ đường trung bình trượt 3 tháng (nổi bật, dày hơn)
    ax.plot(
        rolling.index,
        rolling.values,
        linewidth=4,
        color="#e74c3c",
        label="Trung bình trượt 3 tháng",
    )

    # Thiết lập tiêu đề và nhãn trục
    ax.set_title(
        "15. Điểm trung bình đánh giá theo thời gian",
        fontsize=20,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Thời gian", fontsize=14)
    ax.set_ylabel("Điểm trung bình", fontsize=14)

    # Giới hạn trục y hợp lý cho thang điểm đánh giá khách sạn (thường 7.5–9.5)
    ax.set_ylim(7.5, 9.5)

    # Hiển thị legend
    ax.legend(fontsize=12)

    # Thêm lưới nhẹ để dễ đọc giá trị
    ax.grid(True, alpha=0.3)

    # Tự động điều chỉnh khoảng cách nhãn trục x để tránh chồng lấn
    ax.xaxis.set_major_locator(MonthLocator(interval=max(1, len(monthly) // 15)))
    ax.xaxis.set_major_formatter(DateFormatter("%m/%Y"))

    # Xoay nhãn ngày tháng cho dễ đọc
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    # Lưu biểu đồ
    save_fig(fig, "15_average_score_over_time.png", output_dir)

# 16. Điểm trung bình theo nhóm khách
def plot_score_by_group_type(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ boxplot ngang hiển thị phân phối điểm đánh giá theo từng loại nhóm khách,
    sắp xếp theo median điểm giảm dần.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'group_type' và 'score'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    if "group_type" not in df.columns or "score" not in df.columns:
        return

    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")

    # Sắp xếp nhóm khách theo median điểm giảm dần
    order = (
        df_plot.groupby("group_type")["score"]
        .median()
        .sort_values(ascending=False)
        .index
    )

    fig, ax = plt.subplots(figsize=(12, 7))

    sns.boxplot(
        data=df_plot,
        x="score",
        y="group_type",
        order=order,
        palette="Set3",
        hue="group_type",
        dodge=False,
        legend=False,
        ax=ax,
    )

    ax.set_title("16. Điểm đánh giá theo loại nhóm khách", fontsize=20, fontweight="bold")
    ax.set_xlabel("Điểm số", fontsize=14)
    ax.set_ylabel("Nhóm khách", fontsize=14)

    save_fig(fig, "16_score_by_group_type.png", output_dir)


# 17. Violin plot điểm theo tỉnh (top 10 - đẹp hơn boxplot)
def plot_violin_score_by_province(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ violin plot ngang hiển thị phân phối điểm đánh giá cho top 10 tỉnh/thành
    có nhiều đánh giá nhất, sắp xếp theo median điểm giảm dần.
    Violin plot thể hiện mật độ phân phối tốt hơn boxplot thông thường.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'province' và 'score'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    df_plot = df[df["province"] != "Khác"]

    # Lấy top 10 tỉnh/thành có số lượng đánh giá nhiều nhất
    top_provinces = df_plot["province"].value_counts().head(10).index
    df_plot = df_plot[df_plot["province"].isin(top_provinces)]

    if df_plot.empty:
        return

    # Sắp xếp theo median điểm giảm dần
    order = (
        df_plot.groupby("province")["score"]
        .median()
        .sort_values(ascending=False)
        .index
    )

    fig, ax = plt.subplots(figsize=(12, 9))

    sns.violinplot(
        data=df_plot,
        x="score",
        y="province",
        order=order,
        palette="coolwarm",
        hue="province",
        dodge=False,
        legend=False,
        ax=ax,
        inner="quartile",  # Hiển thị quartiles bên trong violin
    )

    ax.set_title(
        "17. Phân phối điểm theo tỉnh/thành (Top 10) - Violin Plot",
        fontsize=20,
        fontweight="bold",
    )
    ax.set_xlabel("Điểm số", fontsize=14)
    ax.set_ylabel("")  # Để trục y sạch sẽ, nhãn tỉnh đã hiển thị trực tiếp

    save_fig(fig, "17_violin_score_by_province.png", output_dir)


# 18. Wordcloud: Điểm cao (9-10) vs Điểm thấp (≤7)
def plot_wordcloud_high_vs_low(df: pd.DataFrame, output_dir: str) -> None:
    """
    Tạo wordcloud so sánh từ khóa phổ biến trong bình luận tiếng Việt
    giữa nhóm điểm cao (9-10) và nhóm điểm thấp (≤7).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'full_text', 'score', và 'is_vietnamese'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    text_col = "full_text"

    if (
        text_col not in df.columns
        or "score" not in df.columns
        or "is_vietnamese" not in df.columns
    ):
        return

    # Chỉ lấy bình luận tiếng Việt
    df_vn = df[df["is_vietnamese"]].copy()
    df_vn["score"] = pd.to_numeric(df_vn["score"], errors="coerce")

    # Chia nhóm điểm cao và điểm thấp
    high = df_vn[df_vn["score"] >= 9]
    low = df_vn[df_vn["score"] <= 7]

    if high.empty or low.empty:
        return

    # Ghép toàn bộ văn bản của từng nhóm
    text_high = " ".join(high[text_col].dropna().astype(str))
    text_low = " ".join(low[text_col].dropna().astype(str))

    # Tạo wordcloud cho điểm cao (màu xanh) và điểm thấp (màu đỏ)
    wc_high = WordCloud(
        width=900,
        height=600,
        background_color="white",
        colormap="Greens",
        max_words=150,
        random_state=42,
    ).generate(text_high)

    wc_low = WordCloud(
        width=900,
        height=600,
        background_color="white",
        colormap="Reds",
        max_words=150,
        random_state=42,
    ).generate(text_low)

    # Vẽ hai wordcloud cạnh nhau
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))

    axes[0].imshow(wc_high, interpolation="bilinear")
    axes[0].set_title(
        "18. Từ khóa phổ biến - Điểm cao (9-10)",
        fontsize=20,
        fontweight="bold",
        color="#27ae60",
    )
    axes[0].axis("off")

    axes[1].imshow(wc_low, interpolation="bilinear")
    axes[1].set_title(
        "18. Từ khóa phổ biến - Điểm thấp (≤7)",
        fontsize=20,
        fontweight="bold",
        color="#e74c3c",
    )
    axes[1].axis("off")

    plt.tight_layout()
    save_fig(fig, "18_wordcloud_high_vs_low_score.png", output_dir)
    
    
# 19. Tỷ lệ đánh giá tiếng Việt theo tỉnh (top 15)
def plot_vietnamese_ratio_by_province(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ biểu đồ thanh ngang hiển thị tỷ lệ đánh giá bằng tiếng Việt (%)
    theo từng tỉnh/thành phố (top 15 cao nhất), loại bỏ tỉnh "Khác".

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'province' và 'is_vietnamese' (boolean).
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    if "province" not in df.columns or "is_vietnamese" not in df.columns:
        return

    # Loại bỏ tỉnh "Khác" và tính tỷ lệ trung bình is_vietnamese (True = 1.0)
    df_plot = df[df["province"] != "Khác"]
    ratio = df_plot.groupby("province")["is_vietnamese"].mean().sort_values(ascending=False)

    # Lấy top 15 tỉnh có tỷ lệ tiếng Việt cao nhất
    top = ratio.head(15)

    if top.empty:
        return

    fig, ax = plt.subplots(figsize=(12, 8))

    # Vẽ thanh ngang với bảng màu xanh dương giảm dần
    bars = ax.barh(
        top.index,
        top.values * 100,
        color=sns.color_palette("Blues_r", len(top)),
    )

    ax.set_title("19. Tỷ lệ đánh giá tiếng Việt theo tỉnh/thành (Top 15)", fontsize=20, fontweight="bold")
    ax.set_xlabel("Tỷ lệ (%)", fontsize=14)
    ax.invert_yaxis()  # Tỉnh cao nhất nằm trên cùng

    # Hiển thị giá trị phần trăm chính xác bên phải mỗi thanh
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 1,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.1f}%",
            va="center",
            fontweight="bold",
            fontsize=11,
        )

    plt.tight_layout()
    save_fig(fig, "19_vietnamese_ratio_by_province.png", output_dir)


# 20. Điểm trung bình theo thời gian lưu trú (stay_duration)
def plot_score_by_stay_duration(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ boxplot hiển thị phân phối điểm đánh giá theo nhóm thời gian lưu trú
    (1 đêm, 2-3 đêm, 4-7 đêm, 8+ đêm) sau khi trích xuất số đêm từ chuỗi văn bản.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'stay_duration' (chuỗi kiểu "X đêm") và 'score'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    if "stay_duration" not in df.columns or "score" not in df.columns:
        return

    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")

    # Trích xuất số đêm từ chuỗi (ví dụ: "3 đêm" → 3)
    df_plot["stay_duration_num"] = df_plot["stay_duration"].str.extract(r"(\d+)").astype(float)

    # Loại bỏ các hàng không hợp lệ
    df_plot = df_plot.dropna(subset=["stay_duration_num", "score"])

    if df_plot.empty:
        print("   → Bỏ qua biểu đồ 20: Không có dữ liệu stay_duration hợp lệ sau khi extract")
        return

    # Phân nhóm thời gian lưu trú
    bins = [0, 1, 3, 7, np.inf]
    labels = ["1 đêm", "2-3 đêm", "4-7 đêm", "8+ đêm"]
    df_plot["duration_group"] = pd.cut(
        df_plot["stay_duration_num"],
        bins=bins,
        labels=labels,
        include_lowest=True,
    )

    # Thứ tự hiển thị cố định
    order = ["1 đêm", "2-3 đêm", "4-7 đêm", "8+ đêm"]

    fig, ax = plt.subplots(figsize=(12, 7))

    sns.boxplot(
        data=df_plot,
        x="duration_group",
        y="score",
        order=order,
        palette="Oranges_r",
        hue="duration_group",
        dodge=False,
        legend=False,
        ax=ax,
    )

    ax.set_title("20. Điểm đánh giá theo thời gian lưu trú", fontsize=20, fontweight="bold", pad=20)
    ax.set_xlabel("Thời gian lưu trú", fontsize=14)
    ax.set_ylabel("Điểm số", fontsize=14)

    # Hiển thị số lượng mẫu (n=...) trên đầu mỗi box
    counts = df_plot["duration_group"].value_counts().reindex(order)
    for i, count in enumerate(counts):
        ax.text(
            i,
            df_plot["score"].max() + 0.1,
            f"n={format_count(count)}",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=11,
        )

    save_fig(fig, "20_score_by_stay_duration.png", output_dir)


# 21. Heatmap số lượng review theo tháng & tỉnh (top 8 tỉnh)
def plot_review_heatmap_by_province(df: pd.DataFrame, top_provinces: List[str], output_dir: str) -> None:
    """
    Vẽ heatmap thể hiện số lượng review theo từng tháng trong năm
    cho top 8 tỉnh/thành có nhiều dữ liệu nhất.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'month_year' và 'province'.
    top_provinces : List[str]
        Danh sách tỉnh/thành được xếp hạng top.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    if "month_year" not in df.columns or df.empty:
        return

    # Lọc top 8 tỉnh và chuẩn bị dữ liệu thời gian
    df_plot = df[df["province"].isin(top_provinces[:8])].copy()
    df_plot["date"] = pd.to_datetime(df_plot["month_year"], format="%Y-%m", errors="coerce")
    df_plot = df_plot.dropna(subset=["date"])

    if df_plot.empty:
        return

    # Tạo pivot table: hàng = tỉnh, cột = tháng (1-12), giá trị = số lượng review
    pivot = df_plot.pivot_table(
        values="score",  # bất kỳ cột nào cũng được vì chỉ dùng count
        index="province",
        columns=df_plot["date"].dt.month,
        aggfunc="count",
        fill_value=0,
    )

    # Đảm bảo cột theo thứ tự tháng 1 → 12
    pivot = pivot.reindex(columns=range(1, 13), fill_value=0)

    fig, ax = plt.subplots(figsize=(14, 8))

    sns.heatmap(
        pivot,
        annot=True,
        fmt="d",
        cmap="YlOrRd",
        linewidths=0.5,
        ax=ax,
        cbar_kws={"label": "Số lượng review"},
    )

    ax.set_title("21. Heatmap số lượng review theo tháng – Top 8 tỉnh", fontsize=20, fontweight="bold", pad=20)
    ax.set_xlabel("Tháng", fontsize=14)
    ax.set_ylabel("Tỉnh/thành", fontsize=14)

    save_fig(fig, "21_review_heatmap_by_province.png", output_dir)
    
# 22. Số lượng review vs Điểm trung bình của khách sạn
def plot_hotel_popularity_vs_score(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ scatter plot thể hiện mối quan hệ giữa độ phổ biến của khách sạn
    (số lượng review) và điểm trung bình đánh giá, sử dụng log scale cho trục x
    để xử lý phân bố lệch mạnh.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'hotel_name' và 'score'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    if "hotel_name" not in df.columns or "score" not in df.columns:
        return

    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")

    # Tính số lượng review và điểm trung bình theo từng khách sạn
    hotel_stats = (
        df_plot.groupby("hotel_name")
        .agg(
            review_count=("score", "count"),
            avg_score=("score", "mean"),
        )
        .reset_index()
    )

    # Lọc bỏ khách sạn có quá ít review để tránh nhiễu
    hotel_stats = hotel_stats[hotel_stats["review_count"] >= 5]

    if hotel_stats.empty:
        return

    fig, ax = plt.subplots(figsize=(14, 9))

    # Scatter plot với kích thước và màu điểm thể hiện số lượng review
    sns.scatterplot(
        data=hotel_stats,
        x="review_count",
        y="avg_score",
        alpha=0.6,
        size="review_count",
        sizes=(20, 200),
        hue="review_count",
        palette="Blues_d",
        legend=False,
        ax=ax,
    )

    ax.set_title(
        "22. Số lượng review vs Điểm trung bình của khách sạn",
        fontsize=20,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Số lượng review (log scale)", fontsize=14)
    ax.set_ylabel("Điểm trung bình", fontsize=14)

    # Sử dụng thang log để hiển thị tốt các khách sạn từ ít đến rất nhiều review
    ax.set_xscale("log")

    save_fig(fig, "22_hotel_popularity_vs_score.png", output_dir)


# 23. So sánh điểm số: Khách Việt vs Khách quốc tế (top 10 tỉnh)
def plot_score_vietnamese_vs_international(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ biểu đồ thanh ngang so sánh điểm trung bình giữa khách Việt Nam
    và khách quốc tế tại top 10 tỉnh/thành có nhiều đánh giá nhất.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'is_vietnamese', 'province', và 'score'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    if "is_vietnamese" not in df.columns or "province" not in df.columns or "score" not in df.columns:
        return

    df_plot = df[df["province"] != "Khác"].copy()

    # Lấy top 10 tỉnh có nhiều đánh giá nhất
    top_provinces = df_plot["province"].value_counts().head(10).index
    df_plot = df_plot[df_plot["province"].isin(top_provinces)]

    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")

    if df_plot.empty:
        return

    # Tính điểm trung bình theo tỉnh và nhóm khách
    summary = (
        df_plot.groupby(["province", "is_vietnamese"])["score"]
        .mean()
        .unstack()
        .rename(columns={False: "Khách quốc tế", True: "Khách Việt Nam"})
    )

    fig, ax = plt.subplots(figsize=(12, 8))

    # Vẽ thanh ngang song song
    summary.plot(kind="barh", ax=ax, color=["#3498db", "#e74c3c"])

    ax.set_title(
        "23. Điểm trung bình: Khách Việt vs Quốc tế – Top 10 tỉnh ",
        fontsize=20,
        fontweight="bold",
    )
    ax.set_xlabel("Điểm trung bình", fontsize=14)
    ax.invert_yaxis()  # Tỉnh nhiều review nhất nằm trên cùng

    plt.tight_layout()
    save_fig(fig, "23_score_vn_vs_international.png", output_dir)


# 24. Top bigrams (cụm 2 từ) theo điểm cao/thấp
def plot_top_bigrams_high_low(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ hai biểu đồ thanh ngang song song hiển thị top 20 bigrams (cụm 2 từ)
    phổ biến nhất trong bình luận tiếng Việt của nhóm điểm cao (≥8) và điểm thấp (≤7).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'full_text', 'score', và 'is_vietnamese'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    if (
        "full_text" not in df.columns
        or "score" not in df.columns
        or "is_vietnamese" not in df.columns
    ):
        return

    df_vn = df[df["is_vietnamese"]].copy()
    df_vn["score"] = pd.to_numeric(df_vn["score"], errors="coerce")

    # Chia nhóm điểm cao và điểm thấp
    high = df_vn[df_vn["score"] >= 8]["full_text"].dropna()
    low = df_vn[df_vn["score"] <= 7]["full_text"].dropna()

    if high.empty or low.empty:
        return

    # Vectorizer để trích xuất bigrams (không dùng stop_words tiếng Việt để giữ nguyên ngữ cảnh thực)
    vec = CountVectorizer(ngram_range=(2, 2), max_features=20)

    # Fit và tính tần suất riêng cho từng nhóm
    high_bigrams = vec.fit_transform(high.astype(str))
    high_counts = dict(zip(vec.get_feature_names_out(), high_bigrams.sum(axis=0).A1))

    low_bigrams = vec.fit_transform(low.astype(str))
    low_counts = dict(zip(vec.get_feature_names_out(), low_bigrams.sum(axis=0).A1))

    fig, axes = plt.subplots(1, 2, figsize=(20, 10))

    # Bigrams điểm cao (xanh lá)
    pd.Series(high_counts).sort_values().plot(
        kind="barh", ax=axes[0], color="#27ae60"
    )
    axes[0].set_title("24. Top bigrams – Điểm cao (8-10)", fontsize=18, fontweight="bold")
    axes[0].set_xlabel("Tần suất")

    # Bigrams điểm thấp (đỏ)
    pd.Series(low_counts).sort_values().plot(
        kind="barh", ax=axes[1], color="#e74c3c"
    )
    axes[1].set_title("24. Top bigrams – Điểm thấp (≤7)", fontsize=18, fontweight="bold")
    axes[1].set_xlabel("Tần suất")

    plt.tight_layout()
    save_fig(fig, "24_top_bigrams_high_vs_low.png", output_dir)

# 25. Điểm trung bình theo loại phòng (Top 15 phổ biến nhất)
def plot_score_by_room_type(df: pd.DataFrame, output_dir: str, top_n: int = 15) -> None:
    """
    Vẽ biểu đồ thanh ngang hiển thị điểm trung bình đánh giá theo từng loại phòng
    phổ biến nhất (top_n), sắp xếp từ cao xuống thấp.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'room_type' và 'score'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    top_n : int, default 15
        Số lượng loại phòng phổ biến nhất muốn hiển thị.
    """
    if "room_type" not in df.columns or "score" not in df.columns:
        return

    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    df_plot = df_plot.dropna(subset=["score"])

    # Lấy top_n loại phòng có nhiều review nhất
    top_rooms = df_plot["room_type"].value_counts().head(top_n).index
    df_plot = df_plot[df_plot["room_type"].isin(top_rooms)]

    if df_plot.empty:
        return

    # Tính điểm trung bình và sắp xếp giảm dần
    mean_scores = df_plot.groupby("room_type")["score"].mean().sort_values(ascending=False)

    # Tính chiều cao figure động dựa trên số lượng loại phòng
    fig_height = max(8, len(mean_scores) * 0.55)
    fig, ax = plt.subplots(figsize=(16, fig_height))

    # Bảng màu Spectral_r đẹp: đỏ (cao) → vàng → xanh (thấp), phân biệt rõ ràng
    colors = sns.color_palette("Spectral_r", len(mean_scores))

    # Vẽ thanh ngang
    bars = ax.barh(mean_scores.index, mean_scores.values, color=colors, height=0.8)

    # Hiển thị giá trị điểm trung bình bên phải thanh
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.05,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.2f}",
            va="center",
            ha="left",
            fontweight="bold",
            fontsize=12,
        )

    ax.set_title(
        f"25. Điểm đánh giá trung bình theo loại phòng (Top {top_n} phổ biến nhất)",
        fontsize=22,
        fontweight="bold",
        pad=25,
    )
    ax.set_xlabel("Điểm trung bình", fontsize=15)
    ax.set_ylabel("Loại phòng", fontsize=15)
    ax.grid(axis="x", alpha=0.3)
    ax.invert_yaxis()  # Loại phòng điểm cao nhất nằm trên cùng

    plt.tight_layout()
    save_fig(fig, "25_score_by_room_type_bar_clean.png", output_dir)


# 26. Độ lệch điểm (deviation) theo nhóm khách
def plot_deviation_by_group_type(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ boxplot ngang hiển thị phân phối độ lệch điểm đánh giá theo từng nhóm khách,
    sắp xếp theo median độ lệch giảm dần, kèm đường tham chiếu tại 0 (không thiên vị).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'deviation' và 'group_type'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    if "deviation" not in df.columns or "group_type" not in df.columns:
        return

    df_plot = df.copy()
    df_plot["deviation"] = pd.to_numeric(df_plot["deviation"], errors="coerce")
    df_plot = df_plot.dropna(subset=["deviation"])

    if df_plot.empty:
        return

    # Sắp xếp theo median độ lệch giảm dần
    order = (
        df_plot.groupby("group_type")["deviation"]
        .median()
        .sort_values(ascending=False)
        .index
    )

    fig, ax = plt.subplots(figsize=(12, 7))

    sns.boxplot(
        data=df_plot,
        x="deviation",
        y="group_type",
        order=order,
        palette="Set3",
        hue="group_type",
        dodge=False,
        legend=False,
        ax=ax,
    )

    # Đường tham chiếu tại 0: không thiên vị
    ax.axvline(0, color="black", linestyle="--", linewidth=2, label="Không thiên vị")

    ax.set_title(
        "26. Độ lệch điểm đánh giá theo nhóm khách – Nhóm nào thiên vị nhất?",
        fontsize=20,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Độ lệch (Score cá nhân − Trung bình khách sạn)", fontsize=14)
    ax.set_ylabel("Nhóm khách", fontsize=14)
    ax.legend(fontsize=12)

    plt.tight_layout()
    save_fig(fig, "26_deviation_by_group_type.png", output_dir)


# 27. Phân phối điểm theo khách sạn (Top 20 hotel nhiều review nhất)
def plot_score_by_top_hotels(df: pd.DataFrame, output_dir: str, top_n: int = 20) -> None:
    """
    Vẽ violin plot ngang hiển thị phân phối điểm số cho top_n khách sạn
    có nhiều review nhất, sắp xếp theo median điểm giảm dần.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'hotel_name' và 'score'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    top_n : int, default 20
        Số lượng khách sạn nhiều review nhất muốn hiển thị.
    """
    if "hotel_name" not in df.columns or "score" not in df.columns:
        return

    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    df_plot = df_plot.dropna(subset=["score"])

    # Lấy top_n khách sạn có nhiều review nhất
    top_hotels = df_plot["hotel_name"].value_counts().head(top_n).index
    df_plot = df_plot[df_plot["hotel_name"].isin(top_hotels)]

    if df_plot.empty:
        return

    # Sắp xếp theo median điểm giảm dần
    order = (
        df_plot.groupby("hotel_name")["score"]
        .median()
        .sort_values(ascending=False)
        .index
    )

    # Tính chiều cao figure động
    fig_height = max(10, len(top_hotels) * 0.65)
    fig, ax = plt.subplots(figsize=(15, fig_height))

    sns.violinplot(
        data=df_plot,
        x="score",
        y="hotel_name",
        order=order,
        palette="coolwarm",
        hue="hotel_name",
        dodge=False,
        legend=False,
        ax=ax,
        inner="quartile",  # Hiển thị quartiles bên trong violin
    )

    ax.set_title(
        f"27. Phân phối điểm theo khách sạn (Top {top_n} nhiều review nhất)",
        fontsize=20,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Điểm số", fontsize=14)
    ax.set_ylabel("Tên khách sạn", fontsize=14)
    ax.tick_params(axis="y", labelsize=10)

    plt.tight_layout(pad=3.0)
    save_fig(fig, "27_score_by_top_hotels.png", output_dir)

# 28. Pairplot các đặc trưng số
def plot_pairplot_numeric_features(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ pairplot cho các đặc trưng số chính để khám phá mối quan hệ pairwise
    và phân bố của từng biến (score, text_length, deviation, hotel_avg_score,
    và stay_duration_num nếu có).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột đặc trưng số.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    cols = ["score", "text_length", "deviation", "hotel_avg_score"]
    if "stay_duration_num" in df.columns:
        cols.append("stay_duration_num")

    df_plot = df[cols].dropna()

    # Nếu dữ liệu quá ít thì bỏ qua
    if len(df_plot) < 100:
        return

    # Lấy mẫu để pairplot không quá chậm và rối
    df_sample = df_plot.sample(min(5000, len(df_plot)), random_state=42)

    g = sns.pairplot(
        df_sample,
        diag_kind="kde",          # Phân bố dạng KDE trên đường chéo
        plot_kws={"alpha": 0.5, "s": 20},
        diag_kws={"fill": True},
        corner=True,              # Chỉ hiển thị nửa dưới để tránh lặp
    )

    g.figure.suptitle(
        "28. Pairplot các đặc trưng số – Mối quan hệ pairwise & phân bố",
        fontsize=22,
        fontweight="bold",
        y=1.02,
    )

    g.tight_layout()
    save_fig(g.figure, "28_pairplot_numeric_features.png", output_dir)


# 29. Score vs Độ dài bình luận – Hexbin Density theo nhóm khách (dọc)
def plot_score_vs_text_length_faceted_vertical(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ các hexbin plot dọc theo từng nhóm khách hiển thị mật độ mối quan hệ
    giữa độ dài bình luận và điểm số, kèm colorbar chung thể hiện số lượng.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'text_length', 'score', và 'group_type'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    required_cols = ["text_length", "score", "group_type"]
    if not all(col in df.columns for col in required_cols):
        return

    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    df_plot = df_plot.dropna(subset=["score", "text_length", "group_type"])

    if df_plot.empty:
        return

    # Đảm bảo thứ tự nhóm khách ổn định
    df_plot["group_type"] = df_plot["group_type"].astype("category")
    unique_groups = df_plot["group_type"].cat.categories.tolist()
    df_plot["group_type"] = df_plot["group_type"].cat.reorder_categories(sorted(unique_groups))

    n_groups = len(unique_groups)

    # Tạo figure với layout tùy chỉnh
    fig = plt.figure(figsize=(14, 4 * n_groups))
    gs = GridSpec(n_groups, 2, width_ratios=[50, 1], wspace=0.05, hspace=0.3)

    # Giới hạn trục x chung (loại bỏ outlier cực đại)
    xlim_max = df_plot["text_length"].quantile(0.98)

    hex_obj = None  # Để tạo colorbar chung

    for i, group in enumerate(unique_groups):
        sub = df_plot[df_plot["group_type"] == group]

        ax = fig.add_subplot(gs[i, 0])

        # Hexbin density plot
        hexbin = ax.hexbin(
            sub["text_length"],
            sub["score"],
            gridsize=60,
            cmap="YlOrRd",
            mincnt=1,
            linewidths=0.2,
        )

        ax.set_xlim(0, xlim_max)
        ax.set_ylim(df_plot["score"].min() - 0.5, df_plot["score"].max() + 0.5)
        ax.set_title(group, fontsize=16, fontweight="bold", pad=15)

        if i == n_groups - 1:
            ax.set_xlabel("Độ dài bình luận (số từ)", fontsize=14)
        else:
            ax.set_xlabel("")

        ax.set_ylabel("Điểm số", fontsize=14)
        ax.grid(alpha=0.3)

        if i == 0:
            hex_obj = hexbin

    # Colorbar chung bên phải
    if hex_obj is not None:
        cax = fig.add_subplot(gs[:, 1])
        cb = plt.colorbar(hex_obj, cax=cax)
        cb.set_label("Số lượng bình luận", fontsize=14, rotation=270, labelpad=20)
        cb.ax.tick_params(labelsize=12)

    fig.suptitle("29. Score vs Độ dài bình luận – Hexbin Density", fontsize=22, fontweight="bold", y=0.98)

    plt.subplots_adjust(top=0.9)
    save_fig(fig, "29_score_vs_text_length_vertical_hexbin.png", output_dir)


# 30. Tỷ lệ và số lượng nhóm khách theo độ dài bình luận (100% stacked bar)
def plot_score_vs_text_length_stacked_bar(df: pd.DataFrame, output_dir: str, bins: int = 10) -> None:
    """
    Vẽ biểu đồ thanh ngang 100% stacked hiển thị tỷ lệ nhóm khách theo khoảng độ dài bình luận,
    kèm label kép phần trăm (số lượng tuyệt đối) cho các segment lớn.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'text_length', 'score', và 'group_type'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    bins : int, default 10
        Số lượng khoảng (bins) để chia độ dài bình luận (sử dụng quantile).
    """
    required_cols = ["text_length", "score", "group_type"]
    if not all(col in df.columns for col in required_cols):
        return

    df_plot = df.copy()
    df_plot["score"] = pd.to_numeric(df_plot["score"], errors="coerce")
    df_plot = df_plot.dropna(subset=["score", "text_length", "group_type"])

    if df_plot.empty:
        return

    # Chia độ dài bình luận thành bins bằng quantile để mỗi bin có số lượng gần đều
    df_plot["length_bin"] = pd.qcut(df_plot["text_length"], q=bins, duplicates="drop")

    # Crosstab số lượng tuyệt đối
    crosstab_count = pd.crosstab(df_plot["length_bin"], df_plot["group_type"])

    # Sắp xếp bin từ dài nhất xuống ngắn nhất
    crosstab_count = crosstab_count.sort_index(ascending=False)

    # Tính tỷ lệ phần trăm
    crosstab_pct = crosstab_count.div(crosstab_count.sum(axis=1), axis=0) * 100

    unique_groups = crosstab_count.columns

    # Bảng màu đẹp và phân biệt rõ
    custom_colors = ["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3"]
    colors = custom_colors[:len(unique_groups)]
    if len(unique_groups) > len(custom_colors):
        colors += sns.color_palette("husl", len(unique_groups) - len(custom_colors))

    # Kích thước figure động
    fig, ax = plt.subplots(figsize=(18, max(9, len(crosstab_count) * 0.9)))

    # Vẽ 100% stacked bar ngang
    crosstab_pct.plot(kind="barh", stacked=True, color=colors, ax=ax, width=0.8)

    ax.set_title("30. Tỷ lệ và số lượng nhóm khách theo độ dài bình luận", fontsize=22, fontweight="bold", pad=30)
    ax.set_xlabel("Tỷ lệ phần trăm (%)", fontsize=15)
    ax.set_ylabel("Khoảng độ dài bình luận (số từ)", fontsize=15)
    ax.grid(axis="x", alpha=0.3)

    # Label kép XX.X% (YYYY) cho segment >= 5%
    rects = ax.patches
    count_flat = crosstab_count.to_numpy().flatten("F")
    pct_flat = crosstab_pct.to_numpy().flatten("F")

    for rect, count, pct in zip(rects, count_flat, pct_flat):
        if pct >= 5:
            label = f"{pct:.1f}% ({int(count)})"
            ax.text(
                rect.get_x() + rect.get_width() / 2,
                rect.get_y() + rect.get_height() / 2,
                label,
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
                color="white",
            )

    # Legend bên ngoài
    ax.legend(title="Nhóm khách", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=12, title_fontsize=13)

    plt.tight_layout()
    save_fig(fig, "30_score_vs_text_length_100percent_stacked_dual_label.png", output_dir)
    

# 31. Tỷ lệ đánh giá Tích cực & Tiêu cực theo nhóm khách (dựa trên positive_text / negative_text)
def plot_sentiment_ratio_by_group(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ biểu đồ thanh ngang 100% stacked hiển thị tỷ lệ bình luận có nội dung tích cực
    (positive_text không rỗng) và có nội dung tiêu cực (negative_text không rỗng)
    theo từng nhóm khách. Chỉ tính các bình luận có ít nhất một trong hai loại nội dung.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'group_type', 'positive_text' và 'negative_text'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    required_cols = ["group_type", "positive_text", "negative_text"]
    if not all(col in df.columns for col in required_cols):
        return

    df_plot = df[required_cols].copy()

    # Kiểm tra nội dung thực sự có hay không (không NaN và không rỗng sau khi strip)
    df_plot["has_positive"] = (
        df_plot["positive_text"].notna()
        & (df_plot["positive_text"].astype(str).str.strip() != "")
    )
    df_plot["has_negative"] = (
        df_plot["negative_text"].notna()
        & (df_plot["negative_text"].astype(str).str.strip() != "")
    )

    # Chỉ giữ các bình luận có ít nhất một loại nội dung (tích cực hoặc tiêu cực)
    df_sent = df_plot[df_plot["has_positive"] | df_plot["has_negative"]].copy()

    if df_sent.empty:
        return

    # Xác định sentiment chính: ưu tiên tiêu cực nếu có cả hai, иначе tích cực
    # (có thể thay đổi logic tùy yêu cầu – ở đây ưu tiên hiển thị tiêu cực để nổi bật vấn đề)
    def get_sentiment(row):
        if row["has_negative"]:
            return "Negative"
        elif row["has_positive"]:
            return "Positive"
        return None

    df_sent["sentiment"] = df_sent.apply(get_sentiment, axis=1)

    # Crosstab số lượng
    crosstab_count = pd.crosstab(df_sent["group_type"], df_sent["sentiment"])

    # Sắp xếp theo tổng số lượng (nhóm lớn ở dưới để dễ đọc)
    crosstab_count["total"] = crosstab_count.sum(axis=1)
    crosstab_count = crosstab_count.sort_values("total", ascending=True)
    crosstab_count = crosstab_count.drop(columns="total")

    # Đảm bảo có cả hai cột Positive và Negative
    for col in ["Positive", "Negative"]:
        if col not in crosstab_count.columns:
            crosstab_count[col] = 0
    crosstab_count = crosstab_count[["Positive", "Negative"]]

    # Tính tỷ lệ phần trăm
    crosstab_pct = crosstab_count.div(crosstab_count.sum(axis=1), axis=0) * 100

    # Màu sắc: xanh lá cho tích cực, cam/đỏ cho tiêu cực
    colors = ["#66c2a5", "#fc8d62"]

    fig, ax = plt.subplots(figsize=(14, max(6, len(crosstab_count) * 0.7)))

    crosstab_pct.plot(
        kind="barh",
        stacked=True,
        color=colors,
        ax=ax,
        width=0.8,
    )

    ax.set_title(
        "31. Tỷ lệ bình luận có nội dung Tích cực & Tiêu cực theo nhóm khách\n(Dựa trên positive_text & negative_text)",
        fontsize=22,
        fontweight="bold",
        pad=30,
    )
    ax.set_xlabel("Tỷ lệ phần trăm (%)", fontsize=15)
    ax.set_ylabel("Nhóm khách", fontsize=15)
    ax.grid(axis="x", alpha=0.3)

    # Label kép XX.X% (YYYY) cho segment lớn
    rects = ax.patches
    count_flat = crosstab_count.to_numpy().flatten("F")
    pct_flat = crosstab_pct.to_numpy().flatten("F")

    for rect, count, pct in zip(rects, count_flat, pct_flat):
        if pct >= 5:
            label = f"{pct:.1f}% ({int(count)})"
            text_color = "white" if pct > 40 else "black"
            ax.text(
                rect.get_x() + rect.get_width() / 2,
                rect.get_y() + rect.get_height() / 2,
                label,
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
                color=text_color,
            )

    ax.legend(title="Nội dung", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=12)

    plt.tight_layout()
    save_fig(fig, "31_sentiment_ratio_by_group_text_based.png", output_dir)

# 32. Phân tích chi tiết nội dung positive_text & negative_text
def plot_sentiment_count_from_text_columns(df: pd.DataFrame, output_dir: str) -> None:
    """
    Vẽ biểu đồ kết hợp pie chart và text box để hiển thị tỷ lệ và số lượng
    bình luận có/không có nội dung tích cực/tiêu cực dựa trên hai cột
    positive_text và negative_text (thường từ mô hình sentiment extraction).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame chứa các cột 'positive_text' và 'negative_text'.
    output_dir : str
        Thư mục đích để lưu file ảnh output.
    """
    required_cols = ["positive_text", "negative_text"]
    if not all(col in df.columns for col in required_cols):
        print("Thiếu cột positive_text hoặc negative_text – Skip biểu đồ này.")
        return

    df_plot = df[required_cols].copy()
    total_rows = len(df_plot)

    if total_rows == 0:
        return

    # Kiểm tra nội dung thực sự có hay không (không NaN và không rỗng)
    pos_has_content = df_plot["positive_text"].notna() & (df_plot["positive_text"].astype(str).str.strip() != "")
    neg_has_content = df_plot["negative_text"].notna() & (df_plot["negative_text"].astype(str).str.strip() != "")

    has_positive_count = pos_has_content.sum()
    has_negative_count = neg_has_content.sum()
    no_positive_count = (~pos_has_content).sum()
    no_negative_count = (~neg_has_content).sum()

    # Tính phần trăm
    has_positive_pct = round(has_positive_count / total_rows * 100, 1)
    has_negative_pct = round(has_negative_count / total_rows * 100, 1)
    no_positive_pct = round(no_positive_count / total_rows * 100, 1)
    no_negative_pct = round(no_negative_count / total_rows * 100, 1)

    counts = [has_positive_count, has_negative_count, no_positive_count, no_negative_count]
    labels = [
        "Có nội dung tích cực",
        "Có nội dung tiêu cực",
        "Không có review tích cực",
        "Không có review tiêu cực",
    ]

    # Màu sắc nhẹ nhàng, thanh lịch
    colors = ["#a8e6cf", "#ffcccb", "#d0e1f9", "#e6e6fa"]

    fig = plt.figure(figsize=(18, 11))
    gs = GridSpec(1, 2, width_ratios=[1.6, 1], wspace=0.4)

    # Pie chart bên trái
    ax_pie = fig.add_subplot(gs[0, 0])
    wedges, texts, autotexts = ax_pie.pie(
        counts,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=colors,
        textprops={"fontsize": 12, "fontweight": "bold"},
        wedgeprops={"linewidth": 3, "edgecolor": "white"},
    )

    for autotext in autotexts:
        autotext.set_fontsize(16)
        autotext.set_fontweight("bold")

    ax_pie.set_title("Tỷ lệ có/không nội dung theo từng loại review", fontsize=18, fontweight="bold", pad=20)

    # Text box chi tiết bên phải
    ax_text = fig.add_subplot(gs[0, 1])
    ax_text.axis("off")

    info_text = (
        f"Tổng số bình luận: {total_rows:,}\n\n"
        f"• Có nội dung tích cực\n   (positive_text): {has_positive_count:,} ({has_positive_pct}%)\n\n"
        f"• Có nội dung tiêu cực\n   (negative_text): {has_negative_count:,} ({has_negative_pct}%)\n\n"
        f"• Không có review tích cực\n   (positive_text trống): {no_positive_count:,} ({no_positive_pct}%)\n\n"
        f"• Không có review tiêu cực\n   (negative_text trống): {no_negative_count:,} ({no_negative_pct}%)"
    )

    ax_text.text(
        0.05,
        0.5,
        info_text,
        fontsize=16,
        verticalalignment="center",
        linespacing=1.8,
        bbox=dict(boxstyle="round,pad=1.5", facecolor="white", edgecolor="#95a5a6", linewidth=2, alpha=0.95),
    )

    fig.suptitle(
        "32. Phân tích chi tiết nội dung positive_text & negative_text",
        fontsize=24,
        fontweight="bold",
        y=0.98,
    )

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

    # # 01. Phân phối điểm số
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

    # # 27. Phân phối điểm theo top 20 khách sạn –
    # plot_score_by_top_hotels(df, output_dir, top_n=20)
    
    # # 28. Pairplot các đặc trưng số 
    # plot_pairplot_numeric_features(df, output_dir)

    # # 29. Score vs Text Length theo group_type – Tương tác 3 feature
    # plot_score_vs_text_length_faceted_vertical(df, output_dir)

    # # 30. Jointplot Score vs Text Length với regression 
    # plot_score_vs_text_length_stacked_bar(df, output_dir)
    
    # 31 Vẽ biểu đồ tỷ lệ sentiment (positive/neutral/negative) theo từng nhóm/category.
    plot_sentiment_ratio_by_group(df, output_dir)
    
    # 32 Vẽ biểu đồ đếm số lượng sentiment trực tiếp từ các cột text đã xử lý.
    plot_sentiment_count_from_text_columns(df, output_dir)
    
    print("\n" + "═" * 90)
    print("        HOÀN TẤT THÀNH CÔNG!")
    print(f"        Đã tạo ĐỦ 32 biểu đồ")
    print(f"        Thư mục lưu: {Path(output_dir).resolve()}")
    # print("\n        Giờ thì in ra, nộp sếp, bảo vệ xuất sắc, crush phải đổ!")
    # print("        Chúc bạn 10 ĐIỂM LUẬN VĂN & THĂNG CHỨC NHANH!")
    print("═" * 90 + "\n")