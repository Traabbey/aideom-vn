import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

# Add project root to sys.path so utils package can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.data_loader import load_macro
from utils.ai_analyst import render_analyst_box
from utils.hide_nav import hide_auto_nav

# ── Page configuration ───────────────────────────────────────────────────────────
st.set_page_config(page_title="Bài 1 — Cobb-Douglas", page_icon="🌱", layout="wide")

hide_auto_nav()

st.markdown("# 🌱 Bài 1 — Hàm sản xuất Cobb-Douglas mở rộng")
st.markdown(
    """
    <span style='background:#22543d;color:#9ae6b4;padding:3px 10px;border-radius:12px;font-size:0.8rem'>CẤP ĐỘ DỄ</span>
    &nbsp;&nbsp;Growth accounting &nbsp;&nbsp; numpy/pandas
    """,
    unsafe_allow_html=True,
)

st.latex(r"Y_t = A_t \cdot K_t^\alpha \cdot L_t^\beta \cdot D_t^\gamma \cdot AI_t^\delta \cdot H_t^\theta")
st.markdown(
    "Ràng buộc CRS: $\\alpha + \\beta + \\gamma + \\delta + \\theta = 1$"
)
st.latex(
    r"\Delta\ln Y = \Delta\ln A + \alpha\Delta\ln K + \beta\Delta\ln L + \gamma\Delta\ln D + \delta\Delta\ln AI + \theta\Delta\ln H"
)

# ── Data loading ──────────────────────────────────────────────────────────────────
df = load_macro()
years  = df["year"].values
Y      = df["GDP_trillion_VND"].values
# In the original problem K and L lists are given explicitly:
K      = np.array([16500, 17800, 19600, 21300, 23500, 25900], dtype=float)
L      = np.array([53.6, 50.5, 51.7, 52.4, 52.9, 53.4], dtype=float)
D      = df["digital_economy_share_GDP_pct"].values.astype(float)
AI     = np.array([55.6, 60.2, 65.4, 67.0, 73.8, 80.1], dtype=float)
H      = np.array([24.1, 26.1, 26.2, 27.0, 28.4, 29.2], dtype=float)

# ── Sidebar: parameter sliders ─────────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Tham số đàn hồi")
st.sidebar.markdown("Tổng α+β+γ+δ phải ≤ 1 (θ = 1 − tổng)")

alpha = st.sidebar.slider("α (vốn K)", 0.20, 0.50, 0.31, 0.01)
beta  = st.sidebar.slider("β (lao động L)", 0.30, 0.55, 0.42, 0.01)
gamma = st.sidebar.slider("γ (số hóa D)", 0.01, 0.20, 0.10, 0.01)
delta = st.sidebar.slider("δ (AI)", 0.01, 0.20, 0.08, 0.01)

remaining = 1.0 - alpha - beta - gamma - delta
if remaining < 0:
    st.sidebar.error("⚠️ Tổng vượt 1! Giảm bớt tham số.")
    theta = 0.0
else:
    theta = round(remaining, 4)
    st.sidebar.metric("θ (nhân lực H) = tự động", f"{theta:.4f}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 Kịch bản GDP 2030")
D_2030  = st.sidebar.slider("Kinh tế số 2030 (%)", 20.0, 40.0, 30.0, 0.5)
AI_2030 = st.sidebar.slider("Doanh nghiệp số 2030 (nghìn)", 80.0, 130.0, 100.0, 1.0)
H_2030  = st.sidebar.slider("Lao động qua đào tạo 2030 (%)", 28.0, 45.0, 35.0, 0.5)
K_growth = st.sidebar.slider("Tăng trưởng K/năm (%)", 3.0, 10.0, 6.0, 0.5)
L_growth = st.sidebar.slider("Tăng trưởng L/năm (%)", 0.5, 3.0, 1.5, 0.1)
TFP_growth = st.sidebar.slider("Tăng TFP/năm (%)", 0.5, 3.0, 1.2, 0.1)

# ── Computation ─────────────────────────────────────────────────────────────────
A = Y / (K**alpha * L**beta * D**gamma * AI**delta * H**theta)

Y_hat = A.mean() * K**alpha * L**beta * D**gamma * AI**delta * H**theta
mape  = np.mean(np.abs((Y - Y_hat) / Y)) * 100

# Growth accounting
dln = lambda x: np.diff(np.log(x))
dln_Y   = dln(Y)
contrib_K   = alpha * dln(K)
contrib_L   = beta  * dln(L)
contrib_D   = gamma * dln(D)
contrib_AI  = delta * dln(AI)
contrib_H   = theta * dln(H)
contrib_TFP = dln_Y - contrib_K - contrib_L - contrib_D - contrib_AI - contrib_H

ga_years = years[1:]
ga_df = pd.DataFrame({
    "Năm": ga_years,
    "Vốn K": contrib_K * 100,
    "Lao động L": contrib_L * 100,
    "Số hóa D": contrib_D * 100,
    "AI": contrib_AI * 100,
    "Nhân lực H": contrib_H * 100,
    "TFP": contrib_TFP * 100,
    "Tổng": dln_Y * 100,
})

# GDP 2030 forecast
K_proj = K[-1] * (1 + K_growth/100)**5
L_proj = L[-1] * (1 + L_growth/100)**5
A_proj = A[-1] * (1 + TFP_growth/100)**5
GDP_2030 = A_proj * K_proj**alpha * L_proj**beta * D_2030**gamma * AI_2030**delta * H_2030**theta

# ── Result Tabs ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 TFP A_t", "🔬 Dự báo & MAPE", "📊 Growth accounting", "🔭 Dự báo 2030"]
)

# Tab 1 — TFP
with tab1:
    st.markdown("### Năng suất nhân tố tổng hợp A_t theo năm")
    data_tab1 = pd.DataFrame({
        "Năm": years, "Y_thực_tế": Y, "K": K, "L": L,
        "D": D, "AI": AI, "H": H, "TFP A_t": A.round(4)
    })
    st.dataframe(data_tab1, use_container_width=True, hide_index=True)

    fig1 = go.Figure()
    fig1.add_scatter(x=years, y=A, mode="lines+markers",
                     line=dict(color="#e94560", width=3),
                     marker=dict(size=9),
                     name="TFP A_t calibrated theo năm")
    fig1.update_layout(
        xaxis_title="Năm", yaxis_title="TFP (A_t)",
        height=350, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig1, use_container_width=True)
    st.info(
        f"**Nhận xét:** TFP dao động từ **{A.min():.2f}** đến **{A.max():.2f}**. "
        "Xu hướng tăng cho thấy chất lượng tăng trưởng đang cải thiện nhờ số hóa."
    )

# Tab 2 — Dự báo & MAPE
with tab2:
    st.markdown("### Sản lượng dự báo vs thực tế (Ȳ A trung bình)")
    df_pred = pd.DataFrame({
        "Năm": years,
        "Y_thực (nghìn tỷ VND)": Y.round(1),
        "Y_dự báo (nghìn tỷ VND)": Y_hat.round(1),
        "Sai số (%)": (np.abs(Y - Y_hat) / Y * 100).round(2),
    })
    st.dataframe(df_pred, use_container_width=True, hide_index=True)
    st.metric("MAPE", f"{mape:.2f}%",
              help="Mean Absolute Percentage Error — càng nhỏ càng tốt")

    fig2 = go.Figure()
    fig2.add_scatter(x=years, y=Y, mode="lines+markers", name="Y thực tế",
                     line=dict(color="#68d391", width=3))
    fig2.add_scatter(x=years, y=Y_hat, mode="lines+markers", name="Y dự báo",
                     line=dict(color="#f6ad55", width=3, dash="dash"))
    fig2.update_layout(
        xaxis_title="Năm", yaxis_title="GDP (nghìn tỷ VND)",
        legend=dict(orientation="h", y=1.05),
        height=350, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig2, use_container_width=True)

# Tab 3 — Growth accounting
with tab3:
    st.markdown("### Phân rã tăng trưởng GDP 2020-2025 (%/năm)")
    st.dataframe(ga_df.round(3), use_container_width=True, hide_index=True)

    avg = ga_df.drop(columns=["Năm", "Tổng"]).mean()
    fig3 = go.Figure(go.Bar(
        x=avg.index, y=avg.values,
        marker_color=["#4299e1","#68d391","#f6ad55","#fc8181","#b794f4","#e94560"],
        text=[f"{v:.3f}%" for v in avg.values], textposition="outside",
    ))
    fig3.update_layout(
        title="Đóng góp trung bình vào tăng trưởng GDP",
        yaxis_title="Điểm phần trăm (%/năm)",
        height=380, margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Waterfall chart for the latest year
    st.markdown("#### Waterfall — phân rã 2024→2025")
    wf_labels = ["Vốn K", "Lao động L", "Số hóa D", "AI", "Nhân lực H", "TFP", "Tổng"]
    wf_values = [
        ga_df.iloc[-1]["Vốn K"], ga_df.iloc[-1]["Lao động L"],
        ga_df.iloc[-1]["Số hóa D"], ga_df.iloc[-1]["AI"],
        ga_df.iloc[-1]["Nhân lực H"], ga_df.iloc[-1]["TFP"],
    ]
    fig_wf = go.Figure(go.Waterfall(
        name="Growth decomposition",
        orientation="v",
        measure=["relative"]*6 + ["total"],
        x=wf_labels,
        y=wf_values + [sum(wf_values)],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#68d391"}},
        decreasing={"marker": {"color": "#fc8181"}},
        totals={"marker": {"color": "#e94560"}},
    ))
    fig_wf.update_layout(
        yaxis_title="Điểm % đóng góp vào tăng trưởng",
        height=350, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_wf, use_container_width=True)

# Tab 4 — Dự báo 2030
with tab4:
    st.markdown("### Kịch bản dự báo GDP Việt Nam 2030")
    col1, col2, col3 = st.columns(3)
    col1.metric("GDP dự báo 2030", f"{GDP_2030:,.0f} nghìn tỷ VND",
                f"≈ {GDP_2030/22:.0f} tỷ USD")
    col2.metric("Tăng so với 2025", f"{(GDP_2030/Y[-1]-1)*100:.1f}%",
                "Tổng 5 năm")
    col3.metric("CAGR 2025-2030", f"{((GDP_2030/Y[-1])**(1/5)-1)*100:.2f}%/năm")

    # Projection chart
    proj_years = list(years) + [2026, 2027, 2028, 2029, 2030]
    # Simple linear interpolation for 2026-2029
    proj_GDP = list(Y)
    step = (GDP_2030 - Y[-1]) / 5
    for i in range(1, 6):
        proj_GDP.append(Y[-1] + step * i)

    fig4 = go.Figure()
    fig4.add_scatter(x=years, y=Y, mode="lines+markers", name="Thực tế",
                     line=dict(color="#68d391", width=3))
    fig4.add_scatter(x=[2025, 2026, 2027, 2028, 2029, 2030],
                     y=[Y[-1]] + proj_GDP[6:],
                     mode="lines+markers", name="Dự báo",
                     line=dict(color="#e94560", width=3, dash="dot"),
                     marker=dict(symbol="diamond"))
    fig4.add_vline(x=2025.5, line_dash="dash", line_color="gray",
                   annotation_text="Thực tế | Dự báo")
    fig4.update_layout(
        xaxis_title="Năm", yaxis_title="GDP (nghìn tỷ VND)",
        legend=dict(orientation="h", y=1.05),
        height=380, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("#### Giả định kịch bản")
    st.table(pd.DataFrame({
        "Biến": ["Kinh tế số D (%)", "DN số AI (nghìn)", "Lao động ĐT H (%)",
                 "Tăng K/năm", "Tăng L/năm", "Tăng TFP/năm"],
        "Năm 2025 (gốc)": [D[-1], AI[-1], H[-1], "—", "—", "—"],
        "Năm 2030 (kịch bản)": [D_2030, AI_2030, H_2030,
                                 f"{K_growth}%", f"{L_growth}%", f"{TFP_growth}%"],
    }))

# ── AI Analyst ────────────────────────────────────────────────────────────────
context_str = (
    f"Tham số: α={alpha}, β={beta}, γ={gamma}, δ={delta}, θ={theta:.4f}\n"
    f"TFP A_t 2020-2025: {A.round(4).tolist()}\n"
    f"MAPE dự báo: {mape:.2f}%\n"
    f"Đóng góp TB Vốn K: {avg['Vốn K']:.3f}%, Lao động L: {avg['Lao động L']:.3f}%, "
    f"Số hóa D: {avg['Số hóa D']:.3f}%, AI: {avg['AI']:.3f}%, "
    f"Nhân lực H: {avg['Nhân lực H']:.3f}%, TFP: {avg['TFP']:.3f}%\n"
    f"GDP dự báo 2030: {GDP_2030:,.0f} nghìn tỷ VND (≈{GDP_2030/22:.0f} tỷ USD)\n"
    f"Kịch bản 2030: D={D_2030}%, AI={AI_2030}k DN, H={H_2030}%, "
    f"K tăng {K_growth}%/năm, L tăng {L_growth}%/năm, TFP tăng {TFP_growth}%/năm"
)

render_analyst_box(
    "Bài 1",
    "Hàm sản xuất Cobb-Douglas mở rộng",
    context_str,
    extra_instruction=(
        "Đặc biệt bình luận về: xu hướng TFP, "
        "đóng góp của số hóa/AI so với vốn vật chất, "
        "tính khả thi của kịch bản 2030."
    ),
)
