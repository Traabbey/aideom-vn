import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.optimize import linprog
import sys
from pathlib import Path

# Add project root to sys.path so utils package can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.ai_analyst import render_analyst_box
from utils.hide_nav import hide_auto_nav

# Page configuration
st.set_page_config(page_title="Bài 2 — LP Ngân sách", page_icon="💰", layout="wide")

hide_auto_nav()

st.markdown("# 💰 Bài 2 — Phân bổ ngân sách 4 hạng mục đầu tư số")
st.markdown(
    """<span style='background:#744210;color:#fbd38d;padding:3px 10px;border-radius:12px;font-size:0.8rem'>CẤP ĐỘ DỄ</span>
    &nbsp;&nbsp;Linear Programming &nbsp;&nbsp; scipy.optimize""",
    unsafe_allow_html=True,
)

st.markdown("### Mô hình toán học")
st.latex(r"\max Z = 0.85x_1 + 1.20x_2 + 0.95x_3 + 1.35x_4")
st.markdown("**Ràng buộc:**")
st.latex(r"x_1 + x_2 + x_3 + x_4 \leq B")
st.latex(r"x_1 \geq 25,\quad x_2 \geq 15,\quad x_3 \geq 20,\quad x_4 \geq 10")
st.latex(r"x_2 + x_4 \geq 0.35(x_1+x_2+x_3+x_4)")

# ── Sidebar parameters ──────────────────────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Tham số")
B = st.sidebar.slider("Ngân sách tổng (nghìn tỷ VND)", 80, 200, 100, 5)
x1_min = st.sidebar.slider("Sàn hạ tầng số x₁ (nghìn tỷ)", 10, 40, 25, 1)
x2_min = st.sidebar.slider("Sàn AI x₂ (nghìn tỷ)", 5, 30, 15, 1)
x3_min = st.sidebar.slider("Sàn nhân lực số x₃ (nghìn tỷ)", 10, 40, 20, 1)
x4_min = st.sidebar.slider("Sàn R&D x₄ (nghìn tỷ)", 5, 20, 10, 1)

c_coef = np.array([0.85, 1.20, 0.95, 1.35])

# ── LP Solver ──────────────────────────────────────────────────────────────────
def solve_lp(budget):
    c = [-0.85, -1.20, -0.95, -1.35]
    A_ub = [
        [1, 1, 1, 1],
        [-1, 0, 0, 0],
        [0, -1, 0, 0],
        [0, 0, -1, 0],
        [0, 0, 0, -1],
        [0.35, -0.65, 0.35, -0.65],
    ]
    b_ub = [budget, -x1_min, -x2_min, -x3_min, -x4_min, 0]
    bounds = [(0, None)] * 4
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    return res

res = solve_lp(B)

# ── Results Layout ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Kết quả tối ưu", "📈 Phân tích độ nhạy", "💡 Shadow Price"])

with tab1:
    if res.success:
        x_opt = res.x
        Z_opt = -res.fun

        col1, col2, col3 = st.columns(3)
        col1.metric("Z* (GDP tăng thêm)", f"{Z_opt:.2f} nghìn tỷ VND")
        col2.metric("Tổng đầu tư", f"{x_opt.sum():.1f} nghìn tỷ VND")
        col3.metric("Hệ số hiệu quả", f"{Z_opt/B:.3f}")

        labels = ["Hạ tầng số (x₁)", "AI & Dữ liệu (x₂)", "Nhân lực số (x₃)", "R&D (x₄)"]
        colors = ["#4299e1", "#68d391", "#f6ad55", "#e94560"]

        df_opt = pd.DataFrame({
            "Hạng mục": labels,
            "Phân bổ tối ưu (nghìn tỷ)": x_opt.round(2),
            "Hệ số tác động": c_coef,
            "GDP tăng (nghìn tỷ)": (x_opt * c_coef).round(2),
            "Tỷ trọng (%)": (x_opt / x_opt.sum() * 100).round(1),
        })
        st.dataframe(df_opt, use_container_width=True, hide_index=True)

        fig = go.Figure()
        fig.add_bar(
            x=labels, y=x_opt,
            marker_color=colors,
            text=[f"{v:.1f}" for v in x_opt],
            textposition="outside",
        )
        fig.update_layout(
            title="Phân bổ ngân sách tối ưu",
            yaxis_title="Nghìn tỷ VND",
            height=380, margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Pie chart
        fig2 = go.Figure(go.Pie(
            labels=labels, values=x_opt,
            marker_colors=colors, hole=0.4,
        ))
        fig2.update_layout(
            title="Cơ cấu phân bổ ngân sách",
            height=350, margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.error("❌ Bài toán không khả thi! Hãy giảm các sàn tối thiểu hoặc tăng ngân sách.")

with tab2:
    st.markdown("### Phân tích độ nhạy theo ngân sách")
    budgets = list(range(80, 201, 10))
    z_vals = []
    x1_vals, x2_vals, x3_vals, x4_vals = [], [], [], []

    for b in budgets:
        r = solve_lp(b)
        if r.success:
            z_vals.append(-r.fun)
            x1_vals.append(r.x[0])
            x2_vals.append(r.x[1])
            x3_vals.append(r.x[2])
            x4_vals.append(r.x[3])
        else:
            z_vals.append(None)
            x1_vals.append(None); x2_vals.append(None)
            x3_vals.append(None); x4_vals.append(None)

    fig3 = go.Figure()
    fig3.add_scatter(x=budgets, y=z_vals, mode="lines+markers",
                     line=dict(color="#e94560", width=3), name="Z*(B)")
    fig3.add_vline(x=B, line_dash="dash", line_color="#f6ad55",
                   annotation_text=f"B={B}")
    fig3.update_layout(
        title="Đường cong Z*(B) — GDP tăng theo ngân sách",
        xaxis_title="Ngân sách B (nghìn tỷ VND)",
        yaxis_title="Z* (nghìn tỷ VND)",
        height=380, margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Sensitivity results table
    df_sens = pd.DataFrame({
        "Ngân sách B": budgets,
        "Z*": [f"{v:.2f}" if v else "N/A" for v in z_vals],
        "x₁ (HT số)": [f"{v:.1f}" if v else "N/A" for v in x1_vals],
        "x₂ (AI)": [f"{v:.1f}" if v else "N/A" for v in x2_vals],
        "x₃ (NL số)": [f"{v:.1f}" if v else "N/A" for v in x3_vals],
        "x₄ (R&D)": [f"{v:.1f}" if v else "N/A" for v in x4_vals],
    })
    st.dataframe(df_sens, use_container_width=True, hide_index=True)

with tab3:
    st.markdown("### Shadow Price (Giá đối ngẫu)")
    st.info(
        "Shadow price của ràng buộc ngân sách = mức tăng Z* khi ngân sách tăng thêm 1 đơn vị. "
        "Đây là chi phí cơ hội của vốn công."
    )

    if res.success:
        # Calculate shadow price manually by solving for B and B+1
        res2 = solve_lp(B + 1)
        shadow_budget = (-res2.fun) - (-res.fun) if res2.success else None

        col1, col2 = st.columns(2)
        col1.metric(
            "Shadow price ngân sách",
            f"{shadow_budget:.4f} nghìn tỷ/nghìn tỷ" if shadow_budget else "N/A",
            help="Tăng ngân sách 1 nghìn tỷ → GDP tăng thêm bao nhiêu"
        )
        col2.metric(
            "Diễn giải",
            f"≈ {shadow_budget*1000:.1f} tỷ GDP / 1 nghìn tỷ đầu tư" if shadow_budget else "N/A"
        )

        st.markdown("#### Ràng buộc nào đang binding (hoạt động)?")
        binding = []
        if abs(x_opt.sum() - B) < 0.01:
            binding.append("✅ Ngân sách tổng — đang binding")
        if abs(x_opt[0] - x1_min) < 0.01:
            binding.append("✅ Sàn hạ tầng số x₁ — đang binding")
        if abs(x_opt[1] - x2_min) < 0.01:
            binding.append("✅ Sàn AI x₂ — đang binding")
        if abs(x_opt[2] - x3_min) < 0.01:
            binding.append("✅ Sàn nhân lực x₃ — đang binding")
        if abs(x_opt[3] - x4_min) < 0.01:
            binding.append("✅ Sàn R&D x₄ — đang binding")
        for b in binding:
            st.markdown(b)

# ── AI Analyst ────────────────────────────────────────────────────────────────
if res.success:
    context_str = (
        f"Ngân sách tổng B = {B} nghìn tỷ VND\n"
        f"Phân bổ tối ưu: x1={res.x[0]:.1f}, x2={res.x[1]:.1f}, "
        f"x3={res.x[2]:.1f}, x4={res.x[3]:.1f} (nghìn tỷ VND)\n"
        f"GDP tăng tối đa Z* = {-res.fun:.2f} nghìn tỷ VND\n"
        f"Shadow price ngân sách ≈ {shadow_budget:.4f}\n"
        f"Hệ số tác động: Hạ tầng=0.85, AI=1.20, Nhân lực=0.95, R&D=1.35"
    )
    render_analyst_box(
        "Bài 2", "LP Phân bổ ngân sách 4 hạng mục", context_str,
        extra_instruction="Bình luận về shadow price và ý nghĩa của nó với chính sách ngân sách Việt Nam."
    )
