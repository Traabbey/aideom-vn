import streamlit as st
import pandas as pd
from core.data_loader import load_macro, load_regions, load_sectors

# Page configuration
st.set_page_config(
    page_title="AIDEOM-VN Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

/* Reset & Base */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Background */
.stApp {
    background-color: #F7F8FA;
}

/* Hide default streamlit header padding */
.block-container {
    padding-top: 2rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
    max-width: 1400px;
}

/* ── Hero Header ── */
.hero-wrapper {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    border: 1px solid #E8ECF0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.hero-left {}
.hero-badge {
    display: inline-block;
    background: #EEF2FF;
    color: #4F46E5;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 0.8rem;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    color: #0F1623;
    line-height: 1.15;
    margin-bottom: 0.6rem;
}
.hero-title span {
    color: #4F46E5;
}
.hero-subtitle {
    font-size: 1rem;
    color: #5A6478;
    max-width: 580px;
    line-height: 1.6;
    margin-bottom: 1.2rem;
}
.hero-meta {
    font-size: 0.82rem;
    color: #9AA3B2;
}
.hero-meta b {
    color: #4F46E5;
    font-weight: 600;
}
.hero-right {
    text-align: right;
}
.stat-pill {
    display: inline-block;
    background: #F0F4FF;
    border: 1px solid #C7D2FE;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-left: 0.8rem;
    text-align: center;
}
.stat-pill .num {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: #4F46E5;
    display: block;
}
.stat-pill .lbl {
    font-size: 0.75rem;
    color: #6B7280;
}

/* ── Section title ── */
.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.15rem;
    font-weight: 600;
    color: #0F1623;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #E8ECF0;
    margin-left: 0.5rem;
}

/* ── Module Cards ── */
.module-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-top: 1rem;
}
.module-card {
    background: #FFFFFF;
    border: 1px solid #E8ECF0;
    border-radius: 12px;
    padding: 1.4rem 1.5rem;
    transition: box-shadow 0.2s, border-color 0.2s, transform 0.2s;
    position: relative;
    overflow: hidden;
}
.module-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: #4F46E5;
    opacity: 0;
    transition: opacity 0.2s;
}
.module-card:hover {
    box-shadow: 0 4px 20px rgba(79,70,229,0.10);
    border-color: #C7D2FE;
    transform: translateY(-2px);
}
.module-card:hover::before {
    opacity: 1;
}
.card-num {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #9AA3B2;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.card-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.95rem;
    font-weight: 600;
    color: #1E2A3B;
    margin-bottom: 0.5rem;
    line-height: 1.3;
}
.card-desc {
    font-size: 0.82rem;
    color: #6B7280;
    line-height: 1.55;
}
.card-tag {
    display: inline-block;
    margin-top: 0.8rem;
    font-size: 0.7rem;
    font-weight: 600;
    color: #4F46E5;
    background: #EEF2FF;
    padding: 2px 8px;
    border-radius: 6px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #FFFFFF;
    border-right: 1px solid #E8ECF0;
}
[data-testid="stSidebar"] .stMarkdown p {
    font-size: 0.85rem;
    color: #5A6478;
}

/* Streamlit dataframe tweaks */
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #E8ECF0 !important;
}

/* Remove red from metric delta default color issue */
[data-testid="stMetricDelta"] { color: #4F46E5 !important; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrapper">
  <div class="hero-left">
    <div class="hero-badge">Phiên bản 2025 · Giai đoạn 2025–2030</div>
    <div class="hero-title">AIDEOM<span>-VN</span></div>
    <div class="hero-subtitle">
      Hệ thống tích hợp 12 mô hình tối ưu hóa và học máy phục vụ phân tích,
      mô phỏng và hỗ trợ quyết định trong chiến lược kinh tế số Việt Nam.
    </div>
    <div class="hero-meta">
      <b>AI · Digital Economy · Optimization Model</b> &nbsp;·&nbsp; Dữ liệu cập nhật 2024
    </div>
  </div>
  <div class="hero-right">
    <div class="stat-pill"><span class="num">12</span><span class="lbl">Module</span></div>
    <div class="stat-pill"><span class="num">6</span><span class="lbl">Vùng KT</span></div>
    <div class="stat-pill"><span class="num">10</span><span class="lbl">Ngành</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Dữ liệu hiện trạng ────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Tổng quan Dữ liệu Hiện trạng</div>', unsafe_allow_html=True)

try:
    macro_df = load_macro()
    regions_df = load_regions()
    sectors_df = load_sectors()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="📈 Dữ liệu Vĩ mô", value=f"{len(macro_df)} năm", delta="2020 – 2025")
        st.dataframe(
            macro_df[["year", "GDP_trillion_VND", "GDP_growth_pct", "digital_economy_share_GDP_pct"]],
            use_container_width=True, hide_index=True
        )
    with col2:
        st.metric(label="🗺️ Vùng Địa lý", value=f"{len(regions_df)} vùng", delta="Mốc 2024")
        st.dataframe(
            regions_df[["region_name_vi", "grdp_trillion_VND", "digital_index_0_100", "ai_readiness_0_100"]],
            use_container_width=True, hide_index=True
        )
    with col3:
        st.metric(label="🏢 Ngành Kinh tế", value=f"{len(sectors_df)} ngành", delta="Mốc 2024")
        st.dataframe(
            sectors_df[["sector_name_vi", "gdp_share_2024_pct", "labor_million", "ai_readiness_0_100"]],
            use_container_width=True, hide_index=True
        )
except Exception as e:
    st.error(f"Lỗi tải dữ liệu CSV: {e}")

# ── 12 Module ─────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-title">🛠️ 12 Module Phân tích & Tối ưu hóa</div>', unsafe_allow_html=True)

modules = [
    ("01", "Cobb-Douglas mở rộng", "Ước lượng TFP và dự báo GDP 2026–2030 theo vai trò của Số hóa, AI, Lao động chất lượng cao và Vốn.", "Kinh tế lượng"),
    ("02", "LP Ngân sách số", "Quy hoạch tuyến tính phân bổ ngân sách tối ưu cho 4 lĩnh vực hạ tầng công nghệ số.", "Linear Programming"),
    ("03", "Priority Ngành", "Xếp hạng ưu tiên chuyển đổi số & AI cho 10 ngành kinh tế bằng phương pháp đa tiêu chí.", "Multi-Criteria"),
    ("04", "LP Ngành – Vùng", "Phân bổ tối ưu ngân sách 6 vùng × 4 hạng mục kết hợp ràng buộc công bằng xã hội.", "LP + Equity"),
    ("05", "MIP Lựa chọn Dự án", "Quy hoạch nguyên hỗn hợp tối đa hóa NPV danh mục dự án số hóa 5 năm.", "Mixed Integer"),
    ("06", "TOPSIS Xếp hạng Vùng", "Đánh giá mức độ số hóa và AI của 6 vùng kinh tế bằng TOPSIS + trọng số Entropy.", "TOPSIS"),
    ("07", "NSGA-II Đa mục tiêu", "Cân bằng Tăng trưởng GDP, Phát thải, Công bằng và Rủi ro AI bằng giải thuật di truyền.", "Genetic Algorithm"),
    ("08", "Quy hoạch động", "Tìm quỹ đạo tích lũy vốn số hóa tối ưu dài hạn 10 năm bằng phương pháp Bellman.", "Dynamic Prog."),
    ("09", "Lao động và AI", "Mô hình dịch chuyển lao động, tác động tự động hóa và tối ưu hóa ngân sách đào tạo.", "Labor Model"),
    ("10", "Stochastic Programming", "Lập trình ngẫu nhiên 2 giai đoạn hoạch định đầu tư dưới bất định của thị trường toàn cầu.", "Stochastic"),
    ("11", "Q-Learning", "AI Agent tương tác tối ưu hóa ngân sách hàng năm theo trạng thái vĩ mô nền kinh tế.", "Reinforcement RL"),
    ("12", "AIDEOM Tích hợp", "Dashboard tổng hợp đa kịch bản chính sách và đánh giá đồng thuận giữa các phương pháp.", "Integrated"),
]

cards_html = '<div class="module-grid">'
for num, title, desc, tag in modules:
    cards_html += f"""
    <div class="module-card">
        <div class="card-num">Bài {num}</div>
        <div class="card-title">{title}</div>
        <div class="card-desc">{desc}</div>
        <div class="card-tag">{tag}</div>
    </div>"""
cards_html += '</div>'

st.markdown(cards_html, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("### 🤖 AIDEOM-VN")
st.sidebar.markdown("Dùng menu bên dưới để chuyển giữa các bài toán phân tích.")
st.sidebar.markdown("---")
st.sidebar.info("💡 Mỗi module có giao diện 2 cột: **Tham số** bên trái và **Kết quả** bên phải.")
