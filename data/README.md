# Dataset — VCB.VN

## Nguồn

Yahoo Finance, truy cập bằng thư viện [`yfinance`](https://pypi.org/project/yfinance/).

```python
import yfinance as yf
yf.download("VCB.VN", period="max", interval="1d")
```

## Mã chứng khoán

`VCB.VN` — Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank), niêm yết trên
Sở Giao dịch Chứng khoán TP.HCM (HOSE). Đây là một trong các mã có vốn hóa
lớn nhất, thanh khoản cao và có ảnh hưởng đáng kể tới chỉ số VN-Index.

## File

`vcb_stock.csv`

## Mô tả các cột

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `Date` | datetime | Ngày/giờ bắt đầu phiên giao dịch (UTC). |
| `Open` | float | Giá mở cửa của phiên (VND). |
| `High` | float | Giá cao nhất trong phiên. |
| `Low` | float | Giá thấp nhất trong phiên. |
| `Close` | float | Giá đóng cửa. |
| `Volume` | int | Khối lượng giao dịch trong phiên (số cổ phiếu). |
| `Interval` | category | Khung thời gian: `1d` (theo ngày) hoặc `1h` (theo giờ). |
| `Ticker` | str | `VCB`. |
| `Symbol` | str | `VCB.VN`. |

## Quy mô

- Tổng số dòng: **7.673**
  - `Interval = "1d"`: **4.209** phiên (từ 2009-06-30 tới 2026-05-15).
  - `Interval = "1h"`: **3.464** phiên giờ (~ 730 ngày gần nhất do giới hạn của Yahoo Finance).
- Số cột thô: **9** (sau feature engineering: thêm 14 đặc trưng và 1 biến mục tiêu).

## Ghi chú

- Dữ liệu khung 1h chỉ có sẵn cho 730 ngày gần nhất (giới hạn Yahoo Finance).
- Khi sinh đặc trưng (`build_features` trong `scripts/ml_utils.py`) các dòng
  ban đầu bị `NaN` do rolling window (~20 phiên) sẽ bị loại bỏ.
- Dữ liệu được sắp xếp theo `Date` tăng dần để bảo đảm tính chất chuỗi
  thời gian khi chia train/test (không xáo trộn).
