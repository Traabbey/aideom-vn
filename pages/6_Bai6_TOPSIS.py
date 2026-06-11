import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

# Add project root to sys.path so utils package can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.data_loader import load_regions
from utils.ai_analyst import render_analyst_box
from utils.hide_nav import hide_auto_nav

# Page configuration
st.set_page_config(page_title="Bài 6 — TOPSIS 6 vùng", page_icon="🏆", layout="wide")

hide_auto_nav()

st.markdown("# 🏆 Bài 6 — TOPSIS Xếp hạng 6 vùng kinh tế")
st.markdown(
    """<span style='background:#2c5282;color:#bee3f8;padding:3px 10px;border-radius:12px;font-size:0.8rem'>CẤP ĐỘ TRUNG BÌNH</span>
    &nbsp;&nbsp;TOPSIS &nbsp;&nbsp; Entropy weights""",
    unsafe_allow_html=True,
)

st.latex(r"C_i^* = \frac{S_i^-}{S_i^* + S_i^-}, \quad 0 \leq C_i^* \leq 1")

# ── Data loading ──────────────────────────────────────────────────────────────────
df = load_regions()
regions = df["region_name_vi"].tolist()

X = df[["grdp_per_capita_million_VND", "fdi_registered_billion_USD",
        "digital_index_0_100", "ai_readiness_0_100",
        "trained_labor_pct", "rd_intensity_pct",
        "internet_penetration_pct", "gini_coef"]].values.astype(float)

criteria = ["GRDP/người", "FDI", "Digital Index", "AI Readiness",
            "LĐ ĐT", "R&D/GRDP", "Internet", "Gini"]
is_benefit = [True, True, True, True, True, True, True, False]

# ── Sidebar expert weights ─────────────────────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Trọng số chuyên gia")
w1 = st.sidebar.slider("GRDP/người", 0.05, 0.30, 0.10, 0.05)
w2 = st.sidebar.slider("FDI", 0.05, 0.30, 0.10, 0.05)
w3 = st.sidebar.slider("Digital Index", 0.05, 0.30, 0.15, 0.05)
w4 = st.sidebar.slider("AI Readiness", 0.05, 0.40, 0.20, 0.05)
w5 = st.sidebar.slider("LĐ qua ĐT", 0.05, 0.30, 0.15, 0.05)
w6 = st.sidebar.slider("R&D/GRDP", 0.05, 0.30, 0.15, 0.05)
w7 = st.sidebar.slider("Internet", 0.05, 0.20, 0.05, 0.05)
w8 = st.sidebar.slider("Gini (chi phí)", 0.05, 0.30, 0.10, 0.05)

w_expert = np.array([w1, w2, w3, w4, w5, w6, w7, w8])
w_expert = w_expert / w_expert.sum()  # Normalize to sum up to 1.0

# ── TOPSIS Algorithm ───────────────────────────────────────────────────────────────
def topsis(X, w, is_benefit):
    # Vector normalization
    R = X / np.sqrt((X**2).sum(axis=0))
    V = R * w
    # Determine ideal best and ideal worst
    A_star = np.where(is_benefit, V.max(axis=0), V.min(axis=0))
    A_neg  = np.where(is_benefit, V.min(axis=0), V.max(axis=0))
    # Compute distances
    S_star = np.sqrt(((V - A_star)**2).sum(axis=1))
    S_neg  = np.sqrt(((V - A_neg)**2).sum(axis=1))
    # Calculate closeness coefficient
    C_star = S_neg / (S_star + S_neg)
    return C_star, S_star, S_neg

def entropy_weights(X):
    X_pos = np.abs(X) + 1e-10
    P = X_pos / X_pos.sum(axis=0)
    k = 1.0 / np.log(len(X))
    E = -k * np.nansum(P * np.log(P + 1e-12), axis=0)
    d = 1 - E
    return d / d.sum()

C_expert, S_star_e, S_neg_e = topsis(X, w_expert, is_benefit)
w_entropy = entropy_weights(X)
C_entropy, S_star_en, S_neg_en = topsis(X, w_entropy, is_benefit)

# ── Result Tabs ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["🏆 Xếp hạng", "📊 So sánh Entropy", "🔬 Độ nhạy AI", "📋 Dữ liệu gốc"]
)

with tab1:
    df_result = pd.DataFrame({
        "Vùng": regions,
        "C* (chuyên gia)": C_expert.round(4),
        "Xếp hạng": pd.Series(C_expert).rank(ascending=False).astype(int),
        "S* (khoảng đến lý tưởng+)": S_star_e.round(4),
        "S⁻ (khoảng đến lý tưởng-)": S_neg_e.round(4),
    }).sort_values("C* (chuyên gia)", ascending=False).reset_index(drop=True)
    df_result.index += 1
    st.dataframe(df_result, use_container_width=True)

    colors = ["#e94560","#f6ad55","#68d391","#4299e1","#b794f4","#718096"]
    fig = go.Figure(go.Bar(
        x=df_result["C* (chuyên gia)"],
        y=df_result["Vùng"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:.4f}" for v in df_result["C* (chuyên gia)"]],
        textposition="outside",
    ))
    fig.update_layout(
        title="TOPSIS Score — Mức độ sẵn sàng AI (cao = tốt hơn)",
        xaxis_title="C* Score",
        yaxis=dict(autorange="reversed"),
        height=380, margin=dict(l=0, r=60, t=40, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    top1 = df_result["Vùng"].iloc[0]
    st.success(f"🥇 **Vùng ưu tiên nhất:** {top1} — nên triển khai trung tâm AI đầu tiên!")

with tab2:
    df_ent = pd.DataFrame({
        "Vùng": regions,
        "C* Chuyên gia": C_expert.round(4),
        "Hạng CG": pd.Series(C_expert).rank(ascending=False).astype(int),
        "C* Entropy": C_entropy.round(4),
        "Hạng Entropy": pd.Series(C_entropy).rank(ascending=False).astype(int),
        "Thay đổi hạng": (pd.Series(C_expert).rank(ascending=False) -
                          pd.Series(C_entropy).rank(ascending=False)).astype(int),
    })
    st.dataframe(df_ent, use_container_width=True, hide_index=True)

    # Entropy vs Expert weights comparison
    df_w = pd.DataFrame({
        "Tiêu chí": criteria,
        "Chuyên gia": w_expert.round(4),
        "Entropy": w_entropy.round(4),
    })
    fig2 = go.Figure()
    fig2.add_bar(x=criteria, y=w_expert, name="Chuyên gia", marker_color="#e94560")
    fig2.add_bar(x=criteria, y=w_entropy, name="Entropy", marker_color="#4299e1")
    fig2.update_layout(
        barmode="group", title="So sánh trọng số Chuyên gia vs Entropy",
        yaxis_title="Trọng số",
        legend=dict(orientation="h", y=1.05),
        height=350, margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.markdown("### Phân tích độ nhạy theo trọng số AI Readiness (w₄)")
    w4_range = np.arange(0.05, 0.55, 0.05)
    rank_track = {r: [] for r in regions}

    for w4_val in w4_range:
        w_temp = w_expert.copy()
        w_temp[3] = w4_val
        w_temp = w_temp / w_temp.sum()
        C_temp, _, _ = topsis(X, w_temp, is_benefit)
        ranks = pd.Series(C_temp, index=regions).rank(ascending=False)
        for r in regions:
            rank_track[r].append(ranks[r])

    fig3 = go.Figure()
    for r in regions:
        fig3.add_scatter(x=w4_range, y=rank_track[r], mode="lines+markers",
                         name=r, line=dict(width=2))
    fig3.update_layout(
        title="Thay đổi xếp hạng khi w₄ (AI Readiness) thay đổi",
        xaxis_title="w₄ (AI Readiness weight)",
        yaxis_title="Xếp hạng (1=tốt nhất)",
        yaxis=dict(autorange="reversed"),
        legend=dict(orientation="h", y=-0.25),
        height=420, margin=dict(l=0, r=0, t=40, b=80),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    st.markdown("### Dữ liệu 6 vùng kinh tế-xã hội")
    st.dataframe(df, use_container_width=True, hide_index=True)

# ── AI Analyst ────────────────────────────────────────────────────────────────
rank_expert = pd.Series(C_expert, index=regions).rank(ascending=False).astype(int)
top3_regions = pd.Series(C_expert, index=regions).nlargest(3).index.tolist()
context_str = (
    f"Trọng số chuyên gia (chuẩn hóa): {dict(zip(criteria, w_expert.round(3)))}\n"
    f"Xếp hạng TOPSIS: {dict(zip(regions, rank_expert))}\n"
    f"Top 3 vùng ưu tiên AI: {top3_regions}\n"
    f"Trọng số Entropy: {dict(zip(criteria, w_entropy.round(3)))}\n"
    f"Thay đổi xếp hạng lớn nhất khi dùng Entropy: "
    f"{(rank_expert - pd.Series(C_entropy, index=regions).rank(ascending=False).astype(int)).abs().idxmax()}"
)
render_analyst_box(
    "Bài 6", "TOPSIS Xếp hạng 6 vùng kinh tế", context_str,
    extra_instruction="Khuyến nghị 3 vùng nên xây dựng trung tâm AI quốc gia theo QĐ 127/QĐ-TTg."
)
