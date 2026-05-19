# KỊCH BẢN THUYẾT TRÌNH (10 PHÚT)

**Đề tài:** Dự đoán giá cổ phiếu VN-Index dựa trên biến động giá trong quá khứ
**Môn:** Học Máy — HCMUTE
**Trình bày:** Bá Hoài Sơn (S) & Bùi Thanh Tú (T)

> **Cách dùng file này:**
> 1. Mở `Presentation/Presentation.html` (slides Reveal) ở một nửa màn hình.
> 2. Mở `Script.md` (file này) ở nửa còn lại hoặc in ra.
> 3. Mỗi slide có:
>    - **[Người nói] (thời gian gợi ý)** — ai nói, dài bao lâu.
>    - **Lời thoại** — đoạn nói tự nhiên, dùng được luôn.
>    - **Điểm nhấn / Thuật ngữ** — giải thích cho người mới.
>    - **Có thể bị hỏi** — câu hỏi giám khảo hay đặt + gợi ý trả lời.
> 4. Đánh dấu chuyển slide bằng `→` ở đầu mỗi đoạn.

**Tổng thời gian dự kiến:** 9 phút 30 giây – 10 phút (chừa ~1 phút phòng hờ cho Q&A).

---

## SLIDE 1 — Trang tiêu đề (30 giây) — **[S]**

> → Bấm slide đầu, đứng giữa, mỉm cười, nhìn lớp.

**Lời thoại:**

"Em xin kính chào thầy/cô và các bạn. Em là **Bá Hoài Sơn**, đây là bạn **Bùi Thanh Tú**, cùng một nhóm thực hiện đề tài *Dự đoán giá cổ phiếu VN-Index dựa trên biến động giá trong quá khứ*. Chúng em sử dụng cổ phiếu **VCB — Vietcombank** làm mã thử nghiệm. Dữ liệu được nhóm thu thập tự động từ Yahoo Finance qua thư viện Python tên là `yfinance`. Bây giờ em xin bắt đầu phần trình bày."

**Điểm nhấn:** đọc đúng *yfinance* (đọc: y-finance).

---

## SLIDE 2 — Bài toán (40 giây) — **[S]**

> → Chuyển sang slide 2.

**Lời thoại:**

"Câu hỏi nhóm muốn trả lời rất đơn giản: **liệu chỉ từ chuỗi giá quá khứ, mình có thể đoán được biến động giá cổ phiếu trong tương lai hay không?**

Đây là một bài toán **hồi quy có giám sát**, nghĩa là:
- *Hồi quy* — dự đoán một con số liên tục (giá hoặc lợi suất), không phải nhãn lớp.
- *Có giám sát* — khi huấn luyện, mô hình có sẵn câu trả lời đúng để học theo.

Nhóm chọn VCB vì đây là một trong những cổ phiếu vốn hóa lớn nhất Việt Nam, thanh khoản cao, có ảnh hưởng đáng kể tới chỉ số VN-Index. Đề tài có ý nghĩa thực tiễn cho nhà đầu tư swing trading, và cũng là cơ hội để kiểm chứng một giả thuyết kinh điển trong tài chính gọi là **Hiệu Quả Thị Trường — EMH**, em sẽ nói kỹ ở cuối bài."

**Giải thích thuật ngữ:**
- **Hồi quy (regression)** = dự đoán con số.
- **Có giám sát (supervised)** = có dữ liệu đã biết kết quả đúng.
- **Swing trading** = chiến lược giữ cổ phiếu vài tuần tới vài tháng, không phải lướt sóng từng ngày.

---

## SLIDE 3 — Dữ liệu (40 giây) — **[S]**

> → Chuyển sang slide 3.

**Lời thoại:**

"Về dữ liệu: nhóm dùng thư viện `yfinance` — một wrapper Python miễn phí của Yahoo Finance — để tải toàn bộ lịch sử giao dịch của mã `VCB.VN`. Kết quả lưu vào file `data/vcb_stock.csv`.

Tổng cộng có **7.673 quan sát**, trong đó **4.209 phiên theo ngày** từ ngày 30 tháng 6 năm 2009 cho tới giữa tháng 5 năm 2026. Mỗi dòng gồm 8 cột chính: ngày, giá mở cửa, cao nhất, thấp nhất, đóng cửa, khối lượng, khung thời gian, và mã chứng khoán. Bộ dữ liệu thỏa các yêu cầu môn học về số lượng và đa dạng kiểu biến."

**Thuật ngữ ngắn:** *OHLCV* = Open–High–Low–Close–Volume, bộ năm con số cơ bản mô tả một phiên giao dịch.

---

## SLIDE 4 — Lịch sử giá VCB (40 giây) — **[S]**

> → Chuyển sang slide 4 — slide có **biểu đồ giá**.

**Lời thoại:**

"Đây là biểu đồ giá đóng cửa của VCB từ 2009 đến nay, kèm khối lượng giao dịch ở dưới.

Có ba điều đáng chú ý:
1. **Xu hướng tăng dài hạn rõ rệt** — giá đã nhân lên nhiều lần kể từ ngày niêm yết.
2. **Các nhịp điều chỉnh sâu** — năm 2018, năm 2020 lúc COVID, và năm 2022.
3. **Khối lượng giao dịch bùng nổ sau 2017** khi thị trường Việt Nam phát triển hơn.

Chính cái xu hướng tăng dài hạn này sẽ là **vấn đề** mà em sẽ nói ở slide tiếp theo — nó khiến cách tiếp cận ngây thơ ban đầu của nhóm bị sai."

> **[Chuyển micro cho Tú]**: "Bây giờ em xin mời bạn Tú trình bày phần phương pháp luận."

---

## SLIDE 5 — Cạm bẫy ban đầu (75 giây) — **[T]**

> → Tú chuyển sang slide 5. **Đây là slide quan trọng nhất** — nên nói chậm.

**Lời thoại:**

"Em là Bùi Thanh Tú. Trên bảng các bạn thấy, nhóm em đã đi qua **ba phiên bản** trước khi đạt kết quả hiện tại.

**Phiên bản 1**: dự đoán giá tuyệt đối — cho mô hình đọc giá hôm nay rồi yêu cầu đoán giá ngày mai. Linear Regression đạt R² = 0.96 nghe có vẻ rất tốt, nhưng phân tích kỹ thì hệ số trên giá hôm nay xấp xỉ 1.0 — tức là mô hình chỉ **sao chép giá hôm nay sang ngày mai**, không thực sự dự đoán gì cả. Còn Random Forest và KNN thì R² âm vì không thể **ngoại suy** ngoài miền giá đã thấy trong tập huấn luyện (do cổ phiếu có xu hướng tăng).

**Phiên bản 2**: chuyển sang dự đoán lợi suất ngày kế tiếp — tức tỉ lệ phần trăm thay đổi giá. Tốt hơn rồi, nhưng DirAcc chỉ đạt 43-44 % — **dưới mức ngẫu nhiên 50 %**. Nguyên nhân: khoảng 10 % phiên VCB có giá đóng cửa không đổi giữa hai ngày, làm mô hình mất điểm DirAcc oan; và tín hiệu ngắn hạn 1 ngày bị **nhiễu áp đảo**.

**Phiên bản 3 — phiên bản hiện tại**: nhóm chuyển sang dự đoán **log-return 20 phiên tới**, tức biến động giá sau khoảng 1 tháng giao dịch. DirAcc đạt **54.8 %**, vượt 50 % rõ ràng. Đây là phát hiện quan trọng của project.

→ **Bài học**: chọn đúng *target* và *horizon* là chìa khóa, quan trọng hơn việc thử thật nhiều mô hình."

**Giải thích thuật ngữ:**
- **R²** = hệ số xác định, càng gần 1 càng tốt; âm = tệ hơn baseline ngẫu nhiên.
- **Ngoại suy (extrapolation)** = đoán ngoài khoảng giá trị đã học.
- **DirAcc** = Direction Accuracy = tỉ lệ đoán đúng chiều (lên/xuống) của lợi suất.
- **Horizon** = khung dự đoán, tức "mấy phiên về phía trước".

**Có thể bị hỏi:** *Vì sao DirAcc 1 ngày dưới 50 %?* → Trả lời: ngoài lý do nhiễu, còn vì cách `np.sign(0)` xử lý các phiên không đổi; thêm nữa các features ngắn hạn (Return_1) có hiệu ứng *mean reversion* nhẹ, dễ dẫn mô hình đến dự đoán ngược dấu.

---

## SLIDE 6 — Giải pháp: log-return 20 phiên (50 giây) — **[T]**

> → Chuyển sang slide 6.

**Lời thoại:**

"Vì sao chọn **horizon = 20 phiên**?

- **20 phiên giao dịch ≈ 1 tháng dương lịch** — đây là khung phổ biến trong chiến lược *swing trading*, và là khung mà các quỹ thực sự rebalance danh mục.
- **Lợi suất 20 ngày smooth hơn 1 ngày** — nhiễu nhất thời (tin tức trong ngày) được trung bình hóa.
- **Tín hiệu xu hướng cơ bản** (kết quả kinh doanh, dòng tiền) thường lộ ra ở khung này.

Vì sao chọn **log-return** thay vì pct_change?

- **Symmetric**: +10 % rồi -10 % của log-return là 0 (đẹp), trong khi pct_change thì không.
- **Cộng được** giữa các kỳ liên tiếp.
- **Phân phối gần Gaussian hơn**, phù hợp với giả định nhiều mô hình.

Sau khi đoán được log-return, ta khôi phục giá dễ dàng: $\hat{C}_{t+20} = C_t \cdot e^{\hat r}$."

**Giải thích thuật ngữ:**
- **Log-return** = $\log(C_{t+h}/C_t)$ — lợi suất logarit, "công cụ chuẩn" của tài chính định lượng.
- **Swing trading** = nắm giữ vài tuần tới vài tháng.

---

## SLIDE 7 — 25 đặc trưng stationary (60 giây) — **[T]**

> → Chuyển sang slide 7.

**Lời thoại:**

"Đầu vào của mô hình là 25 đặc trưng kỹ thuật, được thiết kế đều **stationary** — tức phân phối không đổi theo thời gian. Chia 7 nhóm:

1. **Momentum** — lợi suất quá khứ 1, 2, 3, 5, 10, 20, 60 phiên. Đo *động lượng* đa khung.
2. **Xu hướng** — tỷ lệ giá hiện tại so với 5 đường trung bình động (5, 10, 20, 50, 100 phiên).
3. **Volatility** — độ lệch chuẩn của lợi suất ngày trong 5/10/20 phiên gần nhất.
4. **Chỉ báo kỹ thuật cổ điển** — **RSI 14**, **MACD** (Moving Average Convergence Divergence), **Bollinger %b** — đo trạng thái quá mua / quá bán và lực đảo chiều.
5. **Biên độ trong phiên** — High-Low và Close-Open chia cho giá.
6. **Khối lượng** — phần trăm thay đổi volume.
7. **Trend dài hạn** — dấu của hiệu (MA50 - MA200), đây là tín hiệu *golden cross / death cross* nổi tiếng trong phân tích kỹ thuật.

Tất cả 25 đặc trưng đều stationary, không phụ thuộc mức giá tuyệt đối → các mô hình phi tuyến mới có thể tổng quát hóa công bằng."

**Giải thích thuật ngữ ngắn:**
- **Stationary** = "tĩnh" — phân phối thống kê không đổi theo thời gian.
- **MA (Moving Average)** = đường trung bình động.
- **RSI** = chỉ số sức mạnh tương đối, giá trị 0-100, > 70 quá mua, < 30 quá bán.
- **MACD** = hiệu của 2 EMA (12, 26) — đo động lực xu hướng.
- **Bollinger %b** = vị trí giá trong dải Bollinger (MA ± 2σ), 0-1 là trong dải.
- **Golden cross** = MA50 cắt lên trên MA200, tín hiệu mua dài hạn.

---

## SLIDE 8 — Bốn mô hình (60 giây) — **[T]**

> → Chuyển sang slide 8.

**Lời thoại:**

"Nhóm thử **4 mô hình** để so sánh:

**1. Linear Regression** — hồi quy tuyến tính. Tìm một siêu phẳng trong không gian 25 chiều khớp tốt nhất với dữ liệu. Ưu điểm: nhanh, dễ giải thích, là *baseline* — mốc cơ sở.

**2. K-Nearest Neighbors với k = 25**. Khi cần đoán một phiên mới, mô hình tìm 25 phiên gần giống nhất trong lịch sử — đo bằng khoảng cách Euclidean trên 25 đặc trưng đã chuẩn hóa — rồi lấy trung bình lợi suất. Phi tham số, không cần giả định gì.

**3. Random Forest với 500 cây quyết định**, mỗi cây học trên một mẫu ngẫu nhiên của dữ liệu, độ sâu tối đa 6, tối thiểu 20 mẫu/lá. Cấu hình "nông" này để hạn chế overfit do dữ liệu tài chính có nhiều nhiễu. Phương pháp này gọi là **bagging**.

**4. Voting Ensemble** — kết hợp ba mô hình trên bằng trung bình đơn giản. Ý tưởng *"ba cái đầu khôn hơn một"*.

Tất cả bọc trong **Pipeline** cùng **StandardScaler** — đưa mọi đặc trưng về cùng thang đo, đảm bảo KNN và LR (nhạy với thang đo) hoạt động đúng, và tránh data leakage qua bước chuẩn hóa."

**Giải thích thuật ngữ:**
- **Bagging** = Bootstrap Aggregating — huấn luyện nhiều mô hình trên các mẫu khác nhau rồi tổng hợp.
- **Overfit** = học thuộc lòng tập train, làm việc tệ trên dữ liệu mới.
- **Data leakage** = thông tin tương lai vô tình lọt vào quá trình huấn luyện.

---

## SLIDE 9 — Pipeline & đánh giá (30 giây) — **[T]**

> → Slide 9.

**Lời thoại:**

"Quy trình 6 bước:
1. Load dữ liệu.
2. Sinh 25 đặc trưng, target = log-return 20 phiên.
3. **Chia train/test theo trật tự thời gian** 80/20, **không xáo trộn** — để tránh leak thông tin tương lai vào lúc học.
4. Huấn luyện 4 mô hình.
5. Đánh giá bằng **MAE, RMSE, R²** trên log-return, **DirAcc** đo tỉ lệ đoán đúng chiều, và **MAPE** trên giá VND.
6. Cuối cùng là sweep đa horizon từ 1 đến 60 phiên.

Bây giờ em mời lại bạn Sơn công bố kết quả."

---

## SLIDE 10 — Kết quả số (30 giây) — **[S]**

> → Sơn quay lại, chỉ vào bảng kết quả trên slide 10 (có 2 bảng: log-return + giá VND).

**Lời thoại:**

"Đây là bảng kết quả cuối cùng trên 798 phiên test (xấp xỉ 3 năm gần nhất).

Trên miền **log-return horizon 20**: **Linear Regression dẫn đầu DirAcc 54.76 %**, Random Forest 52.38 %, Ensemble 52.76 %, KNN 50.88 %. **Cả 4 mô hình đều vượt mức ngẫu nhiên 50 %.**

Trên miền **giá VND**: MAE của Random Forest là 2.715 đồng cho horizon 1 tháng, MAPE 4.47 %. Tức là sai số trung bình chưa tới 5 % giá thật sau 20 phiên."

---

## SLIDE 11 — So sánh 4 mô hình (45 giây) — **[S]**

> → Slide 11 — biểu đồ cột so sánh, có đường ngang đỏ ở 50 %.

**Lời thoại:**

"Ở các biểu đồ cột DirAcc, đường ngang **màu đỏ đứt nét là mốc ngẫu nhiên 50 %**. Có thể thấy cả 4 mô hình đều vượt lên trên.

Ba phát hiện chính:

1. **Linear Regression dẫn đầu**, chứ không phải Random Forest. Đây là một bài học: **mô hình đơn giản không phải lúc nào cũng yếu**. Khi mối quan hệ giữa đặc trưng dài hạn (Return_60, MA100_Ratio, MACD) và target gần như tuyến tính, LR khai thác hiệu quả mà không bị overfit nhiễu như RF/KNN.

2. **KNN xếp cuối**. Lý do là *curse of dimensionality* — **lời nguyền chiều cao**: trong không gian 25 chiều, khái niệm "phiên gần giống" trở nên ít ý nghĩa vì mọi điểm gần như cách nhau bằng nhau.

3. **Ensemble không vượt được Linear Regression đơn lẻ** — bị KNN kéo xuống. Trung bình đơn giản chỉ có lợi khi *các thành viên đều đủ tốt và sai theo các hướng khác nhau*."

**Thuật ngữ:** *Curse of dimensionality* = lời nguyền chiều cao, hiện tượng thuật toán dựa khoảng cách hoạt động kém khi số chiều lớn.

---

## SLIDE 12 — Dự đoán vs Thực tế (30 giây) — **[S]**

> → Slide 12 — biểu đồ giá thực và 4 đường dự đoán.

**Lời thoại:**

"Đường đen là giá thật sau 20 phiên trên tập test. Bốn đường màu là dự đoán từ 4 mô hình. Cả bốn đường bám khá sát giá thật — MAPE chỉ ~ 4.5 %. Tuy nhiên các bạn để ý: ở các nhịp đảo chiều mạnh năm 2022 và đầu 2024, mô hình bị trễ — đây là hạn chế cố hữu của việc chỉ dùng giá quá khứ, không có thông tin về tin tức."

> **[Chuyển micro cho Tú]**: "Em mời bạn Tú trình bày phân tích đa horizon — phần thú vị nhất của project."

---

## SLIDE 13 — SWEEP ĐA HORIZON (75 giây) — **[T]**

> → Slide 13 — biểu đồ DirAcc theo horizon (đường đi lên rõ).

**Lời thoại:**

"Đây là **phát hiện chính của project**, được trình bày trên một biểu đồ duy nhất.

Trục hoành là **horizon** — số phiên dự đoán về phía trước. Trục tung là DirAcc. Đường đỏ đứt nét là mốc ngẫu nhiên 50 %. Bốn đường màu là 4 mô hình.

Quan sát:

- **Horizon 1 ngày**: tất cả ngấp nghé 50 % — **xác nhận EMH dạng yếu** ở khung ngắn.
- **Horizon 5 ngày**: tệ hơn — vùng nhiễu nặng nhất.
- **Horizon 10 ngày**: bắt đầu nhú lên trên 50 %.
- **Horizon 20 ngày**: LR đạt **54.76 %**.
- **Horizon 60 ngày**: Ensemble đạt **61.65 %**, LR 61.14 %.

→ **Tín hiệu xu hướng tăng theo horizon.**

**Diễn giải vật lý**: giá cổ phiếu chịu hai loại tác động — **xu hướng cơ bản** (kinh tế vĩ mô, kết quả kinh doanh) và **nhiễu ngắn hạn** (tin tức nhất thời, giao dịch thuật toán). Ở khung ngắn, nhiễu áp đảo nên khó dự đoán. Ở khung dài, nhiễu được trung bình hóa nên xu hướng cơ bản lộ ra rõ.

**Ý nghĩa thống kê**: trên 800 mẫu test, sai số chuẩn quanh 50 % là khoảng 1.77 %. 54.8 % cách 50 % là **2.7 σ** — có ý nghĩa. 61.6 % cách 50 % là **6.5 σ** — rất có ý nghĩa."

**Giải thích thuật ngữ:**
- **Sigma (σ)** = đơn vị độ lệch chuẩn. Trong thống kê, kết quả cách trung bình từ 2σ trở lên thường được coi là "có ý nghĩa thống kê".
- **EMH dạng yếu** = giả thuyết: giá hiện tại đã phản ánh hết thông tin lịch sử về giá.

---

## SLIDE 14 — EMH (45 giây) — **[T]**

> → Slide 14.

**Lời thoại:**

"Phát hiện đa horizon dẫn tới một thảo luận thú vị về **Hiệu Quả Thị Trường — EMH**, lý thuyết của Eugene Fama (Nobel Kinh tế 2013).

Dạng yếu của EMH phát biểu: *giá hiện tại đã phản ánh toàn bộ thông tin lịch sử về giá; do đó không thể kiếm lợi nhuận vượt trội chỉ bằng phân tích chuỗi giá*.

Kết quả của nhóm:
- Ở horizon 1 ngày: DirAcc ~ 50 % → **xác nhận** EMH dạng yếu.
- Ở horizon 20-60 ngày: DirAcc 55-62 % → **dường như mâu thuẫn** với EMH.

Lý giải hòa hợp: EMH thực ra nói về *khả năng kiếm lợi nhuận sau chi phí giao dịch*, không phải về độ chính xác dự đoán tuyệt đối. **55-62 % accuracy, sau khi trừ phí giao dịch, spread, slippage, và chi phí cơ hội, có thể KHÔNG đủ để thắng thị trường ổn định**. Đặc biệt với một mã đơn lẻ — chưa phải danh mục đa dạng."

---

## SLIDE 15 — Hạn chế & hướng phát triển (40 giây) — **[T]**

> → Slide 15.

**Lời thoại:**

"Nhóm thẳng thắn nhận các hạn chế:
- Chỉ dùng **giá quá khứ**, không có tin tức, không có thông tin cơ bản như P/E, doanh thu, không có dòng tiền khối ngoại.
- Chỉ thử **một mã VCB**, một lần chia 80/20.
- Siêu tham số chọn theo kinh nghiệm, chưa qua grid search nghiêm túc.

Hướng phát triển nếu có thời gian:
- **Walk-forward validation** + bootstrap để xác lập khoảng tin cậy DirAcc.
- Bổ sung **phân tích cảm xúc** từ tin tức và biến vĩ mô (lãi suất, USD/VND).
- Thử **LSTM hoặc Transformer** chuyên cho chuỗi thời gian.
- Mở rộng sang rổ **VN30** và tích hợp **chi phí giao dịch** vào backtest."

**Thuật ngữ:**
- **Walk-forward validation** = chia train/test trượt theo thời gian, đánh giá nhiều lần.
- **LSTM** = Long Short-Term Memory, mạng nơ-ron chuyên xử lý chuỗi thời gian.

---

## SLIDE 16 — Cảm ơn & Q&A (15 giây) — **[S + T cùng nói]**

> → Slide cuối. Hai bạn cùng đứng.

**Lời thoại (Sơn nói trước):**

"Đó là toàn bộ phần trình bày của nhóm em. Tóm tắt một câu: với horizon **20 phiên**, mô hình của nhóm đạt **DirAcc 54.76 %**, vượt mức ngẫu nhiên với ý nghĩa thống kê. Mã nguồn được tổ chức gọn trong `scripts/ml_utils.py` và có thể tái lập đầy đủ.

**Em xin cảm ơn thầy/cô và các bạn đã lắng nghe. Chúng em rất sẵn sàng nhận câu hỏi.**"

---

## NGÂN HÀNG CÂU HỎI Q&A (chuẩn bị trước)

| # | Câu hỏi | Người trả lời | Gợi ý đáp án |
|---|---------|---------------|--------------|
| 1 | *Vì sao chọn VCB mà không phải mã khác?* | S | Thanh khoản cao, niêm yết lâu, vốn hóa lớn → đại diện tốt cho VN-Index nhóm ngân hàng. |
| 2 | *Vì sao chọn horizon = 20 mà không phải 5 hay 10?* | T | Sweep đa horizon cho thấy DirAcc vượt 50 % rõ rệt từ horizon = 20 trở đi. 20 phiên ≈ 1 tháng giao dịch — phổ biến trong swing trading. |
| 3 | *RSI / MACD / Bollinger là gì?* | T | • RSI 14 = chỉ số động lượng 0-100, > 70 quá mua < 30 quá bán.<br>• MACD = hiệu EMA12 - EMA26, đường tín hiệu EMA9.<br>• Bollinger %b = vị trí giá trong dải MA ± 2σ. |
| 4 | *Vì sao chia train/test theo thời gian, không random?* | T | Tránh **data leakage** — nếu shuffle, mô hình thấy "tương lai" lúc huấn luyện. Chia chronological phản ánh đúng kịch bản triển khai. |
| 5 | *Random Forest có overfit không?* | T | Đã giới hạn `max_depth=6` và `min_samples_leaf=20` để buộc cây không học thuộc nhiễu, cộng với 500 cây + bootstrap giảm phương sai. |
| 6 | *Tại sao Linear Regression vượt Random Forest?* | T | Đặc trưng dài hạn (Return_60, MA100_Ratio, MACD) cùng dấu với target một cách gần tuyến tính → LR khai thác hiệu quả mà không bị overfit nhiễu như RF. Bài học: mô hình phức tạp không phải luôn tốt hơn. |
| 7 | *Mô hình có dùng để đầu tư thực được không?* | S | Không nên trực tiếp. 54.8 % DirAcc sau khi trừ phí giao dịch, spread, slippage có thể không đủ thắng thị trường. Cần thêm risk management và position sizing. |
| 8 | *MAPE 4.5 % có ý nghĩa thực tế không?* | S | Trên giá ~80.000 VND, 4.5 % là ~3.600 VND cho horizon 1 tháng. Đây là sai số chấp nhận được nhưng không đột phá — biên độ biến động bình thường của cổ phiếu trong 1 tháng cũng cỡ này. |
| 9 | *Vì sao không dùng LSTM / Transformer?* | T | Project tập trung vào các mô hình cổ điển của môn Học Máy. LSTM/Transformer là hướng phát triển ở slide hạn chế. Với ~4.000 quan sát thì các mô hình deep cũng khó vượt RF. |
| 10 | *DirAcc dưới 50 % ở 1 ngày có vô lý không?* | T | Không vô lý: thị trường có nhiều phiên giảm hơn tăng nhẹ (45-46 % phiên lên), thêm ~10 % phiên có Return = 0 → cộng với hiệu ứng mean-reversion nhẹ, mô hình hay dự đoán ngược dấu. Đây là một quan sát thú vị. |
| 11 | *Ý nghĩa thống kê của 54.8 % là gì?* | T | Trên 798 mẫu test, sai số chuẩn dưới giả thiết 50 % là 1.77 %. 54.8 % cách 50 % là 2.7σ — vượt ngưỡng 2σ thông thường để khẳng định có ý nghĩa. |
| 12 | *Có sử dụng GPU không?* | T | Không cần GPU. Pipeline đầy đủ (load + 25 đặc trưng + train 4 mô hình + sweep 5 horizons + plot) chạy trên CPU laptop ~ 90 giây. |

---

## CHECKLIST TRƯỚC KHI THUYẾT TRÌNH

- [ ] Mở sẵn `Presentation/Presentation.html` ở chế độ full-screen (Reveal.js: bấm `F`).
- [ ] Mở sẵn `Report/Report.html` ở tab khác — phòng khi giám khảo hỏi chi tiết.
- [ ] Kiểm tra biểu đồ hiển thị đúng (folder `image/` không bị di chuyển).
- [ ] Thử chạy `python -c "import sys; sys.path.insert(0,'scripts'); from ml_utils import compare_horizons; print(compare_horizons([1,20]))"` để bảo đảm code không hỏng.
- [ ] Hai bạn tập nói thử **2 lần** trước presentation, bấm đồng hồ.
- [ ] In file `Script.md` hoặc mở trên tablet/điện thoại để liếc khi quên.

---

## TIMELINE TỔNG HỢP

| Slide | Nội dung | Người | Giây | Cộng dồn |
|------:|----------|:-----:|-----:|---------:|
| 1 | Tiêu đề | S | 30 | 0:30 |
| 2 | Bài toán | S | 40 | 1:10 |
| 3 | Dữ liệu | S | 40 | 1:50 |
| 4 | Lịch sử giá VCB | S | 40 | 2:30 |
| 5 | Cạm bẫy ban đầu | T | 75 | 3:45 |
| 6 | Giải pháp log-return 20 | T | 50 | 4:35 |
| 7 | 25 đặc trưng | T | 60 | 5:35 |
| 8 | 4 mô hình | T | 60 | 6:35 |
| 9 | Pipeline & đánh giá | T | 30 | 7:05 |
| 10 | Kết quả số | S | 30 | 7:35 |
| 11 | So sánh 4 mô hình | S | 45 | 8:20 |
| 12 | Dự đoán vs thực tế | S | 30 | 8:50 |
| 13 | Sweep đa horizon | T | 75 | 10:05 |
| 14 | EMH | T | 45 | 10:50 |
| 15 | Hạn chế | T | 40 | 11:30 |
| 16 | Q&A | S+T | 15 | 11:45 |

**Tổng dự kiến:** ~ 11 phút 45 giây — **CẦN CẮT 1-2 PHÚT** trong khi tập.

**Gợi ý cắt:**
- Slide 5 (cạm bẫy): rút phiên bản 1 còn ~ 1 câu, giữ phiên bản 2 và 3 → tiết kiệm 20 giây.
- Slide 7 (25 đặc trưng): nói tóm tắt 3 nhóm chính thay vì 7 nhóm → tiết kiệm 25 giây.
- Slide 13 (sweep horizon): bỏ phần "diễn giải vật lý", chỉ giữ phần số → tiết kiệm 25 giây.
- Slide 15 (hạn chế): nói nhanh hơn → tiết kiệm 10 giây.

**Mục tiêu sau khi cắt:** 10 phút 00 giây (chừa ~ 30 giây phòng hờ).

---

*Chúc Sơn và Tú thuyết trình thành công !*
