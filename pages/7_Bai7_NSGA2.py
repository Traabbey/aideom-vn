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
st.set_page_config(page_title="Bài 7 — NSGA-II Pareto", page_icon="🌐", layout="wide")

hide_auto_nav()

st.markdown("# 🌐 Bài 7 — NSGA-II Tối ưu đa mục tiêu Pareto")
st.markdown(
    """<span style='background:#553c9a;color:#e9d8fd;padding:3px 10px;border-radius:12px;font-size:0.8rem'>CẤP ĐỘ KHÁ KHÓ</span>
    &nbsp;&nbsp;NSGA-II &nbsp;&nbsp; pymoo &nbsp;&nbsp; Biên Pareto 3D""",
    unsafe_allow_html=True,
)

st.markdown("### 4 mục tiêu xung đột")
col1, col2 = st.columns(2)
col1.latex(r"\max f_1(x) = \sum_r \sum_j \beta_{j,r} x_{j,r} \quad \text{(GDP)}")
col1.latex(r"\min f_2(x) = G(x) \quad \text{(Bất bình đẳng)}")
col2.latex(r"\min f_3(x) = \sum_r e_r(x_{I,r}+x_{AI,r}) \quad \text{(Phát thải)}")
col2.latex(r"\min f_4(x) = \sum_r \rho_r x_{AI,r} - \sigma_r x_{H,r} \quad \text{(Rủi ro)}")

# ── Sidebar parameters ──────────────────────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Tham số NSGA-II")
pop_size = st.sidebar.slider("Population size", 50, 200, 100, 10)
n_gen    = st.sidebar.slider("Số thế hệ", 50, 300, 150, 10)
seed     = st.sidebar.number_input("Random seed", 0, 999, 42)

w_gdp  = st.sidebar.slider("Trọng số GDP (TOPSIS)", 0.1, 0.6, 0.40, 0.05)
w_inc  = st.sidebar.slider("Trọng số Bao trùm", 0.1, 0.5, 0.25, 0.05)
w_env  = st.sidebar.slider("Trọng số Môi trường", 0.05, 0.4, 0.20, 0.05)
w_sec  = st.sidebar.slider("Trọng số An ninh", 0.05, 0.4, 0.15, 0.05)

if st.button("🚀 Chạy NSGA-II", type="primary"):
    try:
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.core.problem import ElementwiseProblem
        from pymoo.optimize import minimize as pymoo_minimize

        beta = np.array([
            [1.15, 0.85, 0.55, 1.30],
            [0.95, 1.25, 1.40, 1.05],
            [1.05, 0.95, 0.85, 1.15],
            [1.20, 0.75, 0.45, 1.35],
            [0.90, 1.30, 1.55, 1.00],
            [1.10, 0.85, 0.65, 1.25],
        ])
        e   = np.array([0.42, 0.55, 0.48, 0.32, 0.62, 0.38])
        rho = np.array([0.18, 0.45, 0.28, 0.12, 0.52, 0.22])
        sig = np.array([0.32, 0.28, 0.30, 0.35, 0.25, 0.30])

        class VNProblem(ElementwiseProblem):
            def __init__(self):
                super().__init__(n_var=24, n_obj=4, n_ieq_constr=8,
                                 xl=np.zeros(24), xu=np.ones(24)*12000)
            def _evaluate(self, x, out, *args, **kwargs):
                X = x.reshape(6, 4)
                f1 = -(beta * X).sum()
                sums = X.sum(axis=1)
                f2 = np.abs(sums - sums.mean()).mean()
                f3 = (e * (X[:,0] + X[:,2])).sum()
                f4 = (rho * X[:,2]).sum() - (sig * X[:,3]).sum()
                g1 = X.sum() - 50000
                g2 = -(X.sum() - 30000)
                g3_to_g8 = [5000 - X[r].sum() for r in range(6)]
                out["F"] = [f1, f2, f3, f4]
                out["G"] = [g1, g2] + g3_to_g8

        with st.spinner(f"Chạy NSGA-II: {pop_size} cá thể × {n_gen} thế hệ..."):
            res = pymoo_minimize(
                VNProblem(), NSGA2(pop_size=pop_size),
                ("n_gen", n_gen), seed=int(seed), verbose=False
            )

        F = res.F
        st.success(f"✅ Tìm được **{len(F)} nghiệm Pareto**!")

        # 3D Pareto Front Chart
        fig = go.Figure(go.Scatter3d(
            x=-F[:,0], y=F[:,1], z=F[:,2],
            mode="markers",
            marker=dict(size=5, color=F[:,3],
                        colorscale="RdYlGn_r", colorbar=dict(title="Rủi ro f₄")),
        ))
        fig.update_layout(
            title="Biên Pareto 3D: GDP vs Bất bình đẳng vs Phát thải",
            scene=dict(xaxis_title="f₁ GDP (max)", yaxis_title="f₂ BĐĐ (min)",
                       zaxis_title="f₃ Phát thải (min)"),
            height=550,
        )
        st.plotly_chart(fig, use_container_width=True)

        # TOPSIS for compromise solution selection
        F_norm = (F - F.min(0)) / (F.max(0) - F.min(0) + 1e-10)
        w_topsis = np.array([w_gdp, w_inc, w_env, w_sec])
        # After changing signs for f1, all objectives are minimized
        V = F_norm * w_topsis
        A_star = V.min(0); A_neg = V.max(0)
        S_star = np.sqrt(((V - A_star)**2).sum(1))
        S_neg  = np.sqrt(((V - A_neg)**2).sum(1))
        C = S_neg / (S_star + S_neg)
        best_idx = C.argmax()

        st.markdown("### 🎯 Nghiệm thỏa hiệp (TOPSIS)")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("GDP gain", f"{-F[best_idx,0]:,.0f} tỷ VND")
        col2.metric("Bất bình đẳng", f"{F[best_idx,1]:.1f}")
        col3.metric("Phát thải", f"{F[best_idx,2]:.1f}")
        col4.metric("Rủi ro ròng", f"{F[best_idx,3]:.1f}")

        st.session_state["nsga_F"] = F
        st.session_state["nsga_best"] = best_idx

        context_str = (
            f"Số nghiệm Pareto: {len(F)}\n"
            f"Nghiệm thỏa hiệp TOPSIS: GDP={-F[best_idx,0]:,.0f}, "
            f"BĐĐ={F[best_idx,1]:.1f}, Phát thải={F[best_idx,2]:.1f}, Rủi ro={F[best_idx,3]:.1f}\n"
            f"Trọng số TOPSIS: GDP={w_gdp}, Bao trùm={w_inc}, MT={w_env}, AN={w_sec}"
        )
        render_analyst_box("Bài 7", "NSGA-II Pareto đa mục tiêu", context_str)

    except ImportError:
        st.error("⚠️ Chưa cài pymoo! Chạy: `pip install pymoo` trong terminal.")
else:
    st.info("👆 Nhấn **Chạy NSGA-II** để bắt đầu tối ưu hóa (mất 30-60 giây).")
    if "nsga_F" in st.session_state:
        st.success("✅ Đã có kết quả từ lần chạy trước!")
        F = st.session_state["nsga_F"]
        best_idx = st.session_state["nsga_best"]

        # Restore 3D chart
        fig = go.Figure(go.Scatter3d(
            x=-F[:,0], y=F[:,1], z=F[:,2],
            mode="markers",
            marker=dict(size=5, color=F[:,3],
                        colorscale="RdYlGn_r", colorbar=dict(title="Rủi ro f₄")),
        ))
        fig.update_layout(
            title="Biên Pareto 3D: GDP vs Bất bình đẳng vs Phát thải",
            scene=dict(xaxis_title="f₁ GDP (max)", yaxis_title="f₂ BĐĐ (min)",
                       zaxis_title="f₃ Phát thải (min)"),
            height=550,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 🎯 Nghiệm thỏa hiệp (TOPSIS) [Lịch sử]")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("GDP gain", f"{-F[best_idx,0]:,.0f} tỷ VND")
        col2.metric("Bất bình đẳng", f"{F[best_idx,1]:.1f}")
        col3.metric("Phát thải", f"{F[best_idx,2]:.1f}")
        col4.metric("Rủi ro ròng", f"{F[best_idx,3]:.1f}")

        context_str = (
            f"Số nghiệm Pareto: {len(F)}\n"
            f"Nghiệm thỏa hiệp TOPSIS: GDP={-F[best_idx,0]:,.0f}, "
            f"BĐĐ={F[best_idx,1]:.1f}, Phát thải={F[best_idx,2]:.1f}, Rủi ro={F[best_idx,3]:.1f}\n"
            f"Trọng số TOPSIS: GDP={w_gdp}, Bao trùm={w_inc}, MT={w_env}, AN={w_sec}"
        )
        render_analyst_box("Bài 7", "NSGA-II Pareto đa mục tiêu", context_str)
