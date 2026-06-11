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
st.set_page_config(page_title="Bài 11 — Q-learning RL", page_icon="🤖", layout="wide")

hide_auto_nav()

st.markdown("# 🤖 Bài 11 — Q-learning Chính sách kinh tế thích nghi")
st.markdown(
    """<span style='background:#742a2a;color:#fed7d7;padding:3px 10px;border-radius:12px;font-size:0.8rem'>CẤP ĐỘ KHÓ</span>
    &nbsp;&nbsp;Q-learning &nbsp;&nbsp; MDP 81 trạng thái &nbsp;&nbsp; Epsilon-greedy""",
    unsafe_allow_html=True,
)

st.latex(r"Q(s,a) \leftarrow Q(s,a) + \alpha [r + \gamma \max_{a'} Q(s',a') - Q(s,a)]")

# ── MDP Action Definition ─────────────────────────────────────────────────────────────
actions = {
    0: ("Truyền thống",   np.array([0.70, 0.10, 0.10, 0.10])),
    1: ("Cân bằng",       np.array([0.40, 0.25, 0.15, 0.20])),
    2: ("Số hóa nhanh",   np.array([0.25, 0.45, 0.15, 0.15])),
    3: ("AI dẫn dắt",     np.array([0.20, 0.20, 0.45, 0.15])),
    4: ("Bao trùm",       np.array([0.30, 0.20, 0.10, 0.40])),
}
action_names = [v[0] for v in actions.values()]
w_reward = np.array([0.40, 0.25, 0.20, 0.15])  # GDP, jobs, environment, security

# ── Sidebar parameters ──────────────────────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Hyperparameters")
alpha    = st.sidebar.slider("α (learning rate)", 0.01, 0.5, 0.1, 0.01)
gamma_rl = st.sidebar.slider("γ (discount)", 0.80, 0.99, 0.95, 0.01)
episodes = st.sidebar.slider("Số episodes", 1000, 20000, 5000, 500)
eps_init = st.sidebar.slider("ε ban đầu", 0.5, 1.0, 1.0, 0.1)
eps_min  = st.sidebar.slider("ε tối thiểu", 0.01, 0.1, 0.05, 0.01)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🌏 Trạng thái ban đầu VN 2026")
gdp_state  = st.sidebar.selectbox("GDP growth", ["Thấp","Trung bình","Cao"], index=1)
dig_state  = st.sidebar.selectbox("Digital Index", ["Thấp","Trung bình","Cao"], index=1)
ai_state   = st.sidebar.selectbox("AI Capacity", ["Thấp","Trung bình","Cao"], index=0)
une_state  = st.sidebar.selectbox("Unemployment Risk", ["Thấp","Trung bình","Cao"], index=1)

state_map = {"Thấp": 0, "Trung bình": 1, "Cao": 2}
init_state = np.array([state_map[gdp_state], state_map[dig_state],
                        state_map[ai_state],  state_map[une_state]])

# ── MDP Environment Helpers ───────────────────────────────────────────────────────
def state_to_idx(s):
    return s[0]*27 + s[1]*9 + s[2]*3 + s[3]

def step_env(state, action):
    alloc = actions[action][1]
    # State update transitions
    gdp_delta  = alloc[0]*0.08 + alloc[1]*0.05 + alloc[2]*0.06 + alloc[3]*0.03
    dig_delta  = alloc[1]*0.12 + alloc[2]*0.08
    ai_delta   = alloc[2]*0.15
    une_delta  = -(alloc[2]*0.05 - alloc[3]*0.08)

    new_state = state.copy()
    new_state[0] = np.clip(state[0] + (1 if gdp_delta > 0.07 else -1 if gdp_delta < 0.04 else 0), 0, 2)
    new_state[1] = np.clip(state[1] + (1 if dig_delta > 0.08 else 0), 0, 2)
    new_state[2] = np.clip(state[2] + (1 if ai_delta > 0.10 else 0), 0, 2)
    new_state[3] = np.clip(state[3] + (-1 if une_delta < -0.03 else 1 if une_delta > 0.03 else 0), 0, 2)

    reward = (w_reward[0]*gdp_delta*10 - w_reward[1]*max(une_delta,0)*5
              - w_reward[2]*alloc[2]*0.02 + w_reward[3]*alloc[3]*0.03)
    return new_state, reward

# ── Q-learning Training Loop ─────────────────────────────────────────────────────
T = 10  # Episode horizon

if st.button("🚀 Huấn luyện Q-learning", type="primary"):
    np.random.seed(42)
    Q = np.zeros((81, 5))
    rewards_history = []

    progress = st.progress(0)
    status_text = st.empty()

    for ep in range(episodes):
        s = init_state.copy()
        ep_reward = 0
        eps = max(eps_min, eps_init - (eps_init - eps_min) * ep / (episodes * 0.7))

        for t in range(T):
            idx = state_to_idx(s)
            if np.random.rand() < eps:
                a = np.random.randint(5)
            else:
                a = np.argmax(Q[idx])

            s2, r = step_env(s, a)
            idx2 = state_to_idx(s2)
            Q[idx, a] += alpha * (r + gamma_rl * Q[idx2].max() - Q[idx, a])
            s = s2
            ep_reward += r

        rewards_history.append(ep_reward)
        if ep % (episodes // 20) == 0:
            progress.progress(ep / episodes)
            status_text.text(f"Episode {ep}/{episodes} | ε={eps:.3f} | Reward={ep_reward:.3f}")

    progress.progress(1.0)
    status_text.text("✅ Huấn luyện xong!")
    st.session_state["Q_table"] = Q
    st.session_state["rewards_history"] = rewards_history

if "Q_table" in st.session_state:
    Q = st.session_state["Q_table"]
    rewards_history = st.session_state["rewards_history"]

    tab1, tab2, tab3 = st.tabs(["🎯 Chính sách π*", "📈 Learning Curve", "📊 Q-table"])

    with tab1:
        st.markdown("### Chính sách tối ưu π*(s) tại trạng thái VN 2026")
        idx = state_to_idx(init_state)
        best_action = np.argmax(Q[idx])
        st.success(f"🎯 **Tại trạng thái hiện tại → Chính sách: {action_names[best_action]}**")

        alloc = actions[best_action][1]
        fig = go.Figure(go.Pie(
            labels=["Vốn K","Hạ tầng số D","AI","Nhân lực H"],
            values=alloc*100,
            marker_colors=["#4299e1","#68d391","#f6ad55","#e94560"],
            hole=0.4,
        ))
        fig.update_layout(
            title=f"Phân bổ ngân sách: {action_names[best_action]}",
            height=350, margin=dict(l=0,r=0,t=40,b=0),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Compare 5 Actions
        st.markdown("### Q-values tại trạng thái hiện tại")
        df_q = pd.DataFrame({
            "Hành động": action_names,
            "Q-value": Q[idx].round(4),
            "Phân bổ K/D/AI/H": [f"{v[1][0]*100:.0f}/{v[1][1]*100:.0f}/{v[1][2]*100:.0f}/{v[1][3]*100:.0f}%"
                                   for v in actions.values()],
        }).sort_values("Q-value", ascending=False)
        st.dataframe(df_q, use_container_width=True, hide_index=True)

        # Baseline Strategy Comparison
        st.markdown("### So sánh với chiến lược rule-based")
        np.random.seed(42)
        strategies = {
            "π* Q-learning": None,
            "Luôn a1 (Cân bằng)": 1,
            "Luôn a3 (AI dẫn dắt)": 3,
            "Random": -1,
        }
        compare_rewards = {k: [] for k in strategies}
        for ep in range(200):
            for name, fixed_a in strategies.items():
                s = init_state.copy()
                ep_r = 0
                for t in range(T):
                    if fixed_a is None:
                        a = np.argmax(Q[state_to_idx(s)])
                    elif fixed_a == -1:
                        a = np.random.randint(5)
                    else:
                        a = fixed_a
                    s, r = step_env(s, a)
                    ep_r += r
                compare_rewards[name].append(ep_r)

        df_compare = pd.DataFrame({
            "Chiến lược": list(strategies.keys()),
            "Reward TB": [np.mean(v) for v in compare_rewards.values()],
            "Reward Max": [np.max(v) for v in compare_rewards.values()],
        })
        st.dataframe(df_compare.round(4), use_container_width=True, hide_index=True)

    with tab2:
        # Learning curve (rolling average)
        window = max(episodes // 50, 10)
        rolling = pd.Series(rewards_history).rolling(window).mean()
        fig2 = go.Figure()
        fig2.add_scatter(x=list(range(episodes)), y=rewards_history,
                         mode="lines", name="Episode reward",
                         line=dict(color="#4299e1", width=1), opacity=0.4)
        fig2.add_scatter(x=list(range(episodes)), y=rolling,
                         mode="lines", name=f"Rolling avg ({window})",
                         line=dict(color="#e94560", width=3))
        fig2.update_layout(
            title="Learning Curve Q-learning",
            xaxis_title="Episode", yaxis_title="Tổng Reward",
            legend=dict(orientation="h", y=1.05),
            height=380, margin=dict(l=0,r=0,t=40,b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.markdown("### Q-table (10 trạng thái đầu)")
        df_qtable = pd.DataFrame(Q[:10], columns=action_names)
        df_qtable.index = [f"State {i}" for i in range(10)]
        st.dataframe(df_qtable.round(4), use_container_width=True)

    context_str = (
        f"Episodes = {episodes}, α={alpha}, γ={gamma_rl}\n"
        f"Trạng thái VN 2026: GDP={gdp_state}, D={dig_state}, AI={ai_state}, U={une_state}\n"
        f"Chính sách tối ưu: {action_names[best_action]}\n"
        f"Q-values: {dict(zip(action_names, Q[idx].round(4)))}\n"
        f"Reward TB π*: {np.mean(compare_rewards['π* Q-learning']):.4f} vs "
        f"AI dẫn dắt: {np.mean(compare_rewards['Luôn a3 (AI dẫn dắt)']):.4f}"
    )
    render_analyst_box("Bài 11", "Q-learning RL chính sách thích nghi", context_str,
                       extra_instruction="Bình luận về chính sách π* chọn và cách tích hợp vào hoạch định thực tế.")
else:
    st.info("👆 Nhấn **Huấn luyện Q-learning** để bắt đầu (mất 5-15 giây).")
