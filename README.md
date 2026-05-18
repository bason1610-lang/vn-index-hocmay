# Dự đoán giá cổ phiếu VN-Index dựa trên biến động giá trong quá khứ

**Môn học:** Học Máy (Machine Learning)
**Trường:** Đại học Sư phạm Kỹ thuật TP.HCM (HCMUTE)
**Sinh viên thực hiện:** Bá Hoài Sơn, Bùi Thanh Tú
**Mã thử nghiệm:** VCB (`VCB.VN` trên Yahoo Finance — Vietcombank)

## Mục tiêu

Áp dụng các kỹ thuật học máy đã học trong môn để xây dựng mô hình dự đoán
biến động giá cổ phiếu trên thị trường Việt Nam. Nhóm chọn mã VCB
(Vietcombank) làm đại diện vì thanh khoản cao và có ảnh hưởng lớn tới
chỉ số VN-Index.

Bài toán được phát biểu dưới dạng **hồi quy lợi suất kỳ kế tiếp**
(`r_{t+1} = Close_{t+1}/Close_t - 1`) thay vì dự đoán giá tuyệt đối, để các mô
hình phi tuyến có thể tổng quát hóa công bằng (xem giải thích chi tiết trong
`Report/Report.ipynb`).

## Mô hình thử nghiệm

1. **Linear Regression** — đường cơ sở tuyến tính.
2. **K-Nearest Neighbors (KNN)** — bắt mẫu cục bộ, phi tuyến.
3. **Random Forest** — ensemble cây quyết định, phi tuyến.
4. **Voting Ensemble** — kết hợp 3 mô hình trên (trung bình dự đoán).

## Cấu trúc thư mục

```
VN_Index/
├── data/                       # vcb_stock.csv + README mô tả dữ liệu
├── image/                      # các biểu đồ xuất ra
├── scripts/
│   ├── ml_utils.py             # tiện ích: load, feature, train, eval, plot
│   └── fetch_data.py           # script tải dữ liệu từ yfinance
├── Proposal/                   # Đề xuất (Proposal.ipynb + .html)
├── Milestone/                  # Tiến độ (Milestone.ipynb + .html)
├── Presentation/               # Bài thuyết trình (Presentation.ipynb + .html)
├── Report/                     # Báo cáo cuối (Report.ipynb + .html)
├── requirements.txt
└── README.md
```

## Cài đặt

```bash
pip install -r requirements.txt
```

## (Tùy chọn) Tải lại dữ liệu mới nhất từ Yahoo Finance

```bash
python scripts/fetch_data.py
```

## Chạy Notebook

Mở Jupyter và mở 4 notebook theo thứ tự gợi ý:

1. `Proposal/Proposal.ipynb`
2. `Milestone/Milestone.ipynb`
3. `Presentation/Presentation.ipynb`
4. `Report/Report.ipynb`

Hoặc xuất HTML:

```bash
jupyter nbconvert --to html Proposal/Proposal.ipynb
jupyter nbconvert --to html Milestone/Milestone.ipynb
jupyter nbconvert --to slides Presentation/Presentation.ipynb
jupyter nbconvert --to html Report/Report.ipynb
```

## Phân công

| Thành viên | Phụ trách chính |
|------------|-----------------|
| Bá Hoài Sơn | Thu thập dữ liệu, EDA, Linear Regression, KNN, Proposal, Presentation |
| Bùi Thanh Tú | Feature engineering, Random Forest, Ensemble, Milestone, Report |

## Tham chiếu

- Yahoo Finance API: <https://pypi.org/project/yfinance/>
- scikit-learn documentation: <https://scikit-learn.org/stable/>
