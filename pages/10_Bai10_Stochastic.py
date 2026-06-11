import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pulp import (LpProblem, LpMaximize, LpVariable, lpSum,
                  LpStatus, value, PULP_CBC_CMD)
import sys
from pathlib import Path

# Add project root to sys.path so utils package can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.ai_analyst import render_analyst_box
from utils.hide_nav import hide_auto_nav

# Page configuration
st.set_page_config(page_title="Bài 10 — Stochastic SP", page_icon="🎲", layout="wide")

hide_auto_nav()

st.markdown("# 🎲 Bài 10 — Quy hoạch ngẫu nhiên hai giai đoạn")
st.markdown(
    """<span style='background:#742a2a;color:#fed7d7;padding:3px 10px;border-radius:12px;font-size:0.8rem'>CẤP ĐỘ KHÓ</span>
    &nbsp;&nbsp;Stochastic Programming &nbsp;&nbsp; VSS &nbsp;&nbsp; EVPI""",
    unsafe_allow_html=True,
)

st.latex(r"\max \sum_j \beta_j x_j + \sum_s p_s \sum_j \beta_j^s y_j^s")

# ── Scenarios Dataset ─────────────────────────────────────────────────────────────────
scenarios = {"s1": "Lạc quan", "s2": "Cơ sở", "s3": "Bi quan", "s4": "Khủng hoảng"}
prob_base = {"s1": 0.30, "s2": 0.45, "s3": 0.20, "s4": 0.05}
beta_base = {"I": 1.00, "D": 1.10, "AI": 1.25, "H": 0.95}
beta_s = {
    "s1": {"I":1.25,"D":1.35,"AI":1.55,"H":1.05},
    "s2": {"I":1.00,"D":1.10,"AI":1.25,"H":0.95},
    "s3": {"I":0.75,"D":0.85,"AI":0.90,"H":1.00},
    "s4": {"I":0.40,"D":0.50,"AI":0.55,"H":1.10},
}
items = ["I", "D", "AI", "H"]
item_labels = ["Hạ tầng số", "Chuyển đổi số", "AI", "Nhân lực"]

# ── Sidebar parameters ──────────────────────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Xác suất kịch bản")
p1 = st.sidebar.slider("P(Lạc quan s1)", 0.05, 0.50, 0.30, 0.05)
p2 = st.sidebar.slider("P(Cơ sở s2)",    0.10, 0.60, 0.45, 0.05)
p3 = st.sidebar.slider("P(Bi quan s3)",  0.05, 0.40, 0.20, 0.05)
p4 = 1 - p1 - p2 - p3
st.sidebar.metric("P(Khủng hoảng s4)", f"{p4:.2f}")
if p4 < 0:
    st.sidebar.error("Tổng xác suất > 1!")

prob = {"s1": p1, "s2": p2, "s3": p3, "s4": max(p4, 0.01)}

budget1 = st.sidebar.slider("Ngân sách GĐ1 (tỷ)", 40000, 80000, 65000, 2500)
budget2 = st.sidebar.slider("Dự phòng GĐ2 (tỷ)", 5000, 25000, 15000, 2500)

# ── Stochastic Solver Function ────────────────────────────────────────────────
def solve_sp(deterministic_scenario=None):
    m = LpProblem("SP_VN", LpMaximize)
    x = {j: LpVariable(f"x_{j}", lowBound=0) for j in items}
    y = {(s, j): LpVariable(f"y_{s}_{j}", lowBound=0)
         for s in scenarios for j in items}

    if deterministic_scenario:
        obj = (lpSum(beta_base[j]*x[j] for j in items) +
               lpSum(beta_s[deterministic_scenario][j]*y[(deterministic_scenario,j)]
                     for j in items))
    else:
        obj = (lpSum(beta_base[j]*x[j] for j in items) +
               lpSum(prob[s] * lpSum(beta_s[s][j]*y[(s,j)] for j in items)
                     for s in scenarios))
    m += obj
    m += lpSum(x[j] for j in items) <= budget1

    for s in scenarios:
        m += lpSum(y[(s,j)] for j in items) <= budget2
        m += y[(s,"AI")] <= 0.5 * x["H"]

    m.solve(PULP_CBC_CMD(msg=False))
    return m, x, y

# ── Three Problem Formulations ──────────────────────────────────────────────────
with st.spinner("Đang giải SP + EV + EVPI..."):
    m_sp, x_sp, y_sp = solve_sp()
    m_ev, x_ev, y_ev = solve_sp(deterministic_scenario="s2")  # EV: average scenario s2

    # EVPI: Solve each scenario separately and take the expected value
    evpi_total = 0
    for s in scenarios:
        ms, xs, ys = solve_sp(deterministic_scenario=s)
        if LpStatus[ms.status] == "Optimal":
            evpi_total += prob[s] * value(ms.objective)

Z_sp = value(m_sp.objective) if LpStatus[m_sp.status] == "Optimal" else None
Z_ev = value(m_ev.objective) if LpStatus[m_ev.status] == "Optimal" else None
VSS  = Z_sp - Z_ev if Z_sp and Z_ev else None
EVPI = evpi_total - Z_sp if Z_sp else None

# ── Results Layout ─────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Kết quả SP", "📈 VSS & EVPI", "🎯 So sánh kịch bản"])

with tab1:
    if Z_sp:
        st.metric("Z* (Stochastic SP)", f"{Z_sp:,.0f} tỷ VND")

        x_vals = {j: value(x_sp[j]) for j in items}
        df_x = pd.DataFrame({
            "Hạng mục": item_labels,
            "x* GĐ1 (tỷ VND)": [x_vals[j] for j in items],
            "Tỷ trọng (%)": [x_vals[j]/budget1*100 for j in items],
        })
        df_x["x* GĐ1 (tỷ VND)"] = df_x["x* GĐ1 (tỷ VND)"].round(0)
        df_x["Tỷ trọng (%)"] = df_x["Tỷ trọng (%)"].round(1)
        st.markdown("#### Quyết định giai đoạn 1 (Here-and-Now)")
        st.dataframe(df_x, use_container_width=True, hide_index=True)

        # Stage 2 based on scenarios
        st.markdown("#### Quyết định giai đoạn 2 (Wait-and-See)")
        y_data = []
        for s, sname in scenarios.items():
            row = {"Kịch bản": f"{s} {sname}", "Xác suất": prob[s]}
            for j, label in zip(items, item_labels):
                row[label] = round(value(y_sp[(s,j)]) or 0, 0)
            y_data.append(row)
        st.dataframe(pd.DataFrame(y_data), use_container_width=True, hide_index=True)

        fig = go.Figure()
        for j, label, color in zip(items, item_labels,
                                    ["#4299e1","#68d391","#f6ad55","#e94560"]):
            fig.add_bar(name=label,
                        x=list(scenarios.values()),
                        y=[value(y_sp[(s,j)]) or 0 for s in scenarios],
                        marker_color=color)
        fig.update_layout(
            barmode="group", title="Phân bổ bổ sung GĐ2 theo kịch bản",
            yaxis_title="Tỷ VND",
            legend=dict(orientation="h", y=1.05),
            height=380, margin=dict(l=0, r=0, t=50, b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    col1, col2, col3 = st.columns(3)
    col1.metric("Z* SP (Stochastic)", f"{Z_sp:,.0f}" if Z_sp else "N/A")
    col2.metric("Z* EV (Deterministic)", f"{Z_ev:,.0f}" if Z_ev else "N/A")
    col3.metric("VSS", f"{VSS:,.0f}" if VSS else "N/A",
                help="Value of Stochastic Solution = Z_SP - Z_EV")

    col4, col5 = st.columns(2)
    col4.metric("EVPI", f"{EVPI:,.0f}" if EVPI else "N/A",
                help="Expected Value of Perfect Information")
    col5.metric("VSS/Z_EV (%)", f"{VSS/Z_ev*100:.2f}%" if VSS and Z_ev else "N/A")

    st.info(
        f"**VSS = {VSS:,.0f}** tỷ → Cân nhắc bất định khi lập kế hoạch mang lại thêm {VSS:,.0f} tỷ GDP.\n\n"
        f"**EVPI = {EVPI:,.0f}** tỷ → Đây là giá trị tối đa sẵn lòng trả để có thông tin hoàn hảo."
        if VSS and EVPI else ""
    )

with tab3:
    st.markdown("### So sánh quyết định GĐ1: SP vs EV")
    if Z_sp and Z_ev:
        compare = pd.DataFrame({
            "Hạng mục": item_labels,
            "SP (nghìn tỷ)": [value(x_sp[j]) for j in items],
            "EV (nghìn tỷ)": [value(x_ev[j]) for j in items],
            "Chênh lệch": [value(x_sp[j]) - value(x_ev[j]) for j in items],
        })
        st.dataframe(compare.round(0), use_container_width=True, hide_index=True)

# ── AI Analyst ────────────────────────────────────────────────────────────────
if Z_sp:
    context_str = (
        f"Z* SP = {Z_sp:,.2f} tỷ | Z* EV = {Z_ev:,.2f} tỷ\n"
        f"VSS = {VSS:,.2f} tỷ ({VSS/Z_ev*100:.2f}%)\n"
        f"EVPI = {EVPI:,.2f} tỷ\n"
        f"Ngân sách GĐ1 = {budget1:,} tỷ | Dự phòng GĐ2 = {budget2:,} tỷ\n"
        f"Xác suất: s1={p1}, s2={p2}, s3={p3}, s4={p4:.2f}\n"
        f"SP đầu tư H nhiều hơn EV: {value(x_sp['H']) - value(x_ev['H']):.0f} tỷ"
    )
    render_analyst_box("Bài 10", "Stochastic SP hai giai đoạn", context_str,
                       extra_instruction="Giải thích ý nghĩa VSS và EVPI với hoạch định ngân sách Việt Nam.")
