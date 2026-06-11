import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root to sys.path so utils package can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.ai_analyst import render_analyst_box
from utils.hide_nav import hide_auto_nav

# Page configuration
st.set_page_config(page_title="Bài 9 — Lao động & AI", page_icon="👷", layout="wide")

hide_auto_nav()

st.markdown("# 👷 Bài 9 — Tác động AI tới thị trường lao động")
st.markdown(
    """<span style='background:#553c9a;color:#e9d8fd;padding:3px 10px;border-radius:12px;font-size:0.8rem'>CẤP ĐỘ KHÁ KHÓ</span>
    &nbsp;&nbsp;CVXPY &nbsp;&nbsp; NetJob optimization""",
    unsafe_allow_html=True,
)

st.latex(r"\text{NetJob}_i = \text{NewJob}_i + \text{UpgradeJob}_i - \text{DisplacedJob}_i \geq 0")
st.latex(r"\max \sum_i \text{NetJob}_i \quad \text{s.t.} \quad \sum_i (x^{AI}_i + x^H_i) \leq B")

# ── 8 Sectors Dataset ──────────────────────────────────────────────────────────
sectors = ["Nông-Lâm-TS", "CN chế biến", "Xây dựng", "Bán buôn-lẻ",
           "Tài chính-NH", "Logistics", "CNTT-TT", "Giáo dục"]
labor   = np.array([13.20, 11.50, 4.80, 7.80, 0.55, 1.95, 0.62, 2.15])
risk    = np.array([18, 42, 25, 38, 52, 35, 28, 22]) / 100
a1 = np.array([8.5, 32.5, 12.8, 22.4, 45.8, 28.5, 62.5, 18.5])
b1 = np.array([45,  28,   35,   32,   22,   30,   20,   55])
c1 = np.array([5.2, 62.4, 18.5, 48.2, 72.5, 42.8, 32.5, 12.5])
d1 = np.array([50,  32,   42,   38,   26,   36,   24,   62])

# ── Sidebar parameters ──────────────────────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Tham số")
budget = st.sidebar.slider("Ngân sách tổng (tỷ VND)", 10000, 50000, 30000, 1000)
max_displace_pct = st.sidebar.slider("Giới hạn dịch chuyển tối đa (%)", 3, 15, 5, 1)
use_limit = st.sidebar.checkbox("Dùng ràng buộc giới hạn dịch chuyển", True)

# ── Optimization Solver ─────────────────────────────────────────────────────────────
try:
    import cvxpy as cp
    N = 8
    x_AI = cp.Variable(N, nonneg=True)
    x_H  = cp.Variable(N, nonneg=True)

    NewJob   = cp.multiply(a1, x_AI)
    Upgrade  = cp.multiply(b1, x_H)
    Displaced = cp.multiply(c1 * risk, x_AI)
    Retrain  = cp.multiply(d1, x_H)
    NetJob   = NewJob + Upgrade - Displaced

    constraints = [
        cp.sum(x_AI + x_H) <= budget,
        NetJob >= 0,
        Displaced <= Retrain,
    ]
    if use_limit:
        for i in range(N):
            constraints.append(
                c1[i] * risk[i] * x_AI[i] <= max_displace_pct/100 * labor[i] * 1e6 / 1e9
            )

    prob = cp.Problem(cp.Maximize(cp.sum(NetJob)), constraints)
    prob.solve(solver=cp.SCS, verbose=False)

    if prob.status in ["optimal", "optimal_inaccurate"]:
        xAI_val = x_AI.value
        xH_val  = x_H.value
        netjob_val = (a1*xAI_val + b1*xH_val - c1*risk*xAI_val)
        displaced_val = c1 * risk * xAI_val
        newjob_val = a1 * xAI_val
        upgrade_val = b1 * xH_val

        tab1, tab2, tab3 = st.tabs(["📊 Kết quả", "📈 Biểu đồ", "🔀 Dòng chảy lao động"])

        with tab1:
            col1, col2, col3 = st.columns(3)
            col1.metric("Tổng NetJob", f"{netjob_val.sum():,.0f} việc làm")
            col2.metric("Tổng ngân sách dùng", f"{(xAI_val+xH_val).sum():,.0f} tỷ")
            col3.metric("NetJob/tỷ đầu tư", f"{netjob_val.sum()/(xAI_val+xH_val).sum():.1f}")

            df_res = pd.DataFrame({
                "Ngành": sectors,
                "x_AI (tỷ)": xAI_val.round(1),
                "x_H (tỷ)": xH_val.round(1),
                "Việc làm mới": newjob_val.round(0).astype(int),
                "Nâng cấp": upgrade_val.round(0).astype(int),
                "Dịch chuyển": displaced_val.round(0).astype(int),
                "NetJob": netjob_val.round(0).astype(int),
            })
            st.dataframe(df_res, use_container_width=True, hide_index=True)

        with tab2:
            fig = go.Figure()
            fig.add_bar(x=sectors, y=newjob_val, name="Việc làm mới AI",
                        marker_color="#68d391")
            fig.add_bar(x=sectors, y=upgrade_val, name="Nâng cấp kỹ năng",
                        marker_color="#4299e1")
            fig.add_bar(x=sectors, y=-displaced_val, name="Dịch chuyển",
                        marker_color="#fc8181")
            fig.update_layout(
                barmode="relative", title="Cấu trúc thay đổi việc làm theo ngành",
                yaxis_title="Số việc làm", xaxis_tickangle=-20,
                legend=dict(orientation="h", y=1.05),
                height=420, margin=dict(l=0, r=0, t=50, b=60),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.markdown("### Dòng chảy lao động (Sankey)")
            # Standard Sankey diagram
            fig_s = go.Figure(go.Sankey(
                node=dict(
                    label=["Nông-LS","CN CB","Xây dựng","Bán lẻ","TC-NH",
                           "Logistics","CNTT","GD",
                           "AI Jobs","Kỹ năng mới","Dịch chuyển"],
                    color=["#4299e1"]*8 + ["#68d391","#f6ad55","#fc8181"],
                    pad=15, thickness=20,
                ),
                link=dict(
                    source=list(range(8)) + list(range(8)) + list(range(8)),
                    target=[8]*8 + [9]*8 + [10]*8,
                    value=list(newjob_val.clip(0)) +
                          list(upgrade_val.clip(0)) +
                          list(displaced_val.clip(0)),
                    color=["rgba(104,211,145,0.4)"]*8 +
                          ["rgba(66,153,225,0.4)"]*8 +
                          ["rgba(252,129,129,0.4)"]*8,
                ),
            ))
            fig_s.update_layout(height=450, margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig_s, use_container_width=True)

        context_str = (
            f"Ngân sách: {budget:,} tỷ VND\n"
            f"Tổng NetJob: {netjob_val.sum():,.0f} việc làm\n"
            f"Ngành cần đầu tư H nhiều nhất: {sectors[xH_val.argmax()]} ({xH_val.max():.0f} tỷ)\n"
            f"Ngành dịch chuyển nhiều nhất: {sectors[displaced_val.argmax()]} ({displaced_val.max():.0f} việc)\n"
            f"NetJob âm: {[sectors[i] for i in range(N) if netjob_val[i] < 0]}"
        )
        render_analyst_box("Bài 9", "Lao động & AI", context_str)

    else:
        st.error(f"❌ Không khả thi: {prob.status}. Thử tắt ràng buộc giới hạn dịch chuyển!")

except ImportError:
    st.error("⚠️ Chưa cài cvxpy! Chạy: `pip install cvxpy` trong terminal.")
