import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pulp import (LpProblem, LpMaximize, LpVariable, lpSum,
                  LpStatus, value, PULP_CBC_CMD)
import sys
from pathlib import Path

# Add project root to sys.path so utils package can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.ai_analyst import render_analyst_box
from utils.hide_nav import hide_auto_nav

# Page configuration
st.set_page_config(page_title="Bài 4 — LP Ngành-Vùng", page_icon="🗺️", layout="wide")

hide_auto_nav()

st.markdown("# 🗺️ Bài 4 — LP Phân bổ ngân sách số ngành-vùng")
st.markdown(
    """<span style='background:#2c5282;color:#bee3f8;padding:3px 10px;border-radius:12px;font-size:0.8rem'>CẤP ĐỘ TRUNG BÌNH</span>
    &nbsp;&nbsp;PuLP &nbsp;&nbsp; 24 biến &nbsp;&nbsp; Ràng buộc công bằng vùng""",
    unsafe_allow_html=True,
)

st.latex(r"\max Z = \sum_r \sum_j \beta_{j,r} \cdot x_{j,r}")

# ── Data ──────────────────────────────────────────────────────────────────
regions = ["Trung du MN phía Bắc", "Đồng bằng sông Hồng",
           "Bắc Trung Bộ+DH TBộ", "Tây Nguyên", "Đông Nam Bộ", "ĐB sông Cửu Long"]
region_codes = ["NMM", "RRD", "NCC", "CH", "SE", "MD"]
items = ["I (Hạ tầng)", "D (CĐS DN)", "AI", "H (Nhân lực)"]
item_codes = ["I", "D", "AI", "H"]

beta = {
    "NMM": [1.15, 0.85, 0.55, 1.30],
    "RRD": [0.95, 1.25, 1.40, 1.05],
    "NCC": [1.05, 0.95, 0.85, 1.15],
    "CH":  [1.20, 0.75, 0.45, 1.35],
    "SE":  [0.90, 1.30, 1.55, 1.00],
    "MD":  [1.10, 0.85, 0.65, 1.25],
}
D0 = {"NMM": 38, "RRD": 78, "NCC": 55, "CH": 32, "SE": 82, "MD": 48}

# ── Sidebar parameters ──────────────────────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Tham số")
total_budget   = st.sidebar.slider("Ngân sách tổng (tỷ VND)",      30000, 80000, 50000, 1000)
floor_region   = st.sidebar.slider("Sàn ngân sách mỗi vùng (tỷ)",  1000,  6000,  3000,  500)
ceiling_region = st.sidebar.slider("Trần ngân sách mỗi vùng (tỷ)", 6000,  20000, 15000, 500)
floor_H        = st.sidebar.slider("Sàn tổng nhân lực số (tỷ)",     3000,  15000, 6000,  500)
gamma_param    = st.sidebar.slider("γ (hiệu quả CĐS)",              0.001, 0.005, 0.002, 0.001)
lambda_param   = st.sidebar.slider("λ (ngưỡng công bằng)",          0.5,   0.9,   0.7,   0.05)
use_fairness   = st.sidebar.checkbox("Dùng ràng buộc công bằng C5", value=True)

# ── Preliminary feasibility check ───────────────────────────────────────────────
n_regions = 6
min_total_needed = floor_region * n_regions + floor_H
feasible_check = (
    floor_region * n_regions <= total_budget
    and floor_region <= ceiling_region
    and floor_H <= total_budget
    and min_total_needed <= total_budget
)
if not feasible_check:
    st.sidebar.error(
        f"⚠️ Tham số xung đột!\n\n"
        f"Sàn tối thiểu cần: **{floor_region*n_regions:,}** (6 vùng × {floor_region:,})\n\n"
        f"+ Sàn nhân lực: **{floor_H:,}**\n\n"
        f"= Tổng tối thiểu: **{min_total_needed:,}** > Ngân sách **{total_budget:,}**\n\n"
        f"→ Hãy tăng ngân sách hoặc giảm sàn."
    )

# ── LP Solver ──────────────────────────────────────────────────────────────────
def solve_lp(fairness=True):
    m = LpProblem("VN_Digital_Budget", LpMaximize)
    x = {(r, j): LpVariable(f"x_{r}_{j}", lowBound=0)
         for r in region_codes for j in item_codes}

    # Objective
    m += lpSum(beta[r][k] * x[(r, item_codes[k])]
               for r in region_codes for k, j in enumerate(item_codes))

    # C1: Total budget
    m += lpSum(x[(r, j)] for r in region_codes for j in item_codes) <= total_budget

    # C2 & C3: Floor/ceiling per region
    for r in region_codes:
        m += lpSum(x[(r, j)] for j in item_codes) >= floor_region
        m += lpSum(x[(r, j)] for j in item_codes) <= ceiling_region

    # C4: HR floor
    m += lpSum(x[(r, "H")] for r in region_codes) >= floor_H

    # C5: Regional Fairness
    if fairness:
        M = LpVariable("Dmax", lowBound=0)
        for r in region_codes:
            m += D0[r] + gamma_param * x[(r, "D")] <= M
        for r in region_codes:
            m += D0[r] + gamma_param * x[(r, "D")] >= lambda_param * M

    m.solve(PULP_CBC_CMD(msg=False))
    return m, x

with st.spinner("Đang giải LP..."):
    m, x = solve_lp(use_fairness)
    m_no_fair, x_no_fair = solve_lp(False)

status = LpStatus[m.status]

# ── Results Layout ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Phân bổ tối ưu", "🗺️ Heatmap", "⚖️ Chi phí công bằng"])

with tab1:
    if status == "Optimal":
        Z_opt = value(m.objective)
        st.metric("Z* (GDP gain kỳ vọng)", f"{Z_opt:,.0f} tỷ VND")

        # Results table
        result_matrix = []
        for i, r in enumerate(region_codes):
            row = [regions[i]]
            total_r = 0
            for j in item_codes:
                v = value(x[(r, j)])
                row.append(round(v, 0) if v else 0)
                total_r += v if v else 0
            row.append(round(total_r, 0))
            result_matrix.append(row)

        df_res = pd.DataFrame(result_matrix,
                              columns=["Vùng"] + items + ["Tổng"])
        st.dataframe(df_res, use_container_width=True, hide_index=True)

        # Stacked bar
        fig = go.Figure()
        colors = ["#4299e1", "#68d391", "#f6ad55", "#e94560"]
        for k, (item, code) in enumerate(zip(items, item_codes)):
            vals = [value(x[(r, code)]) or 0 for r in region_codes]
            fig.add_bar(x=regions, y=vals, name=item,
                        marker_color=colors[k])
        fig.update_layout(
            barmode="stack", title="Phân bổ ngân sách tối ưu theo vùng",
            yaxis_title="Tỷ VND", xaxis_tickangle=-20,
            legend=dict(orientation="h", y=1.05),
            height=420, margin=dict(l=0, r=0, t=50, b=60),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"❌ Không tìm được nghiệm tối ưu: **{status}**")
        st.info(
            f"💡 **Gợi ý sửa:**\n\n"
            f"- Tăng **Ngân sách tổng** lên ≥ **{floor_region*6 + floor_H:,}** tỷ\n\n"
            f"- Hoặc giảm **Sàn mỗi vùng** (hiện: {floor_region:,} × 6 = {floor_region*6:,} tỷ)\n\n"
            f"- Hoặc giảm **Sàn nhân lực** (hiện: {floor_H:,} tỷ)\n\n"
            f"- Hoặc tắt ràng buộc công bằng C5"
        )

with tab2:
    if status == "Optimal":
        heatmap_data = []
        for i, r in enumerate(region_codes):
            for j in item_codes:
                heatmap_data.append([regions[i], j, value(x[(r, j)]) or 0])

        df_heat = pd.DataFrame(heatmap_data, columns=["Vùng", "Hạng mục", "Giá trị"])
        pivot = df_heat.pivot(index="Vùng", columns="Hạng mục", values="Giá trị")

        fig2 = px.imshow(
            pivot,
            labels=dict(x="Hạng mục đầu tư", y="Vùng", color="Tỷ VND"),
            color_continuous_scale="Blues",
            aspect="auto",
            text_auto=".0f",
        )
        fig2.update_layout(
            title="Heatmap phân bổ tối ưu (tỷ VND)",
            height=400, margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig2, use_container_width=True)

with tab3:
    Z_fair = value(m.objective)
    Z_no_fair = value(m_no_fair.objective)
    cost_fair = Z_no_fair - Z_fair

    col1, col2, col3 = st.columns(3)
    col1.metric("Z* có công bằng", f"{Z_fair:,.0f} tỷ VND")
    col2.metric("Z* không công bằng", f"{Z_no_fair:,.0f} tỷ VND")
    col3.metric("Chi phí công bằng", f"{cost_fair:,.0f} tỷ VND",
                delta=f"{cost_fair/Z_no_fair*100:.1f}%", delta_color="inverse")

    st.info(
        f"Ràng buộc công bằng vùng làm giảm GDP gain **{cost_fair:,.0f} tỷ VND** "
        f"({cost_fair/Z_no_fair*100:.1f}%) so với không có ràng buộc."
    )

# ── AI Analyst ────────────────────────────────────────────────────────────────
if status == "Optimal":
    context_str = (
        f"Ngân sách tổng: {total_budget:,} tỷ VND\n"
        f"Z* (có công bằng): {Z_fair:,.0f} tỷ VND\n"
        f"Z* (không công bằng): {Z_no_fair:,.0f} tỷ VND\n"
        f"Chi phí công bằng: {cost_fair:,.0f} tỷ VND ({cost_fair/Z_no_fair*100:.1f}%)\n"
        f"Sàn mỗi vùng: {floor_region:,} | Trần: {ceiling_region:,} tỷ VND\n"
        f"λ công bằng = {lambda_param}"
    )
    render_analyst_box(
        "Bài 4", "LP Phân bổ ngân sách ngành-vùng", context_str,
        extra_instruction="Bình luận về chi phí kinh tế của công bằng vùng miền và gợi ý chính sách."
    )
