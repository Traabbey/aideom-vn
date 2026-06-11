import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pulp import (LpProblem, LpMaximize, LpVariable, lpSum,
                  LpBinary, LpStatus, value, PULP_CBC_CMD)
import sys
from pathlib import Path

# Add project root to sys.path so utils package can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.ai_analyst import render_analyst_box
from utils.hide_nav import hide_auto_nav

# Page configuration
st.set_page_config(page_title="Bài 5 — MIP 15 dự án", page_icon="🏗️", layout="wide")

hide_auto_nav()

st.markdown("# 🏗️ Bài 5 — MIP Lựa chọn 15 dự án CĐS quốc gia")
st.markdown(
    """<span style='background:#2c5282;color:#bee3f8;padding:3px 10px;border-radius:12px;font-size:0.8rem'>CẤP ĐỘ TRUNG BÌNH</span>
    &nbsp;&nbsp;Mixed Integer Programming &nbsp;&nbsp; PuLP/CBC""",
    unsafe_allow_html=True,
)

st.latex(r"\max \sum_{i=1}^{15} B_i \cdot y_i \quad \text{s.t.} \quad y_i \in \{0,1\}")

# ── 15 Projects Dataset ─────────────────────────────────────────────────────────
projects = {
    1:  {"name": "TTDL quốc gia Hòa Lạc",       "field": "Hạ tầng",    "C": 12000, "B": 21500, "C1": 8500},
    2:  {"name": "TTDL quốc gia phía Nam",        "field": "Hạ tầng",    "C": 11500, "B": 20800, "C1": 7500},
    3:  {"name": "5G phủ sóng toàn quốc",         "field": "Hạ tầng",    "C": 18000, "B": 32500, "C1": 12000},
    4:  {"name": "VNeID 2.0",                     "field": "CP số",       "C": 4500,  "B": 9200,  "C1": 3500},
    5:  {"name": "Cổng DVC quốc gia v3",          "field": "CP số",       "C": 3200,  "B": 6800,  "C1": 2500},
    6:  {"name": "Y tế số quốc gia",              "field": "Y tế số",     "C": 5800,  "B": 11400, "C1": 4000},
    7:  {"name": "Giáo dục số K-12",              "field": "Giáo dục",   "C": 6500,  "B": 12200, "C1": 4500},
    8:  {"name": "Trung tâm AI quốc gia",         "field": "AI",          "C": 15000, "B": 28500, "C1": 9000},
    9:  {"name": "Sandbox tài chính số",          "field": "Tài chính",  "C": 2500,  "B": 5800,  "C1": 1800},
    10: {"name": "Logistics thông minh",          "field": "Logistics",  "C": 7200,  "B": 13800, "C1": 5000},
    11: {"name": "Nông nghiệp số ĐBSCL",          "field": "Nông nghiệp","C": 4800,  "B": 8500,  "C1": 3500},
    12: {"name": "Đào tạo 50k kỹ sư AI",          "field": "Nhân lực",   "C": 8500,  "B": 16200, "C1": 5500},
    13: {"name": "KCN bán dẫn Bắc Ninh-Bắc Giang","field": "Bán dẫn",   "C": 20000, "B": 35000, "C1": 13000},
    14: {"name": "An ninh mạng quốc gia SOC",     "field": "An ninh",    "C": 3800,  "B": 7500,  "C1": 2800},
    15: {"name": "Open Data quốc gia",            "field": "Dữ liệu",    "C": 1500,  "B": 3800,  "C1": 1200},
}

# ── Sidebar parameters ──────────────────────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Ràng buộc")
budget_total = st.sidebar.slider("Ngân sách tổng 5 năm (tỷ)", 60000, 120000, 80000, 5000)
budget_y12   = st.sidebar.slider("Ngân sách năm 1-2 (tỷ)", 25000, 60000, 40000, 2500)
min_proj     = st.sidebar.slider("Số dự án tối thiểu", 5, 10, 7, 1)
max_proj     = st.sidebar.slider("Số dự án tối đa", 8, 15, 11, 1)
force_p1p2   = st.sidebar.checkbox("Bắt buộc chọn cả P1 và P2 (redundancy)", False)

# Completion probability (Question 5.4.4)
prob = {1:0.85,2:0.85,3:0.85,4:0.75,5:0.75,6:0.80,7:0.80,
        8:0.65,9:0.80,10:0.80,11:0.80,12:0.65,13:0.65,14:0.80,15:0.80}
use_expected = st.sidebar.checkbox("Tối đa hóa lợi ích kỳ vọng E[Z] (có rủi ro)", False)

# ── MIP Solver ─────────────────────────────────────────────────────────────────
def solve_mip():
    m = LpProblem("VN_Project_Selection", LpMaximize)
    y = {i: LpVariable(f"y{i}", cat=LpBinary) for i in projects}

    B_eff = {i: projects[i]["B"] * (prob[i] if use_expected else 1.0) for i in projects}
    m += lpSum(B_eff[i] * y[i] for i in projects)

    m += lpSum(projects[i]["C"] * y[i] for i in projects) <= budget_total
    m += lpSum(projects[i]["C1"] * y[i] for i in projects) <= budget_y12
    m += y[1] + y[2] <= (2 if force_p1p2 else 1)
    m += y[8] <= y[12]
    m += y[13] <= y[12]
    m += y[4] + y[5] >= 1
    m += y[14] >= 1
    m += lpSum(y[i] for i in projects) >= min_proj
    m += lpSum(y[i] for i in projects) <= max_proj

    if force_p1p2:
        m += y[1] >= 1
        m += y[2] >= 1

    m.solve(PULP_CBC_CMD(msg=False))
    return m, y

with st.spinner("Đang giải MIP..."):
    m, y = solve_mip()

status = LpStatus[m.status]

# ── Result Tabs ─────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["✅ Dự án được chọn", "📊 Phân tích", "💡 Thay đổi ngân sách"])

with tab1:
    if status == "Optimal":
        selected = [i for i in projects if value(y[i]) > 0.5]
        not_selected = [i for i in projects if value(y[i]) <= 0.5]

        Z_opt = value(m.objective)
        total_cost = sum(projects[i]["C"] for i in selected)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng lợi ích Z*", f"{Z_opt:,.0f} tỷ VND")
        col2.metric("Số dự án chọn", len(selected))
        col3.metric("Tổng chi phí", f"{total_cost:,} tỷ VND")
        col4.metric("NPV/Chi phí", f"{Z_opt/total_cost:.2f}x")

        df_selected = pd.DataFrame([{
            "Mã": f"P{i}",
            "Tên dự án": projects[i]["name"],
            "Lĩnh vực": projects[i]["field"],
            "Chi phí (tỷ)": projects[i]["C"],
            "Lợi ích NPV (tỷ)": projects[i]["B"],
            "B/C ratio": round(projects[i]["B"]/projects[i]["C"], 2),
        } for i in selected])
        st.success(f"✅ **{len(selected)} dự án được chọn:**")
        st.dataframe(df_selected, use_container_width=True, hide_index=True)

        df_not = pd.DataFrame([{
            "Mã": f"P{i}",
            "Tên dự án": projects[i]["name"],
            "Lý do loại": "Ngân sách/ràng buộc",
            "B/C ratio": round(projects[i]["B"]/projects[i]["C"], 2),
        } for i in not_selected])
        st.warning("❌ Dự án không được chọn:")
        st.dataframe(df_not, use_container_width=True, hide_index=True)
    else:
        st.error(f"❌ Không khả thi: {status}. Thử nới ngân sách hoặc giảm số dự án tối thiểu!")

with tab2:
    if status == "Optimal":
        fig = go.Figure()
        colors_sel = ["#68d391" if value(y[i]) > 0.5 else "#fc8181" for i in projects]
        fig.add_scatter(
            x=[projects[i]["C"] for i in projects],
            y=[projects[i]["B"] for i in projects],
            mode="markers+text",
            text=[f"P{i}" for i in projects],
            textposition="top center",
            marker=dict(size=14, color=colors_sel, line=dict(width=2, color="white")),
        )
        fig.update_layout(
            title="Chi phí vs Lợi ích (xanh=chọn, đỏ=không chọn)",
            xaxis_title="Chi phí (tỷ VND)",
            yaxis_title="Lợi ích NPV (tỷ VND)",
            height=420, margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("### Phân tích khi nới ngân sách")
    budgets = [70000, 80000, 90000, 100000, 110000, 120000]
    results = []
    for b in budgets:
        # Solve with different budgets
        m2 = LpProblem(f"mip_{b}", LpMaximize)
        y2 = {i: LpVariable(f"y2_{b}_{i}", cat=LpBinary) for i in projects}
        m2 += lpSum(projects[i]["B"] * y2[i] for i in projects)
        m2 += lpSum(projects[i]["C"] * y2[i] for i in projects) <= b
        m2 += lpSum(projects[i]["C1"] * y2[i] for i in projects) <= b * 0.5
        m2 += y2[1] + y2[2] <= 1
        m2 += y2[8] <= y2[12]; m2 += y2[13] <= y2[12]
        m2 += y2[4] + y2[5] >= 1; m2 += y2[14] >= 1
        m2 += lpSum(y2[i] for i in projects) >= 7
        m2 += lpSum(y2[i] for i in projects) <= 11
        m2.solve(PULP_CBC_CMD(msg=False))
        if LpStatus[m2.status] == "Optimal":
            sel = [i for i in projects if value(y2[i]) > 0.5]
            results.append({"Ngân sách": b, "Z*": value(m2.objective), "Số dự án": len(sel)})

    df_budget = pd.DataFrame(results)
    st.dataframe(df_budget, use_container_width=True, hide_index=True)

    fig3 = go.Figure()
    fig3.add_bar(x=df_budget["Ngân sách"], y=df_budget["Z*"],
                 marker_color="#4299e1", name="Z*")
    fig3.update_layout(
        xaxis_title="Ngân sách (tỷ VND)", yaxis_title="Z* (tỷ VND)",
        height=350, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig3, use_container_width=True)

# ── AI Analyst ────────────────────────────────────────────────────────────────
if status == "Optimal":
    context_str = (
        f"Ngân sách: {budget_total:,} tỷ VND | Năm 1-2: {budget_y12:,} tỷ\n"
        f"Dự án được chọn: {[f'P{i}' for i in selected]}\n"
        f"Tổng lợi ích Z* = {Z_opt:,.0f} tỷ | Chi phí = {total_cost:,} tỷ\n"
        f"Dự án không chọn: {[f'P{i}' for i in not_selected]}\n"
        f"Ràng buộc tiên quyết: P8≤P12, P13≤P12, P14 bắt buộc"
    )
    render_analyst_box(
        "Bài 5", "MIP Lựa chọn 15 dự án CĐS", context_str,
        extra_instruction="Giải thích tại sao P15 (Open Data, B/C cao) thường không được chọn."
    )
