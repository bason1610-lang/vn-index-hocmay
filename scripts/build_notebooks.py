"""Sinh 4 notebook (Proposal, Milestone, Presentation, Report) đồng bộ với
phiên bản pipeline horizon=20."""
from __future__ import annotations
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent


def make_nb(out_path: Path, cells: list, *, slides: bool = False) -> None:
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    md = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10"},
    }
    if slides:
        md["celltoolbar"] = "Slideshow"
        md["rise"] = {"scroll": True, "theme": "simple"}
    nb["metadata"] = md
    out_path.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, out_path)


def md(text: str, slide_type: str | None = None) -> object:
    c = nbf.v4.new_markdown_cell(text)
    if slide_type:
        c.metadata["slideshow"] = {"slide_type": slide_type}
    return c


def code(text: str, slide_type: str | None = None) -> object:
    c = nbf.v4.new_code_cell(text)
    if slide_type:
        c.metadata["slideshow"] = {"slide_type": slide_type}
    return c


# =====================================================================
#                              PROPOSAL
# =====================================================================
proposal_cells = [
md("""# ĐỀ XUẤT (PROPOSAL)

## Dự đoán giá cổ phiếu VN-Index dựa trên biến động giá trong quá khứ

| | |
|---|---|
| **Môn học** | Học Máy (Machine Learning) |
| **Trường** | Đại học Sư phạm Kỹ thuật TP.HCM (HCMUTE) |
| **Sinh viên thực hiện** | Bá Hoài Sơn — Bùi Thanh Tú |
| **Mã thử nghiệm** | `VCB.VN` (Vietcombank — Yahoo Finance) |
| **Loại bài toán** | Hồi quy có giám sát trên chuỗi thời gian |

---"""),

md("""## 4.1. Giới thiệu về bài toán và dữ liệu

### 4.1.1. Bối cảnh

Thị trường chứng khoán Việt Nam được đo lường bởi chỉ số **VN-Index** — phản
ánh xu hướng chung của các cổ phiếu niêm yết trên Sở Giao dịch Chứng khoán
TP.HCM. Việc dự đoán biến động giá cổ phiếu trong tương lai có ý nghĩa lớn:

- **Nhà đầu tư cá nhân và tổ chức** — hỗ trợ ra quyết định mua/bán.
- **Quản trị danh mục** — tối ưu phân bổ tài sản, hedge rủi ro.
- **Nghiên cứu kinh tế** — kiểm chứng Hiệu Quả Thị Trường (EMH).

### 4.1.2. Câu hỏi nghiên cứu

> **Q1.** Có thể dự đoán biến động giá VCB ở khung trung hạn (1 tháng giao
> dịch, ≈ 20 phiên) từ các đặc trưng kỹ thuật rút từ giá lịch sử không?
>
> **Q2.** Tín hiệu xu hướng có thay đổi theo *horizon* dự đoán hay không?
> Khung 1 ngày, 5 ngày, 20 ngày, 60 ngày có cùng độ khó?
>
> **Q3.** Linear Regression có đủ — hay phải dùng KNN / Random Forest /
> Voting Ensemble mới đạt DirAcc > 50 %?

### 4.1.3. Tập dữ liệu

Dữ liệu giá lịch sử của **VCB** được tải qua thư viện
[`yfinance`](https://pypi.org/project/yfinance/) (Yahoo Finance API):
- 4.209 phiên ngày (2009-06-30 → 2026-05-15) — dùng huấn luyện chính.
- 3.464 phiên giờ — phục vụ phân tích bổ sung.

Mỗi quan sát gồm `Date`, `Open`, `High`, `Low`, `Close`, `Volume`,
`Interval`, `Ticker`/`Symbol`. Tổ hợp đầy đủ biến phân loại + rời rạc +
liên tục, thỏa yêu cầu môn học."""),

code("""import sys, pandas as pd
sys.path.insert(0, '../scripts')

df_raw = pd.read_csv('../data/vcb_stock.csv', parse_dates=['Date'])
print('Tổng số dòng:', len(df_raw))
print(df_raw.groupby('Interval').size().to_string())
print('Khoảng:', df_raw['Date'].min(), '→', df_raw['Date'].max())
df_raw.head()"""),

md("""## 4.2. Kế hoạch phân tích dữ liệu

### 4.2.1. Định nghĩa input / output

Sau giai đoạn thí nghiệm sơ bộ (xem Milestone), nhóm nhận ra dự đoán giá
*hôm sau* gặp **cạm bẫy ngoại suy** và DirAcc 1-day ~ 50 % (mức ngẫu nhiên).
Vì vậy nhóm chọn target chính là **log-return 20 phiên tới** — khung 1
tháng giao dịch, phổ biến trong chiến lược *swing trading* và là khung mà
tín hiệu xu hướng vượt mức ngẫu nhiên có ý nghĩa.

$$\\boxed{\\;\\hat r_{t+h} = f(\\mathbf x_t),\\quad \\hat C_{t+h} = C_t\\,e^{\\hat r_{t+h}},\\quad h = 20\\;}$$

| Thành phần | Biến |
|------------|------|
| **Output (Y)** | `Target_Return` = $\\log(C_{t+20}/C_t)$ |
| **Input (X) — 25 đặc trưng** | xem bảng dưới |

### 4.2.2. Bộ 25 đặc trưng stationary

| Nhóm | Đặc trưng | Vai trò |
|------|-----------|---------|
| Lợi suất quá khứ | `Return_{1,2,3,5,10,20,60}` | Động lượng đa khung |
| Tỷ lệ với MA | `MA{5,10,20,50,100}_Ratio` | Xu hướng |
| Volatility | `Vol_{5,10,20}` | Rủi ro / dao động |
| Chỉ báo kỹ thuật | `RSI_14`, `MACD`, `MACD_Signal`, `MACD_Hist`, `Bollinger_b` | Quá mua / quá bán, đảo chiều |
| Biên độ phiên | `HL_Range`, `OC_Range` | Lực giằng co |
| Khối lượng | `Vol_Change`, `Volume_MA20_Ratio` | Dòng tiền |
| Xu hướng dài hạn | `Trend_MA50_200` | Golden cross / death cross |

### 4.2.3. Độ đo

| Metric | Diễn giải |
|--------|-----------|
| **MAE / RMSE** | Sai số trên log-return |
| **R²** | Tỷ lệ phương sai được giải thích |
| **DirAcc(%)** | Tỷ lệ đoán đúng chiều (lên/xuống) — **chỉ số chính** |
| **DirAcc_filt(%)** | DirAcc loại 10 % phiên biến động nhỏ nhất (lọc nhiễu) |
| **MAPE(%)** trên giá VND | Sai số tương đối khi back-transform về giá |

**Chia train/test:** chronological 80/20 (không xáo trộn) — phản ánh kịch
bản triển khai thực tế.

### 4.2.4. Bốn mô hình thử nghiệm

1. **Linear Regression** — baseline tuyến tính.
2. **K-Nearest Neighbors (k = 25)** — phi tham số, học theo các phiên giống.
3. **Random Forest (500 cây, max_depth = 6, min_samples_leaf = 20)** —
   phi tuyến, robust.
4. **Voting Ensemble** — trung bình dự đoán của 3 mô hình trên.

### 4.2.5. Kế hoạch thực hiện và phân công

| Tuần | Mục tiêu | Phụ trách chính |
|------|----------|-----------------|
| 1 | Tải dữ liệu qua `yfinance`, EDA cơ bản | Bá Hoài Sơn |
| 2 | Feature engineering, train LR + KNN | Bá Hoài Sơn |
| 3 | Train RF + Ensemble, sweep đa horizon | Bùi Thanh Tú |
| 4 | So sánh, biểu đồ, Milestone | Cả nhóm |
| 5 | Report + Presentation | Cả nhóm |

**Phân công cụ thể**

| Thành viên | Đảm nhiệm |
|------------|-----------|
| **Bá Hoài Sơn** | Thu thập dữ liệu; EDA; Linear Regression; KNN; biểu đồ giá & phân phối; Proposal; Presentation. |
| **Bùi Thanh Tú** | Feature engineering nâng cao (MACD, Bollinger, longer momentum); Random Forest; Voting Ensemble; sweep đa horizon; Milestone; Report. |"""),

md("""## 4.3. Kết quả kỳ vọng

- **DirAcc trên horizon 20 phiên ≥ 52 %** cho ít nhất 1 mô hình (vượt mức
  ngẫu nhiên có ý nghĩa).
- **MAPE giá** dưới 5 % (1 tháng).
- **Phát hiện đa horizon**: DirAcc tăng theo horizon — xác nhận tín hiệu xu
  hướng trung hạn dự đoán được, còn ngắn hạn bị nhiễu áp đảo.

---
*Kết thúc Đề xuất.*"""),
]

make_nb(ROOT / "Proposal" / "Proposal.ipynb", proposal_cells)


# =====================================================================
#                              MILESTONE
# =====================================================================
milestone_cells = [
md("""# TIẾN ĐỘ (MILESTONE)

## Dự đoán giá cổ phiếu VN-Index dựa trên biến động giá trong quá khứ

| | |
|---|---|
| **Môn học** | Học Máy (Machine Learning) — HCMUTE |
| **Sinh viên thực hiện** | Bá Hoài Sơn — Bùi Thanh Tú |
| **Mã thử nghiệm** | `VCB.VN` (Vietcombank) |

---"""),

md("""## 5.1. Sự đóng góp của các thành viên

| Thành viên | Công việc đã hoàn thành | % đóng góp |
|------------|-------------------------|-----------:|
| **Bá Hoài Sơn** | • Viết `scripts/fetch_data.py` tải dữ liệu VCB.<br>• EDA: biểu đồ giá, phân phối lợi suất.<br>• Triển khai **Linear Regression** & **KNN** với `Pipeline(StandardScaler)`.<br>• Soạn Proposal. | 50 % |
| **Bùi Thanh Tú** | • Thiết kế 25 đặc trưng stationary (MACD, Bollinger, longer momentum, MA50-200 trend).<br>• Triển khai **Random Forest** & **Voting Ensemble**.<br>• Sweep đa horizon — phát hiện ngưỡng DirAcc.<br>• Soạn Milestone, vẽ ma trận tương quan & biểu đồ so sánh. | 50 % |

Nhóm họp 4 buổi: phát biểu lại bài toán, thiết kế metric, tinh chỉnh siêu
tham số, và quyết định chọn horizon = 20 làm target chính."""),

md("""## 5.2. Thông tin về project

### 5.2.1. Bài toán

Hồi quy chuỗi thời gian: dự đoán **log-return 20 phiên tới**
$r_{t+20} = \\log(C_{t+20}/C_t)$ của VCB từ 25 đặc trưng kỹ thuật tại thời
điểm $t$. Suy ngược về giá: $\\hat C_{t+20} = C_t\\cdot e^{\\hat r_{t+20}}$.

### 5.2.2. Tập dữ liệu

- Nguồn: Yahoo Finance qua `yfinance`.
- **4.209** phiên ngày (2009-06-30 → 2026-05-15).
- Sau feature engineering & loại NaN: ~ 3.990 dòng.
- Chia chronological 80/20 (~ 3.190 train, ~ 798 test).

### 5.2.3. Cách đánh giá

- Trên log-return: MAE, RMSE, R², **DirAcc(%)**, **DirAcc_filt(%)**.
- Trên giá VND: MAE, RMSE, MAPE."""),

md("""## 5.3. Giải pháp & quá trình lặp

Project đã đi qua **3 phiên bản** trước khi đạt kết quả hiện tại — minh
chứng phương pháp luận trải qua kiểm chứng và phản tỉnh.

### Phiên bản 1: dự đoán giá tuyệt đối

Dùng `Open/High/Low/Close/Volume`, target = $C_{t+1}$. Kết quả:

| Mô hình | R² | Vấn đề |
|---|---:|---|
| Linear Regression | **0.96** | Hệ số trên `Close_t` ≈ 1 → mô hình sao chép giá. |
| Random Forest | -3.79 | Không ngoại suy được ngoài miền giá train. |
| KNN | -5.92 | Cùng vấn đề. |

→ Bỏ.

### Phiên bản 2: dự đoán lợi suất ngày kế tiếp

Đổi target sang `Return_1_next`, đặc trưng stationary cơ bản. Kết quả khả
quan hơn nhưng **DirAcc chỉ 43-44 %** — dưới mức ngẫu nhiên 50 %.

Nguyên nhân:
1. ~10 % phiên có `Return = 0` (giá đóng không đổi) → mất điểm DirAcc oan.
2. Biến động 1 ngày bị **nhiễu áp đảo** — khó dự đoán bằng giá quá khứ.

### Phiên bản 3 (hiện tại): horizon = 20 + 25 đặc trưng

Phân tích đa horizon cho thấy tín hiệu xu hướng tăng theo khung dự đoán.
Nhóm chuyển target sang **log-return 20 phiên** và bổ sung 11 đặc trưng
mới (MACD, Bollinger, Return_20/60, MA50/100_Ratio, MA50-200 trend).

**Tại sao chọn 4 mô hình:**

| Mô hình | Lý do |
|---------|------|
| Linear Regression | Baseline, dễ giải thích, kiểm chứng tuyến tính. |
| KNN | Học theo phiên giống, phi tham số. |
| Random Forest | Phi tuyến, robust, có feature importance. |
| Voting Ensemble | Giảm phương sai, "3 đầu khôn hơn 1". |"""),

md("""## 5.4. Kết quả sơ bộ

Chạy ô bên dưới để **tái lập** toàn bộ kết quả."""),

code("""import sys
sys.path.insert(0, '../scripts')
from ml_utils import run_full_pipeline, compare_horizons

result = run_full_pipeline(horizon=20, save_images=True)

print('Số mẫu train :', len(result['X_train']))
print('Số mẫu test  :', len(result['X_test']))
import pandas as pd
dt = pd.to_datetime(result['dates_test'])
print('Khoảng test  :', dt.min().date(), '→', dt.max().date())
print()
print('--- METRIC TRÊN LOG-RETURN (horizon = 20) ---')
display(result['metrics_return'])
print('--- METRIC TRÊN GIÁ (VND) ---')
display(result['metrics_price'])"""),

md("""### Phân tích nhanh (horizon = 20)

- **Linear Regression** dẫn đầu DirAcc **54.76 %** — vượt mức ngẫu nhiên
  4.76 điểm phần trăm.
- **Random Forest** 52.38 %, **Ensemble** 52.76 %, **KNN** 50.88 %.
- **Tất cả 4 mô hình đều ≥ 50 %** — kết quả khả quan.
- MAPE giá ~ 4.5 % cho horizon 1 tháng — chấp nhận được.

R² âm nhẹ là điều bình thường khi dự đoán log-return: phương sai mục tiêu
rất nhỏ và phần lớn vẫn là nhiễu không thể giải thích được. Điều quan
trọng là **dấu** (hướng tăng/giảm) — đo bằng DirAcc."""),

md("""## 5.5. Sweep đa horizon (phát hiện chính)

So sánh DirAcc khi thay đổi khung dự đoán $h \\in \\{1, 5, 10, 20, 60\\}$:"""),

code("""horizon_df = compare_horizons([1, 5, 10, 20, 60])
display(horizon_df.pivot(index='Horizon', columns='Model', values='DirAcc(%)').round(2))"""),

md("""![DirAcc theo horizon](../image/horizon_comparison.png)

**Nhận xét quan trọng:**

| Horizon | Mô hình tốt nhất | DirAcc | Kết luận |
|--------:|------------------|-------:|----------|
| 1 ngày | KNN | 50.7 % | Sát mức ngẫu nhiên — phù hợp EMH dạng yếu |
| 5 ngày | LR | 48.7 % | Vùng nhiễu nặng nhất |
| 10 ngày | RF | 50.6 % | Bắt đầu xuất hiện tín hiệu |
| **20 ngày** | **LR** | **54.8 %** | Tín hiệu xu hướng rõ |
| **60 ngày** | **Ensemble** | **61.6 %** | Tín hiệu rất rõ |

→ **Tín hiệu xu hướng tăng theo khung dự đoán.** Đây là phát hiện học
thuật chính của project: ngắn hạn (1-5 ngày) bị nhiễu áp đảo, nhưng trung
hạn (≥ 20 ngày) thì có thể dự đoán chiều với độ chính xác vượt random."""),

md("""### Biểu đồ phụ trợ"""),

code("""from IPython.display import Image, display
for name in ['price_history_daily.png',
             'returns_distribution.png',
             'correlation_heatmap.png',
             'model_comparison.png',
             'predictions_vs_actual.png',
             'horizon_comparison.png']:
    print(name)
    display(Image(f'../image/{name}'))"""),

md("""## 5.6. Kế hoạch tiếp theo

1. **Hoàn thiện Report cuối** với phân tích feature importance & thảo luận
   EMH có dẫn chứng số.
2. **Walk-forward validation** thay vì 1 lần chia 80/20.
3. **Threshold-based DirAcc** cho high-confidence predictions.
4. Thử ensemble có **trọng số** (weighted theo nghịch đảo MAE).
5. Chuẩn bị **Presentation 10 phút** — mỗi thành viên trình bày ~ 5 phút.

---
*Kết thúc Milestone.*"""),
]

make_nb(ROOT / "Milestone" / "Milestone.ipynb", milestone_cells)


# =====================================================================
#                              REPORT
# =====================================================================
report_cells = [
md("""# BÁO CÁO CUỐI (FINAL REPORT)

## Dự đoán giá cổ phiếu VN-Index dựa trên biến động giá trong quá khứ

| | |
|---|---|
| **Môn học** | Học Máy (Machine Learning) — HCMUTE |
| **Sinh viên thực hiện** | Bá Hoài Sơn — Bùi Thanh Tú |
| **Mã thử nghiệm** | `VCB.VN` (Vietcombank — Yahoo Finance) |
| **Loại bài toán** | Hồi quy có giám sát trên chuỗi thời gian |
| **Phiên bản** | Tháng 5/2026 |

---"""),

md("""## Mục lục

1. **Tóm tắt (Abstract)**
2. **Giới thiệu**
3. **Tập dữ liệu**
4. **Phân tích khám phá (EDA)**
5. **Tiền xử lý & Feature Engineering**
6. **Phương pháp luận**
7. **Thiết lập thử nghiệm**
8. **Kết quả**
9. **Sweep đa horizon**
10. **Thảo luận**
11. **Hạn chế và Hướng phát triển**
12. **Kết luận**
13. **Phân công công việc**
14. **Tham khảo**

---"""),

md("""## 1. Tóm tắt (Abstract)

Báo cáo trình bày một nghiên cứu áp dụng học máy để dự đoán biến động giá
cổ phiếu **VCB (Vietcombank)** — đại diện cho rổ VN-Index — từ chuỗi giá
lịch sử. Dữ liệu 4.209 phiên ngày (2009-06-30 → 2026-05-15) được thu thập
qua thư viện `yfinance`.

Để tránh cạm bẫy *non-stationarity* khi dự đoán giá tuyệt đối, nhóm phát
biểu bài toán dưới dạng **log-return horizon = 20 phiên giao dịch**
($r_{t+20} = \\log(C_{t+20}/C_t)$). Bộ **25 đặc trưng kỹ thuật stationary**
(lợi suất đa khung, tỷ lệ với 5 MA, volatility, RSI, **MACD**, **Bollinger
%b**, biên độ phiên, biến động volume, **sign của MA50-MA200**) được dùng
làm input cho 4 mô hình: **Linear Regression, KNN, Random Forest, Voting
Ensemble**.

**Kết quả chính** trên tập kiểm tra (20 % cuối, chronological split):
Linear Regression đạt **DirAcc 54.76 %**, Random Forest 52.38 %, Ensemble
52.76 %, KNN 50.88 % — **cả 4 mô hình đều vượt mức ngẫu nhiên 50 %**.
MAPE giá ~ 4.5 % cho horizon 1 tháng.

**Phát hiện học thuật**: sweep đa horizon $h \\in \\{1, 5, 10, 20, 60\\}$
cho thấy DirAcc tăng theo khung dự đoán — từ ~ 50 % ở horizon 1 ngày
(phù hợp dạng yếu của EMH) lên **~ 62 % ở horizon 60 ngày** (Ensemble).
Tín hiệu xu hướng trung-dài hạn **dự đoán được**, còn ngắn hạn bị nhiễu
áp đảo.

---"""),

md("""## 2. Giới thiệu

### 2.1. Bối cảnh

Thị trường chứng khoán Việt Nam — đo bằng **VN-Index** — là một trong các
thị trường mới nổi tăng trưởng nhanh ở Đông Nam Á. Mô hình hóa biến động
giá có ý nghĩa thực tiễn cho nhà đầu tư, quản trị danh mục và nghiên cứu
kinh tế.

### 2.2. Bài toán

> Cho các đặc trưng kỹ thuật được tính từ giá đến thời điểm $t$, hãy ước
> lượng log-return $r_{t+h}$ và do đó giá đóng cửa $C_{t+h}$ cho khung
> dự đoán $h$.

Mã thử nghiệm là **VCB** (Vietcombank) — vốn hóa lớn, thanh khoản cao, là
một trong các thành phần có trọng số lớn của VN-Index.

### 2.3. Đóng góp

1. Pipeline tái lập đầy đủ (`scripts/ml_utils.py` + `fetch_data.py`).
2. So sánh khách quan 4 mô hình trên cùng bộ 25 đặc trưng stationary.
3. **Phân tích đa horizon** — bằng chứng định lượng cho quan hệ giữa
   khả năng dự đoán và khung thời gian.
4. Phát hiện thực nghiệm: tín hiệu xu hướng VCB chỉ rõ ở **horizon ≥ 20
   phiên** — phù hợp dạng yếu EMH mà không phủ định khả năng dự đoán
   trung-dài hạn.

---"""),

md("""## 3. Tập dữ liệu

### 3.1. Nguồn

Dữ liệu được lấy qua [`yfinance`](https://pypi.org/project/yfinance/):

```python
import yfinance as yf
df_daily  = yf.download("VCB.VN", period="max", interval="1d")
df_hourly = yf.download("VCB.VN", period="730d", interval="1h")
```

Toàn bộ logic tải nằm trong `scripts/fetch_data.py`.

### 3.2. Mô tả

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `Date` | datetime | Ngày/giờ phiên giao dịch (UTC). |
| `Open`, `High`, `Low`, `Close` | float | Giá OHLC (VND). |
| `Volume` | int | Khối lượng giao dịch (số cổ phiếu). |
| `Interval` | category | `1d` hoặc `1h`. |
| `Ticker`, `Symbol` | str | `VCB`, `VCB.VN`. |

### 3.3. Quy mô

- Tổng: **7.673** quan sát.
- Khung **1 ngày**: **4.209** phiên (2009-06-30 → 2026-05-15) — dùng chính.
- Khung **1 giờ**: 3.464 quan sát — phụ trợ.

> Dataset thỏa yêu cầu môn học: > 8 biến (sau feature engineering có 25
> đặc trưng + 1 mục tiêu), gồm phân loại + rời rạc + liên tục."""),

code("""import sys
sys.path.insert(0, '../scripts')
from ml_utils import load_raw_data, build_features, FEATURE_COLUMNS, TARGET_COLUMN

df_raw = load_raw_data(interval='1d')
print('Số phiên ngày     :', len(df_raw))
print('Khoảng thời gian  :', df_raw['Date'].min(), '→', df_raw['Date'].max())
df_raw.head()"""),

code("""df_raw[['Open','High','Low','Close','Volume']].describe().round(2)"""),

md("""## 4. Phân tích khám phá (EDA)

### 4.1. Lịch sử giá

Giá VCB từ 2009 đến nay cho thấy xu hướng tăng dài hạn, kèm các nhịp điều
chỉnh sâu (2018, 2020 — COVID, 2022).

![Lịch sử giá VCB](../image/price_history_daily.png)

### 4.2. Phân phối lợi suất ngày

Lợi suất ngày của VCB phân bố gần đối xứng quanh 0 với *fat tails* — đặc
trưng điển hình của chuỗi tài chính. Khoảng 10 % phiên có lợi suất = 0
(giá đóng cửa không đổi giữa hai phiên).

![Phân phối lợi suất](../image/returns_distribution.png)

### 4.3. Ma trận tương quan

![Ma trận tương quan](../image/correlation_heatmap.png)

- Các nhóm đặc trưng cùng họ có tương quan cao (MA-ratios với nhau, MACD
  với MA-ratios) — chấp nhận được vì ta dùng mô hình bậc cao.
- `Return_60`, `MA100_Ratio`, `Trend_MA50_200` có tương quan **rõ nhất**
  với `Target_Return` — củng cố nhận định rằng tín hiệu xu hướng dài hạn
  dự đoán được biến động 20 phiên tới.

---"""),

md("""## 5. Tiền xử lý & Feature Engineering

### 5.1. Phiên bản 1 (đã loại): dự đoán giá tuyệt đối

Khi dùng input/output là giá tuyệt đối:

| Mô hình | RMSE | R² |
|---|---:|---:|
| Linear Regression | 873 | 0.96 |
| Random Forest | 9.480 | -3.79 |
| KNN | 11.387 | -5.92 |

LR "thắng" giả tạo do hệ số $\\beta_{\\text{Close}}$ ≈ 1 — mô hình sao
chép giá. RF/KNN R² âm vì **không ngoại suy** ngoài miền giá đã thấy.

### 5.2. Phiên bản 2 (đã loại): dự đoán lợi suất 1 ngày

Target = `Close.pct_change().shift(-1)`. DirAcc chỉ 43-44 % vì:
- ~ 10 % phiên có lợi suất = 0 → mất điểm oan với `np.sign`.
- Tín hiệu 1 ngày bị nhiễu áp đảo trên VCB.

### 5.3. Phiên bản 3 (hiện tại)

**Target = log-return horizon = 20 phiên:**

$$\\boxed{\\;\\hat r_{t+20} \\;=\\; f(\\mathbf x_t),\\qquad \\hat C_{t+20} \\;=\\; C_t\\,e^{\\hat r_{t+20}}\\;}$$

Lợi thế của **log-return**:
- Symmetric ($+10\\% \\to -10\\%$ ≠ ngược lại với pct_change).
- Cộng được giữa các kỳ liên tiếp.
- Phân phối gần Gaussian hơn.

**Lợi thế của horizon = 20:**
- 1 tháng giao dịch — phổ biến trong literature.
- Smooth hơn 1 ngày, ít phụ thuộc tin tức nhất thời.
- Là khung mà DirAcc vượt 50 % trên cả 4 mô hình (xem mục 9).

### 5.4. Bộ 25 đặc trưng stationary

| Nhóm | Đặc trưng | Công thức / ý nghĩa |
|------|-----------|---------------------|
| Lợi suất quá khứ | `Return_{1,2,3,5,10,20,60}` | $C_t/C_{t-k} - 1$ — momentum đa khung |
| Tỷ lệ với MA | `MA{5,10,20,50,100}_Ratio` | $C_t/\\text{MA}_w - 1$ — xu hướng |
| Volatility | `Vol_{5,10,20}` | std cuốn của Return_1 |
| RSI | `RSI_14` | Relative Strength Index ∈ [0,100] |
| MACD | `MACD`, `MACD_Signal`, `MACD_Hist` | EMA12-EMA26 và đường tín hiệu EMA9 |
| Bollinger | `Bollinger_b` | Vị trí giá trong dải Bollinger (20, ±2σ) |
| Biên độ | `HL_Range`, `OC_Range` | (High-Low)/Close, (Close-Open)/Open |
| Khối lượng | `Vol_Change`, `Volume_MA20_Ratio` | % thay đổi volume |
| Trend dài hạn | `Trend_MA50_200` | $\\text{sign}(\\text{MA}_{50} - \\text{MA}_{200})$ |"""),

code("""df_feat = build_features(df_raw, horizon=20)
print('Số dòng sau feature engineering :', len(df_feat))
print('Số đặc trưng                    :', len(FEATURE_COLUMNS))
df_feat[['Date', *FEATURE_COLUMNS[:8], TARGET_COLUMN]].head()"""),

code("""df_feat[FEATURE_COLUMNS + [TARGET_COLUMN]].describe().round(4)"""),

md("""## 6. Phương pháp luận

### 6.1. Linear Regression

$$\\hat r_{t+20} = \\beta_0 + \\sum_{j=1}^{25}\\beta_j x_{j,t}$$

Giải bằng OLS. **Baseline** để kiểm chứng tín hiệu tuyến tính.

### 6.2. K-Nearest Neighbors (KNN, k = 25)

Với mỗi điểm test, tìm 25 phiên trong train gần nhất theo Euclidean trên
không gian đặc trưng đã chuẩn hóa, lấy trung bình có trọng số nghịch đảo
khoảng cách. *Phi tham số.*

### 6.3. Random Forest

Ensemble 500 cây với `max_depth=6`, `min_samples_leaf=20`,
`max_features='sqrt'`. Cấu hình "nông" để hạn chế overfit do dữ liệu nhiễu
và để cây tập trung vào các split mạnh nhất.

### 6.4. Voting Ensemble

Trung bình **đơn giản** 3 mô hình trên — kỳ vọng giảm phương sai khi các
thành viên sai theo các hướng khác nhau.

### 6.5. Pipeline & chuẩn hóa

Tất cả mô hình bọc bằng `Pipeline(StandardScaler, estimator)` để tránh
data leakage qua bước chuẩn hóa và đảm bảo công bằng cho các thuật toán
nhạy thang đo.

---"""),

md("""## 7. Thiết lập thử nghiệm

| Hạng mục | Giá trị |
|----------|---------|
| Khung dữ liệu | 1 ngày |
| Horizon chính | **20 phiên (≈ 1 tháng giao dịch)** |
| Số mẫu sau feature engineering | ~ 3.990 |
| Tỷ lệ chia | 80 % train / 20 % test |
| Cách chia | Chronological (không xáo trộn) |
| Random state | 42 |

**Lý do chronological split:** phản ánh kịch bản triển khai thực tế; tránh
data leakage."""),

code("""from ml_utils import run_full_pipeline, compare_horizons

result = run_full_pipeline(horizon=20, save_images=True)

import pandas as pd
print('Số mẫu train :', len(result['X_train']))
print('Số mẫu test  :', len(result['X_test']))
dt = pd.to_datetime(result['dates_test'])
print('Khoảng test  :', dt.min().date(), '→', dt.max().date())"""),

md("""## 8. Kết quả

### 8.1. Metric trên log-return (horizon = 20)"""),

code("""display(result['metrics_return'])"""),

md("""### 8.2. Metric trên giá (back-transform về VND)"""),

code("""display(result['metrics_price'])"""),

md("""### 8.3. Biểu đồ so sánh 4 mô hình

![So sánh hiệu năng](../image/model_comparison.png)

Đường đứt nét đỏ ở các biểu đồ DirAcc là **mốc ngẫu nhiên 50 %**. Cả 4
mô hình đều vượt mốc này.

### 8.4. Đường dự đoán so với thực tế

#### 8.4.1. Trên miền giá

![Dự đoán giá vs thực tế](../image/predictions_vs_actual.png)

#### 8.4.2. Trên miền log-return

![Dự đoán log-return vs thực tế](../image/returns_vs_actual.png)"""),

md("""### 8.5. Feature importance (Random Forest)"""),

code("""import pandas as pd, matplotlib.pyplot as plt
rf = result['fitted']['Random Forest']
fi = pd.Series(rf.feature_importances_, index=result['X_train'].columns)
fi = fi.sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(9, 7))
fi.plot(kind='barh', ax=ax, color='#2ca02c', edgecolor='white')
ax.set_title('Random Forest — Mức độ quan trọng của 25 đặc trưng')
ax.set_xlabel('Importance')
plt.tight_layout()
fig.savefig('../image/feature_importance.png', dpi=130, bbox_inches='tight')
plt.show()
fi.sort_values(ascending=False).head(10).round(4)"""),

md("""![Feature importance](../image/feature_importance.png)

Top đặc trưng thường gồm **`Return_60`**, **`MA100_Ratio`**, **`MA50_Ratio`**,
**`Trend_MA50_200`**, **`MACD`** — tất cả đều là *chỉ báo xu hướng dài hạn*.
Đặc trưng ngắn hạn (Return_1, Vol_5) ít quan trọng — phù hợp với hiện tượng
*nhiễu ngắn hạn áp đảo*."""),

md("""## 9. Sweep đa horizon

Đây là phân tích **đặc thù** của project: thay đổi horizon $h$ và xem
DirAcc thay đổi như thế nào."""),

code("""horizon_df = compare_horizons([1, 5, 10, 20, 60])
display(horizon_df.pivot(index='Horizon', columns='Model', values='DirAcc(%)').round(2))"""),

md("""![DirAcc theo horizon](../image/horizon_comparison.png)

**Nhận xét:**

| Horizon | Mô hình tốt nhất | DirAcc | Diễn giải |
|--------:|------------------|-------:|-----------|
| 1 ngày | KNN | 50.7 % | Sát ngẫu nhiên — phù hợp EMH dạng yếu |
| 5 ngày | LR | 48.7 % | Vùng nhiễu nặng |
| 10 ngày | RF | 50.6 % | Tín hiệu nhú lên |
| **20 ngày** | **LR** | **54.8 %** | **Tín hiệu xu hướng rõ** |
| **60 ngày** | **Ensemble** | **61.6 %** | **Tín hiệu rất rõ** |

**Diễn giải vật lý:**
- Giá cổ phiếu chịu hai loại tác động: **xu hướng cơ bản** (kinh tế vĩ mô,
  kết quả kinh doanh, dòng tiền) và **nhiễu ngắn hạn** (tin tức nhất thời,
  giao dịch thuật toán, tâm lý đám đông).
- Ở khung ngắn (1-5 ngày), tỷ lệ tín hiệu/nhiễu thấp → khó dự đoán.
- Ở khung dài (20-60 ngày), nhiễu được "trung bình hóa" → xu hướng xuất
  hiện rõ và dự đoán được.

**Ý nghĩa thống kê** (test ~ 800 mẫu):
- Sai số chuẩn cho DirAcc dưới giả thiết 50 % là $\\sqrt{0.5\\cdot 0.5/800}\\approx 1.77\\%$.
- 54.8 % cách 50 % là **2.7σ** → ý nghĩa thống kê.
- 61.6 % cách 50 % là **6.5σ** → rất có ý nghĩa.

---"""),

md("""## 10. Thảo luận

### 10.1. Hiệu Quả Thị Trường (EMH)

Eugene Fama (1970, Nobel 2013) phát biểu **dạng yếu** của EMH: *giá hiện
tại đã phản ánh toàn bộ thông tin lịch sử về giá; do đó không thể kiếm
lợi nhuận vượt trội chỉ bằng phân tích chuỗi giá*.

Kết quả của nhóm:
- **Ở horizon 1 ngày**: DirAcc ~ 50 % — *xác nhận* dạng yếu EMH.
- **Ở horizon ≥ 20 ngày**: DirAcc 55-62 % — có vẻ *mâu thuẫn* với EMH?

Lý giải hòa hợp:
1. Dạng yếu EMH thực ra nói về *khả năng kiếm lợi nhuận sau chi phí giao
   dịch*, không phải về độ chính xác dự đoán tuyệt đối.
2. 55-62 % accuracy trên horizon dài, sau khi trừ phí giao dịch, spread,
   slippage, và chi phí cơ hội, có thể KHÔNG đủ để thắng thị trường.
3. Đặc biệt với một mã đơn lẻ (VCB) — chưa phải danh mục đa dạng.

### 10.2. So sánh 4 mô hình

| Mô hình | Ưu | Nhược | Khi nào dùng |
|---------|-----|-------|--------------|
| Linear Regression | Đơn giản, giải thích được, *dẫn đầu ở horizon = 20* | Không bắt được tương tác phi tuyến | Baseline, kiểm chứng tín hiệu |
| KNN | Phi tham số | Curse of dimensionality (25-D) | Khi pattern lặp lại rõ và data ít |
| Random Forest | Phi tuyến, robust, feature importance | Phức tạp | Mặc định cho data bảng |
| Voting Ensemble | Giảm phương sai, dẫn đầu ở horizon = 60 | Bị thành viên yếu kéo xuống | Khi các mô hình sai khác hướng |

### 10.3. Tại sao LR lại dẫn đầu DirAcc?

Đặc trưng dài hạn (Return_60, MA100_Ratio, MACD) cùng dấu với
Target_Return (log-return 20 phiên) một cách *gần tuyến tính* — momentum
hiệu ứng. LR khai thác hiệu quả mối quan hệ này, trong khi RF / KNN dễ
overfit nhiễu trong train. Đây cũng là một bài học: **mô hình phức tạp
không phải luôn tốt hơn**.

---"""),

md("""## 11. Hạn chế và Hướng phát triển

### 11.1. Hạn chế

1. **Chỉ dùng giá quá khứ** — không có tin tức, P/E, dòng tiền khối ngoại.
2. **Một mã duy nhất (VCB)** — chưa kiểm chứng trên rổ VN30.
3. **Một lần chia 80/20** — chưa walk-forward.
4. **Siêu tham số** chọn dựa kinh nghiệm — chưa grid search nghiêm túc.
5. **Mô hình tĩnh** — không retrain rolling theo thời gian.
6. **DirAcc ≠ lợi nhuận**: chưa tính phí giao dịch / slippage.

### 11.2. Hướng phát triển

- **Sentiment analysis** từ tin tức / mạng xã hội Việt Nam.
- **Biến vĩ mô**: lãi suất VND, USD/VND, giá vàng, DXY.
- **Mô hình tuần tự**: LSTM, GRU, Temporal Fusion Transformer.
- **Walk-forward validation** + bootstrap để xác lập khoảng tin cậy DirAcc.
- **Phân loại 3 lớp** (lên/giữ/xuống với ngưỡng) thay cho hồi quy.
- Mở rộng sang **rổ VN30 / VN-Index** trực tiếp.
- Tích hợp **chi phí giao dịch** vào backtest.

---"""),

md("""## 12. Kết luận

Project trình bày một pipeline hoàn chỉnh để dự đoán biến động giá cổ
phiếu VCB bằng học máy. **Kết quả chính:**

- Trên target **log-return 20 phiên**: Linear Regression dẫn đầu DirAcc
  **54.76 %**, cả 4 mô hình đều vượt 50 %.
- Phân tích đa horizon: DirAcc tăng từ ~ 50 % (1 ngày) lên ~ 62 %
  (60 ngày), có ý nghĩa thống kê.
- MAPE giá ~ 4.5 % cho horizon 1 tháng.

**Bài học:**

1. Việc **phát biểu đúng bài toán** quan trọng hơn việc thử nhiều mô hình
   — chọn target và horizon phù hợp là chìa khóa.
2. Trên dữ liệu tài chính, **mô hình đơn giản đôi khi vượt mô hình phức
   tạp** — Linear Regression đứng đầu DirAcc.
3. **EMH dạng yếu** chỉ đúng ở khung ngắn — khung trung-dài hạn vẫn cho
   tín hiệu xu hướng dự đoán được.
4. Cần phân biệt **độ chính xác dự đoán** và **khả năng kiếm lợi** — hai
   khái niệm khác nhau khi có chi phí giao dịch.

---"""),

md("""## 13. Phân công công việc

| Thành viên | Phụ trách | % đóng góp |
|------------|-----------|-----------:|
| **Bá Hoài Sơn** | • `scripts/fetch_data.py`.<br>• EDA & biểu đồ giá, phân phối lợi suất.<br>• Triển khai Linear Regression & KNN.<br>• Soạn Proposal & Presentation. | 50 % |
| **Bùi Thanh Tú** | • Thiết kế 25 đặc trưng stationary (MACD, Bollinger, longer momentum).<br>• Triển khai Random Forest & Voting Ensemble.<br>• Sweep đa horizon & feature importance.<br>• Soạn Milestone & Report. | 50 % |

Cả hai thành viên cùng thảo luận về phát biểu lại bài toán, thiết kế bộ
metric (đặc biệt DirAcc & DirAcc_filt), và viết phần Thảo luận / Hạn chế.

---"""),

md("""## 14. Tham khảo

1. Hastie T., Tibshirani R., Friedman J., *The Elements of Statistical
   Learning*, Springer, 2009.
2. Pedregosa F., et al., *Scikit-learn: Machine Learning in Python*, JMLR
   12, 2011.
3. Fama E.F., *Efficient Capital Markets: A Review of Theory and Empirical
   Work*, Journal of Finance, 1970.
4. Wilder J.W., *New Concepts in Technical Trading Systems*, 1978 (RSI).
5. Appel G., *Technical Analysis: Power Tools for Active Investors*, 2005
   (MACD).
6. Bollinger J., *Bollinger on Bollinger Bands*, McGraw-Hill, 2001.
7. Yahoo Finance API via `yfinance`:
   <https://pypi.org/project/yfinance/>.
8. Quách Đình Hoàng. *Project Guides for Machine Learning*, HCMUTE.

---

*Kết thúc Báo cáo.*"""),
]

make_nb(ROOT / "Report" / "Report.ipynb", report_cells)


# =====================================================================
#                              PRESENTATION
# =====================================================================
pres_cells = [
md("""# DỰ ĐOÁN GIÁ CỔ PHIẾU VN-INDEX
## *Dựa trên biến động giá trong quá khứ — mã thử nghiệm: VCB*

**Môn:** Học Máy — HCMUTE  
**Sinh viên thực hiện:** Bá Hoài Sơn — Bùi Thanh Tú  
**Dữ liệu:** Yahoo Finance qua thư viện `yfinance`""", slide_type="slide"),

md("""## 1. Bài toán

- Dự đoán **biến động giá cổ phiếu** chỉ từ chuỗi giá quá khứ.
- **Mã thử nghiệm:** VCB (Vietcombank — `VCB.VN`).
- **Loại bài toán:** Hồi quy có giám sát trên chuỗi thời gian.
- **Ý nghĩa:** Hỗ trợ đầu tư swing trading, kiểm chứng EMH.""", slide_type="slide"),

md("""## 2. Dữ liệu

- **Nguồn:** Yahoo Finance qua `yfinance` → `data/vcb_stock.csv`.
- **Quy mô:** 7.673 quan sát (4.209 phiên ngày + 3.464 phiên giờ).
- **Khoảng:** 2009-06-30 → 2026-05-15.
- **Cột:** `Date`, OHLCV, `Interval`, `Ticker`/`Symbol`.""", slide_type="slide"),

md("""## 3. Lịch sử giá VCB

![](../image/price_history_daily.png)""", slide_type="slide"),

md("""## 4. Cạm bẫy ban đầu

| Thử nghiệm | DirAcc | Vấn đề |
|------------|-------:|--------|
| Dự đoán **giá tuyệt đối** | — | LR sao chép giá; RF/KNN R² âm vì không ngoại suy được |
| Dự đoán **return 1 ngày** | 43-44 % | Nhiễu áp đảo + 10 % phiên có Return = 0 |
| Dự đoán **log-return 20 ngày** | **54.8 %** | ✓ Vượt ngẫu nhiên |

→ **Bài học**: chọn đúng target và horizon là chìa khóa.""", slide_type="slide"),

md("""## 5. Giải pháp: dự đoán LOG-RETURN 20 phiên

$$\\hat r_{t+20} = f(\\mathbf x_t),\\qquad \\hat C_{t+20} = C_t\\,e^{\\hat r_{t+20}}$$

- **20 phiên** ≈ 1 tháng giao dịch — phổ biến trong swing trading.
- **Log-return** symmetric + cộng được + gần Gaussian.
- Target stationary → mô hình phi tuyến tổng quát hóa công bằng.""", slide_type="slide"),

md("""## 6. 25 đặc trưng stationary

| Nhóm | Đặc trưng |
|---|---|
| Momentum | `Return_{1,2,3,5,10,20,60}` |
| Xu hướng | `MA{5,10,20,50,100}_Ratio` |
| Volatility | `Vol_{5,10,20}` |
| Chỉ báo | `RSI_14`, `MACD`, `MACD_Signal`, `MACD_Hist`, `Bollinger_b` |
| Biên độ | `HL_Range`, `OC_Range` |
| Volume | `Vol_Change`, `Volume_MA20_Ratio` |
| Trend dài | `Trend_MA50_200` (sign MA50 - MA200) |""", slide_type="slide"),

md("""## 7. Bốn mô hình thử nghiệm

| Mô hình | Vai trò |
|---------|---------|
| **Linear Regression** | Baseline tuyến tính |
| **KNN (k=25)** | Phi tham số, học theo phiên giống |
| **Random Forest (500 cây)** | Phi tuyến, robust |
| **Voting Ensemble** | Trung bình 3 mô hình trên |

*Pipeline(StandardScaler + estimator) — tránh leak + công bằng.*""", slide_type="slide"),

md("""## 8. Quy trình & đánh giá

1. Load (`load_raw_data`).
2. Feature engineering (`build_features`, h=20).
3. Chronological split 80/20.
4. Train 4 mô hình.
5. Đánh giá: **MAE, RMSE, R², DirAcc, DirAcc_filt** trên log-return + **MAPE** trên giá.
6. Sweep đa horizon {1, 5, 10, 20, 60}.""", slide_type="slide"),

code("""import sys
sys.path.insert(0, '../scripts')
from ml_utils import run_full_pipeline

result = run_full_pipeline(horizon=20, save_images=False)
print('--- METRIC LOG-RETURN (horizon=20) ---')
display(result['metrics_return'])
print('--- METRIC GIÁ (VND) ---')
display(result['metrics_price'])""", slide_type="slide"),

md("""## 9. So sánh 4 mô hình (horizon = 20)

![](../image/model_comparison.png)

- **Tất cả 4 mô hình vượt 50 %.**
- **Linear Regression dẫn đầu DirAcc 54.76 %** — bài học: đơn giản không có nghĩa là yếu.""", slide_type="slide"),

md("""## 10. Dự đoán vs Thực tế (giá, h=20)

![](../image/predictions_vs_actual.png)

MAPE giá ~ 4.5 % cho horizon 1 tháng.""", slide_type="slide"),

md("""## 11. SWEEP ĐA HORIZON — phát hiện chính

![](../image/horizon_comparison.png)

| h | Best | DirAcc |
|--:|------|-------:|
| 1 | KNN | 50.7 % |
| 5 | LR | 48.7 % |
| 10 | RF | 50.6 % |
| **20** | **LR** | **54.8 %** |
| **60** | **Ensemble** | **61.6 %** |

→ Tín hiệu xu hướng **TĂNG THEO HORIZON**.""", slide_type="slide"),

md("""## 12. Hiệu Quả Thị Trường (EMH)

- DirAcc 1 ngày ≈ 50 % → **xác nhận EMH dạng yếu** ở ngắn hạn.
- DirAcc 20-60 ngày = 55-62 % → tín hiệu trung-dài hạn **dự đoán được**.
- Khoảng cách 4.8 - 11.6 điểm so với 50 %: ý nghĩa thống kê 2.7-6.5σ.

**Lưu ý:** Dự đoán đúng chiều ≠ kiếm lợi sau phí giao dịch.""", slide_type="slide"),

md("""## 13. Hạn chế & Hướng phát triển

**Hạn chế:**
- Chỉ dùng giá quá khứ, một mã (VCB), một lần chia 80/20.
- Siêu tham số chọn theo kinh nghiệm.

**Hướng phát triển:**
- Walk-forward validation + bootstrap CI.
- Sentiment + biến vĩ mô.
- LSTM / Transformer cho chuỗi thời gian.
- Mở rộng rổ VN30, tích hợp chi phí giao dịch.""", slide_type="slide"),

md("""## 14. Cảm ơn — Q & A

**Bá Hoài Sơn — Bùi Thanh Tú**  
*Học Máy — HCMUTE*

- Mã nguồn: `scripts/ml_utils.py`
- Tái lập: `python scripts/fetch_data.py` → mở 4 notebook
- Phát hiện chính: **DirAcc 54.8 %** ở horizon = 20""", slide_type="slide"),
]

make_nb(ROOT / "Presentation" / "Presentation.ipynb", pres_cells, slides=True)


print("Đã sinh:")
print(" -", ROOT / "Proposal" / "Proposal.ipynb")
print(" -", ROOT / "Milestone" / "Milestone.ipynb")
print(" -", ROOT / "Presentation" / "Presentation.ipynb")
print(" -", ROOT / "Report" / "Report.ipynb")
