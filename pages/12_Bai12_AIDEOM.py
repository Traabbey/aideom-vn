import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, PULP_CBC_CMD, value, LpStatus
import sys
from pathlib import Path

# Add project root to sys.path so utils package can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.data_loader import load_macro, load_regions, load_sectors
from utils.ai_analyst import render_analyst_box
from utils.hide_nav import hide_auto_nav

# Page configuration
st.set_page_config(page_title="Bài 12 — AIDEOM Tích hợp", page_icon="🇻🇳", layout="wide")

hide_auto_nav()

st.markdown("# 🇻🇳 Bài 12 — AIDEOM-VN Tích hợp")
st.markdown(
    """<span style='background:#742a2a;color:#fed7d7;padding:3px 10px;border-radius:12px;font-size:0.8rem'>CẤP ĐỘ KHÓ</span>
    &nbsp;&nbsp;6 Module &nbsp;&nbsp; 5 kịch bản chính sách""",
    unsafe_allow_html=True,
)

# ── 5 Scenarios Dataset ───────────────────────────────────────────────────────────
scenarios = {
    "S1. Truyền thống":  {"K": 0.70, "D": 0.10, "AI": 0.10, "H": 0.10, "color": "#718096"},
    "S2. Số hóa nhanh":  {"K": 0.25, "D": 0.45, "AI": 0.15, "H": 0.15, "color": "#4299e1"},
    "S3. AI dẫn dắt":    {"K": 0.20, "D": 0.20, "AI": 0.45, "H": 0.15, "color": "#e94560"},
    "S4. Bao trùm số":   {"K": 0.30, "D": 0.20, "AI": 0.10, "H": 0.40, "color": "#68d391"},
    "S5. Tối ưu cân bằng":{"K": 0.28, "D": 0.27, "AI": 0.22, "H": 0.23, "color": "#f6ad55"},
}

# ── Sidebar parameters ──────────────────────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Tham số chung")
total_budget = st.sidebar.slider("Tổng ngân sách (nghìn tỷ VND/năm)", 500, 2000, 1200, 100)
horizon = st.sidebar.slider("Chân trời dự báo (năm)", 3, 10, 5, 1)
alpha_cd = st.sidebar.slider("α Cobb-Douglas (vốn K)", 0.25, 0.40, 0.33, 0.01)
beta_cd  = st.sidebar.slider("β Cobb-Douglas (lao động)", 0.35, 0.50, 0.42, 0.01)

# ── Module M1: GDP Forecasting ─────────────────────────────────────────────────
df_macro = load_macro()
Y0 = df_macro["GDP_trillion_VND"].iloc[-1]
K0 = 25900; L0 = 53.4; D0 = 19.5; AI0 = 80.1; H0 = 29.2; A0 = 39.99

def forecast_gdp(alloc, T=5):
    K, D, AI, H, A = K0, D0, AI0, H0, A0
    Ys = [Y0]
    budget = total_budget
    for t in range(T):
        IK  = alloc["K"]  * budget
        ID  = alloc["D"]  * budget
        IAI = alloc["AI"] * budget
        IH  = alloc["H"]  * budget
        K  = 0.95*K + IK
        D  = 0.88*D + ID/100
        AI = 0.85*AI + IAI/20
        H  = H + 0.8*IH/200 - 0.02*H
        A  = A * (1 + 0.003*D + 0.002*AI + 0.004*H)
        Y = A * (K**alpha_cd) * (L0**beta_cd) * (D**0.10) * (AI**0.08) * (H**0.07)
        Ys.append(Y)
    return Ys

# ── Module M3: LP Allocation Optimization ─────────────────────────────────────
def solve_allocation(alloc_pct):
    m = LpProblem("alloc", LpMaximize)
    regions = ["NMM","RRD","NCC","CH","SE","MD"]
    beta_mat = {
        "NMM": [1.15,0.85,0.55,1.30], "RRD": [0.95,1.25,1.40,1.05],
        "NCC": [1.05,0.95,0.85,1.15], "CH":  [1.20,0.75,0.45,1.35],
        "SE":  [0.90,1.30,1.55,1.00], "MD":  [1.10,0.85,0.65,1.25],
    }
    items = ["I","D","AI","H"]
    x = {(r,j): LpVariable(f"x_{r}_{j}", lowBound=0) for r in regions for j in items}
    m += lpSum(beta_mat[r][k]*x[(r,items[k])] for r in regions for k in range(4))
    budget_alloc = total_budget * 50  # scale
    m += lpSum(x[(r,j)] for r in regions for j in items) <= budget_alloc
    for r in regions:
        m += lpSum(x[(r,j)] for j in items) >= budget_alloc/10
    m.solve(PULP_CBC_CMD(msg=False))
    return value(m.objective) if LpStatus[m.status] == "Optimal" else 0.0

# ── Compute Scenario Results ──────────────────────────────────────────────────
years_proj = list(range(2025, 2025 + horizon + 1))
results = {}
for sname, alloc in scenarios.items():
    gdp_path = forecast_gdp(alloc, horizon)
    gdp_2030 = gdp_path[-1]
    cagr = (gdp_2030/Y0)**(1/horizon) - 1
    gdp_gain = solve_allocation(alloc)
    results[sname] = {
        "GDP 2030 (nghìn tỷ)": round(gdp_2030, 0),
        "GDP 2030 (tỷ USD)": round(gdp_2030/23, 0),
        "CAGR (%)": round(cagr*100, 2),
        "GDP Gain (tỷ)": round(gdp_gain, 0),
        "Đầu tư K (%)": round(alloc["K"]*100, 0),
        "Đầu tư D (%)": round(alloc["D"]*100, 0),
        "Đầu tư AI (%)": round(alloc["AI"]*100, 0),
        "Đầu tư H (%)": round(alloc["H"]*100, 0),
        "path": gdp_path,
        "color": alloc["color"],
    }

# ── Dashboard Layout ──────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Tổng quan 5 kịch bản", "📈 Quỹ đạo GDP", "🗺️ Phân bổ ngân sách", "⚠️ Cảnh báo rủi ro"]
)

with tab1:
    st.markdown("### So sánh KPI 5 kịch bản chính sách")
    df_summary = pd.DataFrame(results).T.drop(columns=["path","color"])
    st.dataframe(df_summary, use_container_width=True)

    # Radar chart
    categories = ["GDP Growth","Số hóa","AI","Nhân lực","Cân bằng"]
    fig_radar = go.Figure()
    radar_scores = {
        "S1. Truyền thống":   [0.5, 0.2, 0.2, 0.2, 0.5],
        "S2. Số hóa nhanh":   [0.7, 0.9, 0.4, 0.4, 0.6],
        "S3. AI dẫn dắt":     [0.8, 0.5, 0.9, 0.3, 0.5],
        "S4. Bao trùm số":    [0.6, 0.5, 0.2, 0.9, 0.9],
        "S5. Tối ưu cân bằng":[0.75,0.6, 0.6, 0.6, 0.75],
    }
    for sname, scores in radar_scores.items():
        color = scenarios[sname]["color"]
        fig_radar.add_scatterpolar(
            r=scores + [scores[0]],
            theta=categories + [categories[0]],
            fill="toself", name=sname,
            line=dict(color=color, width=2),
            fillcolor=color, opacity=0.15,
        )
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        title="Radar chart — So sánh 5 kịch bản",
        height=450, margin=dict(l=0,r=0,t=40,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.1),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

with tab2:
    fig2 = go.Figure()
    for sname, data in results.items():
        fig2.add_scatter(
            x=years_proj, y=data["path"],
            mode="lines+markers", name=sname,
            line=dict(color=data["color"], width=3),
        )
    fig2.add_vline(x=2025, line_dash="dash", line_color="gray",
                   annotation_text="2025 (gốc)")
    fig2.update_layout(
        title="Quỹ đạo GDP 5 kịch bản chính sách",
        xaxis_title="Năm", yaxis_title="GDP (nghìn tỷ VND)",
        legend=dict(orientation="h", y=1.05),
        height=420, margin=dict(l=0,r=0,t=50,b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig2, use_container_width=True)

    # GDP 2030 bar
    fig3 = go.Figure(go.Bar(
        x=list(results.keys()),
        y=[results[s]["GDP 2030 (tỷ USD)"] for s in results],
        marker_color=[scenarios[s]["color"] for s in results],
        text=[f"{results[s]['GDP 2030 (tỷ USD)']:.0f} tỷ USD" for s in results],
        textposition="outside",
    ))
    fig3.update_layout(
        title="GDP 2030 theo kịch bản (tỷ USD)",
        yaxis_title="Tỷ USD",
        height=380, margin=dict(l=0,r=0,t=40,b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.markdown("### Cơ cấu phân bổ ngân sách 5 kịch bản")
    alloc_items = ["Vốn K","Hạ tầng số D","AI","Nhân lực H"]
    alloc_keys  = ["K","D","AI","H"]
    colors_alloc = ["#4299e1","#68d391","#f6ad55","#e94560"]

    fig4 = go.Figure()
    for key, label, color in zip(alloc_keys, alloc_items, colors_alloc):
        fig4.add_bar(
            x=list(scenarios.keys()),
            y=[scenarios[s][key]*100 for s in scenarios],
            name=label, marker_color=color,
        )
    fig4.update_layout(
        barmode="stack", title="Cơ cấu phân bổ ngân sách (%)",
        yaxis_title="%", legend=dict(orientation="h", y=1.05),
        height=400, margin=dict(l=0,r=0,t=50,b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig4, use_container_width=True)

with tab4:
    st.markdown("### ⚠️ Ma trận rủi ro 5 kịch bản")
    risk_data = {
        "S1. Truyền thống":    {"Rủi ro số hóa thấp": "🔴 Cao", "Rủi ro lao động": "🟡 TB", "Rủi ro phụ thuộc CN": "🟢 Thấp", "Rủi ro bất bình đẳng": "🟡 TB"},
        "S2. Số hóa nhanh":    {"Rủi ro số hóa thấp": "🟢 Thấp","Rủi ro lao động": "🟡 TB", "Rủi ro phụ thuộc CN": "🟡 TB",   "Rủi ro bất bình đẳng": "🟡 TB"},
        "S3. AI dẫn dắt":      {"Rủi ro số hóa thấp": "🟢 Thấp","Rủi ro lao động": "🔴 Cao","Rủi ro phụ thuộc CN": "🔴 Cao",  "Rủi ro bất bình đẳng": "🔴 Cao"},
        "S4. Bao trùm số":     {"Rủi ro số hóa thấp": "🟡 TB",  "Rủi ro lao động": "🟢 Thấp","Rủi ro phụ thuộc CN": "🟢 Thấp","Rủi ro bất bình đẳng": "🟢 Thấp"},
        "S5. Tối ưu cân bằng": {"Rủi ro số hóa thấp": "🟢 Thấp","Rủi ro lao động": "🟡 TB", "Rủi ro phụ thuộc CN": "🟡 TB",   "Rủi ro bất bình đẳng": "🟡 TB"},
    }
    st.dataframe(pd.DataFrame(risk_data).T, use_container_width=True)

    st.markdown("### 💡 Khuyến nghị chính sách")
    best_gdp = max(results, key=lambda s: results[s]["GDP 2030 (tỷ USD)"])
    best_balanced = "S5. Tối ưu cân bằng"
    st.success(f"🚀 **GDP cao nhất:** {best_gdp} — GDP 2030 ≈ {results[best_gdp]['GDP 2030 (tỷ USD)']:.0f} tỷ USD")
    st.info(f"⚖️ **Cân bằng nhất:** {best_balanced} — CAGR {results[best_balanced]['CAGR (%)']:.2f}%/năm, rủi ro trung bình")

# ── AI Analyst ────────────────────────────────────────────────────────────────
gdp_2030_summary = ", ".join([f"{s}: {results[s]['GDP 2030 (tỷ USD)']:.0f}" for s in results])
context_str = (
    f"5 kịch bản GDP 2030 (tỷ USD): {gdp_2030_summary}\n"
    f"Kịch bản GDP cao nhất: {best_gdp}\n"
    f"Tổng ngân sách: {total_budget} nghìn tỷ/năm\n"
    f"Chân trời: {horizon} năm\n"
    f"Kịch bản S5 CAGR: {results['S5. Tối ưu cân bằng']['CAGR (%)']:.2f}%/năm"
)
render_analyst_box(
    "Bài 12", "AIDEOM-VN Tích hợp 5 kịch bản", context_str,
    extra_instruction=(
        "So sánh 5 kịch bản và khuyến nghị kịch bản nào phù hợp nhất "
        "với mục tiêu Việt Nam 2030 theo Nghị quyết 57-NQ/TW."
    ),
)
