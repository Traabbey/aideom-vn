import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.optimize import minimize
import sys
from pathlib import Path

# Add project root to sys.path so utils package can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.ai_analyst import render_analyst_box
from utils.hide_nav import hide_auto_nav

# Page configuration
st.set_page_config(page_title="Bài 8 — Tối ưu động", page_icon="⏳", layout="wide")

hide_auto_nav()

st.markdown("# ⏳ Bài 8 — Tối ưu động phân bổ 2026-2035")
st.markdown(
    """<span style='background:#553c9a;color:#e9d8fd;padding:3px 10px;border-radius:12px;font-size:0.8rem'>CẤP ĐỘ KHÁ KHÓ</span>
    &nbsp;&nbsp;scipy SLSQP &nbsp;&nbsp; Dynamic optimization""",
    unsafe_allow_html=True,
)

st.latex(r"\max \sum_{t=2026}^{2035} \rho^{t-2026} \ln(C_t)")
st.latex(r"Y_t = A_t \cdot K_t^{0.33} \cdot L_t^{0.42} \cdot D_t^{0.10} \cdot AI_t^{0.08} \cdot H_t^{0.07}")

# ── Sidebar parameters ──────────────────────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Tham số mô hình")
rho    = st.sidebar.slider("ρ (hệ số chiết khấu)", 0.90, 0.99, 0.97, 0.01)
dK     = st.sidebar.slider("δK (khấu hao vốn)", 0.03, 0.10, 0.05, 0.01)
dD     = st.sidebar.slider("δD (khấu hao HT số)", 0.05, 0.20, 0.12, 0.01)
dAI    = st.sidebar.slider("δAI (khấu hao AI)", 0.05, 0.25, 0.15, 0.01)
phi1   = st.sidebar.slider("φ₁ (TFP từ D)", 0.001, 0.006, 0.003, 0.001)
phi2   = st.sidebar.slider("φ₂ (TFP từ AI)", 0.001, 0.005, 0.002, 0.001)
phi3   = st.sidebar.slider("φ₃ (TFP từ H)", 0.001, 0.008, 0.004, 0.001)
shock_year = st.sidebar.selectbox("Năm cú sốc (giảm 8% GDP)", ["Không có", "2028", "2029", "2030"])

# Initial conditions (2026)
K0  = st.sidebar.number_input("K₀ (nghìn tỷ VND)", 20000, 35000, 27500, 500)
D0  = st.sidebar.number_input("D₀ (% GDP)", 15.0, 25.0, 20.3, 0.1)
AI0 = st.sidebar.number_input("AI₀ (nghìn DN số)", 60, 120, 86, 1)
H0  = st.sidebar.number_input("H₀ (% LĐ qua ĐT)", 25.0, 40.0, 30.0, 0.5)
A0  = st.sidebar.number_input("A₀ (TFP ban đầu)", 30.0, 50.0, 39.99, 0.1)
L0  = 53.9  # Million laborers

T = 10
years = list(range(2026, 2036))

# ── Dynamic Simulation ─────────────────────────────────────────────────────────────────
def simulate(alloc_flat, shock=None):
    """alloc_flat: 4*T values [IK, ID, IAI, IH] * T"""
    IK  = alloc_flat[0*T:1*T]
    ID  = alloc_flat[1*T:2*T]
    IAI = alloc_flat[2*T:3*T]
    IH  = alloc_flat[3*T:4*T]

    K, D, AI, H, A = K0, D0, AI0, H0, A0
    Ys, Cs, Ks, Ds, AIs, Hs, As = [], [], [], [], [], [], []

    for t in range(T):
        Y = A * (K**0.33) * (L0**0.42) * (D**0.10) * (AI**0.08) * (H**0.07)
        if shock and str(2026+t) == shock:
            Y *= 0.92
        C = max(Y - IK[t] - ID[t] - IAI[t] - IH[t], 1)
        Ys.append(Y); Cs.append(C); Ks.append(K)
        Ds.append(D); AIs.append(AI); Hs.append(H); As.append(A)
        K  = (1 - dK)  * K  + IK[t]
        D  = (1 - dD)  * D  + ID[t]
        AI = (1 - dAI) * AI + IAI[t]
        H  = H + 0.8 * IH[t] - 0.02 * H
        A  = A * (1 + phi1*D + phi2*AI + phi3*H)

    return np.array(Ys), np.array(Cs), np.array(Ks), np.array(Ds), np.array(AIs), np.array(Hs), np.array(As)

def objective(alloc_flat):
    _, Cs, *_ = simulate(alloc_flat, shock_year if shock_year != "Không có" else None)
    disc = np.array([rho**t for t in range(T)])
    return -np.sum(disc * np.log(np.maximum(Cs, 1)))

if st.button("🚀 Tối ưu hóa", type="primary"):
    with st.spinner("Đang chạy SLSQP..."):
        budget_annual = 1200  # Thousand trillion VND per year
        x0 = np.ones(4*T) * budget_annual / 4

        bounds = [(0, budget_annual)] * (4*T)

        def budget_con(x):
            return np.array([budget_annual - x[t] - x[T+t] - x[2*T+t] - x[3*T+t]
                             for t in range(T)])

        result = minimize(
            objective, x0, method="SLSQP",
            bounds=bounds,
            constraints={"type": "ineq", "fun": budget_con},
            options={"maxiter": 500, "ftol": 1e-8},
        )

    Ys, Cs, Ks, Ds, AIs, Hs, As = simulate(result.x,
        float(shock_year) if shock_year != "Không có" else None)

    st.success(f"✅ Tối ưu hóa xong! Welfare = {-result.fun:.4f}")

    # ── Trajectory Charts ─────────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["📈 Quỹ đạo tối ưu", "💰 Phân bổ đầu tư"])

    with tab1:
        fig = go.Figure()
        fig.add_scatter(x=years, y=Ys, mode="lines+markers", name="GDP (Y)",
                        line=dict(color="#68d391", width=3))
        fig.add_scatter(x=years, y=Cs, mode="lines+markers", name="Tiêu dùng (C)",
                        line=dict(color="#e94560", width=3, dash="dot"))
        if shock_year != "Không có":
            fig.add_vline(x=int(shock_year), line_dash="dash", line_color="red",
                          annotation_text=f"Cú sốc {shock_year}")
        fig.update_layout(
            title="Quỹ đạo GDP và Tiêu dùng 2026-2035",
            xaxis_title="Năm", yaxis_title="Nghìn tỷ VND",
            legend=dict(orientation="h", y=1.05),
            height=380, margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        fig2 = go.Figure()
        fig2.add_scatter(x=years, y=Ks, name="K (vốn)", line=dict(width=2))
        fig2.add_scatter(x=years, y=[d*100 for d in Ds], name="D×100", line=dict(width=2))
        fig2.add_scatter(x=years, y=AIs, name="AI (nghìn DN)", line=dict(width=2))
        fig2.add_scatter(x=years, y=Hs, name="H (% LĐ)", line=dict(width=2))
        fig2.update_layout(
            title="Quỹ đạo K, D, AI, H",
            legend=dict(orientation="h", y=1.05),
            height=350, margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        IK  = result.x[0*T:1*T]
        ID  = result.x[1*T:2*T]
        IAI = result.x[2*T:3*T]
        IH  = result.x[3*T:4*T]

        fig3 = go.Figure()
        fig3.add_bar(x=years, y=IK,  name="I_K (vốn vật chất)", marker_color="#4299e1")
        fig3.add_bar(x=years, y=ID,  name="I_D (HT số)",         marker_color="#68d391")
        fig3.add_bar(x=years, y=IAI, name="I_AI",                marker_color="#f6ad55")
        fig3.add_bar(x=years, y=IH,  name="I_H (nhân lực)",      marker_color="#e94560")
        fig3.update_layout(
            barmode="stack", title="Phân bổ đầu tư tối ưu 2026-2035",
            yaxis_title="Nghìn tỷ VND/năm",
            legend=dict(orientation="h", y=1.05),
            height=380, margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig3, use_container_width=True)

    context_str = (
        f"ρ={rho}, δK={dK}, δD={dD}, δAI={dAI}\n"
        f"φ1={phi1}, φ2={phi2}, φ3={phi3}\n"
        f"Welfare tối ưu = {-result.fun:.4f}\n"
        f"GDP 2035 dự báo = {Ys[-1]:,.0f} nghìn tỷ VND\n"
        f"Cú sốc: {shock_year}\n"
        f"Tỷ lệ đầu tư TB: IK={IK.mean():.0f}, ID={ID.mean():.0f}, "
        f"IAI={IAI.mean():.0f}, IH={IH.mean():.0f} nghìn tỷ/năm"
    )
    render_analyst_box("Bài 8", "Tối ưu động 2026-2035", context_str,
                       extra_instruction="Nhận xét về quỹ đạo đầu tư có front-loaded không và tỷ lệ AI/H.")
else:
    st.info("👆 Nhấn **Tối ưu hóa** để chạy mô hình (mất 10-30 giây).")
