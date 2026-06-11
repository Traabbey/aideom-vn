import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

# Add project root to sys.path so utils package can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.data_loader import load_sectors
from utils.ai_analyst import render_analyst_box
from utils.hide_nav import hide_auto_nav

# Page configuration
st.set_page_config(page_title="Bài 3 — Priority 10 ngành", page_icon="🏭", layout="wide")

hide_auto_nav()

st.markdown("# 🏭 Bài 3 — Chỉ số ưu tiên 10 ngành Việt Nam")
st.markdown(
    """<span style='background:#744210;color:#fbd38d;padding:3px 10px;border-radius:12px;font-size:0.8rem'>CẤP ĐỘ DỄ</span>
    &nbsp;&nbsp;Min-max normalization &nbsp;&nbsp; Weighted scoring""",
    unsafe_allow_html=True,
)

st.latex(
    r"\text{Priority}_i = a_1\tilde{G}_i + a_2\tilde{P}_i + a_3\tilde{S}_i + "
    r"a_4\tilde{X}_i + a_5\tilde{E}_i + a_6\tilde{AI}_i - a_7\tilde{R}_i"
)

# ── Data ──────────────────────────────────────────────────────────────────
df = load_sectors()

# Short names for sectors
sector_names = [
    "Nông-Lâm-Thủy sản", "CN chế biến chế tạo", "Xây dựng", "Khai khoáng",
    "Bán buôn-bán lẻ", "Tài chính-Ngân hàng", "Logistics-Vận tải",
    "CNTT-Truyền thông", "Giáo dục-Đào tạo", "Y tế"
]

# 7 Criteria datasets
growth     = np.array([3.27, 9.64, 7.45, -1.20, 7.10, 7.36, 9.93, 7.85, 6.42, 6.85])
productivity = np.array([103.4, 241.2, 168.8, 1290.5, 145.3, 1072.4, 321.4, 713.8, 205.7, 437.1])
spillover  = np.array([0.35, 0.78, 0.42, 0.30, 0.55, 0.85, 0.72, 0.92, 0.65, 0.60])
export     = np.array([40.5, 290.9, 2.5, 8.2, 5.5, 1.2, 3.1, 178.0, 0.0, 0.0])
employment = np.array([13.20, 11.50, 4.80, 0.30, 7.80, 0.55, 1.95, 0.62, 2.15, 0.75])
ai_ready   = np.array([15, 55, 20, 30, 48, 72, 42, 88, 38, 45])
risk       = np.array([18, 42, 25, 55, 38, 52, 35, 28, 22, 18])

# ── Sidebar weights ─────────────────────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Trọng số")
st.sidebar.markdown("Tổng phải = 1.0")

a1 = st.sidebar.slider("a₁ Tăng trưởng", 0.05, 0.40, 0.15, 0.05)
a2 = st.sidebar.slider("a₂ Năng suất", 0.05, 0.40, 0.15, 0.05)
a3 = st.sidebar.slider("a₃ Lan tỏa", 0.05, 0.40, 0.20, 0.05)
a4 = st.sidebar.slider("a₄ Xuất khẩu", 0.05, 0.40, 0.15, 0.05)
a5 = st.sidebar.slider("a₅ Việc làm", 0.05, 0.40, 0.10, 0.05)
a6 = st.sidebar.slider("a₆ AI Readiness", 0.05, 0.40, 0.20, 0.05)
a7 = st.sidebar.slider("a₇ Rủi ro (trừ)", 0.05, 0.40, 0.15, 0.05)

total_w = a1 + a2 + a3 + a4 + a5 + a6 + a7
st.sidebar.metric("Tổng trọng số", f"{total_w:.2f}", delta=f"{total_w-1:.2f}")
if abs(total_w - 1.0) > 0.01:
    st.sidebar.warning("⚠️ Tổng ≠ 1! Kết quả có thể lệch.")

# ── Min-max normalization ────────────────────────────────────────────────────────
def norm_good(x):
    return (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else np.zeros_like(x)

def norm_bad(x):
    return (x.max() - x) / (x.max() - x.min()) if x.max() != x.min() else np.zeros_like(x)

G_n  = norm_good(growth)
P_n  = norm_good(productivity)
S_n  = norm_good(spillover)
X_n  = norm_good(export)
E_n  = norm_good(employment)
AI_n = norm_good(ai_ready)
R_n  = norm_bad(risk)

priority = a1*G_n + a2*P_n + a3*S_n + a4*X_n + a5*E_n + a6*AI_n - a7*(1-R_n)

# ── Result Tabs ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["🏆 Xếp hạng", "📊 Ma trận chuẩn hóa", "🔬 Độ nhạy", "⚖️ So sánh 2 bộ trọng số"]
)

with tab1:
    df_result = pd.DataFrame({
        "Ngành": sector_names,
        "Priority Score": priority.round(4),
        "Xếp hạng": pd.Series(priority).rank(ascending=False).astype(int),
        "Tăng trưởng (%)": growth,
        "AI Readiness": ai_ready,
        "Rủi ro TĐH (%)": risk,
    }).sort_values("Priority Score", ascending=False).reset_index(drop=True)
    df_result.index += 1

    st.dataframe(df_result, use_container_width=True)

    colors = ["#e94560" if i < 3 else "#4299e1" if i < 6 else "#718096"
              for i in range(10)]
    fig = go.Figure(go.Bar(
        x=df_result["Priority Score"],
        y=df_result["Ngành"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:.4f}" for v in df_result["Priority Score"]],
        textposition="outside",
    ))
    fig.update_layout(
        title="Chỉ số ưu tiên 10 ngành (cao = ưu tiên hơn)",
        xaxis_title="Priority Score",
        yaxis=dict(autorange="reversed"),
        height=420, margin=dict(l=0, r=60, t=40, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    top3 = df_result["Ngành"].head(3).tolist()
    st.success(f"🏆 **Top 3 ngành ưu tiên:** {top3[0]} → {top3[1]} → {top3[2]}")

with tab2:
    st.markdown("### Ma trận chuẩn hóa min-max [0,1]")
    norm_df = pd.DataFrame({
        "Ngành": sector_names,
        "Tăng trưởng": G_n.round(3),
        "Năng suất": P_n.round(3),
        "Lan tỏa": S_n.round(3),
        "Xuất khẩu": X_n.round(3),
        "Việc làm": E_n.round(3),
        "AI Readiness": AI_n.round(3),
        "Rủi ro (đảo)": R_n.round(3),
    })
    st.dataframe(norm_df, use_container_width=True, hide_index=True)

    fig2 = px.imshow(
        norm_df.set_index("Ngành").values,
        labels=dict(x="Tiêu chí", y="Ngành", color="Giá trị"),
        x=["Tăng trưởng","Năng suất","Lan tỏa","Xuất khẩu","Việc làm","AI Ready","Rủi ro↓"],
        y=sector_names,
        color_continuous_scale="RdYlGn",
        aspect="auto",
    )
    fig2.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.markdown("### Độ nhạy theo trọng số a₆ (AI Readiness)")
    a6_range = np.arange(0.05, 0.45, 0.05)
    top3_track = []
    scores_track = {n: [] for n in sector_names}

    for a6_val in a6_range:
        # Re-normalize other weights so sum is 1
        other = 1 - a6_val
        ratio = other / (a1 + a2 + a3 + a4 + a5 + a7)
        p = (a1*ratio)*G_n + (a2*ratio)*P_n + (a3*ratio)*S_n + \
            (a4*ratio)*X_n + (a5*ratio)*E_n + a6_val*AI_n - (a7*ratio)*(1-R_n)
        top3_track.append(pd.Series(p, index=sector_names).nlargest(3).index.tolist())
        for i, n in enumerate(sector_names):
            scores_track[n].append(p[i])

    fig3 = go.Figure()
    highlight = ["CNTT-Truyền thông", "CN chế biến chế tạo", "Tài chính-Ngân hàng",
                 "Logistics-Vận tải", "Y tế"]
    for n in highlight:
        fig3.add_scatter(x=a6_range, y=scores_track[n], mode="lines+markers",
                         name=n, line=dict(width=2))
    fig3.update_layout(
        title="Thay đổi Priority Score khi a₆ (AI Readiness) thay đổi",
        xaxis_title="a₆ (AI Readiness weight)",
        yaxis_title="Priority Score",
        legend=dict(orientation="h", y=-0.2),
        height=400, margin=dict(l=0, r=0, t=40, b=60),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("#### Top-3 thay đổi theo a₆")
    sens_df = pd.DataFrame(
        top3_track,
        columns=["#1", "#2", "#3"],
        index=[f"a₆={v:.2f}" for v in a6_range]
    )
    st.dataframe(sens_df, use_container_width=True)

with tab4:
    st.markdown("### So sánh 2 bộ trọng số chính sách")

    # Weights 1: Growth-oriented
    w_growth = np.array([0.25, 0.20, 0.15, 0.25, 0.05, 0.05, 0.05])
    # Weights 2: Inclusive-oriented
    w_inclusive = np.array([0.10, 0.05, 0.20, 0.05, 0.25, 0.10, 0.25])

    p_growth = w_growth[0]*G_n + w_growth[1]*P_n + w_growth[2]*S_n + \
               w_growth[3]*X_n + w_growth[4]*E_n + w_growth[5]*AI_n - w_growth[6]*(1-R_n)
    p_inclusive = w_inclusive[0]*G_n + w_inclusive[1]*P_n + w_inclusive[2]*S_n + \
                  w_inclusive[3]*X_n + w_inclusive[4]*E_n + w_inclusive[5]*AI_n - w_inclusive[6]*(1-R_n)

    df_compare = pd.DataFrame({
        "Ngành": sector_names,
        "Định hướng tăng trưởng": p_growth.round(4),
        "Hạng (TT)": pd.Series(p_growth).rank(ascending=False).astype(int),
        "Định hướng bao trùm": p_inclusive.round(4),
        "Hạng (BT)": pd.Series(p_inclusive).rank(ascending=False).astype(int),
    }).sort_values("Định hướng tăng trưởng", ascending=False)
    st.dataframe(df_compare, use_container_width=True, hide_index=True)

    fig4 = go.Figure()
    fig4.add_bar(x=sector_names, y=p_growth, name="Tăng trưởng",
                 marker_color="#e94560", opacity=0.8)
    fig4.add_bar(x=sector_names, y=p_inclusive, name="Bao trùm",
                 marker_color="#4299e1", opacity=0.8)
    fig4.update_layout(
        barmode="group", title="So sánh 2 bộ trọng số",
        xaxis_tickangle=-30, yaxis_title="Priority Score",
        legend=dict(orientation="h", y=1.05),
        height=420, margin=dict(l=0, r=0, t=40, b=80),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── AI Analyst ────────────────────────────────────────────────────────────────
top3_list = df_result["Ngành"].head(3).tolist()
context_str = (
    f"Trọng số: a1={a1}, a2={a2}, a3={a3}, a4={a4}, a5={a5}, a6={a6}, a7={a7}\n"
    f"Top 3 ngành ưu tiên: {top3_list}\n"
    f"Priority scores: {dict(zip(sector_names, priority.round(4)))}\n"
    f"Ngành CNTT-TT đứng thứ: {int(pd.Series(priority, index=sector_names).rank(ascending=False)['CNTT-Truyền thông'])}\n"
    f"Ngành Khai khoáng đứng thứ: {int(pd.Series(priority, index=sector_names).rank(ascending=False)['Khai khoáng'])}"
)
render_analyst_box(
    "Bài 3", "Chỉ số ưu tiên 10 ngành", context_str,
    extra_instruction="Giải thích tại sao Khai khoáng dù năng suất cao nhất nhưng không được ưu tiên."
)
