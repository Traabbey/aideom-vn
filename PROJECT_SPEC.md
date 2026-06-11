# THIẾT KẾ CHI TIẾT — AIDEOM-VN STREAMLIT APP
## Dựa trên dữ liệu thực tế 3 file CSV

---

## CỘT THỰC TẾ TỪNG FILE

### macro (6 dòng × 19 cột)
year, GDP_trillion_VND, GDP_billion_USD, GDP_growth_pct, GDP_per_capita_USD,
population_million, agriculture_share_pct, industry_share_pct, services_share_pct,
taxes_share_pct, agri_growth_pct, industry_growth_pct, services_growth_pct,
inflation_CPI_pct, FDI_disbursed_billion_USD, exports_billion_USD, imports_billion_USD,
digital_economy_share_GDP_pct, labor_productivity_million_VND

### regions (6 dòng × 15 cột)
region_id, region_name_vi, region_name_en, population_million, grdp_trillion_VND,
grdp_growth_pct, grdp_per_capita_million_VND, fdi_registered_billion_USD,
exports_billion_USD, digital_index_0_100, ai_readiness_0_100, trained_labor_pct,
gini_coef, rd_intensity_pct, internet_penetration_pct

### sectors (10 dòng × 13 cột)
sector_id, sector_name_vi, sector_name_en, gdp_share_2024_pct, growth_rate_2024_pct,
labor_million, labor_share_pct, export_billion_USD, digital_index_0_100,
ai_readiness_0_100, fdi_attraction_billion_USD, spillover_coef_0_1,
automation_risk_pct, rd_intensity_pct

---

## BÀI 1 — Cobb-Douglas mở rộng

### Dataset
macro (toàn bộ 6 năm 2020–2025)

### Dữ liệu dùng từ file
- Y = GDP_trillion_VND
- K proxy = GDP_trillion_VND × industry_share_pct/100 × 3 (ước vốn tích lũy)
  → THỰC TẾ: Đề bài cung cấp K riêng trong bảng 1.3: [16500,17800,19600,21300,23500,25900]
- L = labor_productivity_million_VND (proxy lao động hiệu quả) → dùng bảng đề: [53.6,50.5,51.7,52.4,52.9,53.4]
- D = digital_economy_share_GDP_pct
- AI = hard-code từ đề: [55.6,60.2,65.4,67.0,73.8,80.1] (nghìn DN số)
- H = hard-code từ đề: [24.1,26.1,26.2,27.0,28.4,29.2] (% lao động qua đào tạo)

### Input (UI controls)
- Slider α (0.1–0.6, default 0.33) — độ co giãn vốn
- Slider β (0.1–0.6, default 0.42) — độ co giãn lao động
- Slider γ (0.01–0.25, default 0.10) — độ co giãn số hóa
- Slider δ (0.01–0.20, default 0.08) — độ co giãn AI
- Slider θ (0.01–0.20, default 0.07) — độ co giãn nhân lực số
- Checkbox "Ràng buộc α+β+γ+δ+θ=1" (auto-normalize nếu tick)
- Năm dự báo mục tiêu: 2026, 2027, 2028, 2029, 2030 (multiselect)
- Kịch bản 2030: D=30%, AI=100k DN, H=35%, K tăng 6%/năm, L tăng 1%/năm, TFP tăng 1.2%/năm

### Output
- Bảng A_t (TFP) từng năm 2020–2025
- Bảng so sánh Y_thực vs Ŷ_ước lượng + sai số % từng năm
- MAPE (Mean Absolute Percentage Error)
- Phân rã tăng trưởng: đóng góp % của K, L, D, AI, H, TFP vào mỗi giai đoạn
- GDP dự báo 2026–2030 theo kịch bản

### Biểu đồ
1. Line chart: Y_thực vs Ŷ_fitted (2020–2025) + dự báo đến 2030 với CI 95%
2. Bar chart stacked: phân rã đóng góp tăng trưởng từng năm (K/L/D/AI/H/TFP)
3. Line chart: A_t theo năm — xu hướng TFP
4. Scatter: Y_thực vs Y_fitted với đường 45° (goodness of fit)

### AI Agent phân tích
- TFP tăng hay giảm → chất lượng tăng trưởng
- Nhân tố đóng góp chủ đạo vào tăng trưởng 2020–2025
- So sánh cấu trúc đóng góp với lý thuyết Solow truyền thống
- Mục tiêu 30% kinh tế số/GDP 2030 có khả thi không
- Gợi ý chính sách từ kết quả hệ số

### Chức năng web
- Slider tham số cập nhật biểu đồ real-time (st.session_state)
- Nút "Reset về mặc định đề bài"
- Nút "Chạy dự báo 2030"
- Download bảng kết quả CSV
- Expander hiển thị phương trình toán học LaTeX

---

## BÀI 2 — LP ngân sách số

### Dataset
macro — tham chiếu GDP và FDI thực tế để contextualize kết quả

### Dữ liệu dùng
Bài này dùng số liệu hard-code từ đề (không lấy từ CSV):
- 4 biến: x1(hạ tầng số), x2(AI), x3(nhân lực số), x4(R&D)
- Hệ số mục tiêu: c = [0.85, 1.20, 0.95, 1.35]
- Tham chiếu: GDP_trillion_VND 2025 = 12847.6 (macro) để tính % tác động

### Input (UI controls)
- Ngân sách tổng B: slider 80–150 nghìn tỷ VND (default 100)
- Sàn x1 ≥: slider 15–40 (default 25)
- Sàn x2 ≥: slider 10–30 (default 15)
- Sàn x3 ≥: slider 10–35 (default 20)
- Sàn x4 ≥: slider 5–20 (default 10)
- Tỷ lệ công nghệ chiến lược (x2+x4) ≥ λ×B: slider 0.25–0.50 (default 0.35)
- Checkbox "Thêm ràng buộc x3 ≥ 30 (ưu tiên nhân lực)"

### Output
- Phân bổ tối ưu x1*, x2*, x3*, x4* (nghìn tỷ VND)
- Giá trị Z* (GDP tăng thêm kỳ vọng)
- Bảng Shadow price (dual values) từng ràng buộc
- Sensitivity range cho từng hệ số mục tiêu
- Trạng thái feasibility (khả thi/không khả thi)

### Biểu đồ
1. Bar chart: phân bổ tối ưu vs sàn tối thiểu (so sánh từng hạng mục)
2. Pie chart: cơ cấu phân bổ ngân sách tối ưu
3. Line chart: Z*(B) khi B tăng từ 80→150 nghìn tỷ (sensitivity ngân sách)
4. Tornado chart: shadow price từng ràng buộc (binding vs non-binding)

### AI Agent phân tích
- Ràng buộc nào đang binding → chi phí cơ hội cao nhất
- Shadow price ngân sách: mỗi thêm 1 tỷ VND → GDP tăng bao nhiêu
- Tại sao R&D hệ số cao nhất (1.35) nhưng sàn thấp nhất (10)
- Tỷ lệ 35% công nghệ chiến lược có khả thi trong thực tế ngân sách VN không
- So sánh phân bổ tối ưu với cơ cấu chi ngân sách thực tế 2024

### Chức năng web
- Solver: radio button chọn scipy.linprog vs pulp CBC
- Bảng dual variables tương tác (highlight binding constraints màu đỏ)
- Cập nhật real-time khi thay slider
- Cảnh báo màu đỏ khi bài toán infeasible

---

## BÀI 3 — Priority ngành

### Dataset
sectors (10 ngành × 13 cột)

### Dữ liệu dùng
- growth_rate_2024_pct → tiêu chí Tăng trưởng
- gdp_share_2024_pct → đại diện Năng suất (proxy)
- spillover_coef_0_1 → tiêu chí Lan tỏa
- export_billion_USD → tiêu chí Xuất khẩu
- labor_million → tiêu chí Việc làm
- ai_readiness_0_100 → tiêu chí AI Readiness
- automation_risk_pct → tiêu chí Rủi ro (bad criterion, đảo dấu)

### Input (UI controls)
- 7 sliders trọng số a1–a7 (mặc định: 0.15,0.15,0.20,0.15,0.10,0.20,0.15)
- Auto-normalize tổng = 1 khi thay đổi
- Dropdown chọn preset: "Định hướng tăng trưởng" / "Định hướng bao trùm" / "Tùy chỉnh"
  - Tăng trưởng: a1=0.25, a2=0.20, a4=0.25, a5=0.05, a6=0.15, a7=0.10
  - Bao trùm: a3=0.25, a5=0.25, a6=0.10, a7=0.20, giảm a1&a4
- Slider sensitivity: a6 (AI Readiness) từ 0.05–0.40

### Output
- Ma trận chuẩn hóa min-max (10×7)
- Bảng Priority_i cho 10 ngành (giảm dần)
- Top-3 ngành ưu tiên được highlight
- Sensitivity: khi a6 thay đổi, top-3 thay đổi thế nào

### Biểu đồ
1. Bar chart ngang: Priority score 10 ngành (màu top-3 khác biệt)
2. Radar chart: 10 ngành × 6 tiêu chí tốt (normalized)
3. Heatmap: ma trận chuẩn hóa 10×7 (màu xanh=tốt, đỏ=kém)
4. Line chart sensitivity: Priority của top-5 ngành khi a6 từ 0.05→0.40

### AI Agent phân tích
- 3 ngành nên ưu tiên chuyển đổi số và AI trước — lý do
- Khai khoáng năng suất cao nhưng không vào top ưu tiên → tại sao
- So sánh kết quả hai bộ trọng số (Tăng trưởng vs Bao trùm) → top-3 khác nhau như thế nào
- Kết quả có phù hợp Nghị quyết 57-NQ/TW không

### Chức năng web
- Bảng điểm Priority tương tác, sortable
- Hai cột so sánh song song: trọng số A vs trọng số B
- Highlight thay đổi xếp hạng khi kéo slider

---

## BÀI 4 — LP ngành-vùng

### Dataset
sectors + regions (kết hợp)

### Dữ liệu dùng
- regions: digital_index_0_100 (D_r ban đầu), fdi_registered_billion_USD
- sectors: growth_rate_2024_pct, ai_readiness_0_100
- Bảng β_{j,r} hard-code từ đề (6 vùng × 4 hạng mục: I, D, AI, H)
- D_r ban đầu: [38,78,55,32,82,48] từ regions.digital_index_0_100

### Input (UI controls)
- Ngân sách tổng: slider 30.000–70.000 tỷ (default 50.000)
- Sàn mỗi vùng: slider 3.000–8.000 (default 5.000)
- Trần mỗi vùng: slider 10.000–15.000 (default 12.000)
- Sàn nhân lực số tổng: slider 8.000–18.000 (default 12.000)
- Tham số công bằng γ: 0.001–0.005 (default 0.002)
- Tham số λ (ngưỡng bắt kịp): 0.5–0.9 (default 0.7)
- Checkbox "Bỏ ràng buộc công bằng C5" để so sánh

### Output
- Ma trận phân bổ tối ưu 6×4 (x_{j,r}) — nghìn tỷ VND
- Tổng GDP gain Z* (tỷ VND)
- Bảng dual variables theo vùng và hạng mục
- Chi phí công bằng: Z*(có C5) vs Z*(không C5) — chênh lệch bao nhiêu %
- Chỉ số số hóa sau đầu tư: D_r + γ×x_D,r

### Biểu đồ
1. Heatmap 6×4: ma trận phân bổ tối ưu (đậm = nhiều)
2. Grouped bar: tổng ngân sách mỗi vùng (so sánh có/không C5)
3. Bar chart: chỉ số số hóa trước vs sau đầu tư (6 vùng)
4. Choropleth map đơn giản (dạng bar hoặc table màu) 6 vùng theo tổng đầu tư

### AI Agent phân tích
- Không có C5: vốn chảy về vùng nào? Tại sao ĐNB và ĐBSH hút vốn nhiều nhất
- Chi phí công bằng bao nhiêu % → có chấp nhận được không
- Tây Nguyên hệ số AI thấp (0.45) → mô hình đề xuất đầu tư H và I trước là đúng không
- So sánh phân bổ tối ưu với FDI thực tế 2024 (regions.fdi_registered)

### Chức năng web
- Toggle on/off từng ràng buộc
- Bảng ma trận phân bổ có thể edit (override thủ công để so sánh)
- Download ma trận kết quả

---

## BÀI 5 — MIP lựa chọn dự án

### Dataset
regions — tham chiếu để gán dự án vào vùng địa lý

### Dữ liệu dùng
Toàn bộ là hard-code từ đề (15 dự án với C_i, C1_i, B_i đã cho sẵn)
Dùng regions để hiển thị context địa lý của dự án

### Input (UI controls)
- Ngân sách tổng 5 năm: slider 60.000–120.000 (default 80.000) tỷ VND
- Ngân sách năm 1-2: slider 30.000–55.000 (default 40.000)
- Số dự án tối thiểu: slider 5–9 (default 7)
- Số dự án tối đa: slider 9–13 (default 11)
- Checkbox từng ràng buộc: C3 (loại trừ P1/P2), C4 (y8≤y12), C5 (y13≤y12), C6 (P14 bắt buộc)
- Checkbox "Dùng lợi ích kỳ vọng E[Z] = Σp_i×B_i×y_i" (với p_i theo loại dự án)
- Checkbox "Buộc chọn cả P1 và P2 (redundancy)"

### Output
- Danh sách dự án được chọn (tên, lĩnh vực, chi phí, lợi ích)
- Tổng chi phí, tổng NPV, NPV/chi phí biên
- Số dự án theo lĩnh vực
- Phân bổ chi phí năm 1-2 vs năm 3-5
- LP relaxation gap (MIP gap)

### Biểu đồ
1. Bar chart: NPV của 15 dự án, đánh dấu được chọn (màu khác)
2. Scatter: Chi phí vs NPV, bubble size=NPV/cost, màu=được chọn
3. Stacked bar: ngân sách năm 1-2 vs năm 3-5 theo lĩnh vực
4. Gantt chart đơn giản: timeline triển khai các dự án được chọn

### AI Agent phân tích
- Tại sao P15 (Open Data) không được chọn dù tỷ lệ B/C cao nhất
- Ràng buộc P14 bắt buộc làm giảm Z* bao nhiêu (so sánh có/không)
- P8 và P13 có lợi ích cộng hưởng trong thực tế → mô hình giả định độc lập có hạn chế không
- Khi ngân sách tăng 100.000 → tập dự án thay đổi thế nào

### Chức năng web
- Checklist 15 dự án — bật/tắt để so sánh thủ công với kết quả MIP
- Progress bar khi solve CBC
- Bảng dự án sortable theo NPV, chi phí, lĩnh vực

---

## BÀI 6 — TOPSIS

### Dataset
regions (6 vùng × 8 tiêu chí)

### Dữ liệu dùng
- grdp_per_capita_million_VND → benefit
- fdi_registered_billion_USD → benefit
- digital_index_0_100 → benefit
- ai_readiness_0_100 → benefit
- trained_labor_pct → benefit
- rd_intensity_pct → benefit
- internet_penetration_pct → benefit
- gini_coef → cost (đảo chiều)

### Input (UI controls)
- 8 sliders trọng số w_j (default: 0.10,0.10,0.15,0.20,0.15,0.15,0.05,0.10)
- Toggle từng tiêu chí: Benefit / Cost
- Slider w_AI từ 0.10→0.40 (sensitivity)
- Radio button: "Trọng số chuyên gia" vs "Trọng số Entropy (tự động)"
- Multiselect chọn vùng để so sánh (mặc định tất cả 6)

### Output
- Bảng TOPSIS đầy đủ: r_ij, v_ij, S*_i, S-_i, C*_i
- Xếp hạng 6 vùng theo C*_i
- So sánh ranking: trọng số chuyên gia vs Entropy
- Entropy weights tự tính từ dữ liệu

### Biểu đồ
1. Bar chart ngang: C*_i score 6 vùng (xếp hạng)
2. Radar chart: 6 vùng × 7 tiêu chí benefit (normalized)
3. Scatter d* vs d- : 6 vùng với đường đẳng C*=0.5
4. Heatmap: ma trận v_ij (chuẩn hóa có trọng số) 6×8

### AI Agent phân tích
- Vùng dẫn đầu → có nên đặt trung tâm AI quốc gia đầu tiên không
- Khi dùng Entropy weights → vùng nào thay đổi xếp hạng nhiều nhất và tại sao
- AI Readiness và Internet có tương quan cao (multicollinearity) → ảnh hưởng kết quả
- Chọn 3 vùng cho 3 trung tâm AI (theo QĐ 127/QĐ-TTg) dựa trên TOPSIS

### Chức năng web
- So sánh 2 bộ trọng số song song (side-by-side ranking)
- Cập nhật ranking real-time khi kéo slider
- Bảng kết quả exportable

---

## BÀI 7 — NSGA-II đa mục tiêu

### Dataset
sectors + regions (kết hợp)

### Dữ liệu dùng
- β_{j,r} từ đề bài 4 (6×4)
- e_r (CO2/tỷ): [0.42,0.55,0.48,0.32,0.62,0.38] — hard-code từ đề
- ρ_r (rủi ro AI): [0.18,0.45,0.28,0.12,0.52,0.22] — hard-code
- σ_r (giảm rủi ro/H): [0.32,0.28,0.30,0.35,0.25,0.30] — hard-code
- regions.gini_coef → để tính Gini baseline so sánh

### Input (UI controls)
- pop_size: slider 50–200 (default 100)
- n_gen: slider 50–500 (default 200)
- Trọng số TOPSIS trên Pareto: 4 sliders (f1=0.40, f2=0.25, f3=0.20, f4=0.15)
- Ràng buộc ngân sách: slider 30.000–70.000 (default 50.000)
- Nút "Chạy NSGA-II" (không real-time vì tốn compute)

### Output
- Số nghiệm Pareto tìm được
- Hypervolume indicator
- Nghiệm thỏa hiệp tối ưu (từ TOPSIS trên Pareto)
- Bảng phân bổ x_{j,r} của nghiệm thỏa hiệp
- Chi phí cơ hội: nghiệm max f1 hi sinh bao nhiêu % f2, f3, f4

### Biểu đồ
1. Scatter 2D: f1 vs f2 (Pareto front, màu theo f3)
2. Parallel coordinates: tất cả nghiệm Pareto × 4 mục tiêu
3. Line chart: hypervolume qua thế hệ (convergence)
4. Bar chart: so sánh 4 mục tiêu giữa nghiệm max-GDP, thỏa hiệp, max-equity

### AI Agent phân tích
- Trade-off tăng trưởng vs bao trùm có rõ không → gợi ý về cấu trúc kinh tế
- Trọng số (0.40,0.25,0.20,0.15) có phản ánh đúng ưu tiên VN hiện tại không
- So sánh nghiệm NSGA-II với nghiệm LP đơn mục tiêu bài 4 — cái nào "tốt hơn"

### Chức năng web
- Progress bar và status khi chạy NSGA-II
- Cache kết quả (st.session_state) tránh chạy lại
- Click điểm Pareto → xem phân bổ 6×4 tương ứng

---

## BÀI 8 — Dynamic Programming

### Dataset
macro (chuỗi thời gian 2020–2025)

### Dữ liệu dùng
- GDP_growth_pct (2020–2025) → calibrate hàm phần thưởng
- FDI_disbursed_billion_USD → tham chiếu scale ngân sách
- digital_economy_share_GDP_pct → điều kiện ban đầu D_0 = 20.3% (2026)
- labor_productivity_million_VND → trend L

Điều kiện ban đầu (từ đề):
- K_0 = 27.500 nghìn tỷ VND (nội suy từ chuỗi K)
- L_0 = 53.9 triệu LĐ (nội suy)
- D_0 = 20.3% GDP
- AI_0 = 86 nghìn DN số
- H_0 = 30%
- A_0 = TFP tính từ bài 1

### Input (UI controls)
- Hệ số chiết khấu ρ: slider 0.85–0.99 (default 0.97)
- Hàm thỏa dụng: radio "Log U(C)=ln(C)" vs "CRRA U(C)=C^(1-γ)/(1-γ)"
- γ (CRRA): slider 0.5–3.0 (default 1.5)
- Horizon T: 2026–2035 (fixed 10 năm)
- Kịch bản cú sốc 2028: checkbox + slider mức giảm Y (5%–15%, default 8%)
- Radio: "Đầu tư trải đều" vs "Front-load 3 năm đầu" vs "Tối ưu DP"

### Output
- Quỹ đạo tối ưu K_t, D_t, AI_t, H_t, Y_t, C_t (2026–2035)
- Tổng welfare W = Σρ^t × U(C_t)
- Bảng backward induction (states × periods)
- So sánh welfare: trải đều vs front-load vs tối ưu

### Biểu đồ
1. Multi-line chart: K, D, AI, H theo thời gian 2026–2035
2. Line chart: Y_t và C_t theo thời gian
3. Heatmap: bảng DP value function (10 giai đoạn × 5 mức trạng thái)
4. Bar chart: tỷ lệ I_K/I_D/I_AI/I_H theo năm (cơ cấu đầu tư tối ưu)

### AI Agent phân tích
- Quỹ đạo tối ưu front-loaded hay back-loaded? Vì sao?
- Tỷ lệ AI/H có ổn định không → đào tạo nhân lực nên đi trước hay đồng thời với AI
- ρ=0.90 vs ρ=0.97 → chính phủ ngắn hạn vs dài hạn → ảnh hưởng R&D thế nào
- Cú sốc 2028 → mô hình điều chỉnh phân bổ ra sao

### Chức năng web
- Slider ρ cập nhật welfare liền
- Toggle xem từng loại vốn (K/D/AI/H) riêng
- So sánh 3 chiến lược trên cùng 1 chart

---

## BÀI 9 — Lao động và AI

### Dataset
sectors (8 ngành, bỏ Khai khoáng và Y tế)

### Dữ liệu dùng
- labor_million → lao động hiện tại (L_i)
- automation_risk_pct → risk_i
- Tham số a1, a2, b1, c1, d1 → hard-code từ bảng đề 9.3

### Input (UI controls)
- Ngân sách tổng: slider 20.000–50.000 tỷ (default 30.000)
- Radio kịch bản AI adoption: "Thấp (×0.5)" / "Trung bình (×1.0)" / "Cao (×1.5)"
- Slider tốc độ tự động hóa (nhân với c1): 0.5–2.0 (default 1.0)
- Checkbox ràng buộc "Không ngành nào mất >5% lao động"
- Ràng buộc NetJob_i ≥ 0: toggle on/off

### Output
- Phân bổ tối ưu x_AI_i và x_H_i cho 8 ngành
- NetJob_i từng ngành (dương = tạo thêm)
- Tổng NetJob ròng
- Số lao động bị dịch chuyển vs được tái đào tạo
- Ngưỡng x_H tối thiểu cho ngành CNCB để NetJob ≥ 0

### Biểu đồ
1. Stacked bar: NewJob + UpgradeJob − DisplacedJob theo ngành
2. Scatter: automation_risk vs ai_readiness (4 nhóm: nguy cơ cao/thấp × sẵn sàng cao/thấp)
3. Bar chart: x_AI vs x_H phân bổ tối ưu từng ngành
4. Line chart: NetJob theo 3 kịch bản AI adoption

### AI Agent phân tích
- Ngành nào cần đầu tư đào tạo lại nhiều nhất → khớp thực tế VN không
- Tài chính-NH: nguy cơ 52% nhưng hệ số tạo việc làm mới cao → chiến lược tối ưu là gì
- Nông-Lâm-Thủy sản: lao động nhiều (13.2M) nhưng hệ số AI thấp → có nên đầu tư AI không
- Ràng buộc "tốc độ TĐH không vượt năng lực đào tạo" trong mô hình

### Chức năng web
- Radio kịch bản cập nhật chart liền
- Bảng phân bổ lao động sortable
- Highlight ngành có NetJob âm bằng màu đỏ

---

## BÀI 10 — Stochastic Programming

### Dataset
macro — GDP_growth_pct, FDI_disbursed_billion_USD để calibrate kịch bản

### Dữ liệu dùng
- GDP_growth_pct (2020–2025) → phân phối lịch sử, ước mean/std kịch bản
- FDI_disbursed_billion_USD → tham chiếu kịch bản FDI
- exports_billion_USD → calibrate kịch bản xuất khẩu

Kịch bản từ đề (4 scenarios):
- s1 Lạc quan: p=0.30, TG growth=3.5%, FDI=32B, XK+12%
- s2 Cơ sở: p=0.45, TG growth=2.8%, FDI=27B, XK+8%
- s3 Bi quan: p=0.20, TG growth=1.5%, FDI=20B, XK+3%
- s4 Khủng hoảng: p=0.05, TG growth=0.2%, FDI=12B, XK-5%

### Input (UI controls)
- 4 sliders xác suất p_s (auto-enforce tổng=1)
- Ngân sách giai đoạn 1: slider 50.000–75.000 (default 65.000) tỷ VND
- Dự phòng stage 2: auto = 80.000 − stage1
- Hệ số phạt penalty: slider 0.1–1.0 (default 0.5)
- Nút "Chạy Monte Carlo" (1000 mẫu)

### Output
- Quyết định first-stage tối ưu x_I, x_D, x_AI, x_H
- GDP gain kỳ vọng E[Z]
- VSS (Value of Stochastic Solution) = Z_SP − Z_EV
- EVPI (Expected Value of Perfect Information) = Z_WS − Z_SP
- Phân phối kết quả Monte Carlo

### Biểu đồ
1. Scenario tree (cây 2 giai đoạn, 4 nhánh)
2. Bar chart: EVPI vs VSS vs EEV (so sánh 3 approaches)
3. Histogram: phân phối GDP gain từ Monte Carlo (1000 mẫu)
4. Bar chart: quyết định x* so sánh SP vs EV (deterministic)

### AI Agent phân tích
- EVPI dương → có đáng mua thông tin dự báo kinh tế toàn cầu không
- VSS dương → giá trị của tư duy xác suất trong hoạch định chính sách VN
- Lời giải SP đầu tư H nhiều hơn EV không → tại sao H là "bảo hiểm" tốt
- So sánh với COVID-2020 và bão Yagi-2024 thực tế

### Chức năng web
- Slider p_s với auto-rebalance (thay s1 → các s khác điều chỉnh)
- Nút "Chạy MC" có spinner
- Bảng so sánh 3 approaches: SP / EV / WS

---

## BÀI 11 — Q-Learning

### Dataset
macro — GDP_growth_pct để calibrate môi trường và phần thưởng

### Dữ liệu dùng
- GDP_growth_pct → định nghĩa ngưỡng trạng thái GDP (low<4%, mid 4-7%, high>7%)
- digital_economy_share_GDP_pct → trạng thái D (low<13%, mid 13-17%, high>17%)
- FDI_disbursed_billion_USD → tham chiếu scale ngân sách hàng năm
- Trạng thái khởi đầu 2026: GDP=high(8.02%), D=mid(19.5%), AI=low, U=mid

### Input (UI controls)
- Learning rate α: slider 0.01–0.5 (default 0.1)
- Discount γ: slider 0.8–0.99 (default 0.95)
- Epsilon ban đầu: slider 0.5–1.0 (default 1.0)
- Epsilon decay: slider 1000–10000 episodes (default 5000)
- Số episodes: slider 1000–20000 (default 10000)
- Nút "Train Agent" + "Reset Q-table"
- Nút "Chạy policy π* từ trạng thái VN 2026"

### Output
- Q-table hội tụ (81×5 hoặc display 9×5 cho trạng thái thường gặp)
- Chính sách tối ưu π*(s) cho 5 trạng thái quan trọng
- Learning curve: cumulative reward vs episode
- So sánh: π* vs luôn chọn a1 vs luôn chọn a3 vs random

### Biểu đồ
1. Heatmap Q-table (9 trạng thái đại diện × 5 hành động)
2. Line chart: learning curve (rolling average 100 episodes)
3. Bar chart: cumulative reward 4 strategies (π*, a1, a3, random)
4. State transition diagram: agent di chuyển qua trạng thái theo π*

### AI Agent phân tích
- Khi GDP thấp+D thấp+U cao → π* chọn hành động gì? Có hợp lý không
- Khi GDP cao+AI cao+U thấp → π* chọn "consolidation" không
- Giới hạn của RL tabular so với thực tế (81 trạng thái quá đơn giản)
- Tích hợp π* vào hoạch định chính sách mà không vi phạm trách nhiệm chính trị

### Chức năng web
- Nút Train với progress bar (episode counter)
- Cache Q-table sau training
- Dropdown chọn trạng thái khởi đầu → xem agent chơi step-by-step
- Cảnh báo nếu chưa converge

---

## BÀI 12 — AIDEOM tích hợp

### Dataset
Tất cả 3 datasets + kết quả các bài 1–11

### Dữ liệu tích hợp
- Kết quả bài 1: GDP forecast 2030, TFP trend
- Kết quả bài 3: Priority ngành top-3
- Kết quả bài 4: ma trận phân bổ tối ưu
- Kết quả bài 6: TOPSIS ranking 6 vùng
- Kết quả bài 7: Pareto front + nghiệm thỏa hiệp
- Kết quả bài 9: NetJob theo ngành
- Kết quả bài 11: chính sách π*

### Input (UI controls)
- Dropdown chọn kịch bản: S1 Truyền thống / S2 Số hóa nhanh / S3 AI dẫn dắt / S4 Bao trùm / S5 Tối ưu
- Trọng số tổng hợp 6 module: 6 sliders (M1–M6)
- Năm mục tiêu: 2027, 2028, 2029, 2030

### Output
- Dashboard KPI tổng hợp: GDP forecast, tổng NetJob, AI readiness trung bình, top vùng
- Bảng so sánh 5 kịch bản × 6 KPI
- Ma trận đồng thuận giữa các phương pháp (khi nào đồng ý/mâu thuẫn)
- Khuyến nghị chính sách tổng hợp

### Biểu đồ
1. Radar chart: 5 kịch bản × 6 KPI (normalized)
2. Heatmap agreement matrix: 6 module × 6 vùng/ngành (màu = đồng thuận)
3. KPI cards: 6 metrics chính với so sánh vs baseline
4. Parallel coordinates: 5 kịch bản × tất cả KPI

### AI Agent phân tích (TỔNG HỢP CHÍNH)
- Khuyến nghị chính sách 2025–2030 tổng hợp từ tất cả mô hình
- Khi nào các mô hình đồng thuận? Khi nào mâu thuẫn và tại sao?
- Kịch bản S5 (tối ưu) khác gì S3 (AI dẫn dắt)?
- Hàm ý cho nhà hoạch định chính sách kinh tế VN

### Chức năng web
- 6 tabs: Tổng quan / Dự báo / Phân bổ / Lao động / Rủi ro / Khuyến nghị
- Toggle bật/tắt từng module
- Export PDF báo cáo tổng hợp
- So sánh 2 kịch bản song song

---

## CẤU TRÚC PROJECT STREAMLIT

```
aideom_vn/
│
├── app.py                          # Entry point, config trang chủ
├── requirements.txt
├── .streamlit/
│   └── config.toml                 # Dark theme, wide layout
│
├── pages/
│   ├── 1_Bai1_CobbDouglas.py
│   ├── 2_Bai2_LP_NganSach.py
│   ├── 3_Bai3_Priority_Nganh.py
│   ├── 4_Bai4_LP_Nganh_Vung.py
│   ├── 5_Bai5_MIP_DuAn.py
│   ├── 6_Bai6_TOPSIS.py
│   ├── 7_Bai7_NSGA2.py
│   ├── 8_Bai8_DynamicProg.py
│   ├── 9_Bai9_LaoDong_AI.py
│   ├── 10_Bai10_Stochastic.py
│   ├── 11_Bai11_QLearning.py
│   └── 12_Bai12_AIDEOM.py
│
├── core/
│   ├── __init__.py
│   ├── data_loader.py              # load_macro(), load_sectors(), load_regions()
│   ├── solvers/
│   │   ├── __init__.py
│   │   ├── cobb_douglas.py         # compute_TFP(), forecast_GDP(), growth_decomp()
│   │   ├── lp_solver.py            # solve_lp_budget(), solve_lp_region()
│   │   ├── mip_solver.py           # solve_mip_projects()
│   │   ├── topsis.py               # topsis_rank(), entropy_weights()
│   │   ├── nsga2_solver.py         # run_nsga2(), extract_pareto()
│   │   ├── dp_solver.py            # solve_dp_cvxpy(), bellman_backward()
│   │   ├── labor_model.py          # solve_netjob(), retraining_threshold()
│   │   ├── stochastic.py           # solve_stochastic(), calc_VSS_EVPI()
│   │   └── qlearning.py            # VietnamEconomyEnv, train_qlearning()
│   │
│   └── viz/
│       ├── __init__.py
│       ├── charts.py               # Plotly chart factory functions
│       └── maps.py                 # Choropleth/bar map 6 vùng
│
├── data/
│   ├── vietnam_macro_2020_2025.csv
│   ├── vietnam_sectors_2024.csv
│   └── vietnam_regions_2024.csv
│
└── assets/
    └── logo.png                    # Logo nếu có
```

---

## THỐNG NHẤT CHUNG CHO TẤT CẢ 12 TRANG

### Layout chuẩn mỗi trang
```
st.title("Bài X — Tên bài")
st.caption("Mục tiêu học tập: ...")

col_left, col_right = st.columns([1, 2])
# col_left: controls (sliders, buttons, dropdowns)
# col_right: kết quả chính + biểu đồ

with st.expander("📐 Mô hình toán học"):
    st.latex(r"...")          # Công thức từ đề

tab1, tab2, tab3 = st.tabs(["📊 Kết quả", "📈 Biểu đồ", "🤖 Phân tích AI"])
# tab1: bảng số liệu kết quả
# tab2: Plotly charts
# tab3: AI Agent phân tích (gọi Claude API)
```

### Streamlit config.toml (dark theme)
```toml
[theme]
base = "dark"
primaryColor = "#FF4B4B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#1A1F2E"
textColor = "#FAFAFA"
font = "sans serif"

[server]
maxUploadSize = 50

[browser]
gatherUsageStats = false
```

### AI Agent — cách gọi API chuẩn
```python
# core/ai_agent.py
import anthropic

def analyze_results(context: str, question: str) -> str:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Bạn là chuyên gia kinh tế phân tích mô hình AIDEOM-VN.
            
Dữ liệu kết quả:
{context}

Câu hỏi phân tích:
{question}

Trả lời súc tích, dùng số liệu cụ thể, đề xuất chính sách thực tế cho Việt Nam."""
        }]
    )
    return message.content[0].text
```

### Dependencies (requirements.txt)
```
streamlit>=1.28
pandas>=2.0
numpy>=1.24
scipy>=1.10
matplotlib>=3.7
plotly>=5.17
pulp>=2.7
cvxpy>=1.4
pyomo>=6.6
pymoo>=0.6.1
gymnasium>=0.29
stable-baselines3>=2.1
torch>=2.0
anthropic>=0.20
seaborn>=0.12
tqdm>=4.65
openpyxl>=3.1
```
