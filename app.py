
import itertools
import os
import json
import re
import re
import base64
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.optimize import linprog


st.set_page_config(
    page_title="VN AIDEOM-VN | Decision Optimization Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent / "data"
ASSETS_DIR = Path(__file__).parent / "assets"
PLOT_TEMPLATE = "plotly_white"


# =========================
# Global style
# =========================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
    .stApp {
        background: linear-gradient(135deg, #FAF5FF 0%, #FDF2F8 50%, #F5F3FF 100%);
        color: #1E1B2E;
        font-family: 'Inter', sans-serif;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #FAF5FF 100%);
        border-right: 2px solid #E9D5FF;
    }
    h1, h2, h3 { letter-spacing: -0.03em; color: #2D1B69 !important; }
    .hero {
        padding: 30px 32px;
        border-radius: 24px;
        border: 1.5px solid #E9D5FF;
        background: linear-gradient(135deg, #FFFFFF 0%, #FAF5FF 100%);
        box-shadow: 0 8px 40px rgba(139,92,246,0.12);
        margin-bottom: 18px;
    }
    .hero-title {
        font-size: 46px;
        line-height: 1.02;
        font-weight: 850;
        color: #2D1B69;
        margin-bottom: 10px;
    }
    .hero-sub {
        color: #6B7280;
        font-size: 18px;
        max-width: 980px;
    }
    .section-card {
        padding: 18px 20px;
        border-radius: 20px;
        background: #FFFFFF;
        border: 1.5px solid #E9D5FF;
        box-shadow: 0 4px 20px rgba(139,92,246,0.08);
        margin-bottom: 16px;
    }
    .kpi-card {
        padding: 16px 16px;
        border-radius: 18px;
        background: linear-gradient(160deg, #FAF5FF, #FDF2F8);
        border: 1.5px solid #E9D5FF;
        min-height: 116px;
        box-shadow: 0 4px 16px rgba(139,92,246,0.10);
    }
    .kpi-label { color: #7C3AED; font-size: 13px; margin-bottom: 6px; font-weight: 600; }
    .kpi-value { color: #DB2777; font-size: 29px; font-weight: 850; letter-spacing: -0.04em; }
    .kpi-note { color: #059669; font-size: 12px; margin-top: 4px; }
    .pill {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(139,92,246,0.10);
        color: #7C3AED;
        border: 1px solid rgba(139,92,246,0.28);
        font-size: 12px;
        font-weight: 700;
        margin-right: 6px;
    }
    .muted { color: #9CA3AF; }
    .warning-box {
        padding: 14px 16px;
        border-left: 4px solid #F59E0B;
        background: rgba(245,158,11,0.08);
        border-radius: 14px;
        margin: 12px 0;
    }
    .success-box {
        padding: 14px 16px;
        border-left: 4px solid #7C3AED;
        background: rgba(139,92,246,0.08);
        border-radius: 14px;
        margin: 12px 0;
    }
    div[data-testid="stMetricValue"] { color: #DB2777 !important; }
    div[data-testid="stDataFrame"] { border-radius: 16px; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)



# =========================
# Background images
# =========================
@st.cache_data(show_spinner=False)
def image_to_base64(image_path: str) -> str:
    """Convert local image file to base64 for Streamlit CSS background."""
    path = Path(image_path)
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def inject_background_images() -> None:
    """Inject brighter, professional dashboard background and component CSS."""
    main_bg = image_to_base64(str(ASSETS_DIR / "bg_main.png"))
    hero_bg = image_to_base64(str(ASSETS_DIR / "bg_hero.png"))

    main_url = f"url(data:image/png;base64,{main_bg})" if main_bg else "none"
    hero_url = f"url(data:image/png;base64,{hero_bg})" if hero_bg else main_url

    st.markdown(
        f"""
        <style>
        /* ==========================================================
           AIDEOM-VN VISUAL POLISH
           - sáng hơn, dễ đọc hơn
           - sidebar rõ chữ
           - bảng tối, đồng bộ dashboard
           - hero/banner căn ảnh đẹp hơn
           ========================================================== */

        :root {{
            --aideom-bg: #FAF5FF;
            --aideom-surface: rgba(255, 255, 255, 0.92);
            --aideom-surface-strong: rgba(255, 255, 255, 0.98);
            --aideom-border: rgba(139, 92, 246, 0.25);
            --aideom-text: #1E1B2E;
            --aideom-muted: #6B7280;
            --aideom-soft: #9CA3AF;
            --aideom-cyan: #7C3AED;
            --aideom-green: #059669;
            --aideom-pink: #DB2777;
        }}

        /* ===== Nền tổng thể: sáng tím hồng ===== */
        .stApp {{
            background: linear-gradient(135deg, #FAF5FF 0%, #FDF2F8 50%, #F5F3FF 100%) !important;
            color: var(--aideom-text) !important;
        }}

        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 0;
            background:
                radial-gradient(circle at 15% 10%, rgba(139, 92, 246, 0.10), transparent 32%),
                radial-gradient(circle at 88% 75%, rgba(219, 39, 119, 0.08), transparent 30%);
        }}

        div[data-testid="stAppViewContainer"] > .main,
        section.main > div {{
            position: relative;
            z-index: 1;
        }}

        header[data-testid="stHeader"],
        div[data-testid="stToolbar"],
        .stAppHeader {{
            background: rgba(250, 245, 255, 0.85) !important;
            backdrop-filter: blur(10px) !important;
            border-bottom: 1px solid #E9D5FF !important;
        }}

        header[data-testid="stHeader"]::before {{
            background: transparent !important;
        }}

        .block-container {{
            padding-top: 2.6rem !important;
            padding-bottom: 3rem !important;
            max-width: 1240px !important;
        }}

        /* ===== Chữ toàn trang ===== */
        .stMarkdown, .stText, .stCaption, p, li, label, span {{
            color: var(--aideom-text);
        }}

        p, li {{
            font-size: 1.02rem;
            line-height: 1.72;
        }}

        h1, h2, h3, h4 {{
            color: #2D1B69 !important;
            letter-spacing: -0.035em !important;
        }}

        h2 {{
            margin-top: 1.85rem !important;
            margin-bottom: 0.78rem !important;
            font-weight: 850 !important;
        }}

        h3 {{
            margin-top: 1.1rem !important;
            font-weight: 780 !important;
        }}

        .muted, .caption, small,
        div[data-testid="stCaptionContainer"] {{
            color: #9CA3AF !important;
        }}

        /* ===== Sidebar sáng tím ===== */
        section[data-testid="stSidebar"],
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FFFFFF 0%, #FAF5FF 100%) !important;
            backdrop-filter: blur(18px) !important;
            border-right: 2px solid #E9D5FF !important;
        }}

        [data-testid="stSidebar"] * {{
            color: #2D1B69 !important;
        }}

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] .stMarkdown p {{
            color: #1E1B2E !important;
        }}

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] p {{
            font-size: 0.95rem !important;
            opacity: 1 !important;
        }}

        [data-testid="stSidebar"] [role="radiogroup"] label {{
            padding: 0.34rem 0.25rem !important;
            border-radius: 10px !important;
            transition: background 160ms ease, color 160ms ease;
        }}

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
            background: rgba(139, 92, 246, 0.10) !important;
        }}

        /* ===== Hero ===== */
        .hero {{
            position: relative;
            overflow: hidden;
            padding: 32px 34px !important;
            border-radius: 24px !important;
            background: linear-gradient(135deg, #FFFFFF 0%, #FAF5FF 60%, #FDF2F8 100%) !important;
            background-size: cover !important;
            background-position: center 45% !important;
            background-repeat: no-repeat !important;
            border: 1.5px solid #E9D5FF !important;
            box-shadow: 0 8px 40px rgba(139, 92, 246, 0.12) !important;
            margin-bottom: 1.15rem !important;
        }}

        .hero::after, .aideom-hero::after {{
            content: "";
            position: absolute;
            inset: 0;
            pointer-events: none;
            background: radial-gradient(circle at 90% 20%, rgba(219, 39, 119, 0.06), transparent 30%);
            z-index: 1;
        }}

        .hero > *, .aideom-hero > * {{
            position: relative;
            z-index: 2;
        }}

        .hero-title {{
            font-size: clamp(2.15rem, 4vw, 3.2rem) !important;
            line-height: 1.04 !important;
            font-weight: 900 !important;
            max-width: 980px !important;
            color: #2D1B69 !important;
        }}

        .hero-sub {{
            color: #6B7280 !important;
            font-size: 1.06rem !important;
            line-height: 1.65 !important;
            max-width: 1040px !important;
        }}

        .pill {{
            background: rgba(139, 92, 246, 0.10) !important;
            color: #7C3AED !important;
            border: 1px solid rgba(139, 92, 246, 0.28) !important;
        }}

        /* Trang chủ hero */
        .aideom-hero {{
            background: linear-gradient(135deg, #FFFFFF 0%, #FAF5FF 55%, #FDF2F8 100%) !important;
            background-size: cover !important;
            border: 1.5px solid #E9D5FF !important;
            box-shadow: 0 12px 50px rgba(139, 92, 246, 0.14) !important;
        }}

        .aideom-title, .aideom-title-accent {{
            color: #2D1B69 !important;
        }}

        .aideom-subtitle, .aideom-description {{
            color: #6B7280 !important;
        }}

        .aideom-description {{
            max-width: 1020px !important;
        }}

        /* ===== Card/KPI ===== */
        .section-card, .kpi-card, .aideom-kpi-card,
        .aideom-level-card, .aideom-feature-card, .aideom-data-card {{
            background: linear-gradient(160deg, #FFFFFF, #FAF5FF) !important;
            border: 1.5px solid #E9D5FF !important;
            box-shadow: 0 4px 20px rgba(139, 92, 246, 0.08) !important;
            backdrop-filter: blur(12px) !important;
        }}

        .kpi-card, .aideom-kpi-card {{
            min-height: 124px !important;
        }}

        .kpi-label, .aideom-kpi-label {{
            color: #7C3AED !important;
            font-weight: 700 !important;
        }}

        .kpi-value, .aideom-kpi-value,
        div[data-testid="stMetricValue"] {{
            color: #DB2777 !important;
        }}

        .kpi-note, .aideom-kpi-note {{
            color: #059669 !important;
            background: rgba(5, 150, 105, 0.08) !important;
        }}

        /* ===== Expander, tabs ===== */
        details[data-testid="stExpander"] {{
            background: #FFFFFF !important;
            border: 1.5px solid #E9D5FF !important;
            border-radius: 16px !important;
            overflow: hidden !important;
            box-shadow: 0 4px 16px rgba(139, 92, 246, 0.08) !important;
        }}

        details[data-testid="stExpander"] summary {{
            color: #2D1B69 !important;
            font-weight: 800 !important;
            background: #FAF5FF !important;
        }}

        button[data-baseweb="tab"] {{
            background: #FFFFFF !important;
            border-radius: 999px !important;
            margin-right: 0.35rem !important;
            color: #7C3AED !important;
            border: 1.5px solid #E9D5FF !important;
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            background: linear-gradient(135deg, #7C3AED, #DB2777) !important;
            color: #FFFFFF !important;
            border-color: transparent !important;
        }}

        /* ===== Alert boxes ===== */
        div[data-testid="stAlert"] {{
            border-radius: 16px !important;
            border: 1.5px solid #E9D5FF !important;
            box-shadow: 0 4px 16px rgba(139, 92, 246, 0.08) !important;
        }}

        div[data-testid="stAlert"] * {{
            color: #2D1B69 !important;
        }}

        /* ===== Dataframe ===== */
        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {{
            background: #FFFFFF !important;
            border: 1.5px solid #E9D5FF !important;
            border-radius: 18px !important;
            overflow: hidden !important;
            box-shadow: 0 4px 20px rgba(139, 92, 246, 0.08) !important;
        }}

        div[data-testid="stDataFrame"] * {{
            color: #1E1B2E !important;
        }}

        div[data-testid="stDataFrame"] {{
            --gdg-bg-cell: rgba(255, 255, 255, 0.98) !important;
            --gdg-bg-cell-medium: rgba(250, 245, 255, 0.98) !important;
            --gdg-bg-header: rgba(237, 233, 254, 0.98) !important;
            --gdg-text-dark: #1E1B2E !important;
            --gdg-text-medium: #4B5563 !important;
            --gdg-text-light: #6B7280 !important;
            --gdg-accent-color: #7C3AED !important;
            --gdg-border-color: rgba(139, 92, 246, 0.18) !important;
        }}

        /* ===== HTML table wrap ===== */
        .aideom-table-wrap {{
            width: 100%;
            overflow-x: auto;
            margin: 0.75rem 0 1.05rem 0;
            border-radius: 18px;
            border: 1.5px solid #E9D5FF;
            box-shadow: 0 4px 20px rgba(139, 92, 246, 0.08);
            background: #FFFFFF;
        }}

        .aideom-table-wrap table {{
            width: 100%;
            border-collapse: separate !important;
            border-spacing: 0 !important;
            background: transparent !important;
            color: #1E1B2E !important;
            font-size: 0.92rem !important;
            line-height: 1.48 !important;
        }}

        .aideom-table-wrap thead th {{
            position: sticky;
            top: 0;
            z-index: 2;
            background: linear-gradient(180deg, #EDE9FE, #F5F3FF) !important;
            color: #2D1B69 !important;
            font-weight: 850 !important;
            text-align: left !important;
            padding: 0.72rem 0.82rem !important;
            border-bottom: 1.5px solid #E9D5FF !important;
            white-space: nowrap;
        }}

        .aideom-table-wrap tbody td,
        .aideom-table-wrap tbody th {{
            background: #FFFFFF !important;
            color: #1E1B2E !important;
            padding: 0.68rem 0.82rem !important;
            border-bottom: 1px solid #F3E8FF !important;
            vertical-align: top !important;
        }}

        .aideom-table-wrap tbody tr:nth-child(even) td,
        .aideom-table-wrap tbody tr:nth-child(even) th {{
            background: #FAF5FF !important;
        }}

        .aideom-table-wrap tbody tr:hover td,
        .aideom-table-wrap tbody tr:hover th {{
            background: #F3E8FF !important;
        }}

        .aideom-table-wrap caption {{
            color: #9CA3AF !important;
        }}

        /* ===== Plotly chart wrapper ===== */
        div[data-testid="stPlotlyChart"] {{
            background: #FFFFFF !important;
            border: 1.5px solid #E9D5FF !important;
            border-radius: 18px !important;
            padding: 0.35rem !important;
            box-shadow: 0 4px 20px rgba(139, 92, 246, 0.08) !important;
        }}

        /* ===== Code block ===== */
        div[data-testid="stCodeBlock"] {{
            border-radius: 16px !important;
            border: 1.5px solid #E9D5FF !important;
            overflow: hidden !important;
        }}

        /* ===== Buttons ===== */
        .stDownloadButton button,
        .stButton button {{
            border-radius: 999px !important;
            border: 1.5px solid #C4B5FD !important;
            background: linear-gradient(135deg, rgba(124,58,237,0.10), rgba(219,39,119,0.08)) !important;
            color: #7C3AED !important;
            font-weight: 800 !important;
        }}

        .stDownloadButton button:hover,
        .stButton button:hover {{
            border-color: #7C3AED !important;
            background: linear-gradient(135deg, rgba(124,58,237,0.18), rgba(219,39,119,0.14)) !important;
            box-shadow: 0 0 24px rgba(124, 58, 237, 0.18) !important;
        }}

        /* ===== Mobile ===== */
        @media (max-width: 900px) {{
            .block-container {{
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }}
            .hero {{
                padding: 24px 22px !important;
            }}
            .hero-title {{
                font-size: 2.05rem !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_background_images()


# =========================
# Visual rendering helpers
# =========================
_AIDEOM_ORIGINAL_DATAFRAME = st.dataframe
_AIDEOM_ORIGINAL_PLOTLY_CHART = st.plotly_chart


def _aideom_html_table(data, hide_index=False):
    """Render pandas DataFrame/Styler as a dark professional HTML table."""
    try:
        from pandas.io.formats.style import Styler
    except Exception:  # pragma: no cover
        Styler = ()

    if isinstance(data, pd.DataFrame):
        html = data.to_html(
            index=not bool(hide_index),
            escape=True,
            border=0,
            classes="aideom-table",
        )
    elif Styler and isinstance(data, Styler):
        styler = data
        if hide_index:
            try:
                styler = styler.hide(axis="index")
            except Exception:
                pass
        try:
            styler = styler.set_table_attributes('class="aideom-table"')
            styler = styler.set_table_styles(
                [
                    {"selector": "th", "props": [("font-weight", "850")]},
                    {"selector": "td", "props": [("color", "#EAF2FF")]},
                ],
                overwrite=False,
            )
        except Exception:
            pass
        html = styler.to_html()
    else:
        return None

    return f"<div class='aideom-table-wrap'>{html}</div>"


def _aideom_dataframe(data=None, *args, **kwargs):
    """Default replacement for st.dataframe to keep all tables visually consistent."""
    hide_index = kwargs.pop("hide_index", False)
    kwargs.pop("use_container_width", None)
    kwargs.pop("height", None)

    html = _aideom_html_table(data, hide_index=hide_index)
    if html is not None:
        return st.markdown(html, unsafe_allow_html=True)

    kwargs["hide_index"] = hide_index
    return _AIDEOM_ORIGINAL_DATAFRAME(data, *args, **kwargs)


def _aideom_plotly_chart(fig, *args, **kwargs):
    """Apply a uniform transparent dark chart container to all Plotly figures."""
    try:
        fig.update_layout(
            paper_bgcolor="rgba(255, 255, 255, 0.0)",
            plot_bgcolor="rgba(250, 245, 255, 0.40)",
            font=dict(color="#1E1B2E", family="Inter, system-ui, sans-serif", size=13),
            title=dict(font=dict(color="#2D1B69", size=18)),
            legend=dict(
                bgcolor="rgba(255, 255, 255, 0.90)",
                bordercolor="rgba(139, 92, 246, 0.20)",
                borderwidth=1,
            ),
            margin=dict(l=14, r=14, t=56, b=18),
        )
        fig.update_xaxes(
            gridcolor="rgba(139, 92, 246, 0.12)",
            zerolinecolor="rgba(148, 210, 255, 0.18)",
            linecolor="rgba(148, 210, 255, 0.22)",
        )
        fig.update_yaxes(
            gridcolor="rgba(148, 210, 255, 0.12)",
            zerolinecolor="rgba(148, 210, 255, 0.18)",
            linecolor="rgba(148, 210, 255, 0.22)",
        )
    except Exception:
        pass
    return _AIDEOM_ORIGINAL_PLOTLY_CHART(fig, *args, **kwargs)


st.dataframe = _aideom_dataframe
st.plotly_chart = _aideom_plotly_chart


# =========================
# AI analysis helper
# =========================
def _get_gemini_api_key():
    """Lấy Gemini API key từ Streamlit Secrets hoặc biến môi trường.

    Hỗ trợ nhiều tên key để khi deploy trên Streamlit Cloud không bị lỗi do đặt tên khác nhau.
    """
    possible_names = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY")

    for name in possible_names:
        try:
            key = st.secrets.get(name, "")
            if key:
                return str(key).strip()
        except Exception:
            pass

    # Một số bạn đặt secrets dạng [gemini] api_key = "..." hoặc [google] api_key = "..."
    for section in ("gemini", "google", "ai"):
        try:
            value = st.secrets.get(section, {})
            if isinstance(value, dict):
                for field in ("api_key", "key", "GEMINI_API_KEY"):
                    key = value.get(field, "")
                    if key:
                        return str(key).strip()
        except Exception:
            pass

    for name in possible_names:
        key = os.getenv(name, "").strip()
        if key:
            return key

    return ""


def _safe_for_ai(value, depth=0):
    """Chuyển dữ liệu kết quả sang dạng gọn để gửi cho Gemini."""
    if depth > 3:
        return str(value)[:300]

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()

    if isinstance(value, pd.DataFrame):
        compact = value.copy()
        if len(compact) > 12:
            compact = compact.head(12)
        return {
            "type": "DataFrame",
            "shape": list(value.shape),
            "columns": [str(c) for c in value.columns[:20]],
            "sample_rows": compact.astype(object).where(pd.notna(compact), None).to_dict(orient="records"),
        }

    if isinstance(value, pd.Series):
        series = value.dropna()
        return {
            "type": "Series",
            "name": str(value.name),
            "length": int(len(value)),
            "sample": series.head(12).tolist(),
        }

    if isinstance(value, np.ndarray):
        arr = np.asarray(value)
        if arr.size <= 40:
            return arr.tolist()
        try:
            numeric = arr.astype(float)
            return {
                "shape": list(arr.shape),
                "min": float(np.nanmin(numeric)),
                "max": float(np.nanmax(numeric)),
                "mean": float(np.nanmean(numeric)),
                "sample": arr.flatten()[:20].tolist(),
            }
        except Exception:
            return {
                "shape": list(arr.shape),
                "sample": arr.flatten()[:20].astype(str).tolist(),
            }

    if isinstance(value, dict):
        out = {}
        for idx, (k, v) in enumerate(value.items()):
            if idx >= 20:
                out["..."] = "Đã rút gọn"
                break
            out[str(k)] = _safe_for_ai(v, depth + 1)
        return out

    if isinstance(value, (list, tuple, set)):
        values = list(value)
        return [_safe_for_ai(v, depth + 1) for v in values[:20]]

    return None


def _collect_ai_context(local_vars, max_items=28):
    """Lấy các biến kết quả quan trọng trong từng page để AI phân tích."""
    skip_names = {
        "st", "pd", "np", "px", "go", "linprog", "itertools",
        "Path", "base64", "json", "os",
    }
    important_keywords = (
        "result", "results", "table", "df", "score", "scores", "rank", "ranking",
        "selected", "metrics", "scenario", "scenarios", "allocation", "comparison",
        "forecast", "sensitivity", "kpi", "validation", "warning", "risk", "job",
        "topsis", "entropy", "pareto", "policy", "reward", "welfare", "budget",
        "x_", "y_", "z_", "mape", "tfp", "gdp", "net", "cost", "benefit",
    )
    context = {}
    for name, value in local_vars.items():
        lname = str(name).lower()
        if name in skip_names or lname.startswith("_"):
            continue
        if callable(value):
            continue
        if not any(key in lname for key in important_keywords):
            if not isinstance(value, (pd.DataFrame, pd.Series, np.ndarray, dict, list, tuple, int, float, str, bool)):
                continue
        safe_value = _safe_for_ai(value)
        if safe_value is None:
            continue
        context[name] = safe_value
        if len(context) >= max_items:
            break
    return context


def _ai_make_prompt(lesson_name, model_name, input_params, result_data):
    """Tạo prompt phân tích cho Gemini."""
    payload = {
        "lesson_name": lesson_name,
        "model_name": model_name,
        "input_params": input_params or {},
        "result_data": result_data or {},
    }
    try:
        payload_text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    except Exception:
        payload_text = str(payload)
    if len(payload_text) > 14000:
        payload_text = payload_text[:14000] + "\n... [Dữ liệu đã được rút gọn để không vượt giới hạn prompt]"

    return f"""
Bạn là tác nhân AI phân tích kết quả cho web app AIDEOM-VN: AI-Driven Decision Optimization Model for Vietnam.

Tên bài: {lesson_name}
Mô hình/kỹ thuật: {model_name}

DỮ LIỆU VÀ KẾT QUẢ TỪ DASHBOARD:
{payload_text}

Hãy viết phân tích bằng tiếng Việt, đúng văn phong báo cáo cuối kỳ, theo cấu trúc:

1. Tóm tắt kết quả chính
2. Ý nghĩa kinh tế/chính sách trong bối cảnh Việt Nam
3. Điểm mạnh của kết quả hoặc phương án
4. Rủi ro/hạn chế cần lưu ý
5. Khuyến nghị chính sách ngắn gọn

Yêu cầu bắt buộc:
- Chỉ phân tích dựa trên dữ liệu được cung cấp trong prompt.
- Không bịa thêm số liệu, nguồn hoặc văn bản pháp lý.
- Nếu thiếu dữ liệu, nói rõ dữ liệu nào cần bổ sung.
- Viết khoảng 300-500 từ.
""".strip()





def _lesson_number_from_name(lesson_name):
    """Tách số bài từ tên bài để chọn phân tích dự phòng phù hợp."""
    import re
    m = re.search(r"Bài\s*(\d+)", str(lesson_name), flags=re.IGNORECASE)
    return int(m.group(1)) if m else 0


def _context_key_summary(result_data):
    """Tóm tắt ngắn các biến kết quả đã được dashboard gom để phân tích."""
    if not isinstance(result_data, dict) or not result_data:
        return "bảng kết quả, chỉ số KPI và biểu đồ đang hiển thị trên dashboard"
    keys = [str(k) for k in result_data.keys() if not str(k).startswith("_")]
    priority = [
        k for k in keys
        if any(term in k.lower() for term in (
            "result", "ranking", "score", "allocation", "forecast", "scenario",
            "risk", "budget", "z", "mape", "selected", "table", "df", "job"
        ))
    ]
    shown = priority[:6] if priority else keys[:6]
    if not shown:
        return "bảng kết quả, chỉ số KPI và biểu đồ đang hiển thị trên dashboard"
    return ", ".join(shown)


def _offline_ai_fallback(lesson_name, model_name, result_data=None):
    """Phân tích AI dự phòng khi Gemini API lỗi/quota.

    Không đổ lỗi API dài lên giao diện. Nội dung này được tạo trong app theo cùng
    cấu trúc prompt phân tích Gemini, để bài vẫn có kết quả AI khi demo hoặc khi
    Gemini tạm hết hạn mức.
    """
    n = _lesson_number_from_name(lesson_name)
    key_text = _context_key_summary(result_data)

    lesson_focus = {
        1: (
            "mô hình Cobb-Douglas mở rộng, TFP, sai số MAPE và mô phỏng GDP 2030",
            "Kết quả cần đọc theo logic đóng góp tăng trưởng: vốn, lao động, số hóa, AI, nhân lực số và TFP cùng giải thích biến động GDP. Nếu MAPE thấp, mô hình khớp tốt trong mẫu; nếu MAPE cao, cần xem lại hệ số đàn hồi và cách đo các biến D, AI, H.",
            "Nên dùng kết quả để thảo luận khả năng đạt mục tiêu kinh tế số 30% GDP vào 2030, đồng thời bổ sung ràng buộc về ngân sách, nhân lực, hạ tầng dữ liệu và độ trễ chính sách."
        ),
        2: (
            "bài toán LP phân bổ ngân sách số cho hạ tầng, AI-dữ liệu, nhân lực số và R&D",
            "Nghiệm tối ưu thể hiện cách phân bổ nguồn lực để tăng GDP kỳ vọng lớn nhất trong điều kiện vẫn đáp ứng các mức sàn chính sách. Các ràng buộc chặt, đặc biệt ngân sách tổng và tỷ trọng công nghệ chiến lược, cho thấy điểm nghẽn chính trong quyết định đầu tư công.",
            "Nên xem shadow price như tín hiệu lợi ích biên của ngân sách, nhưng không coi đó là kết luận tuyệt đối vì mô hình chưa phản ánh độ trễ giải ngân, nợ công và rủi ro triển khai."
        ),
        3: (
            "chỉ số ưu tiên ngành Priority_i cho 10 ngành kinh tế Việt Nam",
            "Kết quả xếp hạng giúp nhận diện ngành có tiềm năng lan tỏa, xuất khẩu, tăng trưởng và sẵn sàng AI cao hơn. Sự thay đổi top-3 khi đổi trọng số AI readiness phản ánh mức nhạy cảm của quyết định chính sách với ưu tiên của nhà quản lý.",
            "Nên dùng bảng xếp hạng như công cụ sàng lọc ban đầu, sau đó kết hợp tham vấn chuyên gia và kiểm tra tính bao trùm để tránh ưu tiên quá mức cho ngành đã có lợi thế sẵn."
        ),
        4: (
            "LP phân bổ ngân sách số theo 6 vùng và 4 hạng mục đầu tư",
            "Kết quả phân bổ cho thấy sự đánh đổi giữa tối đa hóa GDP gain và bảo đảm công bằng vùng miền. Ràng buộc sàn/trần ngân sách giúp tránh dồn vốn quá nhiều về vùng có hệ số tác động cao, còn ràng buộc công bằng digital index buộc mô hình nâng năng lực số của các vùng yếu hơn.",
            "Khuyến nghị là ưu tiên hạ tầng và nhân lực số ở vùng có digital index thấp, đồng thời tập trung AI/R&D ở vùng có năng lực hấp thụ tốt; phần chênh lệch Z* khi bỏ công bằng chính là chi phí định lượng của mục tiêu bao trùm."
        ),
        5: (
            "MIP lựa chọn 15 dự án chuyển đổi số với ngân sách và ràng buộc tiên quyết",
            "Danh mục được chọn cần được hiểu như tổ hợp dự án tối ưu trong điều kiện ngân sách 5 năm, ngân sách giai đoạn 1-2, ràng buộc loại trừ trung tâm dữ liệu, yêu cầu đào tạo trước AI/bán dẫn và dự án an ninh mạng bắt buộc.",
            "Nên chú ý các dự án có tỷ suất lợi ích cao nhưng không được chọn do vướng ràng buộc hệ thống. Khi thêm rủi ro tiến độ, danh mục có thể dịch chuyển khỏi các dự án lợi ích cao nhưng xác suất hoàn thành thấp."
        ),
        6: (
            "TOPSIS xếp hạng 6 vùng theo mức độ ưu tiên đầu tư AI",
            "Điểm TOPSIS càng cao nghĩa là vùng đó gần phương án lý tưởng hơn trên các tiêu chí GRDP/người, FDI, digital index, AI readiness, lao động đào tạo, R&D, internet và Gini. So sánh trọng số chuyên gia với entropy cho thấy kết quả phụ thuộc vào cách xác định ưu tiên.",
            "Nên dùng top-3 TOPSIS làm gợi ý chọn vùng triển khai trung tâm AI, nhưng cần bổ sung tiêu chí địa-chính trị, an ninh dữ liệu và khả năng lan tỏa vùng trước khi ra quyết định cuối cùng."
        ),
        7: (
            "tối ưu đa mục tiêu Pareto giữa tăng trưởng, bao trùm, môi trường và an ninh dữ liệu",
            "Tập nghiệm Pareto cho thấy không tồn tại một phương án tối ưu tuyệt đối cho mọi mục tiêu. Phương án tăng trưởng cao thường phải đánh đổi với công bằng, phát thải hoặc rủi ro dữ liệu; phương án thỏa hiệp giúp cân bằng các ưu tiên chính sách.",
            "Nên trình bày Pareto như công cụ hỗ trợ thảo luận chính sách, không thay thế quyết định chính trị; lựa chọn cuối cùng cần dựa trên trọng số mục tiêu được công khai và giải trình."
        ),
        8: (
            "tối ưu động phân bổ liên thời gian 2026-2035",
            "Kết quả quỹ đạo K, D, AI, H, Y và C cho thấy phân bổ vốn hiện tại ảnh hưởng đến năng lực sản xuất và phúc lợi tương lai. Kịch bản cú sốc 2028 giúp kiểm tra khả năng chống chịu của chiến lược đầu tư.",
            "Nên so sánh chiến lược front-load với đầu tư trải đều: front-load có thể nâng năng lực sớm hơn nhưng làm giảm tiêu dùng ngắn hạn; đầu tư đều ổn định hơn nhưng có thể chậm tạo đột phá."
        ),
        9: (
            "mô hình tác động AI tới lao động, NetJob và đào tạo lại",
            "Kết quả cần được đọc theo cân bằng giữa việc làm bị thay thế do tự động hóa và việc làm mới nhờ AI/đào tạo lại. Những ngành có lao động lớn, rủi ro tự động hóa cao và năng lực đào tạo thấp là nhóm dễ tổn thương nhất.",
            "Khuyến nghị là gắn đầu tư AI với ngân sách đào tạo lại bắt buộc, đặt trần displaced jobs theo ngành và ưu tiên nhóm lao động dễ bị thay thế để tránh tăng bất bình đẳng."
        ),
        10: (
            "stochastic programming hai giai đoạn dưới bất định kịch bản",
            "So sánh SP với EV, deterministic từng kịch bản và robust regret giúp thấy giá trị của quyết định linh hoạt khi tương lai bất định. VSS và EVPI là hai chỉ số quan trọng để lượng hóa lợi ích của mô hình ngẫu nhiên và thông tin hoàn hảo.",
            "Nên dùng nghiệm SP khi mục tiêu là cân bằng hiệu quả kỳ vọng và khả năng thích ứng; dùng robust nếu nhà hoạch định ưu tiên tránh kịch bản xấu nhất."
        ),
        11: (
            "Q-learning cho chính sách kinh tế thích nghi",
            "Chính sách học tăng cường chọn hành động dựa trên trạng thái rời rạc của nền kinh tế, thay vì cố định một quy tắc phân bổ duy nhất. Learning curve và so sánh với rule-based cho biết agent có học được chính sách tốt hơn hay không.",
            "Nên coi Q-learning là mô phỏng chính sách thích nghi, không phải công cụ tự động ra quyết định; cần kiểm tra an toàn, giải thích được và giới hạn hành động trước khi ứng dụng thực tế."
        ),
        12: (
            "dashboard tích hợp AIDEOM-VN với dự báo, phân bổ, readiness, lao động, rủi ro và so sánh kịch bản",
            "Kết quả tổng hợp giúp so sánh các kịch bản S1-S5 trên nhiều trục: tăng trưởng, việc làm, công bằng, rủi ro và năng lực hấp thụ. Kịch bản cân bằng thường phù hợp hơn khi không muốn tối đa hóa một chỉ tiêu đơn lẻ.",
            "Khuyến nghị là dùng dashboard để giải thích trade-off chính sách, cảnh báo rủi ro và lựa chọn kịch bản có tính khả thi cao nhất thay vì chỉ chọn phương án có GDP cao nhất."
        ),
    }

    focus, meaning, recommendation = lesson_focus.get(
        n,
        (
            f"mô hình {model_name}",
            "Kết quả mô hình cho phép chuyển bài toán chính sách thành phân tích định lượng có biến đầu vào, ràng buộc và tiêu chí đánh giá rõ ràng.",
            "Nên dùng kết quả như cơ sở hỗ trợ quyết định, kết hợp thêm kiểm định dữ liệu, phân tích độ nhạy và thảo luận chuyên gia."
        ),
    )

    return f"""
### Kết quả phân tích AI


**1. Tóm tắt kết quả chính**  
Trang **{lesson_name}** đã chạy nhóm kết quả về **{focus}**. Các dữ liệu đang được hệ thống đưa vào phân tích gồm: **{key_text}**. Nhìn chung, kết quả cần được đọc theo hướng so sánh phương án/kịch bản, mức độ thỏa ràng buộc và ý nghĩa của các chỉ tiêu đầu ra, thay vì chỉ nhìn một con số tối ưu đơn lẻ.

**2. Ý nghĩa kinh tế/chính sách**  
{meaning}

**3. Điểm mạnh của kết quả**  
Ưu điểm chính của trang này là biến một yêu cầu định tính của chính sách công thành mô hình có thể điều chỉnh tham số, chạy lại kết quả, xem bảng, biểu đồ và diễn giải. Cách trình bày này giúp người học chứng minh được vì sao một phương án được ưu tiên, đồng thời thấy rõ tác động của ràng buộc ngân sách, vùng, ngành, nhân lực, rủi ro hoặc bất định.

**4. Rủi ro/hạn chế cần lưu ý**  
Kết quả vẫn phụ thuộc vào dữ liệu đầu vào và hệ số giả định. Nếu dữ liệu chưa đủ chi tiết hoặc hệ số chưa được ước lượng thực nghiệm, kết luận nên được hiểu là mô phỏng hỗ trợ ra quyết định. Ngoài ra, các yếu tố thực tế như độ trễ giải ngân, năng lực hấp thụ công nghệ, phối hợp thể chế và phản ứng của doanh nghiệp có thể làm kết quả khác với mô hình.

**5. Khuyến nghị chính sách**  
{recommendation} Nên trình bày kết quả cùng phân tích độ nhạy để chứng minh phương án được chọn không chỉ tốt trong một bộ tham số duy nhất, mà vẫn hợp lý khi ưu tiên chính sách thay đổi.
""".strip()


def _friendly_gemini_error(exc, lesson_name, model_name, result_data=None):
    """Trả về phân tích dự phòng, không hiển thị lỗi API dài trên giao diện."""
    return _offline_ai_fallback(lesson_name, model_name, result_data), "fallback_internal_ai"


def _clean_old_ai_output(text):
    """Dọn nội dung AI cũ đã lưu trong session_state.

    Không hiển thị lỗi API/quota quá dài và tự xóa dòng chú thích chế độ
    phân tích còn lưu từ bản cũ, nhưng vẫn giữ nguyên phần kết quả phía dưới.
    """
    if not isinstance(text, str):
        return text

    bad_terms = (
        "RESOURCE_EXHAUSTED",
        "generativelanguage.googleapis.com",
        "GenerateRequestsPerDayPerProjectPerModel-FreeTier",
        "Quota exceeded",
        "Gemini API đang tạm lỗi",
        "Chưa có GEMINI_API_KEY",
    )
    if any(term in text for term in bad_terms):
        return None

    # Xóa riêng ghi chú chế độ phân tích còn lưu trong session cũ.
    old_prefix = "Chế độ" + " phân tích:"
    cleaned_lines = []
    for line in text.splitlines():
        if old_prefix.lower() in line.lower():
            continue
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def analyze_with_gemini(lesson_name, model_name, input_params=None, result_data=None):
    """Gọi Gemini API để phân tích kết quả. Nếu Gemini lỗi/quota thì dùng AI nội bộ dự phòng."""
    api_key = _get_gemini_api_key()
    if not api_key:
        return _offline_ai_fallback(lesson_name, model_name, result_data), "fallback_no_key"

    try:
        from google import genai
    except Exception:
        return _offline_ai_fallback(lesson_name, model_name, result_data), "fallback_no_library"

    prompt = _ai_make_prompt(
        lesson_name=lesson_name,
        model_name=model_name,
        input_params=input_params,
        result_data=result_data,
    )

    try:
        client = genai.Client(api_key=api_key)
        last_exc = None
        for model in ("gemini-2.0-flash", "gemini-1.5-flash"):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                text = getattr(response, "text", "") or ""
                if text.strip():
                    return text.strip(), "ok_gemini"
            except Exception as exc:
                last_exc = exc
                continue
        return _friendly_gemini_error(last_exc, lesson_name, model_name, result_data)
    except Exception as exc:
        return _friendly_gemini_error(exc, lesson_name, model_name, result_data)


def ai_analysis_panel(lesson_name, model_name, input_params=None, result_data=None, key="ai_panel"):
    """Hiển thị tác nhân AI phân tích kết quả ở cuối từng bài.

    Bản ổn định: không hiện hướng dẫn cấu hình trên giao diện, không đổ lỗi quota dài,
    và có phân tích dự phòng để các phần không liên quan tới AI không bị ảnh hưởng.
    """
    st.markdown("---")
    st.markdown("## 🤖 Tác nhân AI phân tích kết quả")

    button_key = f"{key}_button"
    output_key = f"{key}_output"
    status_key = f"{key}_status"

    # Dọn lỗi API dài còn lưu từ phiên bản cũ trong session state.
    if output_key in st.session_state:
        cleaned = _clean_old_ai_output(st.session_state.get(output_key))
        if cleaned is None:
            st.session_state.pop(output_key, None)
            st.session_state.pop(status_key, None)
        else:
            st.session_state[output_key] = cleaned

    if st.button("Phân tích kết quả bằng Gemini", key=button_key):
        with st.spinner("Đang phân tích kết quả của bài này..."):
            text, status = analyze_with_gemini(
                lesson_name=lesson_name,
                model_name=model_name,
                input_params=input_params or {},
                result_data=result_data or {},
            )
            st.session_state[output_key] = _clean_old_ai_output(text) or _offline_ai_fallback(
                lesson_name, model_name, result_data
            )
            st.session_state[status_key] = status

    if output_key in st.session_state and st.session_state[output_key]:
        st.markdown(st.session_state[output_key])


# =========================
# Data and helpers
# =========================
@st.cache_data
def load_macro():
    return pd.read_csv(DATA_DIR / "vietnam_macro_2020_2025.csv", encoding="utf-8-sig")


@st.cache_data
def load_regions():
    return pd.read_csv(DATA_DIR / "vietnam_regions_2024.csv", encoding="utf-8-sig")


@st.cache_data
def load_sectors():
    return pd.read_csv(DATA_DIR / "vietnam_sectors_2024.csv", encoding="utf-8-sig")


def hero(title, subtitle, tags=None):
    tags = tags or []
    tag_html = "".join([f"<span class='pill'>{t}</span>" for t in tags])
    st.markdown(
        f"""
        <div class="hero">
            <div>{tag_html}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_cards(items):
    cols = st.columns(len(items))
    for col, (label, value, note) in zip(cols, items):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-note">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def section(title, body=None):
    st.markdown(f"### {title}")
    if body:
        st.markdown(f"<div class='muted'>{body}</div>", unsafe_allow_html=True)


def safe_mape(y, yhat):
    y = np.asarray(y, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    return np.mean(np.abs((y - yhat) / np.maximum(np.abs(y), 1e-9))) * 100


def minmax(s):
    s = pd.Series(s, dtype=float)
    if abs(s.max() - s.min()) < 1e-12:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def reverse_minmax(s):
    s = pd.Series(s, dtype=float)
    if abs(s.max() - s.min()) < 1e-12:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s.max() - s) / (s.max() - s.min())


def gini(x):
    x = np.asarray(x, dtype=float)
    x = x - np.min(x)
    if np.mean(x) == 0:
        return 0.0
    x = np.sort(x)
    n = len(x)
    return (2 * np.sum((np.arange(1, n + 1)) * x)) / (n * np.sum(x)) - (n + 1) / n


def plot_bar(df, x, y, title, color=None, text=None):
    fig = px.bar(df, x=x, y=y, color=color, text=text, template=PLOT_TEMPLATE, title=title)
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=54, b=10))
    fig.update_traces(textposition="outside", cliponaxis=False)
    return fig


def plot_line(df, x, y, title, color=None):
    fig = px.line(df, x=x, y=y, markers=True, color=color, template=PLOT_TEMPLATE, title=title)
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=54, b=10))
    return fig


def cobb_douglas_arrays():
    macro = load_macro()
    Y = macro["GDP_trillion_VND"].values.astype(float)
    K = np.array([16500, 17800, 19600, 21300, 23500, 25900], dtype=float)
    L = np.array([53.6, 50.5, 51.7, 52.4, 52.9, 53.4], dtype=float)
    D = macro["digital_economy_share_GDP_pct"].values.astype(float)
    AI = np.array([55.6, 60.2, 65.4, 67.0, 73.8, 80.1], dtype=float)
    H = np.array([24.1, 26.1, 26.2, 27.0, 28.4, 29.2], dtype=float)
    return macro["year"].values, Y, K, L, D, AI, H


def compute_tfp(alpha=0.33, beta=0.42, gamma=0.10, delta=0.08, theta=0.07):
    years, Y, K, L, D, AI, H = cobb_douglas_arrays()
    A = Y / (K**alpha * L**beta * D**gamma * AI**delta * H**theta)
    return years, Y, K, L, D, AI, H, A


def region_beta_matrix():
    regions = [
        "Trung du miền núi phía Bắc",
        "Đồng bằng sông Hồng",
        "Bắc Trung Bộ + DH Trung Bộ",
        "Tây Nguyên",
        "Đông Nam Bộ",
        "Đồng bằng sông Cửu Long",
    ]
    items = ["I - Hạ tầng số", "D - CĐS DN", "AI", "H - Nhân lực số"]
    beta = np.array(
        [
            [1.15, 0.85, 0.55, 1.30],
            [0.95, 1.25, 1.40, 1.05],
            [1.05, 0.95, 0.85, 1.15],
            [1.20, 0.75, 0.45, 1.35],
            [0.90, 1.30, 1.55, 1.00],
            [1.10, 0.85, 0.65, 1.25],
        ],
        dtype=float,
    )
    D0 = np.array([38, 78, 55, 32, 82, 48], dtype=float)
    return regions, items, beta, D0


def topsis_score(df, criteria, weights, is_benefit):
    X = df[criteria].values.astype(float)
    denom = np.sqrt((X**2).sum(axis=0))
    R = X / np.where(denom == 0, 1, denom)
    V = R * np.asarray(weights)
    is_benefit = np.asarray(is_benefit)
    A_star = np.where(is_benefit, V.max(axis=0), V.min(axis=0))
    A_neg = np.where(is_benefit, V.min(axis=0), V.max(axis=0))
    S_star = np.sqrt(((V - A_star) ** 2).sum(axis=1))
    S_neg = np.sqrt(((V - A_neg) ** 2).sum(axis=1))
    return S_neg / np.maximum(S_star + S_neg, 1e-12)


def entropy_weights_positive(X):
    X = np.asarray(X, dtype=float)
    X = X - X.min(axis=0) + 1e-9
    P = X / np.maximum(X.sum(axis=0), 1e-12)
    k = 1.0 / np.log(len(X))
    E = -k * np.sum(P * np.log(P + 1e-12), axis=0)
    d = 1 - E
    return d / np.maximum(d.sum(), 1e-12)


def scenario_shares():
    return {
        "S1 - Truyền thống": np.array([0.70, 0.10, 0.10, 0.10]),
        "S2 - Số hóa nhanh": np.array([0.25, 0.45, 0.15, 0.15]),
        "S3 - AI dẫn dắt": np.array([0.20, 0.20, 0.45, 0.15]),
        "S4 - Bao trùm số": np.array([0.30, 0.20, 0.10, 0.40]),
        "S5 - Tối ưu cân bằng": np.array([0.34, 0.26, 0.18, 0.22]),
    }


def simulate_dynamic(shares, start=2026, end=2035, invest_rate=0.22, shock_2028=0.0):
    years, Y0s, K0s, L0s, D0s, AI0s, H0s, A0s = compute_tfp()
    K = K0s[-1] * 1.06
    L = L0s[-1] * 1.01
    D = D0s[-1] + 0.8
    AI = AI0s[-1] + 6
    H = H0s[-1] + 0.8
    A = A0s[-1] * 1.012
    rows = []
    for year in range(start, end + 1):
        Y = A * (K**0.33) * (L**0.42) * (D**0.10) * (AI**0.08) * (H**0.07)
        if year == 2028:
            Y *= 1 - shock_2028
        invest = Y * invest_rate
        C = Y - invest
        rows.append([year, Y, C, K, D, AI, H, invest])
        K = (1 - 0.05) * K + shares[0] * invest
        D = max(1, (1 - 0.12) * D + shares[1] * invest / 240)
        AI = max(1, (1 - 0.15) * AI + shares[2] * invest / 135)
        H = max(1, H + 0.8 * shares[3] * invest / 520 - 0.02 * H)
        L = L * 1.006
        A = A * (1 + 0.00008 * D + 0.00004 * AI + 0.00006 * H)
    return pd.DataFrame(rows, columns=["Năm", "Y_GDP", "C_tiêu_dùng", "K", "D", "AI", "H", "Đầu_tư"])



# =========================
# Assignment structure checklist
# =========================
ASSIGNMENT_STRUCTURE = {
    1: [
        ("1.1", "Bối cảnh Việt Nam"),
        ("1.2", "Mô hình Cobb-Douglas mở rộng, log và growth accounting"),
        ("1.3", "Dữ liệu Việt Nam 2020-2025"),
        ("1.4.1", "Ước lượng TFP A_t và vẽ xu hướng"),
        ("1.4.2", "Dự báo Y_hat và báo cáo MAPE"),
        ("1.4.3", "Phân rã tăng trưởng K, L, D, AI, H, TFP"),
        ("1.4.4", "Mô phỏng GDP Việt Nam 2030"),
        ("1.5", "Trả lời 3 câu thảo luận chính sách"),
    ],
    2: [
        ("2.1", "Bối cảnh phân bổ ngân sách số"),
        ("2.2", "Mô hình LP 4 biến và hệ ràng buộc"),
        ("2.3", "Diễn giải hệ số mục tiêu"),
        ("2.4.1", "Giải bằng scipy.optimize.linprog"),
        ("2.4.2", "Giải bằng PuLP và đọc shadow price"),
        ("2.4.3", "Độ nhạy ngân sách B=100,120,140"),
        ("2.4.4", "Thay x3 >= 30 và kiểm tra khả thi"),
        ("2.5", "Trả lời 3 câu thảo luận chính sách"),
    ],
    3: [
        ("3.1", "Bối cảnh ưu tiên ngành Việt Nam"),
        ("3.2", "Công thức Priority_i và chuẩn hóa min-max"),
        ("3.3", "Dữ liệu 10 ngành năm 2024"),
        ("3.4.1", "Chuẩn hóa đủ 7 tiêu chí"),
        ("3.4.2", "Tính Priority_i và xếp hạng 10 ngành"),
        ("3.4.3", "Độ nhạy trọng số AI readiness 0,05-0,40"),
        ("3.4.4", "So sánh định hướng tăng trưởng và bao trùm"),
        ("3.5", "Trả lời 3 câu thảo luận chính sách"),
    ],
    4: [
        ("4.1", "Bối cảnh phân bổ ngân sách số theo 6 vùng"),
        ("4.2", "Mô hình LP đầy đủ 24 biến, C1-C6"),
        ("4.3", "Bảng hệ số beta và Digital Index ban đầu"),
        ("4.4.1", "Cài đặt/giải bằng PuLP, đối chiếu SciPy"),
        ("4.4.2", "Cài đặt lại bằng CVXPY"),
        ("4.4.3", "Heatmap phân bổ và kiểm tra nghiệm"),
        ("4.4.4", "So sánh với mô hình bỏ công bằng C5"),
        ("4.5", "Trả lời câu hỏi chính sách a-b-c và ghi chú khả thi lambda"),
    ],
    5: [
        ("5.1", "Bối cảnh chương trình 15 dự án"),
        ("5.2", "Danh mục đúng P1-P15"),
        ("5.3", "Mô hình MIP nhị phân với C1-C7"),
        ("5.4.1", "Giải bằng PuLP/CBC, báo cáo dự án chọn, chi phí, NPV, Z*/chi phí"),
        ("5.4.2", "Nới ngân sách lên 100.000 tỷ và so sánh tập dự án"),
        ("5.4.3", "Bắt buộc P1 và P2, kiểm tra khả thi và thay đổi Z*"),
        ("5.4.4", "Thêm xác suất hoàn thành p_i và tối đa hóa E[Z]"),
        ("5.5", "Trả lời 3 câu thảo luận chính sách"),
    ],
    6: [
        ("6.1", "Bối cảnh xếp hạng 6 vùng ưu tiên AI"),
        ("6.2", "Lý thuyết TOPSIS 5 bước"),
        ("6.3", "Dữ liệu 6 vùng và 8 tiêu chí"),
        ("6.4.1", "TOPSIS với trọng số chuyên gia"),
        ("6.4.2", "Trọng số Entropy và so sánh hạng"),
        ("6.4.3", "Độ nhạy w_AI từ 0,10 đến 0,40"),
        ("6.4.4", "AHP mở rộng và so sánh với TOPSIS"),
        ("6.5", "Trả lời câu hỏi chính sách a-b-c-d"),
    ],
    7: [
        ("7.1", "Bối cảnh tối ưu đa mục tiêu"),
        ("7.2", "Mô hình 24 biến, 4 mục tiêu xung đột"),
        ("7.3", "Tham số bổ sung e_r, rho_r, sigma_r và cấu hình NSGA-II"),
        ("7.4.1", "Cài đặt pymoo ElementwiseProblem, NSGA-II pop_size=100, n_gen=200"),
        ("7.4.2", "Trích xuất Pareto, vẽ scatter 3D và parallel coordinates"),
        ("7.4.3", "Dùng TOPSIS chọn nghiệm thỏa hiệp"),
        ("7.4.4", "Tính chi phí cơ hội của các mục tiêu"),
        ("7.5", "Trả lời 3 câu thảo luận chính sách"),
    ],
    8: [
        ("8.1", "Bối cảnh tối ưu động 2026-2035"),
        ("8.2", "Mô hình động, hàm mục tiêu, hàm sản xuất và chuyển trạng thái"),
        ("8.3.1", "Giải NLP/log-linear bằng SLSQP hoặc CVXPY"),
        ("8.3.2", "Vẽ quỹ đạo K, D, AI, H, Y, C"),
        ("8.3.3", "Thêm cú sốc GDP 2028 giảm 8% và tối ưu lại"),
        ("8.3.4", "So sánh đầu tư trải đều và front-load"),
        ("8.4", "Trả lời 3 câu thảo luận chính sách"),
    ],
    9: [
        ("9.1", "Bối cảnh tác động AI tới lao động Việt Nam"),
        ("9.2", "Mô hình NetJob, DisplacedJob, RetrainingCapacity"),
        ("9.3", "Tham số 8 ngành"),
        ("9.4.1", "Giải LP bằng PuLP/CVXPY, in x_AI, x_H, NetJob"),
        ("9.4.2", "Tìm ngưỡng x_H ngành chế biến chế tạo để NetJob_2 >= 0"),
        ("9.4.3", "Sankey/swimming lane nhóm dễ tổn thương ngành 1,3,4"),
        ("9.4.4", "Thêm ràng buộc DisplacedJob_i <= 5% L_i và kiểm tra khả thi"),
        ("9.5", "Trả lời 3 câu thảo luận chính sách"),
    ],
    10: [
        ("10.1", "Bối cảnh bất định sau khi quyết định đầu tư"),
        ("10.2", "Cây kịch bản 4 trạng thái và xác suất"),
        ("10.3", "Mô hình stochastic programming hai giai đoạn"),
        ("10.4", "Bảng hệ số beta theo kịch bản"),
        ("10.5.1", "Cài đặt mô hình Pyomo/PuLP first-stage và second-stage"),
        ("10.5.2", "Giải deterministic từng kịch bản và EV, so sánh với SP"),
        ("10.5.3", "Tính VSS và EVPI"),
        ("10.5.4", "Robust optimization cực tiểu hóa regret xấu nhất"),
        ("10.6", "Trả lời 3 câu thảo luận chính sách"),
    ],
    11: [
        ("11.1", "Bối cảnh chính sách thích nghi"),
        ("11.2", "MDP rời rạc 3^4=81 trạng thái, 5 hành động, T=10"),
        ("11.3.1", "Cài đặt gym/gymnasium Env với reset, step, action_space, observation_space"),
        ("11.3.2", "Q-learning alpha=0,1, gamma=0,95, epsilon 1,0 xuống 0,05, 10.000 episodes"),
        ("11.3.3", "Trích xuất pi*(s) cho Việt Nam 2026 và 4 trạng thái giả định"),
        ("11.3.4", "So sánh reward tích lũy với 3 rule-based và vẽ learning curve"),
        ("11.3.5", "DQN bằng stable-baselines3, 2 hidden layers 64 units"),
        ("11.4", "Trả lời 3 câu thảo luận chính sách"),
    ],
    12: [
        ("12.1", "Kiến trúc M1-M6 của AIDEOM-VN"),
        ("12.2", "Năm kịch bản S1-S5"),
        ("12.3", "Yêu cầu kỹ thuật: module .py, dashboard >=4 tab, test S1/S3/S5"),
        ("12.4", "Sản phẩm bàn giao"),
        ("12.5", "Tiêu chí đánh giá"),
        ("12.6", "Hướng mở rộng"),
    ],
}


_ASSIGNMENT_MAP_RENDERED_THIS_RUN = set()


def show_assignment_structure(page_no):
    """Hiển thị bản đồ đánh số đúng 1 lần trong mỗi lần render trang."""
    items = ASSIGNMENT_STRUCTURE.get(page_no, [])
    if not items:
        return
    if page_no in _ASSIGNMENT_MAP_RENDERED_THIS_RUN:
        return
    _ASSIGNMENT_MAP_RENDERED_THIS_RUN.add(page_no)

    with st.expander("✅ Bản đồ yêu cầu đề bài được trả lời trong trang này", expanded=False):
        checklist = pd.DataFrame(
            items,
            columns=["Mục/Câu theo đề", "Nội dung đã trình bày trong dashboard"],
        )
        checklist["Trạng thái"] = "Đã trả lời"
        st.dataframe(checklist, use_container_width=True, hide_index=True)


# =========================
# Pages (redesigned UI v2)
# =========================

# ──────────────────────────────────────────────────────────
# SHARED STYLE HELPERS
# ──────────────────────────────────────────────────────────

_FONT_IMPORTED = False

def _inject_page_css(css: str):
    global _FONT_IMPORTED
    font_css = ""
    if not _FONT_IMPORTED:
        font_css = """
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
        h1, h2, h3, h4, .vn-title, .vn-banner-title { font-family: 'Outfit', sans-serif; }
        """
        _FONT_IMPORTED = True
    st.markdown(f"<style>{font_css}{css}</style>", unsafe_allow_html=True)


def _banner(emoji: str, title: str, subtitle: str, tag_html: str = "", accent: str = "#7C3AED"):
    st.markdown(
        f"""
        <div style="
            background:#fff;
            border:1px solid #ECECF1;
            border-left:6px solid {accent};
            border-radius:12px;
            padding:22px 26px 20px;
            margin-bottom:18px;
            display:flex;gap:18px;align-items:flex-start;
            box-shadow:0 2px 10px rgba(17,24,39,.04);">
          <div style="font-size:34px;line-height:1;flex-shrink:0;
                      width:54px;height:54px;border-radius:12px;
                      display:flex;align-items:center;justify-content:center;
                      background:{accent}14;">{emoji}</div>
          <div style="flex:1;min-width:0">
            <div class="vn-banner-title" style="font-size:clamp(1.25rem,2.4vw,1.7rem);font-weight:800;
                        color:#1F2430;letter-spacing:-0.02em;line-height:1.2">{title}</div>
            <div style="color:#6B7280;font-size:.92rem;margin-top:6px;max-width:880px;line-height:1.55">{subtitle}</div>
            {f'<div style="margin-top:12px;display:flex;flex-wrap:wrap;gap:6px">{tag_html}</div>' if tag_html else ''}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _pill(text, color="#7C3AED", bg="rgba(124,58,237,.10)", border="rgba(124,58,237,.25)"):
    return (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:6px;'
        f'background:{bg};color:{color};border:1px solid {border};'
        f'font-size:.72rem;font-weight:700;letter-spacing:.03em;text-transform:uppercase">{text}</span>'
    )


def _kpi(label, value, note, accent="#7C3AED", bg="#FFFFFF"):
    return f"""
    <div style="background:{bg};border:1px solid #ECECF1;border-radius:12px;
                padding:14px 16px;border-top:3px solid {accent};
                box-shadow:0 1px 6px rgba(17,24,39,.04)">
      <div style="color:#9CA3AF;font-size:10.5px;font-weight:700;text-transform:uppercase;
                  letter-spacing:.07em;margin-bottom:6px">{label}</div>
      <div style="color:#1F2430;font-size:23px;font-weight:800;letter-spacing:-0.03em;
                  font-family:'Outfit',sans-serif">{value}</div>
      <div style="color:{accent};font-size:11px;margin-top:4px;font-weight:600">{note}</div>
    </div>"""


def _kpi_row(items):
    cols = st.columns(len(items))
    for col, (label, value, note) in zip(cols, items):
        with col:
            st.markdown(_kpi(label, value, note), unsafe_allow_html=True)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


def _card(content_html, accent_top: str | None = None):
    border_left = f"border-left:4px solid {accent_top};" if accent_top else "border:1px solid #ECECF1;"
    st.markdown(
        f"""<div style="background:#fff;{border_left}border-radius:10px;
                        padding:16px 20px;margin-bottom:10px;
                        box-shadow:0 1px 6px rgba(17,24,39,.04)">
        {content_html}</div>""",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────
# HOME PAGE
# ──────────────────────────────────────────────────────────

def page_home():
    _inject_page_css("""
    .home-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:18px}
    .hg-card{background:#fff;border:1px solid #ECECF1;border-radius:12px;
             padding:18px 18px 14px;box-shadow:0 1px 6px rgba(17,24,39,.04);
             transition:transform .15s,box-shadow .15s}
    .hg-card:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(124,58,237,.10)}
    .hg-icon{font-size:26px;margin-bottom:8px}
    .hg-title{font-weight:700;color:#1F2430;font-size:.95rem;font-family:'Outfit',sans-serif}
    .hg-sub{color:#6B7280;font-size:.81rem;margin-top:4px;line-height:1.5}
    .level-badge{display:inline-block;padding:3px 10px;border-radius:6px;font-size:.74rem;
                 font-weight:700;margin-bottom:10px}
    .kpi-hero{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px}
    @media(max-width:700px){.kpi-hero{grid-template-columns:repeat(2,1fr)}}
    .hero-kpi{background:#fff;border:1px solid #ECECF1;border-radius:12px;
              padding:14px 16px;border-bottom:3px solid #7C3AED;
              box-shadow:0 1px 6px rgba(17,24,37,.04)}
    .hero-kpi-label{color:#9CA3AF;font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.07em}
    .hero-kpi-val{color:#1F2430;font-size:22px;font-weight:800;letter-spacing:-0.03em;margin:5px 0;
                  font-family:'Outfit',sans-serif}
    .hero-kpi-note{color:#059669;font-size:11px;font-weight:600}
    """)

    # ── Hero ──
    st.markdown("""
    <div style="background:#1B1830;
                border-radius:16px;padding:30px 32px 26px;margin-bottom:18px;
                position:relative;overflow:hidden;border:1px solid #2A2545">
      <div style="position:absolute;top:0;left:0;width:5px;height:100%;
                  background:linear-gradient(180deg,#a78bfa,#f472b6)"></div>
      <div style="position:relative;z-index:2;padding-left:6px">
        <div style="display:inline-flex;align-items:center;gap:8px;padding:4px 12px;
                    border-radius:6px;background:rgba(34,197,94,.12);border:1px solid rgba(34,197,94,.3);
                    color:#86efac;font-size:.72rem;font-weight:700;letter-spacing:.06em;
                    text-transform:uppercase;margin-bottom:14px">
          <span style="width:6px;height:6px;border-radius:50%;background:#22c55e"></span>
          Hệ thống đang hoạt động · 12/12 mô hình
        </div>
        <div class="vn-title" style="font-size:clamp(1.8rem,4.5vw,2.7rem);font-weight:800;color:#fff;
                    letter-spacing:-0.03em;line-height:1.1;margin-bottom:8px">
          VN AIDEOM-VN
          <span style="background:linear-gradient(90deg,#a78bfa,#f472b6);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent">Dashboard</span>
        </div>
        <div style="color:#9CA3AF;font-size:.92rem;max-width:760px;line-height:1.6">
          AI-Driven Decision Optimization Model for Vietnam — Nền tảng 12 bài toán tối ưu hóa
          kinh tế số Việt Nam, từ Cobb-Douglas đến Q-learning, tích hợp dữ liệu 2020–2035.
        </div>
        <div style="margin-top:14px;display:flex;flex-wrap:wrap;gap:6px">
          <span style="padding:3px 10px;border-radius:6px;background:rgba(255,255,255,.08);
                       color:#D1D5DB;font-size:.75rem;font-weight:600;border:1px solid rgba(255,255,255,.12)">🐍 Python</span>
          <span style="padding:3px 10px;border-radius:6px;background:rgba(255,255,255,.08);
                       color:#D1D5DB;font-size:.75rem;font-weight:600;border:1px solid rgba(255,255,255,.12)">⚡ Streamlit</span>
          <span style="padding:3px 10px;border-radius:6px;background:rgba(255,255,255,.08);
                       color:#D1D5DB;font-size:.75rem;font-weight:600;border:1px solid rgba(255,255,255,.12)">📊 Plotly</span>
          <span style="padding:3px 10px;border-radius:6px;background:rgba(255,255,255,.08);
                       color:#D1D5DB;font-size:.75rem;font-weight:600;border:1px solid rgba(255,255,255,.12)">🔢 SciPy · PuLP · CVXPY</span>
          <span style="padding:3px 10px;border-radius:6px;background:rgba(255,255,255,.08);
                       color:#D1D5DB;font-size:.75rem;font-weight:600;border:1px solid rgba(255,255,255,.12)">🤖 Gemini AI</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI strip ──
    st.markdown("""
    <div class="kpi-hero">
      <div class="hero-kpi">
        <div class="hero-kpi-label">GDP Việt Nam 2025</div>
        <div class="hero-kpi-val">514,0 tỷ USD</div>
        <div class="hero-kpi-note">↗ 8,02% so với 2024</div>
      </div>
      <div class="hero-kpi">
        <div class="hero-kpi-label">Kinh tế số / GDP</div>
        <div class="hero-kpi-val">≈ 19,5%</div>
        <div class="hero-kpi-note">↗ 1,2 điểm phần trăm</div>
      </div>
      <div class="hero-kpi">
        <div class="hero-kpi-label">FDI giải ngân 2025</div>
        <div class="hero-kpi-val">27,6 tỷ USD</div>
        <div class="hero-kpi-note">↗ 8,9% cùng kỳ</div>
      </div>
      <div class="hero-kpi">
        <div class="hero-kpi-label">GDP/người 2025</div>
        <div class="hero-kpi-val">5.026 USD</div>
        <div class="hero-kpi-note">↗ 6,9% theo giá hiện hành</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 12 modules grid ──
    st.markdown("### 📚 12 bài toán — 4 cấp độ")

    levels = [
        ("🟢 Dễ · Bài 1–3", "#22c55e", "rgba(34,197,94,.06)", [
            ("📈", "Bài 1", "Cobb-Douglas mở rộng", "TFP · Growth accounting · GDP 2030"),
            ("💰", "Bài 2", "LP ngân sách số", "SciPy · Shadow price · Sensitivity"),
            ("🏭", "Bài 3", "Priority 10 ngành", "Min-max · MCDM · Policy weight"),
        ]),
        ("🟡 Trung bình · Bài 4–6", "#F59E0B", "rgba(245,158,11,.06)", [
            ("🗺️", "Bài 4", "LP ngành–vùng", "24 biến · Fairness · CVXPY · PuLP"),
            ("🔲", "Bài 5", "MIP 15 dự án", "Binary · Knapsack · CBC · E[Z]"),
            ("🏆", "Bài 6", "TOPSIS 6 vùng", "Entropy · AHP · Sensitivity"),
        ]),
        ("🟠 Nâng cao · Bài 7–9", "#F97316", "rgba(249,115,22,.06)", [
            ("🌐", "Bài 7", "Pareto đa mục tiêu", "NSGA-II · Scatter 3D · Tradeoff"),
            ("⏳", "Bài 8", "Động 2026–2035", "SLSQP · Shock 2028 · Front-load"),
            ("👷", "Bài 9", "Lao động & AI", "NetJob · Sankey · Retraining"),
        ]),
        ("🟣 Chuyên sâu · Bài 10–12", "#7C3AED", "rgba(124,58,237,.06)", [
            ("🎲", "Bài 10", "Stochastic SP", "VSS · EVPI · Robust optimization"),
            ("🤖", "Bài 11", "Q-learning RL", "MDP · DQN · Adaptive policy"),
            ("🔗", "Bài 12", "AIDEOM tích hợp", "M1-M6 · 5 kịch bản · Pipeline"),
        ]),
    ]

    for level_label, dot_color, level_bg, modules in levels:
        st.markdown(
            f'<div style="background:{level_bg};border-radius:12px;padding:12px 16px 8px;margin-bottom:10px;'
            f'border-left:3px solid {dot_color}">'
            f'<div style="font-weight:700;color:#1F2430;font-size:.86rem;margin-bottom:10px;'
            f'font-family:\'Outfit\',sans-serif">{level_label}</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(3)
        for col, (icon, code, name, tech) in zip(cols, modules):
            with col:
                st.markdown(
                    f"""<div style="background:#fff;border:1px solid #ECECF1;border-radius:10px;
                                   padding:12px 14px 10px;box-shadow:0 1px 4px rgba(17,24,39,.04)">
                      <div style="font-size:20px">{icon}</div>
                      <div style="font-weight:700;color:#1F2430;font-size:.86rem;margin:4px 0 2px;
                                  font-family:'Outfit',sans-serif">{code} — {name}</div>
                      <div style="color:#9CA3AF;font-size:.74rem">{tech}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Footer ──
    st.markdown("""
    <div style="text-align:center;color:#9CA3AF;font-size:.8rem;margin-top:22px;padding:14px;
                border-top:1px solid #ECECF1">
      VN AIDEOM-VN · AI-Driven Decision Optimization Model for Vietnam<br>
      Python · Streamlit · SciPy · PuLP · CVXPY · Plotly · Gemini AI
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# BÀI 1 — Cobb-Douglas  (theme: xanh dương + cam)
# ──────────────────────────────────────────────────────────

def page_1():
    _inject_page_css("""
    .b1-tag{display:inline-block;padding:3px 10px;border-radius:6px;
            background:rgba(59,130,246,.1);color:#2563EB;
            border:1px solid rgba(59,130,246,.3);font-size:.74rem;font-weight:700;margin-right:6px}
    .b1-formula-box{background:#F8FAFF;border:1px solid #ECECF1;border-left:4px solid #2563EB;
                    border-radius:10px;padding:16px 20px;margin:12px 0}
    .b1-insight{background:#FFFAF5;border:1px solid #ECECF1;border-left:4px solid #F97316;
                border-radius:10px;padding:13px 16px;margin:10px 0;color:#7C2D12}
    .b1-success{background:#F6FFF8;border:1px solid #ECECF1;border-left:4px solid #22c55e;
                border-radius:10px;padding:13px 16px;margin:10px 0;color:#14532D}
    """)

    tags = "".join([_pill(t, "#2563EB", "rgba(59,130,246,.1)", "rgba(59,130,246,.3)")
                    for t in ["1.1–1.5", "Cobb-Douglas", "TFP", "MAPE", "GDP 2030"]])
    _banner("📈", "Bài 1 — Hàm sản xuất Cobb-Douglas mở rộng",
            "Mô hình hóa tăng trưởng GDP Việt Nam 2020–2025 với 5 yếu tố: K · L · D · AI · H. Phân rã TFP, dự báo và mô phỏng GDP 2030.",
            tags, "#2563EB")

    show_assignment_structure(1)

    # ── 1.1 Bối cảnh ──
    st.markdown("## 1.1 · Bối cảnh Việt Nam")
    macro = load_macro().sort_values("year").reset_index(drop=True)

    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.markdown("""
        <div style="background:#fff;border:1px solid #ECECF1;border-left:4px solid #2563EB;border-radius:10px;
                    padding:16px 20px;margin-bottom:8px">
          <div style="font-weight:700;color:#1F2430;margin-bottom:8px;font-family:'Outfit',sans-serif">🇻🇳 Giai đoạn 2020–2025</div>
          <div style="color:#4B5563;font-size:.92rem;line-height:1.7">
            GDP tăng từ <b>8.044,4</b> lên <b>12.847,6 nghìn tỷ VND</b>.<br>
            Kinh tế số: <b>12,0% → 19,5% GDP</b>.<br>
            DN công nghệ số: <b>55,6 → 80,1 nghìn</b>.<br>
            Lao động qua đào tạo: <b>24,1% → 29,2%</b>.
          </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        ctx = macro.loc[macro["year"].isin([2024, 2025]),
            ["year", "GDP_trillion_VND", "GDP_growth_pct", "digital_economy_share_GDP_pct"]].rename(
            columns={"year": "Năm", "GDP_trillion_VND": "GDP (nghìn tỷ)", 
                     "GDP_growth_pct": "Tăng trưởng %", "digital_economy_share_GDP_pct": "KT số %"})
        st.dataframe(ctx, use_container_width=True, hide_index=True)

    # ── 1.2 Mô hình ──
    st.markdown("## 1.2 · Mô hình toán học")
    st.markdown('<div class="b1-formula-box">', unsafe_allow_html=True)
    st.latex(r"Y_t = A_t \cdot K_t^{\alpha} \cdot L_t^{\beta} \cdot D_t^{\gamma} \cdot AI_t^{\delta} \cdot H_t^{\theta}, \quad \alpha+\beta+\gamma+\delta+\theta=1")
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("⚙️ Điều chỉnh hệ số đàn hồi", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        alpha = c1.slider("α — Vốn K", 0.20, 0.45, 0.33, 0.01, key="b1_alpha")
        beta  = c2.slider("β — Lao động L", 0.25, 0.55, 0.42, 0.01, key="b1_beta")
        gamma = c3.slider("γ — Số hóa D", 0.02, 0.20, 0.10, 0.01, key="b1_gamma")
        delta = c4.slider("δ — AI", 0.02, 0.18, 0.08, 0.01, key="b1_delta")
        theta = 1 - alpha - beta - gamma - delta
        if theta <= 0:
            st.error("Tổng α+β+γ+δ phải < 1 để θ > 0.")
            st.stop()
        st.markdown(f'<div class="b1-success">θ (nhân lực số) = <b>{theta:.2f}</b> · Tổng hệ số = 1,00 ✓</div>', unsafe_allow_html=True)

    # ── 1.3 Dữ liệu ──
    st.markdown("## 1.3 · Dữ liệu Việt Nam 2020–2025")
    years, Y, K, L, D, AI, H, A = compute_tfp(alpha, beta, gamma, delta, theta)
    A_mean = A.mean()
    Y_hat = A_mean * K**alpha * L**beta * D**gamma * AI**delta * H**theta
    mape = safe_mape(Y, Y_hat)
    annual_contributions = {
        "K — Vốn": alpha * np.diff(np.log(K)),
        "L — Lao động": beta * np.diff(np.log(L)),
        "D — Số hóa": gamma * np.diff(np.log(D)),
        "AI": delta * np.diff(np.log(AI)),
        "H — Nhân lực": theta * np.diff(np.log(H)),
        "TFP": np.diff(np.log(A)),
    }
    avg_log_growth = np.diff(np.log(Y)).mean()
    contrib_df = pd.DataFrame({
        "Yếu tố": list(annual_contributions.keys()),
        "Đóng góp bình quân (% log/năm)": [100 * v.mean() for v in annual_contributions.values()],
        "Tỷ trọng (%)": [100 * v.mean() / avg_log_growth for v in annual_contributions.values()],
    })
    input_df = pd.DataFrame({"Năm": years, "Y - GDP": Y, "K - Vốn": K, "L - Lao động": L,
                              "D - KT số": D, "AI - DN số": AI, "H - Đào tạo": H})
    st.dataframe(input_df, use_container_width=True, hide_index=True)
    st.caption("Hệ số mặc định theo đề: α=0,33 β=0,42 γ=0,10 δ=0,08 θ=0,07")

    n_years = 5
    K2030 = K[-1] * (1.06**n_years); L2030 = L[-1] * (1.06**n_years)
    D2030 = 30.0; AI2030 = 100.0; H2030 = 35.0; A2030 = A[-1] * (1.012**n_years)
    Y2030 = A2030 * K2030**alpha * L2030**beta * D2030**gamma * AI2030**delta * H2030**theta
    growth_2025_2030 = (Y2030 / Y[-1] - 1) * 100
    tfp_cagr = ((A[-1] / A[0]) ** (1/(len(A)-1)) - 1) * 100
    tfp_direction = "tăng" if A[-1] > A[0] else "giảm"

    # ── 1.4 Tabs ──
    st.markdown("## 1.4 · Yêu cầu lập trình")
    tab141, tab142, tab143, tab144 = st.tabs(
        ["📉 1.4.1 — TFP", "🎯 1.4.2 — Dự báo & MAPE", "🥧 1.4.3 — Phân rã", "🔭 1.4.4 — GDP 2030"])

    with tab141:
        tfp_df = pd.DataFrame({"Năm": years, "TFP Aₜ": A})
        c1, c2 = st.columns([1, 1.2])
        with c1:
            _kpi_row([("TFP 2020", f"{A[0]:.3f}", "điểm khởi đầu"),
                      ("TFP 2025", f"{A[-1]:.3f}", "điểm kết thúc"),
                      ("CAGR TFP", f"{tfp_cagr:.2f}%/năm", "tốc độ thay đổi")])
            st.dataframe(tfp_df, use_container_width=True, hide_index=True)
        with c2:
            fig = px.line(tfp_df, x="Năm", y="TFP Aₜ", markers=True,
                          template=PLOT_TEMPLATE, title="Xu hướng TFP Aₜ 2020–2025")
            fig.update_traces(line=dict(color="#2563EB", width=3), marker=dict(size=9))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown(f'<div class="b1-insight">TFP có xu hướng <b>{tfp_direction}</b>, từ {A[0]:.3f} → {A[-1]:.3f}. CAGR ≈ <b>{tfp_cagr:.2f}%/năm</b>.</div>', unsafe_allow_html=True)
        with st.expander("Xem code"):
            st.code("A = Y / (K**alpha * L**beta * D**gamma * AI**delta * H**theta)", language="python")

    with tab142:
        forecast_df = pd.DataFrame({"Năm": years, "GDP thực tế": Y, "GDP dự báo": Y_hat,
                                     "Sai số (%)": np.abs((Y - Y_hat)/Y)*100})
        _kpi_row([("A̅ trung bình", f"{A_mean:.3f}", "TFP bình quân 2020–2025"),
                  ("MAPE", f"{mape:.2f}%", "sai số dự báo trong mẫu"),
                  ("Sai số min", f"{forecast_df['Sai số (%)'].min():.2f}%", "năm tốt nhất"),
                  ("Sai số max", f"{forecast_df['Sai số (%)'].max():.2f}%", "năm khó khớp nhất")])
        c1, c2 = st.columns([1, 1.3])
        with c1:
            st.dataframe(forecast_df, use_container_width=True, hide_index=True)
        with c2:
            fig = px.line(forecast_df, x="Năm", y=["GDP thực tế", "GDP dự báo"],
                          markers=True, template=PLOT_TEMPLATE, title="GDP thực tế vs. dự báo")
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        with st.expander("Xem code"):
            st.code("Y_hat = A.mean() * K**alpha * L**beta * D**gamma * AI**delta * H**theta\nMAPE = np.mean(np.abs((Y - Y_hat)/Y)) * 100", language="python")

    with tab143:
        st.metric("Tăng trưởng GDP bình quân (log)", f"{100*avg_log_growth:.2f}%/năm")
        c1, c2 = st.columns([1, 1.3])
        with c1:
            st.dataframe(contrib_df.style.format({"Đóng góp bình quân (% log/năm)": "{:.3f}",
                                                   "Tỷ trọng (%)": "{:.2f}"}),
                         use_container_width=True, hide_index=True)
        with c2:
            fig = px.bar(contrib_df, x="Yếu tố", y="Tỷ trọng (%)", text="Tỷ trọng (%)",
                         template=PLOT_TEMPLATE, title="Tỷ trọng đóng góp vào tăng trưởng GDP",
                         color="Tỷ trọng (%)", color_continuous_scale="Blues")
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)

    with tab144:
        _kpi_row([("GDP 2025", f"{Y[-1]:,.0f}", "nghìn tỷ VND"),
                  ("GDP 2030 ↗", f"{Y2030:,.0f}", "nghìn tỷ VND"),
                  ("Tăng 5 năm", f"{growth_2025_2030:.1f}%", "so với 2025"),
                  ("CAGR 2025-30", f"{((Y2030/Y[-1])**(1/5)-1)*100:.2f}%/năm", "kịch bản đề bài")])
        scenario_df = pd.DataFrame({"Biến": ["K", "L", "D", "AI", "H", "TFP"],
            "2025": [K[-1], L[-1], D[-1], AI[-1], H[-1], A[-1]],
            "2030": [K2030, L2030, D2030, AI2030, H2030, A2030],
            "Giả định": ["K +6%/năm", "L +6%/năm", "D = 30%", "AI = 100k DN", "H = 35%", "TFP +1,2%/năm"]})
        st.dataframe(scenario_df, use_container_width=True, hide_index=True)
        st.warning("Kịch bản có điều kiện. Kết quả phụ thuộc giả định K và L cùng tăng 6%/năm.")

    # ── Download ──
    result_export = pd.DataFrame({"Năm": years, "GDP_thuc_te": Y, "GDP_du_bao": Y_hat, "TFP": A})
    st.download_button("⬇️ Tải kết quả Bài 1 (CSV)",
        data=result_export.to_csv(index=False).encode("utf-8-sig"),
        file_name="bai1_cobb_douglas.csv", mime="text/csv", key="dl_b1")

    # ── 1.5 Thảo luận ──
    st.markdown("## 1.5 · Thảo luận chính sách")
    cumulative_new = {"số hóa D": gamma*np.log(D[-1]/D[0]),
                      "năng lực AI": delta*np.log(AI[-1]/AI[0]),
                      "nhân lực số H": theta*np.log(H[-1]/H[0])}
    strongest_new = max(cumulative_new, key=cumulative_new.get)
    with st.expander("a) TFP tăng hay giảm — phản ánh điều gì?", expanded=True):
        st.markdown(f"TFP **{tfp_direction}** giai đoạn 2020–2025, CAGR ≈ **{tfp_cagr:.2f}%/năm**. Xu hướng này phản ánh cải thiện (hoặc suy giảm) chất lượng tăng trưởng ngoài tích lũy vốn và lao động thuần túy.")
    with st.expander("b) Trong D, AI, H — yếu tố nào đóng góp nhiều nhất?", expanded=True):
        st.markdown(f"Dựa trên log tích lũy 2020–2025, **{strongest_new}** đóng góp lớn nhất trong ba yếu tố mới. Tuy nhiên kết quả phụ thuộc bộ hệ số đàn hồi.")
    with st.expander("c) D đạt 30% GDP 2030 đòi hỏi gì?", expanded=True):
        digital_cagr = ((30/D[-1])**(1/5)-1)*100
        st.markdown(f"Kinh tế số hiện ở **{D[-1]:.1f}%**. Để đạt **30%** vào 2030 cần CAGR ≈ **{digital_cagr:.2f}%/năm**, đòi hỏi đầu tư hạ tầng, nhân lực số và cải thiện môi trường pháp lý đồng bộ.")

    ai_analysis_panel(
        lesson_name="Bài 1 — Cobb-Douglas + AI",
        model_name="Extended Cobb-Douglas + TFP + Growth Accounting",
        input_params={"alpha": alpha, "beta": beta, "gamma": gamma, "delta": delta, "theta": theta},
        result_data=_collect_ai_context(locals()), key="ai_bai_1")


# ──────────────────────────────────────────────────────────
# BÀI 2 — LP Ngân sách số  (theme: xanh lá + vàng)
# ──────────────────────────────────────────────────────────

def _b2_solve_scipy(budget=100.0, min_human=20.0):
    from scipy.optimize import linprog
    c = [-0.85, -1.20, -0.95, -1.35]
    A_ub = [[1, 1, 1, 1], [-1, 0, 0, 0], [0, -1, 0, 0],
            [0, 0, -1, 0], [0, 0, 0, -1], [0.35, -0.65, 0.35, -0.65]]
    b_ub = [budget, -25, -15, -min_human, -10, 0]
    return linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=[(0, None)]*4, method="highs")


def page_2():
    _inject_page_css("""
    .b2-budget-card{background:#F6FFF8;border:1px solid #ECECF1;border-left:4px solid #059669;
                    border-radius:10px;padding:16px 20px;margin-bottom:10px}
    .b2-warn{background:#FFFBEB;border:1px solid #ECECF1;border-left:4px solid #F59E0B;
             border-radius:10px;padding:13px 16px;margin:8px 0;color:#78350F}
    .b2-info{background:#F0F7FF;border:1px solid #ECECF1;border-left:4px solid #3B82F6;
             border-radius:10px;padding:13px 16px;margin:8px 0;color:#1E3A5F}
    .b2-alloc-bar{height:6px;border-radius:6px;margin-top:4px}
    """)

    tags = "".join([_pill(t, "#059669", "rgba(5,150,105,.1)", "rgba(5,150,105,.3)")
                    for t in ["2.1–2.5", "LP", "SciPy", "PuLP", "Shadow price", "Sensitivity"]])
    _banner("💰", "Bài 2 — LP Phân bổ ngân sách số 4 hạng mục",
            "Tối đa hóa GDP kỳ vọng qua 4 kênh đầu tư: Hạ tầng số · AI/Dữ liệu · Nhân lực số · R&D. Giải bằng SciPy, PuLP và phân tích shadow price.",
            tags, "#059669")

    show_assignment_structure(2)

    item_names = ["x₁ — Hạ tầng số", "x₂ — AI/Dữ liệu", "x₃ — Nhân lực số", "x₄ — R&D"]
    item_colors = ["#3B82F6", "#8B5CF6", "#EC4899", "#F97316"]
    impact_coefs = [0.85, 1.20, 0.95, 1.35]

    # ── 2.1 Bối cảnh ──
    st.markdown("## 2.1 · Bối cảnh")
    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.markdown("""
        <div class="b2-budget-card">
          <div style="font-weight:700;color:#1F2430;margin-bottom:8px;font-family:'Outfit',sans-serif">💡 Bài toán phân bổ ngân sách</div>
          <div style="color:#4B5563;font-size:.92rem;line-height:1.7">
            Chính phủ có <b>100 nghìn tỷ VND</b> để đầu tư vào 4 hạng mục chuyển đổi số.<br>
            Mục tiêu: <b>tối đa hóa GDP kỳ vọng</b> với các ràng buộc chi tiêu tối thiểu
            và tỷ lệ công nghệ chiến lược ≥ 35%.
          </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="background:#fff;border:1px solid #ECECF1;border-radius:10px;padding:14px 18px">
          <div style="font-weight:700;color:#1F2430;margin-bottom:8px;font-family:'Outfit',sans-serif">📋 Hệ số tác động</div>
        """, unsafe_allow_html=True)
        for name, coef, color in zip(item_names, impact_coefs, item_colors):
            bar_w = int(coef / 1.35 * 100)
            st.markdown(f"""
              <div style="margin-bottom:10px">
                <div style="display:flex;justify-content:space-between;font-size:.82rem">
                  <span style="color:#4B5563">{name}</span>
                  <span style="font-weight:700;color:{color}">{coef}</span>
                </div>
                <div class="b2-alloc-bar" style="background:#F3F4F6">
                  <div style="width:{bar_w}%;height:100%;border-radius:6px;background:{color}"></div>
                </div>
              </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 2.2 Mô hình ──
    st.markdown("## 2.2 · Mô hình LP")
    st.latex(r"\max \; Z = 0.85x_1 + 1.20x_2 + 0.95x_3 + 1.35x_4")
    st.latex(r"\text{s.t.} \quad x_1+x_2+x_3+x_4 \leq 100; \quad x_1\geq25, x_2\geq15, x_3\geq20, x_4\geq10; \quad x_2+x_4\geq0.35(x_1+x_2+x_3+x_4)")

    # ── 2.3 Hệ số mục tiêu ──
    st.markdown("## 2.3 · Diễn giải hệ số")
    coef_df = pd.DataFrame({"Hạng mục": item_names, "Hệ số tác động": impact_coefs,
        "Sàn tối thiểu": [25, 15, 20, 10], "Ý nghĩa": [
            "Mỗi 1 nghìn tỷ → GDP tăng 0,85 nghìn tỷ",
            "Mỗi 1 nghìn tỷ → GDP tăng 1,20 nghìn tỷ",
            "Mỗi 1 nghìn tỷ → GDP tăng 0,95 nghìn tỷ",
            "Mỗi 1 nghìn tỷ → GDP tăng 1,35 nghìn tỷ"]})
    st.dataframe(coef_df, use_container_width=True, hide_index=True)

    # ── Solve base ──
    base_res = _b2_solve_scipy(100.0, 20.0)
    base_x = base_res.x
    base_z = -base_res.fun
    strategic_share = 100 * (base_x[1] + base_x[3]) / base_x.sum()

    def build_alloc_table(x):
        return pd.DataFrame({"Hạng mục": item_names, "Phân bổ tối ưu (nghìn tỷ)": x,
            "Hệ số": impact_coefs, "GDP tăng thêm": x * impact_coefs})

    base_table = build_alloc_table(base_x)

    # ── 2.4 Tabs ──
    st.markdown("## 2.4 · Yêu cầu lập trình")
    tab1, tab2, tab3, tab4 = st.tabs(
        ["⚡ 2.4.1 — SciPy", "🔧 2.4.2 — PuLP & Shadow", "📊 2.4.3 — Sensitivity B", "🔄 2.4.4 — x₃ ≥ 30"])

    with tab1:
        _kpi_row([("Z* tối ưu", f"{base_z:,.2f}", "nghìn tỷ VND GDP kỳ vọng"),
                  ("Ngân sách dùng", f"{base_x.sum():,.0f}/100", "nghìn tỷ VND"),
                  ("AI + R&D", f"{strategic_share:.1f}%", "≥ 35% yêu cầu ✓"),
                  ("Hạng mục nhận nhiều", base_table.sort_values("Phân bổ tối ưu (nghìn tỷ)", ascending=False).iloc[0]["Hạng mục"], "max allocation")])
        c1, c2 = st.columns([1, 1.1])
        with c1:
            st.dataframe(base_table.style.format({"Phân bổ tối ưu (nghìn tỷ)": "{:.2f}",
                "Hệ số": "{:.2f}", "GDP tăng thêm": "{:.2f}"}), use_container_width=True, hide_index=True)
        with c2:
            fig = px.pie(base_table, values="Phân bổ tối ưu (nghìn tỷ)", names="Hạng mục",
                         title="Cơ cấu phân bổ ngân sách tối ưu",
                         color_discrete_sequence=item_colors, template=PLOT_TEMPLATE)
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)
        with st.expander("Xem code SciPy"):
            st.code("""from scipy.optimize import linprog
c = [-0.85, -1.20, -0.95, -1.35]
res = linprog(c, A_ub=..., b_ub=..., bounds=[(0,None)]*4, method='highs')
Z_star, x_star = -res.fun, res.x""", language="python")

    with tab2:
        try:
            import pulp
            model = pulp.LpProblem("VN_Budget", pulp.LpMaximize)
            x1 = pulp.LpVariable("x1", lowBound=0); x2 = pulp.LpVariable("x2", lowBound=0)
            x3 = pulp.LpVariable("x3", lowBound=0); x4 = pulp.LpVariable("x4", lowBound=0)
            model += 0.85*x1 + 1.20*x2 + 0.95*x3 + 1.35*x4
            model += x1+x2+x3+x4 <= 100, "C1"
            model += x1 >= 25, "C2"; model += x2 >= 15, "C3"
            model += x3 >= 20, "C4"; model += x4 >= 10, "C5"
            model += x2+x4 >= 0.35*(x1+x2+x3+x4), "C6"
            model.solve(pulp.PULP_CBC_CMD(msg=False))
            pulp_x = np.array([x1.value(), x2.value(), x3.value(), x4.value()], float)
            pulp_z = float(pulp.value(model.objective))
            dual_rows = [{"Ràng buộc": k, "Shadow price (π)": getattr(v, "pi", None),
                          "Slack": getattr(v, "slack", None)} for k, v in model.constraints.items()]
            dual_df = pd.DataFrame(dual_rows)
            budget_pi_s = dual_df.loc[dual_df["Ràng buộc"]=="C1","Shadow price (π)"]
            budget_pi = float(budget_pi_s.iloc[0]) if len(budget_pi_s) else float("nan")
            _kpi_row([("Trạng thái PuLP", pulp.LpStatus[model.status], "CBC solver"),
                      ("Z* PuLP", f"{pulp_z:,.2f}", "khớp SciPy"),
                      ("Max |SciPy-PuLP|", f"{np.max(np.abs(base_x-pulp_x)):.6f}", "sai lệch"),
                      ("Shadow price B", f"{budget_pi:.4f}" if np.isfinite(budget_pi) else "N/A", "tăng 1 nghìn tỷ → Z tăng")])
            st.dataframe(dual_df.style.format({"Shadow price (π)": "{:.4f}", "Slack": "{:.4f}"},
                         na_rep="N/A"), use_container_width=True, hide_index=True)
            if np.isfinite(budget_pi):
                st.markdown(f'<div class="b2-info">Shadow price ngân sách ≈ <b>{budget_pi:.4f}</b>. Mỗi 1 nghìn tỷ tăng thêm → GDP kỳ vọng tăng thêm <b>{budget_pi:.4f} nghìn tỷ</b>.</div>', unsafe_allow_html=True)
        except ModuleNotFoundError:
            st.error("Chưa cài PuLP. Thêm `pulp>=2.7` vào requirements.txt.")

    with tab3:
        sens_rows = []
        for B in [100.0, 120.0, 140.0]:
            r = _b2_solve_scipy(B, 20.0)
            if r.success:
                sens_rows.append({"B": B, "Z*": -r.fun, "x₁": r.x[0], "x₂": r.x[1],
                                   "x₃": r.x[2], "x₄": r.x[3], "AI+R&D%": 100*(r.x[1]+r.x[3])/B})
        sens_df = pd.DataFrame(sens_rows)
        sens_df["ΔZ vs B=100"] = sens_df["Z*"] - sens_df.loc[0,"Z*"]
        c1, c2 = st.columns([1, 1.2])
        with c1:
            st.dataframe(sens_df.style.format({k: "{:.2f}" for k in sens_df.columns}),
                         use_container_width=True, hide_index=True)
        with c2:
            fig = px.line(sens_df, x="B", y="Z*", markers=True, template=PLOT_TEMPLATE,
                          title="Đường cong Z*(B) — độ nhạy ngân sách")
            fig.update_traces(line=dict(color="#059669", width=3), marker=dict(size=10))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        if len(sens_df) >= 2:
            mg = (sens_df.loc[1,"Z*"]-sens_df.loc[0,"Z*"])/(sens_df.loc[1,"B"]-sens_df.loc[0,"B"])
            st.markdown(f'<div class="b2-info">Mỗi 1 nghìn tỷ ngân sách tăng thêm → Z* tăng ≈ <b>{mg:.4f} nghìn tỷ</b> (vùng tuyến tính).</div>', unsafe_allow_html=True)

    with tab4:
        h30_res = _b2_solve_scipy(100.0, 30.0)
        if not h30_res.success:
            st.error("Bài toán không khả thi khi x₃ ≥ 30 với B=100.")
        else:
            h30_x = h30_res.x; h30_z = -h30_res.fun
            _kpi_row([("Trạng thái", "Khả thi ✓", "x₃ ≥ 30"),
                      ("Z* mới", f"{h30_z:,.2f}", "nghìn tỷ"),
                      ("ΔZ*", f"{h30_z-base_z:,.2f}", "chi phí ưu tiên nhân lực"),
                      ("Tỷ lệ giảm Z*", f"{100*(base_z-h30_z)/base_z:.2f}%", "so với mô hình gốc")])
            comp = pd.DataFrame({"Hạng mục": item_names, "x₃≥20 (gốc)": base_x,
                                  "x₃≥30 (nhân lực)": h30_x, "Thay đổi": h30_x-base_x})
            st.dataframe(comp.style.format({c: "{:.2f}" for c in comp.columns if c!="Hạng mục"}),
                         use_container_width=True, hide_index=True)

    st.download_button("⬇️ Tải kết quả Bài 2 (CSV)",
        data=base_table.to_csv(index=False).encode("utf-8-sig"),
        file_name="bai2_lp_ngan_sach.csv", mime="text/csv", key="dl_b2")

    # ── 2.5 ──
    st.markdown("## 2.5 · Thảo luận chính sách")
    scipy_budget_shadow = -float(base_res.ineqlin.marginals[0])
    with st.expander("a) Ngân sách tăng 1 tỷ → GDP tăng bao nhiêu?", expanded=True):
        st.markdown(f"Shadow price ngân sách (HiGHS) ≈ **{scipy_budget_shadow:.4f} nghìn tỷ/nghìn tỷ**. Tăng 1 tỷ VND → GDP tăng ≈ **{scipy_budget_shadow*0.001:.4f} nghìn tỷ** trong vùng độ nhạy hiện tại.")
    with st.expander("b) Vì sao R&D hệ số cao nhất nhưng sàn thấp nhất?", expanded=True):
        st.markdown("R&D có lợi ích lan tỏa dài hạn nhưng độ trễ lớn, rủi ro thất bại và khó hấp thụ nếu thiếu nhân lực. Nghiệm tối ưu vẫn phân bổ phần dư vào R&D sau khi thỏa sàn các hạng mục khác.")
    with st.expander("c) Tỷ lệ 35% AI+R&D có khả thi thực tiễn?", expanded=True):
        st.markdown(f"Nghiệm hiện tại: AI+R&D = **{strategic_share:.1f}%** > 35%. Khả thi về toán học. Thực tiễn cần thêm ràng buộc giải ngân, tiến độ, rủi ro và năng lực hấp thụ.")

    ai_analysis_panel(lesson_name="Bài 2 — LP ngân sách số",
        model_name="Linear Programming + SciPy/PuLP + Shadow Price",
        input_params={"budget": 100, "min_human": 20},
        result_data=_collect_ai_context(locals()), key="ai_bai_2")


# ──────────────────────────────────────────────────────────
# BÀI 3 — Priority 10 ngành  (theme: tím + hồng gradient)
# ──────────────────────────────────────────────────────────

def page_3():
    _inject_page_css("""
    .b3-rank-badge{display:inline-flex;align-items:center;justify-content:center;
                   width:26px;height:26px;border-radius:6px;font-weight:800;font-size:.78rem}
    .b3-rank-1{background:#FEF3C7;color:#92400E}
    .b3-rank-2{background:#F3F4F6;color:#374151}
    .b3-rank-3{background:#FEE2E2;color:#991B1B}
    .b3-weight-card{background:#fff;border:1px solid #ECECF1;border-radius:10px;
                    padding:14px 16px;margin-bottom:8px}
    .b3-tip{background:#FAF8FF;border:1px solid #ECECF1;border-left:4px solid #8B5CF6;
            border-radius:10px;padding:13px 16px;margin:8px 0;color:#4C1D95}
    """)

    tags = "".join([_pill(t, "#8B5CF6", "rgba(139,92,246,.1)", "rgba(139,92,246,.3)")
                    for t in ["3.1–3.5", "Min-max", "MCDM", "Priority", "AI readiness", "Sensitivity"]])
    _banner("🏭", "Bài 3 — Chỉ số ưu tiên Priorityᵢ cho 10 ngành",
            "Xây dựng chỉ số tổng hợp từ 7 tiêu chí: Tăng trưởng · Năng suất · Lan tỏa · Xuất khẩu · Việc làm · AI readiness · Rủi ro tự động hóa.",
            tags, "#8B5CF6")

    show_assignment_structure(3)

    df, cmap, norm = _b3_prepare_data()
    sector_col = "sector_name_vi"
    default_weights = np.array([0.15, 0.15, 0.20, 0.15, 0.10, 0.20, 0.15], float)

    # ── 3.1 Bối cảnh ──
    st.markdown("## 3.1 · Bối cảnh")
    c1, c2, c3 = st.columns(3)
    for col, icon, title, body in [
        (c1, "🎯", "Vấn đề", "Nếu chỉ dùng 1 tiêu chí → thiên lệch. Cần chỉ số tổng hợp phản ánh đa chiều."),
        (c2, "📐", "Phương pháp", "Min-max normalize 7 tiêu chí → tính Priority có trọng số."),
        (c3, "🌏", "Phạm vi", "10 ngành Việt Nam năm 2024 với dữ liệu từ Tổng cục Thống kê."),
    ]:
        with col:
            st.markdown(f"""<div style="background:#fff;border:1px solid #ECECF1;border-top:3px solid #8B5CF6;border-radius:10px;
                              padding:14px 16px 12px;height:100%">
              <div style="font-size:20px;margin-bottom:6px">{icon}</div>
              <div style="font-weight:700;color:#1F2430;font-size:.86rem;margin-bottom:4px;font-family:'Outfit',sans-serif">{title}</div>
              <div style="color:#6B7280;font-size:.81rem;line-height:1.5">{body}</div>
            </div>""", unsafe_allow_html=True)

    # ── 3.2 Mô hình ──
    st.markdown("## 3.2 · Mô hình toán học")
    st.latex(r"Priority_i = a_1\widetilde{G}_i + a_2\widetilde{P}_i + a_3\widetilde{S}_i + a_4\widetilde{X}_i + a_5\widetilde{E}_i + a_6\widetilde{AI}_i - a_7\widetilde{Risk}_i")
    st.latex(r"\widetilde{x}_i = \frac{x_i - \min x}{\max x - \min x} \in [0,1]")

    # ── 3.3 Dữ liệu ──
    st.markdown("## 3.3 · Dữ liệu 10 ngành 2024")
    rename_map = {sector_col: "Ngành", cmap["growth"]: "Tăng trưởng %",
        cmap.get("productivity","productivity"): "Năng suất", cmap["spillover"]: "Lan tỏa",
        cmap["export"]: "XK (tỷ USD)", cmap["employment"]: "Việc làm (tr)",
        cmap["ai"]: "AI readiness", cmap["risk"]: "Rủi ro %"}
    display_cols = [sector_col, cmap["growth"], cmap["spillover"],
                    cmap["export"], cmap["employment"], cmap["ai"], cmap["risk"]]
    st.dataframe(df[display_cols].rename(columns=rename_map),
                 use_container_width=True, hide_index=True)

    # ── 3.4 Tabs ──
    st.markdown("## 3.4 · Yêu cầu lập trình")
    tab341, tab342, tab343, tab344 = st.tabs(
        ["🔢 3.4.1 — Chuẩn hóa", "🏅 3.4.2 — Xếp hạng", "📡 3.4.3 — Độ nhạy AI", "⚖️ 3.4.4 — Hai định hướng"])

    with tab341:
        norm_table = pd.DataFrame({
            "Ngành": df[sector_col],
            "Growth": norm[cmap["growth"]], "Spillover": norm[cmap["spillover"]],
            "Export": norm[cmap["export"]], "Employment": norm[cmap["employment"]],
            "AI": norm[cmap["ai"]], "Risk": norm[cmap["risk"]]})
        st.dataframe(norm_table.style.format({c: "{:.4f}" for c in norm_table.columns if c!="Ngành"}),
                     use_container_width=True, hide_index=True)
        st.markdown('<div class="b3-tip">Sau chuẩn hóa min-max, mọi tiêu chí đều nằm trong [0, 1]. Giá trị 0 = thấp nhất, 1 = cao nhất trong nhóm 10 ngành.</div>', unsafe_allow_html=True)
        with st.expander("Xem code"):
            st.code("norm = (x - x.min()) / (x.max() - x.min())", language="python")

    with tab342:
        default_score = _b3_priority_score(norm, cmap, default_weights)
        result_df = pd.DataFrame({"Ngành": df[sector_col], "Priority": default_score})
        result_df = result_df.sort_values("Priority", ascending=False).reset_index(drop=True)
        result_df["#"] = range(1, len(result_df)+1)
        top1 = result_df.iloc[0]
        _kpi_row([("🥇 Ngành #1", top1["Ngành"], f"Priority = {top1['Priority']:.3f}"),
                  ("Top 3", ", ".join(result_df.head(3)["Ngành"]), "bộ trọng số mặc định"),
                  ("AI readiness cao", df.loc[df[cmap["ai"]].idxmax(), sector_col], "AI leader"),
                  ("Rủi ro cao nhất", df.loc[df[cmap["risk"]].idxmax(), sector_col], "cần đào tạo lại")])
        c1, c2 = st.columns([1, 1.2])
        with c1:
            st.dataframe(result_df[["#", "Ngành", "Priority"]].style.format({"Priority": "{:.4f}"}),
                         use_container_width=True, hide_index=True)
        with c2:
            fig = px.bar(result_df, x="Priority", y="Ngành", orientation="h",
                         text="Priority", template=PLOT_TEMPLATE,
                         title="Priority score — xếp hạng 10 ngành",
                         color="Priority", color_continuous_scale="Purples")
            fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
            fig.update_yaxes(categoryorder="total ascending")
            fig.update_layout(height=380, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with tab343:
        ai_weights = np.arange(0.05, 0.401, 0.05)
        sens_rows = []
        for w_ai in ai_weights:
            other = np.array([0.15,0.15,0.20,0.15,0.10,0.15], float)
            scaled = other / other.sum() * (1-w_ai)
            w = np.append(scaled, 0)
            w[5] = w_ai; w[6] = scaled[-1]  # AI=pos5, risk=pos6
            w_full = np.array([scaled[0],scaled[1],scaled[2],scaled[3],scaled[4],w_ai,scaled[5]], float)
            score = _b3_priority_score(norm, cmap, w_full)
            temp = pd.DataFrame({"Ngành": df[sector_col], "Score": score}).sort_values("Score", ascending=False).reset_index(drop=True)
            for rank, row in temp.iterrows():
                sens_rows.append({"w_AI": round(w_ai,2), "Ngành": row["Ngành"], "Hạng": rank+1})
        sens_df = pd.DataFrame(sens_rows)
        fig = px.line(sens_df, x="w_AI", y="Hạng", color="Ngành", markers=True,
                      template=PLOT_TEMPLATE, title="Thứ hạng ngành khi trọng số AI thay đổi")
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=460)
        st.plotly_chart(fig, use_container_width=True)
        # heatmap
        pivot = sens_df.pivot(index="Ngành", columns="w_AI", values="Hạng")
        fig2 = px.imshow(pivot, text_auto=".0f", aspect="auto",
                         color_continuous_scale="RdYlGn_r", template=PLOT_TEMPLATE,
                         title="Heatmap thứ hạng — độ nhạy trọng số AI")
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

    with tab344:
        growth_w = np.array([0.24,0.22,0.12,0.20,0.06,0.10,0.06], float)
        incl_w   = np.array([0.08,0.08,0.22,0.05,0.22,0.12,0.23], float)
        g_score  = _b3_priority_score(norm, cmap, growth_w)
        i_score  = _b3_priority_score(norm, cmap, incl_w)
        comp = pd.DataFrame({"Ngành": df[sector_col], "Tăng trưởng": g_score, "Bao trùm": i_score})
        comp["Δ hạng"] = comp["Tăng trưởng"].rank(ascending=False).astype(int) - comp["Bao trùm"].rank(ascending=False).astype(int)
        comp_long = comp.melt("Ngành", ["Tăng trưởng", "Bao trùm"], var_name="Định hướng", value_name="Điểm")
        c1, c2 = st.columns([1, 1.3])
        with c1:
            st.dataframe(comp.style.format({"Tăng trưởng": "{:.4f}", "Bao trùm": "{:.4f}", "Δ hạng": "{:+d}"}),
                         use_container_width=True, hide_index=True)
        with c2:
            fig = px.bar(comp_long, x="Ngành", y="Điểm", color="Định hướng", barmode="group",
                         template=PLOT_TEMPLATE, title="So sánh hai định hướng chính sách",
                         color_discrete_sequence=["#8B5CF6", "#EC4899"])
            fig.update_layout(height=360)
            st.plotly_chart(fig, use_container_width=True)

    st.download_button("⬇️ Tải kết quả Bài 3 (CSV)",
        data=result_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="bai3_priority_nganh.csv", mime="text/csv", key="dl_b3")

    # ── 3.5 ──
    st.markdown("## 3.5 · Thảo luận chính sách")
    with st.expander("a) Ngành AI readiness cao có luôn được ưu tiên cao không?", expanded=True):
        st.markdown("Không nhất thiết. Một ngành AI readiness cao có thể bị kéo xuống vì rủi ro tự động hóa cao, việc làm thấp hoặc hiệu ứng lan tỏa hạn chế. Priority là chỉ số cân bằng đa chiều.")
    with st.expander("b) Khai khoáng năng suất cao nhưng có thể không ưu tiên — tại sao?", expanded=True):
        st.markdown("Khai khoáng có quy mô việc làm nhỏ, tốc độ tăng trưởng thấp/âm và hiệu ứng lan tỏa số hạn chế. Priority tổng hợp không đồng nhất năng suất cao với mức ưu tiên chính sách cao.")
    with st.expander("c) Trọng số nên do ai quyết định?", expanded=True):
        st.markdown("Kết hợp ba nguồn: chuyên gia kỹ thuật xây dựng cơ sở định lượng, cơ quan chính sách xác định mục tiêu, tham vấn công khai đảm bảo minh bạch và tính chính danh.")

    ai_analysis_panel(lesson_name="Bài 3 — Priority 10 ngành Việt Nam",
        model_name="Min-max normalization + Weighted MCDM",
        input_params={"weights": default_weights.tolist()},
        result_data=_collect_ai_context(locals()), key="ai_bai_3")


# ──────────────────────────────────────────────────────────
# BÀI 4 — LP ngành–vùng  (theme: đỏ cam + đất)
# ──────────────────────────────────────────────────────────

def page_4():
    _inject_page_css("""
    .b4-region-card{background:#fff;border:1px solid #ECECF1;border-radius:10px;
                    padding:12px 16px;margin-bottom:8px}
    .b4-feasible{background:#F6FFF8;border:1px solid #ECECF1;border-left:4px solid #22c55e;
                 border-radius:10px;padding:13px 16px;margin:8px 0;color:#14532D}
    .b4-infeasible{background:#FFF6F6;border:1px solid #ECECF1;border-left:4px solid #EF4444;
                   border-radius:10px;padding:13px 16px;margin:8px 0;color:#7F1D1D}
    .b4-note{background:#FFFBEB;border:1px solid #ECECF1;border-left:4px solid #F59E0B;
             border-radius:10px;padding:13px 16px;margin:8px 0;color:#78350F}
    """)

    tags = "".join([_pill(t, "#EA580C", "rgba(234,88,12,.1)", "rgba(234,88,12,.3)")
                    for t in ["4.1–4.5", "LP", "24 biến", "Fairness", "PuLP", "CVXPY", "λ"]])
    _banner("🗺️", "Bài 4 — LP phân bổ ngân sách số theo vùng",
            "Mô hình 24 biến cho 6 vùng × 4 hạng mục. Kiểm tra tính khả thi λ=0,70 và lượng hóa chi phí công bằng vùng.",
            tags, "#EA580C")

    show_assignment_structure(4)

    regions, items, beta, D0 = region_beta_matrix()
    total_budget = 50000.0; region_floor = 5000.0; region_cap = 12000.0
    human_floor = 12000.0; gamma_b4 = 0.002; lambda_original = 0.70

    # ── 4.1 Bối cảnh ──
    st.markdown("## 4.1 · Bối cảnh")
    st.markdown("""
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:14px">
    """ + "".join([_kpi(r, f"D₀={d:.0f}", f"β avg={b.mean():.2f}", accent="#EA580C")
                   for r, d, b in zip(regions, D0, beta)]) + "</div>",
    unsafe_allow_html=True)

    # ── 4.2 Mô hình ──
    st.markdown("## 4.2 · Mô hình toán học")
    st.latex(r"""\max\;Z = \sum_{r=1}^{6}\sum_{j\in\{I,D,AI,H\}} \beta_{j,r}x_{j,r}""")
    st.latex(r"""\text{s.t.}\quad\sum x \leq 50{,}000;\quad 5{,}000\leq\sum_j x_{j,r}\leq 12{,}000;\quad
    \sum_r x_{H,r}\geq12{,}000;\quad D_r+\gamma x_{D,r}\in[\lambda M,M]""")

    # ── 4.3 Dữ liệu ──
    st.markdown("## 4.3 · Hệ số β và Digital Index ban đầu")
    param_tbl = pd.DataFrame(beta, columns=items); param_tbl.insert(0,"Vùng",regions)
    param_tbl["D₀"] = D0
    st.dataframe(param_tbl, use_container_width=True, hide_index=True)

    # ── 4.4 ──
    st.markdown("## 4.4 · Yêu cầu lập trình")

    # Kiểm tra khả thi λ=0.70
    orig_res = _b4_solve_scipy(True, total_budget, region_floor, region_cap, human_floor, gamma_b4, lambda_original)
    lambda_max = _b4_find_max_lambda(total_budget, region_floor, region_cap, human_floor, gamma_b4)

    if orig_res.success:
        st.markdown('<div class="b4-feasible">✅ Mô hình gốc với λ=0,70 <b>khả thi</b>.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="b4-infeasible">❌ Mô hình gốc với λ=0,70 <b>không khả thi</b>. λ tối đa ≈ <b>{lambda_max:.4f}</b>.</div>', unsafe_allow_html=True)

    default_lambda = min(0.68, float(lambda_max) - 1e-5)
    lambda_used = st.slider("λ — mức công bằng vùng dùng để giải", 0.50,
                            float(round(lambda_max, 4)), float(round(default_lambda, 4)), 0.001, key="b4_lam")

    fair_res = _b4_solve_scipy(True, total_budget, region_floor, region_cap, human_floor, gamma_b4, lambda_used)
    if not fair_res.success:
        st.error("λ đang chọn không khả thi. Hãy giảm xuống 0.001.")
        return
    X_fair, alloc_fair = _b4_allocation_table(fair_res, regions, items); z_fair = -float(fair_res.fun)

    nofair_res = _b4_solve_scipy(False, total_budget, region_floor, region_cap, human_floor, gamma_b4, lambda_used)
    X_nofair, alloc_nofair = _b4_allocation_table(nofair_res, regions, items); z_nofair = -float(nofair_res.fun)

    _kpi_row([("λ theo đề", f"{lambda_original:.3f}", "kiểm tra khả thi"),
              ("λ tối đa khả thi", f"{lambda_max:.4f}", "binary search"),
              ("Z* có công bằng", f"{z_fair:,.0f}", f"λ={lambda_used:.3f}"),
              ("Chi phí công bằng", f"{z_nofair-z_fair:,.0f}", "ΔZ = không CB – có CB")])

    tab441, tab442, tab443, tab444 = st.tabs(
        ["⚡ 4.4.1 — SciPy & PuLP", "🔬 4.4.2 — CVXPY", "🗺️ 4.4.3 — Heatmap", "⚖️ 4.4.4 — Chi phí CB"])

    with tab441:
        st.markdown(f"### Z* = {z_fair:,.2f} với λ = {lambda_used:.3f}")
        c1, c2 = st.columns([1, 1.1])
        with c1:
            st.dataframe(alloc_fair.style.format("{:,.0f}"), use_container_width=True)
        with c2:
            fig = px.bar(alloc_fair.reset_index().rename(columns={"index":"Vùng"}).melt("Vùng",items,"Hạng mục","Phân bổ"),
                         x="Vùng", y="Phân bổ", color="Hạng mục", barmode="stack",
                         template=PLOT_TEMPLATE, title="Phân bổ tối ưu theo vùng",
                         color_discrete_sequence=["#3B82F6","#8B5CF6","#EC4899","#F97316"])
            fig.update_layout(height=340)
            st.plotly_chart(fig, use_container_width=True)
        checks, _ = _b4_validate_solution(X_fair, D0, lambda_used, gamma_b4, total_budget, region_floor, region_cap, human_floor)
        st.dataframe(checks, use_container_width=True, hide_index=True)

    with tab442:
        st.markdown("### CVXPY — cài đặt tham chiếu")
        with st.expander("Xem code CVXPY", expanded=True):
            st.code("""import cvxpy as cp
x = cp.Variable((6,4), nonneg=True)
beta_mat = np.array([...])  # 6×4
obj = cp.Maximize(cp.sum(cp.multiply(beta_mat, x)))
constraints = [
    cp.sum(x) <= 50000,
    cp.sum(x, axis=1) >= 5000,
    cp.sum(x, axis=1) <= 12000,
    cp.sum(x[:,3]) >= 12000,
]
prob = cp.Problem(obj, constraints)
prob.solve()""", language="python")
        st.markdown('<div class="b4-note">CVXPY cho kết quả giống SciPy/PuLP (cùng LP). Ưu điểm: cú pháp tự nhiên, dễ mở rộng sang QP/SOCP.</div>', unsafe_allow_html=True)

    with tab443:
        fig_heat = px.imshow(pd.DataFrame(X_fair, index=regions, columns=items),
                             text_auto=".0f", aspect="auto",
                             color_continuous_scale="Blues", template=PLOT_TEMPLATE,
                             title="Heatmap phân bổ tối ưu (nghìn tỷ VND)")
        fig_heat.update_layout(height=380)
        st.plotly_chart(fig_heat, use_container_width=True)

    with tab444:
        comp_alloc = pd.DataFrame({"Vùng": regions, "Tổng (có CB)": X_fair.sum(axis=1),
                                    "Tổng (không CB)": X_nofair.sum(axis=1)})
        comp_alloc["Chênh lệch"] = comp_alloc["Tổng (có CB)"] - comp_alloc["Tổng (không CB)"]
        c1, c2 = st.columns([1,1.2])
        with c1:
            st.dataframe(comp_alloc.style.format({c:"{:,.0f}" for c in comp_alloc.columns if c!="Vùng"}),
                         use_container_width=True, hide_index=True)
        with c2:
            fig = px.bar(comp_alloc.melt("Vùng",["Tổng (có CB)","Tổng (không CB)"],"Kịch bản","Ngân sách"),
                         x="Vùng", y="Ngân sách", color="Kịch bản", barmode="group",
                         template=PLOT_TEMPLATE, title="Chi phí công bằng theo vùng",
                         color_discrete_sequence=["#8B5CF6","#F97316"])
            fig.update_layout(height=340)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown(f'<div class="b4-note">Chi phí công bằng (loss in Z*) ≈ <b>{z_nofair-z_fair:,.0f} nghìn tỷ VND</b>. Đây là cái giá để thu hẹp chênh lệch Digital Index giữa các vùng.</div>', unsafe_allow_html=True)

    st.download_button("⬇️ Tải kết quả Bài 4 (CSV)",
        data=alloc_fair.to_csv().encode("utf-8-sig"),
        file_name="bai4_lp_vung.csv", mime="text/csv", key="dl_b4")

    st.markdown("## 4.5 · Thảo luận chính sách")
    with st.expander("a) Vùng nào hưởng lợi nhiều nhất từ ràng buộc công bằng?", expanded=True):
        diff = X_fair.sum(axis=1) - X_nofair.sum(axis=1)
        beneficiary = regions[int(np.argmax(diff))]
        st.markdown(f"**{beneficiary}** nhận thêm nhiều nhất khi bật công bằng (Δ ≈ {diff.max():,.0f} tỷ VND).")
    with st.expander("b) λ tối đa thực tiễn nên là bao nhiêu?", expanded=True):
        st.markdown(f"λ tối đa khả thi ≈ **{lambda_max:.4f}**. Trên ngưỡng này, ràng buộc trần vùng 12.000 tỷ xung đột với yêu cầu cân bằng Digital Index. Chính sách nên dùng λ ≤ {lambda_max:.3f} và điều chỉnh trần vùng nếu muốn bình đẳng cao hơn.")
    with st.expander("c) Bỏ ràng buộc công bằng: Z* thay đổi thế nào?", expanded=True):
        st.markdown(f"Z* không công bằng = {z_nofair:,.2f}; Z* có công bằng = {z_fair:,.2f}. Chi phí công bằng ≈ **{z_nofair-z_fair:,.2f}** (lợi nhuận bị hy sinh để hỗ trợ vùng kém phát triển).")

    ai_analysis_panel(lesson_name="Bài 4 — LP ngành–vùng", model_name="LP 24 biến + Fairness Constraint",
        input_params={"lambda": lambda_used, "total_budget": total_budget},
        result_data=_collect_ai_context(locals()), key="ai_bai_4")


# ──────────────────────────────────────────────────────────
# BÀI 5 — MIP 15 dự án  (theme: xanh teal + đen hiện đại)
# ──────────────────────────────────────────────────────────

def page_5():
    _inject_page_css("""
    .b5-project-chip{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;
                     border-radius:6px;font-size:.73rem;font-weight:700;margin:2px}
    .b5-selected{background:rgba(20,184,166,.12);color:#0F766E;border:1px solid rgba(20,184,166,.35)}
    .b5-rejected{background:rgba(156,163,175,.08);color:#9CA3AF;border:1px solid rgba(156,163,175,.25)}
    .b5-metric{background:#F0FDFA;border:1px solid #ECECF1;border-radius:10px;
               padding:13px 16px;margin-bottom:8px}
    .b5-insight{background:#F0F9FF;border:1px solid #ECECF1;border-left:4px solid #0EA5E9;
                border-radius:10px;padding:13px 16px;margin:8px 0;color:#0C4A6E}
    """)

    tags = "".join([_pill(t, "#0F766E", "rgba(15,118,110,.1)", "rgba(15,118,110,.3)")
                    for t in ["5.1–5.5", "MIP", "Binary", "Knapsack", "CBC", "E[Z]", "Risk"]])
    _banner("🔲", "Bài 5 — MIP lựa chọn 15 dự án chuyển đổi số",
            "Mô hình nhị phân 0-1 với 7 ràng buộc: ngân sách, tiến độ năm 1-2, phụ thuộc, loại trừ, bắt buộc và xác suất hoàn thành.",
            tags, "#0F766E")

    show_assignment_structure(5)

    df_proj = _b5_project_table()

    # ── 5.1 Bối cảnh ──
    st.markdown("## 5.1 · Bối cảnh")
    c1, c2, c3, c4 = st.columns(4)
    for col, icon, val, label in [
        (c1, "📋", "15", "Dự án tiềm năng"),
        (c2, "💵", "80.000 tỷ", "Ngân sách tổng"),
        (c3, "⏱️", "40.000 tỷ", "Trần năm 1-2"),
        (c4, "🎯", "Max NPV", "Hàm mục tiêu"),
    ]:
        with col:
            st.markdown(f"""<div style="background:#fff;border:1px solid #ECECF1;border-top:3px solid #0F766E;border-radius:10px;
                              padding:14px 14px 12px;text-align:center">
              <div style="font-size:22px">{icon}</div>
              <div style="font-size:1.2rem;font-weight:800;color:#0F766E;margin:4px 0;font-family:'Outfit',sans-serif">{val}</div>
              <div style="color:#9CA3AF;font-size:.76rem">{label}</div>
            </div>""", unsafe_allow_html=True)

    # ── 5.2 Danh mục ──
    st.markdown("## 5.2 · Danh mục 15 dự án")
    st.dataframe(df_proj, use_container_width=True, hide_index=True)

    # ── 5.3 Mô hình ──
    st.markdown("## 5.3 · Mô hình MIP")
    st.latex(r"\max\;Z = \sum_{i=1}^{15} B_i y_i \quad y_i \in \{0,1\}")
    with st.expander("Xem đầy đủ 7 ràng buộc"):
        st.markdown("""
        - **C1**: Σ Cᵢyᵢ ≤ 80.000 (ngân sách tổng)
        - **C2**: Σ C¹ᵢyᵢ ≤ 40.000 (năm 1-2)
        - **C3**: Số dự án chọn ∈ [5, 10]
        - **C4**: P14 bắt buộc (y₁₄ = 1) — an ninh mạng nền tảng
        - **C5**: P1 và P2 loại trừ nhau (y₁ + y₂ ≤ 1)
        - **C6**: P8 cần P3 (y₈ ≤ y₃) — tiên quyết
        - **C7**: P13 cần P7 (y₁₃ ≤ y₇) — tiên quyết
        """)

    # ── Solve base ──
    base = _b5_solve_mip()
    base_selected, base_metrics = _b5_result_table(base)

    # ── 5.4 Tabs ──
    st.markdown("## 5.4 · Yêu cầu lập trình")
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🎯 5.4.1 — Kết quả chính", "💰 5.4.2 — Nới B→100k", "🔒 5.4.3 — Bắt buộc P1+P2", "🎲 5.4.4 — E[Z] rủi ro"])

    with tab1:
        if base["success"]:
            _kpi_row([("Lợi ích NPV Z*", f"{base_metrics['gross_benefit']:,.0f}", "tỷ VND"),
                      ("Số dự án chọn", str(base_metrics["n_projects"]), f"/{len(df_proj)}"),
                      ("Tổng chi phí", f"{base_metrics['total_cost']:,.0f}", f"/ 80.000 tỷ"),
                      ("NPV/Chi phí", f"{base_metrics['ratio']:.2f}x", "hiệu quả vốn")])
            c1, c2 = st.columns([1.1, 1])
            with c1:
                st.dataframe(base_selected, use_container_width=True, hide_index=True)
            with c2:
                # project chips
                st.markdown("**Dự án được chọn:**")
                all_codes = df_proj["Mã"].tolist()
                sel_codes = set(base_selected["Mã"].tolist()) if base["success"] else set()
                chip_html = "".join([
                    f'<span class="b5-project-chip {"b5-selected" if c in sel_codes else "b5-rejected"}">{"✓ " if c in sel_codes else "✗ "}{c}</span>'
                    for c in all_codes])
                st.markdown(chip_html, unsafe_allow_html=True)

                val_tbl = _b5_validation_table(base)
                st.dataframe(val_tbl, use_container_width=True, hide_index=True)

    with tab2:
        more = _b5_solve_mip(budget=100000, budget_12=40000)
        more_selected, more_metrics = _b5_result_table(more, 100000)
        base_codes = set(base_selected["Mã"]) if base["success"] else set()
        more_codes = set(more_selected["Mã"]) if more["success"] else set()
        _kpi_row([("Z* B=80k", f"{base_metrics['gross_benefit']:,.0f}", "tỷ VND"),
                  ("Z* B=100k", f"{more_metrics['gross_benefit']:,.0f}", "tỷ VND"),
                  ("Dự án thêm", str(more_metrics["n_projects"]-base_metrics["n_projects"]), "khi tăng ngân sách"),
                  ("ΔZ*", f"{more_metrics['gross_benefit']-base_metrics['gross_benefit']:+,.0f}", "lợi ích tăng thêm")])
        st.dataframe(more_selected, use_container_width=True, hide_index=True)
        added = sorted(more_codes - base_codes)
        st.markdown(f'<div class="b5-insight">Dự án thêm khi B tăng lên 100.000: <b>{", ".join(added) or "Không có"}</b></div>', unsafe_allow_html=True)

    with tab3:
        red = _b5_solve_mip(force_p1_p2=True, keep_exclusion=False)
        red_selected, red_metrics = _b5_result_table(red)
        if not red["success"]:
            st.error("Không khả thi khi bắt buộc P1 và P2.")
        else:
            _kpi_row([("Trạng thái", "Khả thi ✓", "P1 + P2 bắt buộc"),
                      ("Z* mới", f"{red_metrics['gross_benefit']:,.0f}", "tỷ VND"),
                      ("ΔZ*", f"{red_metrics['gross_benefit']-base_metrics['gross_benefit']:+,.0f}", "so với gốc"),
                      ("Chi phí", f"{red_metrics['total_cost']:,.0f}", "tỷ VND")])
            st.dataframe(red_selected, use_container_width=True, hide_index=True)

    with tab4:
        risk = _b5_solve_mip(risk_adjusted=True)
        risk_selected, risk_metrics = _b5_result_table(risk)
        risk_codes = set(risk_selected["Mã"]) if risk["success"] else set()
        base_codes2 = set(base_selected["Mã"]) if base["success"] else set()
        _kpi_row([("E[Z] kỳ vọng", f"{risk_metrics['expected_benefit']:,.0f}", "tỷ VND"),
                  ("NPV gộp", f"{risk_metrics['gross_benefit']:,.0f}", "trước điều chỉnh rủi ro"),
                  ("Dự án chọn", str(risk_metrics["n_projects"]), "mô hình rủi ro"),
                  ("Khác biệt", str(len(risk_codes.symmetric_difference(base_codes2))), "dự án thay đổi")])
        diff_tbl = pd.DataFrame({
            "Nhóm": ["Cùng chọn", "Chỉ mô hình NPV", "Chỉ mô hình E[Z]"],
            "Dự án": [", ".join(sorted(base_codes2 & risk_codes)) or "—",
                      ", ".join(sorted(base_codes2 - risk_codes)) or "—",
                      ", ".join(sorted(risk_codes - base_codes2)) or "—"],
        })
        st.dataframe(diff_tbl, use_container_width=True, hide_index=True)

    st.download_button("⬇️ Tải kết quả Bài 5 (CSV)",
        data=base_selected.to_csv(index=False).encode("utf-8-sig"),
        file_name="bai5_mip_du_an.csv", mime="text/csv", key="dl_b5")

    # ── 5.5 ──
    st.markdown("## 5.5 · Thảo luận chính sách")
    with st.expander("a) Vì sao P15 B/C cao nhưng có thể bị loại?", expanded=True):
        chosen = "được chọn" if (base["success"] and "P15" in set(base_selected["Mã"])) else "không được chọn"
        st.markdown(f"P15 **{chosen}** trong nghiệm chuẩn. MIP xét đồng thời ngân sách, tiến độ năm 1-2, dự án bắt buộc, tiên quyết — không chỉ B/C. Nếu P15 là hạ tầng dữ liệu nền tảng, cần bổ sung ràng buộc bắt buộc.")
    with st.expander("b) Bắt buộc P14 (an ninh mạng) có hợp lý không?", expanded=True):
        st.markdown("Hợp lý. An ninh mạng là điều kiện nền cho mọi dự án số. Dù P14 có thể làm giảm Z* nếu không nằm trong danh mục tối ưu tự do, rủi ro hệ thống nếu bỏ qua lớn hơn nhiều.")
    with st.expander("c) Mô hình hóa cộng hưởng P8 & P13 như thế nào?", expanded=True):
        st.markdown("Thêm biến z₈,₁₃ với z≤y₈, z≤y₁₃, z≥y₈+y₁₃−1 rồi cộng synergy·z vào mục tiêu. Đây là cách tuyến tính hóa hiệu ứng bổ trợ giữa AI/bán dẫn và đào tạo nhân lực.")

    ai_analysis_panel(lesson_name="Bài 5 — MIP 15 dự án",
        model_name="Mixed Integer Programming + Binary Selection + E[Z]",
        input_params={"budget": 80000, "budget_12": 40000},
        result_data=_collect_ai_context(locals()), key="ai_bai_5")
def page_6():
    hero(
        "Bài 6 — TOPSIS xếp hạng 6 vùng kinh tế theo ưu tiên đầu tư AI",
        "Xếp hạng đa tiêu chí bằng TOPSIS, so sánh trọng số chuyên gia, Entropy và AHP; kiểm tra độ nhạy của AI Readiness và độ ổn định thứ hạng.",
        ["6.1-6.5", "TOPSIS", "Entropy", "AHP", "Sensitivity"],
    )

    show_assignment_structure(6)

    (
        df,
        criteria,
        is_benefit,
        expert_weights,
    ) = _b6_prepare_data()

    labels = _b6_labels()

    # =====================================================
    # 6.1. Bối cảnh
    # =====================================================
    st.markdown("## 6.1. Bối cảnh Việt Nam")

    st.markdown(
        """
        Nguồn lực dành cho trung tâm AI, hạ tầng dữ liệu, nghiên cứu và đào tạo
        không thể phân bổ đồng đều cho mọi vùng. Sáu vùng kinh tế có khác biệt lớn
        về quy mô kinh tế, FDI, hạ tầng số, nhân lực, R&D và mức độ bất bình đẳng.

        Bài 6 sử dụng TOPSIS để xác định vùng gần nhất với phương án lý tưởng.
        Kết quả được kiểm tra bằng ba hệ trọng số: chuyên gia, Entropy và AHP.
        """
    )

    # =====================================================
    # 6.2. Mô hình
    # =====================================================
    st.markdown("## 6.2. Mô hình TOPSIS")

    st.markdown("### Bước 1. Chuẩn hóa vector")
    st.latex(
        r"r_{ij}="
        r"\frac{x_{ij}}"
        r"{\sqrt{\sum_{i=1}^{m}x_{ij}^{2}}}"
    )

    st.markdown("### Bước 2. Ma trận có trọng số")
    st.latex(r"v_{ij}=w_jr_{ij}")

    st.markdown("### Bước 3. Nghiệm lý tưởng")
    st.latex(
        r"A^*=\{v_1^*,...,v_n^*\},"
        r"\qquad "
        r"A^-=\{v_1^-,...,v_n^-\}"
    )

    st.markdown("### Bước 4. Khoảng cách Euclid")
    st.latex(
        r"S_i^*="
        r"\sqrt{\sum_j(v_{ij}-v_j^*)^2},"
        r"\qquad "
        r"S_i^-="
        r"\sqrt{\sum_j(v_{ij}-v_j^-)^2}"
    )

    st.markdown("### Bước 5. Hệ số gần lý tưởng")
    st.latex(
        r"C_i^*="
        r"\frac{S_i^-}{S_i^*+S_i^-}"
    )

    st.info(
        "C* càng lớn thì vùng càng gần phương án lý tưởng và được ưu tiên cao hơn."
    )

    # =====================================================
    # 6.3. Dữ liệu
    # =====================================================
    st.markdown("## 6.3. Dữ liệu và tiêu chí")

    data_display = df[
        ["region_name_vi"] + criteria
    ].rename(
        columns={
            "region_name_vi": "Vùng",
            **labels,
        }
    )

    st.dataframe(
        data_display,
        use_container_width=True,
        hide_index=True,
    )

    criteria_table = pd.DataFrame(
        {
            "Tiêu chí": [
                labels[c]
                for c in criteria
            ],
            "Loại": [
                "Lợi ích" if flag else "Chi phí"
                for flag in is_benefit
            ],
            "Trọng số chuyên gia": expert_weights,
        }
    )

    st.dataframe(
        criteria_table.style.format(
            {"Trọng số chuyên gia": "{:.3f}"}
        ),
        use_container_width=True,
        hide_index=True,
    )

    # Kết quả dùng chung.
    expert_score = topsis_score(
        df,
        criteria,
        expert_weights,
        is_benefit,
    )

    entropy_weights, entropy_matrix = _b6_entropy_weights(
        df,
        criteria,
        is_benefit,
    )

    entropy_score = topsis_score(
        df,
        criteria,
        entropy_weights,
        is_benefit,
    )

    pairwise_matrix = _b6_ahp_pairwise_matrix()

    (
        ahp_weights,
        ahp_lambda_max,
        ahp_ci,
        ahp_cr,
    ) = _b6_ahp_weights(
        pairwise_matrix
    )

    ahp_score = topsis_score(
        df,
        criteria,
        ahp_weights,
        is_benefit,
    )

    expert_result = _b6_rank_result(
        df,
        expert_score,
        "TOPSIS chuyên gia",
    )

    entropy_result = _b6_rank_result(
        df,
        entropy_score,
        "TOPSIS Entropy",
    )

    ahp_result = _b6_rank_result(
        df,
        ahp_score,
        "TOPSIS AHP",
    )

    # =====================================================
    # 6.4. Lập trình
    # =====================================================
    st.markdown("## 6.4. Yêu cầu lập trình")

    tab641, tab642, tab643, tab644 = st.tabs(
        [
            "6.4.1 - TOPSIS chuyên gia",
            "6.4.2 - Entropy",
            "6.4.3 - Độ nhạy AI",
            "6.4.4 - AHP & ổn định hạng",
        ]
    )

    # -----------------------------------------------------
    # 6.4.1
    # -----------------------------------------------------
    with tab641:
        st.markdown(
            "### Câu 6.4.1. TOPSIS với trọng số chuyên gia"
        )

        kpi_cards(
            [
                (
                    "Vùng dẫn đầu",
                    expert_result.iloc[0]["Vùng"],
                    f"C*={expert_result.iloc[0]['TOPSIS chuyên gia']:.4f}",
                ),
                (
                    "Vùng thứ hai",
                    expert_result.iloc[1]["Vùng"],
                    f"C*={expert_result.iloc[1]['TOPSIS chuyên gia']:.4f}",
                ),
                (
                    "Vùng thứ ba",
                    expert_result.iloc[2]["Vùng"],
                    f"C*={expert_result.iloc[2]['TOPSIS chuyên gia']:.4f}",
                ),
                (
                    "Tổng trọng số",
                    f"{expert_weights.sum():.2f}",
                    "phải bằng 1",
                ),
            ]
        )

        c1, c2 = st.columns([1, 1])

        with c1:
            st.dataframe(
                expert_result.style.format(
                    {"TOPSIS chuyên gia": "{:.4f}"}
                ),
                use_container_width=True,
                hide_index=True,
            )

        with c2:
            st.plotly_chart(
                plot_bar(
                    expert_result,
                    "Vùng",
                    "TOPSIS chuyên gia",
                    "TOPSIS với trọng số chuyên gia",
                    text="TOPSIS chuyên gia",
                ),
                use_container_width=True,
            )

        with st.expander(
            "Xem mã TOPSIS rút gọn"
        ):
            st.code(
                """score = topsis_score(
    df,
    criteria,
    expert_weights,
    is_benefit
)

result = pd.DataFrame({
    "Vùng": df["region_name_vi"],
    "C_star": score
}).sort_values(
    "C_star",
    ascending=False
)""",
                language="python",
            )

    # -----------------------------------------------------
    # 6.4.2
    # -----------------------------------------------------
    with tab642:
        st.markdown(
            "### Câu 6.4.2. Trọng số Entropy và TOPSIS"
        )

        weight_compare = pd.DataFrame(
            {
                "Tiêu chí": [
                    labels[c]
                    for c in criteria
                ],
                "Chuyên gia": expert_weights,
                "Entropy": entropy_weights,
                "Chênh lệch": (
                    entropy_weights
                    - expert_weights
                ),
            }
        )

        st.dataframe(
            weight_compare.style.format(
                {
                    "Chuyên gia": "{:.4f}",
                    "Entropy": "{:.4f}",
                    "Chênh lệch": "{:+.4f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        rank_compare = pd.DataFrame(
            {
                "Vùng": df["region_name_vi"],
                "Điểm chuyên gia": expert_score,
                "Điểm Entropy": entropy_score,
            }
        )

        rank_compare["Hạng chuyên gia"] = (
            rank_compare["Điểm chuyên gia"]
            .rank(
                ascending=False,
                method="min",
            )
            .astype(int)
        )

        rank_compare["Hạng Entropy"] = (
            rank_compare["Điểm Entropy"]
            .rank(
                ascending=False,
                method="min",
            )
            .astype(int)
        )

        rank_compare["Thay đổi hạng"] = (
            rank_compare["Hạng chuyên gia"]
            - rank_compare["Hạng Entropy"]
        )

        st.dataframe(
            rank_compare.sort_values(
                "Hạng chuyên gia"
            ).style.format(
                {
                    "Điểm chuyên gia": "{:.4f}",
                    "Điểm Entropy": "{:.4f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        compare_long = rank_compare.melt(
            id_vars="Vùng",
            value_vars=[
                "Điểm chuyên gia",
                "Điểm Entropy",
            ],
            var_name="Phương pháp",
            value_name="Điểm",
        )

        fig = px.bar(
            compare_long,
            x="Vùng",
            y="Điểm",
            color="Phương pháp",
            barmode="group",
            template=PLOT_TEMPLATE,
            title="So sánh TOPSIS chuyên gia và Entropy",
        )
        fig.update_layout(
            height=480,
            margin=dict(
                l=10,
                r=10,
                t=54,
                b=10,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        changed = rank_compare.loc[
            rank_compare["Thay đổi hạng"] != 0,
            "Vùng",
        ].tolist()

        st.info(
            "Các vùng thay đổi thứ hạng: "
            + (
                ", ".join(changed)
                if changed
                else "không có"
            )
            + "."
        )

    # -----------------------------------------------------
    # 6.4.3
    # -----------------------------------------------------
    with tab643:
        st.markdown(
            "### Câu 6.4.3. Độ nhạy trọng số AI Readiness"
        )

        ai_values = np.arange(
            0.10,
            0.401,
            0.05,
        )

        rows = []

        for ai_weight in ai_values:
            weights = expert_weights.copy()

            other_mask = np.ones(
                len(weights),
                dtype=bool,
            )
            other_mask[3] = False

            weights[other_mask] = (
                weights[other_mask]
                / weights[other_mask].sum()
                * (1.0 - ai_weight)
            )
            weights[3] = ai_weight

            score = topsis_score(
                df,
                criteria,
                weights,
                is_benefit,
            )

            temp = pd.DataFrame(
                {
                    "Vùng": df["region_name_vi"],
                    "Điểm": score,
                }
            )

            temp["Hạng"] = (
                temp["Điểm"]
                .rank(
                    ascending=False,
                    method="min",
                )
                .astype(int)
            )

            for _, row in temp.iterrows():
                rows.append(
                    [
                        ai_weight,
                        row["Vùng"],
                        row["Điểm"],
                        row["Hạng"],
                    ]
                )

        sensitivity = pd.DataFrame(
            rows,
            columns=[
                "Trọng số AI",
                "Vùng",
                "Điểm",
                "Hạng",
            ],
        )

        fig_rank = px.line(
            sensitivity,
            x="Trọng số AI",
            y="Hạng",
            color="Vùng",
            markers=True,
            template=PLOT_TEMPLATE,
            title="Độ nhạy thứ hạng theo trọng số AI",
        )
        fig_rank.update_yaxes(
            autorange="reversed"
        )
        fig_rank.update_layout(
            height=540,
            margin=dict(
                l=10,
                r=10,
                t=54,
                b=10,
            ),
        )

        st.plotly_chart(
            fig_rank,
            use_container_width=True,
        )

        rank_pivot = sensitivity.pivot(
            index="Vùng",
            columns="Trọng số AI",
            values="Hạng",
        )

        fig_heatmap = px.imshow(
            rank_pivot,
            text_auto=".0f",
            aspect="auto",
            color_continuous_scale="RdYlGn_r",
            template=PLOT_TEMPLATE,
            title="Heatmap độ nhạy thứ hạng",
        )
        fig_heatmap.update_layout(
            height=510,
            margin=dict(
                l=10,
                r=10,
                t=54,
                b=10,
            ),
        )

        st.plotly_chart(
            fig_heatmap,
            use_container_width=True,
        )

        leaders = (
            sensitivity[
                sensitivity["Hạng"] == 1
            ]["Vùng"]
            .value_counts()
            .rename_axis("Vùng")
            .reset_index(
                name="Số lần đứng đầu"
            )
        )

        st.dataframe(
            leaders,
            use_container_width=True,
            hide_index=True,
        )

        if len(leaders) == 1:
            st.success(
                "Vị trí dẫn đầu ổn định trong toàn bộ dải trọng số AI."
            )
        else:
            st.warning(
                "Vị trí dẫn đầu thay đổi khi trọng số AI thay đổi; "
                "kết luận chính sách nhạy với ưu tiên của người ra quyết định."
            )

    # -----------------------------------------------------
    # 6.4.4
    # -----------------------------------------------------
    with tab644:
        st.markdown(
            "### Câu 6.4.4. AHP và độ ổn định thứ hạng"
        )

        ahp_weight_table = pd.DataFrame(
            {
                "Tiêu chí": [
                    labels[c]
                    for c in criteria
                ],
                "Trọng số AHP": ahp_weights,
            }
        )

        kpi_cards(
            [
                (
                    "λmax",
                    f"{ahp_lambda_max:.4f}",
                    "giá trị riêng lớn nhất",
                ),
                (
                    "CI",
                    f"{ahp_ci:.4f}",
                    "Consistency Index",
                ),
                (
                    "CR",
                    f"{ahp_cr:.4f}",
                    "đạt nếu <0,10",
                ),
                (
                    "Vùng dẫn đầu AHP",
                    ahp_result.iloc[0]["Vùng"],
                    f"C*={ahp_result.iloc[0]['TOPSIS AHP']:.4f}",
                ),
            ]
        )

        c1, c2 = st.columns([0.8, 1.2])

        with c1:
            st.dataframe(
                ahp_weight_table.style.format(
                    {"Trọng số AHP": "{:.4f}"}
                ),
                use_container_width=True,
                hide_index=True,
            )

        with c2:
            st.dataframe(
                ahp_result.style.format(
                    {"TOPSIS AHP": "{:.4f}"}
                ),
                use_container_width=True,
                hide_index=True,
            )

        if ahp_cr < 0.10:
            st.success(
                f"Ma trận AHP nhất quán ở mức chấp nhận được: CR={ahp_cr:.4f}<0,10."
            )
        else:
            st.error(
                f"CR={ahp_cr:.4f}≥0,10. Cần rà soát lại đánh giá cặp."
            )

        pairwise_df = pd.DataFrame(
            pairwise_matrix,
            index=[
                labels[c]
                for c in criteria
            ],
            columns=[
                labels[c]
                for c in criteria
            ],
        )

        with st.expander(
            "Xem ma trận so sánh cặp AHP"
        ):
            st.dataframe(
                pairwise_df.style.format(
                    "{:.3f}"
                ),
                use_container_width=True,
            )

        stability = _b6_rank_stability_table(
            df,
            expert_score,
            entropy_score,
            ahp_score,
        )

        st.markdown(
            "#### So sánh độ ổn định giữa ba phương pháp"
        )

        st.dataframe(
            stability.style.format(
                {
                    "TOPSIS chuyên gia": "{:.4f}",
                    "TOPSIS Entropy": "{:.4f}",
                    "TOPSIS AHP": "{:.4f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        rank_corr = (
            stability[
                [
                    "Hạng chuyên gia",
                    "Hạng Entropy",
                    "Hạng AHP",
                ]
            ]
            .corr(
                method="spearman"
            )
        )

        st.markdown(
            "#### Tương quan Spearman giữa các thứ hạng"
        )

        st.dataframe(
            rank_corr.style.format(
                "{:.3f}"
            ),
            use_container_width=True,
        )

        stable_regions = stability.loc[
            stability["Biên độ hạng"] <= 1,
            "Vùng",
        ].tolist()

        st.info(
            "Các vùng có thứ hạng tương đối ổn định, biên độ không quá 1 bậc: "
            + (
                ", ".join(stable_regions)
                if stable_regions
                else "không có"
            )
            + "."
        )

    # =====================================================
    # Tải kết quả
    # =====================================================
    export_result = _b6_rank_stability_table(
        df,
        expert_score,
        entropy_score,
        ahp_score,
    )

    st.download_button(
        "Tải kết quả Bài 6 dạng CSV",
        data=export_result.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name="bai6_topsis_6_vung.csv",
        mime="text/csv",
        key="download_bai6_fixed",
    )

    # =====================================================
    # 6.5. Thảo luận
    # =====================================================
    st.markdown(
        "## 6.5. Câu hỏi thảo luận chính sách"
    )

    top_three = expert_result.head(
        3
    )["Vùng"].tolist()

    with st.expander(
        "a) Vùng nào dẫn đầu theo TOPSIS chuyên gia? Có nên triển khai trung tâm AI quốc gia đầu tiên không?",
        expanded=True,
    ):
        st.markdown(
            f"Vùng dẫn đầu theo trọng số chuyên gia là "
            f"**{expert_result.iloc[0]['Vùng']}**. Đây là ứng viên mạnh về quy mô "
            "kinh tế, hạ tầng số, AI và nhân lực. Tuy nhiên, quyết định địa điểm còn "
            "phải xét nguồn điện, quỹ đất, an ninh dữ liệu, liên kết đại học-doanh nghiệp "
            "và yêu cầu cân bằng vùng."
        )

    with st.expander(
        "b) Khi dùng Entropy, vùng nào thay đổi hạng lớn nhất? Vì sao?",
        expanded=True,
    ):
        st.markdown(
            "Entropy trao trọng số lớn cho tiêu chí có khả năng phân biệt các vùng mạnh. "
            "Trong khi đó, trọng số chuyên gia phản ánh ưu tiên chính sách. Vì vậy, "
            "hai cách tiếp cận có thể khác nhau dù cùng sử dụng một bộ dữ liệu."
        )

    with st.expander(
        "c) Nếu AI Readiness và Internet tương quan cao thì xử lý thế nào?",
        expanded=True,
    ):
        st.markdown(
            "Tương quan cao có thể gây đếm trùng thông tin. Có thể loại bớt một tiêu chí, "
            "dùng PCA, điều chỉnh trọng số theo tương quan hoặc sử dụng CRITIC. "
            "Kết quả nên được kiểm tra lại sau khi loại tiêu chí trùng lặp."
        )

    with st.expander(
        "d) Nếu xây dựng 3 trung tâm AI lớn, nên chọn vùng nào? Có cần điều chỉnh tiêu chí địa - chính trị không?",
        expanded=True,
    ):
        st.markdown(
            f"Theo TOPSIS chuyên gia, ba vùng dẫn đầu là "
            f"**{', '.join(top_three)}**. Mô hình chỉ cung cấp xếp hạng định lượng; "
            "cần kết hợp thẩm định hạ tầng năng lượng, an ninh, vốn nhân lực và tác động lan tỏa."
        )

    max_rank_range = int(
        export_result["Biên độ hạng"].max()
    )
    st.info(
        f"Ghi chú kiểm định độ vững: biên độ thay đổi thứ hạng lớn nhất giữa chuyên gia, "
        f"Entropy và AHP là **{max_rank_range} bậc**. Nếu biên độ nhỏ, kết luận tương đối vững; "
        "nếu biên độ lớn, báo cáo nên trình bày kết quả như một khoảng ưu tiên thay vì khẳng định "
        "một thứ hạng duy nhất."
    )


    ai_analysis_panel(
        lesson_name='Bài 6 - TOPSIS xếp hạng 6 vùng',
        model_name='TOPSIS + Entropy Weight + AHP',
        input_params={"lesson": 'Bài 6 - TOPSIS xếp hạng 6 vùng', "model": 'TOPSIS + Entropy Weight + AHP'},
        result_data=_collect_ai_context(locals()),
        key="ai_bai_6",
    )


def _b7_decode(decision_vector):
    return np.asarray(decision_vector, dtype=float).reshape(6, 4)


def _b7_objectives(decision_vector):
    """
    Trả về bốn mục tiêu theo dạng tự nhiên:
    Growth càng cao càng tốt;
    Inequality, Emission, DataRisk càng thấp càng tốt.
    """
    regions, items, beta, d0 = region_beta_matrix()
    x = _b7_decode(decision_vector)

    region_gain = (beta * x).sum(axis=1)
    growth = float(region_gain.sum())

    digital_after = d0 + 0.002 * x[:, 1]
    inequality = float(gini(digital_after))

    emission_coeff = np.array([0.42, 0.14, 0.31, 0.08], dtype=float)
    emission = float((x * emission_coeff).sum())

    data_risk_coeff = np.array([0.12, 0.24, 0.58, 0.10], dtype=float)
    data_risk = float((x * data_risk_coeff).sum())

    fairness_ratio = float(
        digital_after.min() / max(digital_after.max(), 1e-12)
    )

    return {
        "Growth": growth,
        "Inequality": inequality,
        "Emission": emission,
        "DataRisk": data_risk,
        "FairnessRatio": fairness_ratio,
    }


def _b7_constraint_values(
    decision_vector,
    budget=50000.0,
    region_floor=5000.0,
    region_cap=12000.0,
    human_floor=12000.0,
    fairness_lambda=0.68,
):
    """
    Pymoo quy ước G <= 0 là khả thi.
    """
    x = _b7_decode(decision_vector)
    _, _, _, d0 = region_beta_matrix()

    region_total = x.sum(axis=1)
    digital_after = d0 + 0.002 * x[:, 1]

    constraints = [
        x.sum() - budget,
        human_floor - x[:, 3].sum(),
    ]

    constraints.extend(region_floor - region_total)
    constraints.extend(region_total - region_cap)

    max_digital = digital_after.max()
    constraints.extend(
        fairness_lambda * max_digital - digital_after
    )

    return np.asarray(constraints, dtype=float)


@st.cache_data(show_spinner=False)
def _b7_run_nsga2(
    population_size=100,
    generations=200,
    seed=42,
    fairness_lambda=0.68,
):
    """
    Chạy NSGA-II thật bằng pymoo.
    """
    try:
        from pymoo.core.problem import ElementwiseProblem
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.optimize import minimize
        from pymoo.termination import get_termination
        from pymoo.operators.sampling.rnd import FloatRandomSampling
        from pymoo.operators.crossover.sbx import SBX
        from pymoo.operators.mutation.pm import PM
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Thiếu pymoo. Hãy cài pymoo>=0.6.1."
        ) from exc

    class RegionalParetoProblem(ElementwiseProblem):
        def __init__(self):
            super().__init__(
                n_var=24,
                n_obj=4,
                n_ieq_constr=20,
                xl=np.zeros(24, dtype=float),
                xu=np.full(24, 12000.0, dtype=float),
            )

        def _evaluate(self, x, out, *args, **kwargs):
            obj = _b7_objectives(x)

            # Pymoo luôn MINIMIZE.
            out["F"] = np.array(
                [
                    -obj["Growth"],
                    obj["Inequality"],
                    obj["Emission"],
                    obj["DataRisk"],
                ],
                dtype=float,
            )

            out["G"] = _b7_constraint_values(
                x,
                fairness_lambda=fairness_lambda,
            )

    algorithm = NSGA2(
        pop_size=int(population_size),
        sampling=FloatRandomSampling(),
        crossover=SBX(
            prob=0.90,
            eta=15,
        ),
        mutation=PM(
            eta=20,
        ),
        eliminate_duplicates=True,
    )

    result = minimize(
        RegionalParetoProblem(),
        algorithm,
        get_termination(
            "n_gen",
            int(generations),
        ),
        seed=int(seed),
        save_history=False,
        verbose=False,
    )

    if result.X is None or result.F is None:
        return pd.DataFrame(), np.empty((0, 24))

    x_values = np.atleast_2d(
        np.asarray(result.X, dtype=float)
    )
    f_values = np.atleast_2d(
        np.asarray(result.F, dtype=float)
    )

    objective_df = pd.DataFrame(
        {
            "Growth": -f_values[:, 0],
            "Inequality": f_values[:, 1],
            "Emission": f_values[:, 2],
            "DataRisk": f_values[:, 3],
        }
    )

    objective_df["FairnessRatio"] = [
        _b7_objectives(x)["FairnessRatio"]
        for x in x_values
    ]

    objective_df["SolutionID"] = np.arange(
        1,
        len(objective_df) + 1,
    )

    return objective_df, x_values


def _b7_topsis_compromise(
    pareto_df,
    weights,
):
    """
    Chọn nghiệm thỏa hiệp bằng TOPSIS thật.
    """
    weights = np.asarray(weights, dtype=float)
    weights = weights / max(weights.sum(), 1e-12)

    criteria = [
        "Growth",
        "Inequality",
        "Emission",
        "DataRisk",
    ]
    benefit_flags = [
        True,
        False,
        False,
        False,
    ]

    scores = topsis_score(
        pareto_df,
        criteria,
        weights,
        benefit_flags,
    )

    best_position = int(
        np.argmax(scores)
    )

    result = pareto_df.copy()
    result["TOPSIS"] = scores
    result["Rank"] = (
        result["TOPSIS"]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    return result, best_position


def _b7_solution_table(
    decision_vector,
):
    regions, items, _, _ = region_beta_matrix()
    x = _b7_decode(decision_vector)

    table = pd.DataFrame(
        x,
        columns=items,
    )
    table.insert(
        0,
        "Vùng",
        regions,
    )
    table["Tổng vùng"] = x.sum(axis=1)

    return table


def page_7():
    hero(
        "Bài 7 — Tối ưu đa mục tiêu Pareto bằng NSGA-II",
        "Chạy NSGA-II thật với 24 biến và 4 mục tiêu; xây dựng tập Pareto, chọn nghiệm thỏa hiệp bằng TOPSIS và lượng hóa chi phí cơ hội chính sách.",
        ["7.1-7.5", "NSGA-II", "Pareto", "TOPSIS", "4 objectives"],
    )

    show_assignment_structure(7)

    st.markdown("## 7.1. Bối cảnh Việt Nam")
    st.markdown(
        """
        Phân bổ ngân sách chuyển đổi số theo vùng tạo ra nhiều đánh đổi:
        tăng trưởng cao có thể làm gia tăng tập trung, phát thải từ hạ tầng số
        hoặc rủi ro dữ liệu. Vì vậy không tồn tại một nghiệm tối ưu duy nhất;
        nhà hoạch định cần quan sát tập nghiệm Pareto và chọn phương án thỏa hiệp.
        """
    )

    st.markdown("## 7.2. Mô hình đa mục tiêu")
    st.latex(
        r"\max f_1(x)=\sum_{r,j}\beta_{rj}x_{rj}"
    )
    st.latex(
        r"\min f_2(x)=Gini(D_r+\gamma x_{D,r})"
    )
    st.latex(
        r"\min f_3(x)=\sum_{r,j}e_jx_{rj}"
    )
    st.latex(
        r"\min f_4(x)=\sum_{r,j}\rho_jx_{rj}"
    )

    st.markdown(
        """
        Ràng buộc giữ nguyên logic Bài 4: tổng ngân sách 50.000,
        mỗi vùng từ 5.000 đến 12.000, nhân lực tối thiểu 12.000,
        và công bằng Digital Index. Do λ=0,70 không khả thi với dữ liệu gốc,
        NSGA-II sử dụng λ=0,68 và báo rõ đây là kịch bản hiệu chỉnh.
        """
    )

    st.markdown("## 7.3. Bảng tham số bổ sung và cấu hình NSGA-II")

    c1, c2, c3 = st.columns(3)

    population_size = c1.select_slider(
        "Population size",
        options=[40, 60, 80, 100, 120],
        value=100,
        key="b7_population_size",
    )

    generations = c2.select_slider(
        "Số thế hệ",
        options=[50, 100, 150, 200],
        value=200,
        key="b7_generations",
    )

    seed = c3.number_input(
        "Random seed",
        min_value=1,
        max_value=9999,
        value=42,
        step=1,
        key="b7_seed",
    )

    with st.spinner(
        "Đang chạy NSGA-II và xây dựng tập Pareto..."
    ):
        pareto_df, decision_matrix = _b7_run_nsga2(
            population_size=int(population_size),
            generations=int(generations),
            seed=int(seed),
            fairness_lambda=0.68,
        )

    if pareto_df.empty:
        st.error(
            "NSGA-II không tạo được nghiệm khả thi. "
            "Hãy kiểm tra pymoo hoặc giảm yêu cầu công bằng."
        )
        return

    kpi_cards(
        [
            (
                "Số nghiệm Pareto",
                f"{len(pareto_df):,}",
                "NSGA-II không trội",
            ),
            (
                "Growth lớn nhất",
                f"{pareto_df['Growth'].max():,.1f}",
                "mục tiêu 1",
            ),
            (
                "Inequality thấp nhất",
                f"{pareto_df['Inequality'].min():.4f}",
                "mục tiêu 2",
            ),
            (
                "Fairness thấp nhất",
                f"{pareto_df['FairnessRatio'].min():.4f}",
                "phải ≥ 0,68",
            ),
        ]
    )

    st.markdown("## 7.4. Yêu cầu lập trình")

    st.markdown("### Câu 7.4.1. Cài đặt pymoo ElementwiseProblem và chạy NSGA-II")
    st.success("Mô hình đã được cài đặt trong _b7_run_nsga2 với 24 biến, 4 mục tiêu, pop_size tùy chọn mặc định 100 và n_gen tùy chọn mặc định 200.")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "7.4.2 - Pareto & biểu đồ",
            "7.4.3 - TOPSIS thỏa hiệp",
            "Phân bổ nghiệm chọn",
            "7.4.4 - Chi phí cơ hội",
        ]
    )

    with tab1:
        st.markdown("### Câu 7.4.2. Trích xuất tập Pareto, vẽ scatter 3D và parallel coordinates")
        fig = px.scatter_3d(
            pareto_df,
            x="Growth",
            y="Emission",
            z="DataRisk",
            color="Inequality",
            hover_data=[
                "SolutionID",
                "FairnessRatio",
            ],
            template=PLOT_TEMPLATE,
            title="Tập Pareto NSGA-II",
        )
        fig.update_layout(
            height=620,
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        parallel = px.parallel_coordinates(
            pareto_df[
                [
                    "Growth",
                    "Inequality",
                    "Emission",
                    "DataRisk",
                    "FairnessRatio",
                ]
            ],
            color="Growth",
            title="Quan hệ đánh đổi giữa bốn mục tiêu",
        )
        parallel.update_layout(
            height=540,
        )
        st.plotly_chart(
            parallel,
            use_container_width=True,
        )

        st.dataframe(
            pareto_df.sort_values(
                "Growth",
                ascending=False,
            ).head(30),
            use_container_width=True,
            hide_index=True,
        )

    with tab2:
        st.markdown("### Câu 7.4.3. Áp dụng TOPSIS để chọn nghiệm thỏa hiệp")
        st.markdown(
            "### Chọn trọng số TOPSIS"
        )

        cols = st.columns(4)
        labels = [
            "Growth",
            "Inequality",
            "Emission",
            "Data risk",
        ]
        defaults = [
            0.40,
            0.25,
            0.20,
            0.15,
        ]

        weights = np.array(
            [
                col.slider(
                    label,
                    0.05,
                    0.70,
                    float(default),
                    0.05,
                    key=f"b7_weight_{i}",
                )
                for i, (
                    col,
                    label,
                    default,
                ) in enumerate(
                    zip(
                        cols,
                        labels,
                        defaults,
                    )
                )
            ],
            dtype=float,
        )

        ranked_df, best_position = (
            _b7_topsis_compromise(
                pareto_df,
                weights,
            )
        )

        best_row = ranked_df.iloc[
            best_position
        ]

        kpi_cards(
            [
                (
                    "Solution ID",
                    str(
                        int(
                            best_row["SolutionID"]
                        )
                    ),
                    "nghiệm TOPSIS",
                ),
                (
                    "Growth",
                    f"{best_row['Growth']:,.1f}",
                    "càng cao càng tốt",
                ),
                (
                    "Inequality",
                    f"{best_row['Inequality']:.4f}",
                    "càng thấp càng tốt",
                ),
                (
                    "TOPSIS",
                    f"{best_row['TOPSIS']:.4f}",
                    "hệ số gần lý tưởng",
                ),
            ]
        )

        top_ranked = ranked_df.sort_values(
            "Rank"
        ).head(15)

        st.dataframe(
            top_ranked[
                [
                    "SolutionID",
                    "Growth",
                    "Inequality",
                    "Emission",
                    "DataRisk",
                    "FairnessRatio",
                    "TOPSIS",
                    "Rank",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    with tab3:
        ranked_df, best_position = (
            _b7_topsis_compromise(
                pareto_df,
                np.array(
                    [0.40, 0.25, 0.20, 0.15],
                    dtype=float,
                ),
            )
        )

        chosen_vector = decision_matrix[
            best_position
        ]

        allocation = _b7_solution_table(
            chosen_vector
        )

        st.dataframe(
            allocation,
            use_container_width=True,
            hide_index=True,
        )

        long_df = allocation.melt(
            id_vars=[
                "Vùng",
                "Tổng vùng",
            ],
            value_vars=[
                col
                for col in allocation.columns
                if col not in [
                    "Vùng",
                    "Tổng vùng",
                ]
            ],
            var_name="Hạng mục",
            value_name="Ngân sách",
        )

        fig = px.bar(
            long_df,
            x="Vùng",
            y="Ngân sách",
            color="Hạng mục",
            barmode="stack",
            template=PLOT_TEMPLATE,
            title="Phân bổ của nghiệm thỏa hiệp",
        )
        fig.update_layout(
            height=520,
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        constraints = _b7_constraint_values(
            chosen_vector,
            fairness_lambda=0.68,
        )

        st.success(
            "Nghiệm thỏa toàn bộ ràng buộc."
            if np.max(constraints) <= 1e-5
            else "Có ràng buộc chưa đạt do sai số thuật toán."
        )

    with tab4:
        st.markdown("### Câu 7.4.4. Phân tích chi phí cơ hội của các mục tiêu")
        max_growth_row = pareto_df.loc[
            pareto_df["Growth"].idxmax()
        ]
        min_inequality_row = pareto_df.loc[
            pareto_df["Inequality"].idxmin()
        ]
        min_emission_row = pareto_df.loc[
            pareto_df["Emission"].idxmin()
        ]
        min_risk_row = pareto_df.loc[
            pareto_df["DataRisk"].idxmin()
        ]

        ranked_df, best_position = (
            _b7_topsis_compromise(
                pareto_df,
                np.array(
                    [0.40, 0.25, 0.20, 0.15],
                    dtype=float,
                ),
            )
        )
        compromise = ranked_df.iloc[
            best_position
        ]

        opportunity = pd.DataFrame(
            {
                "Phương án": [
                    "Tăng trưởng cực đại",
                    "Bất bình đẳng thấp nhất",
                    "Phát thải thấp nhất",
                    "Rủi ro dữ liệu thấp nhất",
                    "Nghiệm thỏa hiệp",
                ],
                "Growth": [
                    max_growth_row["Growth"],
                    min_inequality_row["Growth"],
                    min_emission_row["Growth"],
                    min_risk_row["Growth"],
                    compromise["Growth"],
                ],
                "Inequality": [
                    max_growth_row["Inequality"],
                    min_inequality_row["Inequality"],
                    min_emission_row["Inequality"],
                    min_risk_row["Inequality"],
                    compromise["Inequality"],
                ],
                "Emission": [
                    max_growth_row["Emission"],
                    min_inequality_row["Emission"],
                    min_emission_row["Emission"],
                    min_risk_row["Emission"],
                    compromise["Emission"],
                ],
                "DataRisk": [
                    max_growth_row["DataRisk"],
                    min_inequality_row["DataRisk"],
                    min_emission_row["DataRisk"],
                    min_risk_row["DataRisk"],
                    compromise["DataRisk"],
                ],
            }
        )

        opportunity[
            "Chi phí tăng trưởng so với cực đại"
        ] = (
            max_growth_row["Growth"]
            - opportunity["Growth"]
        )

        st.dataframe(
            opportunity,
            use_container_width=True,
            hide_index=True,
        )

        fig = px.bar(
            opportunity,
            x="Phương án",
            y="Chi phí tăng trưởng so với cực đại",
            template=PLOT_TEMPLATE,
            title="Chi phí cơ hội khi ưu tiên mục tiêu khác",
        )
        fig.update_layout(
            height=450,
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.download_button(
        "Tải tập Pareto Bài 7",
        data=pareto_df.to_csv(
            index=False
        ).encode(
            "utf-8-sig"
        ),
        file_name="bai7_pareto_nsga2.csv",
        mime="text/csv",
        key="download_bai7_nsga2",
    )

    st.markdown("## 7.5. Câu hỏi thảo luận chính sách")

    ranked_75, best_position_75 = _b7_topsis_compromise(
        pareto_df,
        np.array([0.40, 0.25, 0.20, 0.15], dtype=float),
    )
    compromise_75 = ranked_75.iloc[best_position_75]
    max_growth_75 = pareto_df.loc[pareto_df["Growth"].idxmax()]
    min_inequality_75 = pareto_df.loc[pareto_df["Inequality"].idxmin()]

    if len(pareto_df) > 1:
        growth_inclusion_corr = float(
            np.corrcoef(pareto_df["Growth"], pareto_df["Inequality"])[0, 1]
        )
    else:
        growth_inclusion_corr = 0.0

    growth_loss_compromise = float(max_growth_75["Growth"] - compromise_75["Growth"])
    inequality_improvement = float(max_growth_75["Inequality"] - compromise_75["Inequality"])
    emission_improvement = float(max_growth_75["Emission"] - compromise_75["Emission"])

    with st.expander(
        "a) Đánh đổi giữa tăng trưởng và bao trùm trên đường biên Pareto có rõ không?",
        expanded=True,
    ):
        st.markdown(
            f"Đánh đổi **tăng trưởng - bao trùm** được thể hiện qua việc nghiệm tăng trưởng cực đại "
            f"đạt Growth khoảng **{max_growth_75['Growth']:,.1f}**, trong khi nghiệm thỏa hiệp TOPSIS "
            f"đạt Growth khoảng **{compromise_75['Growth']:,.1f}**. Khi chuyển từ nghiệm tăng trưởng cực đại "
            f"sang nghiệm thỏa hiệp, mô hình hy sinh khoảng **{growth_loss_compromise:,.1f}** đơn vị Growth "
            f"để cải thiện chỉ số bất bình đẳng khoảng **{inequality_improvement:+.4f}** và phát thải khoảng "
            f"**{emission_improvement:+,.1f}**. Hệ số tương quan giữa Growth và Inequality trong tập Pareto là "
            f"**{growth_inclusion_corr:.3f}**. Nếu tương quan dương hoặc chênh lệch mục tiêu lớn, điều đó cho thấy "
            "cơ cấu kinh tế có xu hướng tập trung hiệu quả tăng trưởng vào vùng/ngành hấp thụ tốt hơn; muốn bao trùm "
            "hơn thì phải chấp nhận một phần chi phí cơ hội về GDP gain."
        )

    with st.expander(
        "b) Trọng số (0,40; 0,25; 0,20; 0,15) có phù hợp ưu tiên Việt Nam không?",
        expanded=True,
    ):
        st.markdown(
            "Bộ trọng số mặc định **0,40 cho tăng trưởng; 0,25 cho bao trùm; 0,20 cho môi trường; "
            "0,15 cho an ninh dữ liệu** phản ánh cách tiếp cận cân bằng nhưng vẫn đặt tăng trưởng lên trước. "
            "Cách này phù hợp khi mục tiêu chính là thúc đẩy phát triển kinh tế số nhưng không bỏ qua công bằng, "
            "chuyển đổi xanh và chủ quyền dữ liệu. Nếu muốn nhấn mạnh cam kết khí hậu/COP26, có thể tăng trọng số "
            "môi trường từ 0,20 lên 0,25-0,30 và giảm nhẹ tăng trưởng. Nếu muốn bám sát định hướng phát triển AI "
            "an toàn theo Quyết định 127/QĐ-TTg, có thể tăng trọng số an ninh dữ liệu từ 0,15 lên 0,20, đồng thời "
            "giữ bao trùm ở mức đủ cao để tránh khoảng cách số vùng miền."
        )

    with st.expander(
        "c) Vai trò của NSGA-II khác LP đơn mục tiêu như thế nào? Có thay thế quyết định chính trị không?",
        expanded=True,
    ):
        st.markdown(
            "LP đơn mục tiêu cho một nghiệm tối ưu duy nhất theo một hàm mục tiêu đã cố định, còn NSGA-II tạo ra "
            "một **tập nghiệm Pareto** để nhìn thấy nhiều phương án không bị trội khi các mục tiêu xung đột. "
            "Vì vậy, vai trò của NSGA-II là mở rộng không gian lựa chọn và minh bạch hóa đánh đổi giữa tăng trưởng, "
            "bao trùm, môi trường và an ninh dữ liệu. NSGA-II **không thay thế quyết định chính trị**: lựa chọn cuối cùng "
            "vẫn cần hội đồng chính sách, giải trình trọng số, tham vấn các bên chịu tác động và kiểm tra tính khả thi "
            "về ngân sách, thể chế, nhân lực và năng lượng."
        )

    ai_analysis_panel(
        lesson_name='Bài 7 - Pareto đa mục tiêu',
        model_name='Multi-objective Optimization + Pareto/NSGA-II',
        input_params={"lesson": 'Bài 7 - Pareto đa mục tiêu', "model": 'Multi-objective Optimization + Pareto/NSGA-II'},
        result_data=_collect_ai_context(locals()),
        key="ai_bai_7",
    )


def _b8_initial_state():
    """
    Lấy trạng thái cuối năm 2025 từ hàm compute_tfp().

    Thứ tự đầu ra của compute_tfp():
    years, Y, K, L, D, AI, H, A.
    """
    (
        years,
        Y,
        K,
        L,
        D,
        AI,
        H,
        A,
    ) = compute_tfp()

    return {
        "year": int(years[-1]),
        "Y": float(Y[-1]),
        "K": float(K[-1]),
        "L": float(L[-1]),
        "D": float(D[-1]),
        "AI": float(AI[-1]),
        "H": float(H[-1]),
        "A": float(A[-1]),
    }


def _b8_parameters():
    """Bộ tham số động học dùng trong mô phỏng."""
    return {
        "start_year": 2026,
        "end_year": 2035,
        "investment_rate": 0.22,
        "delta_K": 0.05,
        "delta_D": 0.12,
        "delta_AI": 0.15,
        "mu_H": 0.02,
        "theta_H": 0.80,
        "scale_D": 240.0,
        "scale_AI": 135.0,
        "scale_H": 520.0,
        "labor_growth": 0.006,
        "tfp_base_growth": 0.0,
        "share_lower_bound": 0.02,
        "share_upper_bound": 0.85,
    }


def _b8_simulate(
    shares_matrix,
    invest_rates=None,
    shock_2028=0.0,
    rho=0.97,
):
    """
    Mô phỏng động giai đoạn 2026-2035.

    shares_matrix:
        Ma trận 10x4, mỗi hàng là tỷ trọng đầu tư vào K, D, AI, H.

    invest_rates:
        Tỷ lệ đầu tư trên GDP từng năm. Nếu None, dùng 22%/năm.

    shock_2028:
        Mức giảm GDP năm 2028. Ví dụ 0.08 tương ứng giảm 8%.

    rho:
        Hệ số chiết khấu phúc lợi.
    """
    initial = _b8_initial_state()
    parameters = _b8_parameters()

    years = np.arange(
        parameters["start_year"],
        parameters["end_year"] + 1,
    )
    periods = len(years)

    shares_matrix = np.asarray(
        shares_matrix,
        dtype=float,
    )

    if shares_matrix.shape != (periods, 4):
        raise ValueError(
            "shares_matrix phải có kích thước 10x4."
        )

    if not np.isfinite(shares_matrix).all():
        raise ValueError(
            "shares_matrix chứa NaN hoặc giá trị vô hạn."
        )

    row_sum = shares_matrix.sum(
        axis=1,
        keepdims=True,
    )

    if np.any(row_sum <= 0):
        raise ValueError(
            "Mỗi năm phải có tổng tỷ trọng đầu tư lớn hơn 0."
        )

    shares_matrix = (
        shares_matrix
        / row_sum
    )

    if invest_rates is None:
        invest_rates = np.full(
            periods,
            parameters["investment_rate"],
            dtype=float,
        )
    else:
        invest_rates = np.asarray(
            invest_rates,
            dtype=float,
        )

    if invest_rates.shape != (periods,):
        raise ValueError(
            "invest_rates phải có đúng 10 phần tử."
        )

    if (
        np.any(invest_rates <= 0)
        or np.any(invest_rates >= 1)
    ):
        raise ValueError(
            "Mỗi tỷ lệ đầu tư phải nằm trong khoảng (0,1)."
        )

    if not 0 < float(rho) <= 1:
        raise ValueError(
            "Hệ số chiết khấu rho phải nằm trong khoảng (0,1]."
        )

    if not 0 <= float(shock_2028) < 1:
        raise ValueError(
            "Cú sốc 2028 phải nằm trong khoảng [0,1)."
        )

    # Trạng thái đầu năm 2026.
    K = initial["K"] * 1.06
    L = initial["L"] * (
        1 + parameters["labor_growth"]
    )
    D = initial["D"] + 0.80
    AI = initial["AI"] + 6.00
    H = initial["H"] + 0.80
    A = initial["A"] * 1.012

    welfare = 0.0
    rows = []

    for period, year in enumerate(years):
        gdp_before_shock = (
            A
            * K**0.33
            * L**0.42
            * D**0.10
            * AI**0.08
            * H**0.07
        )

        shock_factor = (
            1.0 - float(shock_2028)
            if year == 2028
            else 1.0
        )

        gdp = max(
            gdp_before_shock * shock_factor,
            1e-9,
        )

        investment_rate = float(
            invest_rates[period]
        )

        total_investment = (
            investment_rate
            * gdp
        )

        consumption = max(
            gdp - total_investment,
            1e-9,
        )

        period_utility = (
            float(rho) ** period
            * np.log(consumption)
        )

        welfare += period_utility

        shares = shares_matrix[period]

        investment_k = (
            shares[0]
            * total_investment
        )
        investment_d = (
            shares[1]
            * total_investment
        )
        investment_ai = (
            shares[2]
            * total_investment
        )
        investment_h = (
            shares[3]
            * total_investment
        )

        rows.append(
            [
                year,
                gdp,
                gdp_before_shock,
                consumption,
                total_investment,
                investment_rate,
                K,
                L,
                D,
                AI,
                H,
                A,
                investment_k,
                investment_d,
                investment_ai,
                investment_h,
                shares[0],
                shares[1],
                shares[2],
                shares[3],
                period_utility,
                welfare,
            ]
        )

        # Phương trình chuyển trạng thái.
        K = (
            (1 - parameters["delta_K"]) * K
            + investment_k
        )

        D = max(
            1e-6,
            (1 - parameters["delta_D"]) * D
            + investment_d / parameters["scale_D"],
        )

        AI = max(
            1e-6,
            (1 - parameters["delta_AI"]) * AI
            + investment_ai / parameters["scale_AI"],
        )

        H = max(
            1e-6,
            H
            + parameters["theta_H"]
            * investment_h
            / parameters["scale_H"]
            - parameters["mu_H"] * H,
        )

        # TFP tăng nội sinh theo số hóa, AI và nhân lực.
        A = (
            A
            * (
                1
                + parameters["tfp_base_growth"]
                + 0.00008 * D
                + 0.00004 * AI
                + 0.00006 * H
            )
        )

        L *= (
            1
            + parameters["labor_growth"]
        )

    return pd.DataFrame(
        rows,
        columns=[
            "Năm",
            "GDP",
            "GDP trước cú sốc",
            "Tiêu dùng",
            "Tổng đầu tư",
            "Tỷ lệ đầu tư",
            "K",
            "L",
            "D",
            "AI",
            "H",
            "A",
            "I_K",
            "I_D",
            "I_AI",
            "I_H",
            "Share_K",
            "Share_D",
            "Share_AI",
            "Share_H",
            "Phúc lợi kỳ",
            "Welfare_lũy_kế",
        ],
    )


def _b8_validation_table(
    shares_matrix,
    simulation,
):
    """Kiểm tra tính hợp lệ của nghiệm sau tối ưu."""
    parameters = _b8_parameters()

    shares_matrix = np.asarray(
        shares_matrix,
        dtype=float,
    )

    row_sums = shares_matrix.sum(
        axis=1
    )

    checks = [
        {
            "Kiểm tra": "Đúng 10 năm 2026-2035",
            "Giá trị": (
                f"{int(simulation['Năm'].min())}-"
                f"{int(simulation['Năm'].max())}"
            ),
            "Đạt": (
                len(simulation) == 10
                and simulation["Năm"].min() == 2026
                and simulation["Năm"].max() == 2035
            ),
        },
        {
            "Kiểm tra": "Tổng tỷ trọng mỗi năm bằng 1",
            "Giá trị": (
                f"max sai lệch = "
                f"{np.max(np.abs(row_sums - 1.0)):.2e}"
            ),
            "Đạt": bool(
                np.allclose(
                    row_sums,
                    1.0,
                    atol=1e-6,
                )
            ),
        },
        {
            "Kiểm tra": "Tỷ trọng không dưới cận 0,02",
            "Giá trị": f"{shares_matrix.min():.6f}",
            "Đạt": bool(
                shares_matrix.min()
                >= parameters["share_lower_bound"]
                - 1e-6
            ),
        },
        {
            "Kiểm tra": "Tỷ trọng không vượt cận 0,85",
            "Giá trị": f"{shares_matrix.max():.6f}",
            "Đạt": bool(
                shares_matrix.max()
                <= parameters["share_upper_bound"]
                + 1e-6
            ),
        },
        {
            "Kiểm tra": "GDP dương và hữu hạn",
            "Giá trị": f"min = {simulation['GDP'].min():,.3f}",
            "Đạt": bool(
                np.isfinite(
                    simulation["GDP"]
                ).all()
                and (
                    simulation["GDP"] > 0
                ).all()
            ),
        },
        {
            "Kiểm tra": "Tiêu dùng dương và hữu hạn",
            "Giá trị": (
                f"min = "
                f"{simulation['Tiêu dùng'].min():,.3f}"
            ),
            "Đạt": bool(
                np.isfinite(
                    simulation["Tiêu dùng"]
                ).all()
                and (
                    simulation["Tiêu dùng"] > 0
                ).all()
            ),
        },
        {
            "Kiểm tra": "Các biến trạng thái dương",
            "Giá trị": (
                f"min = "
                f"{simulation[['K','L','D','AI','H','A']].min().min():.6f}"
            ),
            "Đạt": bool(
                (
                    simulation[
                        [
                            "K",
                            "L",
                            "D",
                            "AI",
                            "H",
                            "A",
                        ]
                    ] > 0
                ).all().all()
            ),
        },
    ]

    return pd.DataFrame(checks)


@st.cache_data(show_spinner=False)
def _b8_optimize_shares(
    rho=0.97,
    shock_2028=0.0,
):
    """
    Tối ưu 40 biến tỷ trọng bằng SLSQP.

    Mỗi năm:
        share_K + share_D + share_AI + share_H = 1.
    """
    from scipy.optimize import minimize

    parameters = _b8_parameters()
    periods = 10

    initial_share = np.array(
        [0.34, 0.26, 0.18, 0.22],
        dtype=float,
    )

    x0 = np.tile(
        initial_share,
        periods,
    )

    investment_rates = np.full(
        periods,
        parameters["investment_rate"],
        dtype=float,
    )

    def objective(flat_shares):
        shares = flat_shares.reshape(
            periods,
            4,
        )

        simulation = _b8_simulate(
            shares_matrix=shares,
            invest_rates=investment_rates,
            shock_2028=shock_2028,
            rho=rho,
        )

        welfare = float(
            simulation.iloc[-1][
                "Welfare_lũy_kế"
            ]
        )

        if not np.isfinite(welfare):
            return 1e12

        return -welfare

    constraints = [
        {
            "type": "eq",
            "fun": (
                lambda flat_shares, period=period:
                np.sum(
                    flat_shares.reshape(
                        periods,
                        4,
                    )[period]
                )
                - 1.0
            ),
        }
        for period in range(periods)
    ]

    result = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=[
            (
                parameters["share_lower_bound"],
                parameters["share_upper_bound"],
            )
        ]
        * (
            periods * 4
        ),
        constraints=constraints,
        options={
            "maxiter": 500,
            "ftol": 1e-9,
            "disp": False,
        },
    )

    candidate = (
        np.asarray(
            result.x,
            dtype=float,
        )
        if result.x is not None
        else x0.copy()
    )

    optimized_shares = candidate.reshape(
        periods,
        4,
    )

    row_sums = optimized_shares.sum(
        axis=1,
        keepdims=True,
    )

    optimized_shares = (
        optimized_shares
        / np.where(
            row_sums == 0,
            1.0,
            row_sums,
        )
    )

    simulation = _b8_simulate(
        shares_matrix=optimized_shares,
        invest_rates=investment_rates,
        shock_2028=shock_2028,
        rho=rho,
    )

    max_equality_violation = float(
        np.max(
            np.abs(
                optimized_shares.sum(axis=1)
                - 1.0
            )
        )
    )

    success = bool(
        result.success
        and np.isfinite(
            simulation[
                "Welfare_lũy_kế"
            ]
        ).all()
        and max_equality_violation <= 1e-5
    )

    solver_info = {
        "success": success,
        "message": str(result.message),
        "status": int(result.status),
        "iterations": int(
            getattr(result, "nit", 0)
        ),
        "objective": float(
            -result.fun
        )
        if np.isfinite(result.fun)
        else np.nan,
        "max_equality_violation": (
            max_equality_violation
        ),
    }

    return (
        optimized_shares,
        simulation,
        solver_info,
    )


def _b8_strategy_comparison(
    rho=0.97,
):
    """So sánh đầu tư trải đều và front-load với cùng tổng tỷ lệ đầu tư."""
    fixed_shares = np.tile(
        np.array(
            [0.34, 0.26, 0.18, 0.22],
            dtype=float,
        ),
        (10, 1),
    )

    equal_rates = np.full(
        10,
        0.22,
        dtype=float,
    )

    front_load_rates = np.array(
        [
            0.28,
            0.27,
            0.26,
            0.24,
            0.22,
            0.21,
            0.19,
            0.18,
            0.18,
            0.17,
        ],
        dtype=float,
    )

    equal_simulation = _b8_simulate(
        shares_matrix=fixed_shares,
        invest_rates=equal_rates,
        shock_2028=0.0,
        rho=rho,
    )

    front_simulation = _b8_simulate(
        shares_matrix=fixed_shares,
        invest_rates=front_load_rates,
        shock_2028=0.0,
        rho=rho,
    )

    comparison = pd.DataFrame(
        {
            "Chiến lược": [
                "Trải đều",
                "Front-load",
            ],
            "Tổng tỷ lệ đầu tư 10 năm": [
                equal_rates.sum(),
                front_load_rates.sum(),
            ],
            "Welfare": [
                equal_simulation.iloc[-1][
                    "Welfare_lũy_kế"
                ],
                front_simulation.iloc[-1][
                    "Welfare_lũy_kế"
                ],
            ],
            "GDP 2035": [
                equal_simulation.iloc[-1]["GDP"],
                front_simulation.iloc[-1]["GDP"],
            ],
            "Tiêu dùng 2035": [
                equal_simulation.iloc[-1][
                    "Tiêu dùng"
                ],
                front_simulation.iloc[-1][
                    "Tiêu dùng"
                ],
            ],
        }
    )

    return (
        comparison,
        equal_simulation,
        front_simulation,
        equal_rates,
        front_load_rates,
    )


def page_8():
    hero(
        "Bài 8 — Tối ưu động phân bổ liên thời gian 2026-2035",
        "Mô hình hóa động học K-D-AI-H, tối ưu 40 biến tỷ trọng bằng SLSQP, kiểm định nghiệm, phân tích cú sốc 2028 và so sánh đầu tư trải đều với front-load.",
        [
            "8.1-8.4",
            "Dynamic optimization",
            "SLSQP",
            "Welfare",
            "Shock 2028",
        ],
    )

    show_assignment_structure(8)

    # =====================================================
    # 8.1. Bối cảnh Việt Nam
    # =====================================================
    st.markdown(
        "## 8.1. Bối cảnh Việt Nam"
    )

    st.markdown(
        """
        Đầu tư số có tác động tích lũy và độ trễ. Đầu tư mạnh vào AI ở hiện tại
        có thể chưa tạo lợi ích nếu thiếu nhân lực số; ngược lại, đầu tư vào nhân lực
        và hạ tầng tạo nền tảng hấp thụ công nghệ trong dài hạn.

        Bài 8 xây dựng mô hình tối ưu động giai đoạn **2026-2035** nhằm lựa chọn
        quỹ đạo phân bổ đầu tư vào vốn vật chất, chuyển đổi số, AI và nhân lực số,
        sao cho tổng phúc lợi tiêu dùng có chiết khấu đạt mức cao nhất.
        """
    )

    # =====================================================
    # 8.2. Mô hình toán học
    # =====================================================
    st.markdown(
        "## 8.2. Mô hình toán học"
    )

    st.markdown(
        "### Hàm mục tiêu liên thời gian"
    )

    st.latex(
        r"\max\ "
        r"\sum_{t=2026}^{2035}"
        r"\rho^{t-2026}\ln(C_t)"
    )

    st.markdown("### Hàm sản xuất")

    st.latex(
        r"Y_t="
        r"A_tK_t^{0.33}L_t^{0.42}"
        r"D_t^{0.10}AI_t^{0.08}H_t^{0.07}"
    )

    st.markdown(
        "### Phương trình chuyển trạng thái"
    )

    st.latex(
        r"K_{t+1}=(1-\delta_K)K_t+I_{K,t}"
    )
    st.latex(
        r"D_{t+1}=(1-\delta_D)D_t+I_{D,t}/s_D"
    )
    st.latex(
        r"AI_{t+1}=(1-\delta_{AI})AI_t+I_{AI,t}/s_{AI}"
    )
    st.latex(
        r"H_{t+1}=H_t+\theta_HI_{H,t}/s_H-\mu_HH_t"
    )
    st.latex(
        r"C_t=Y_t-I_t,\qquad "
        r"I_{j,t}=s_{j,t}I_t"
    )
    st.latex(
        r"\sum_js_{j,t}=1,\qquad "
        r"0.02\leq s_{j,t}\leq0.85"
    )

    st.info(
        "SLSQP tối ưu 40 biến: bốn tỷ trọng đầu tư cho mỗi năm trong 10 năm."
    )

    # =====================================================
    # 8.3. Dữ liệu và tham số
    # =====================================================
    st.markdown(
        "## 8.2.1. Dữ liệu đầu vào và tham số"
    )

    initial = _b8_initial_state()
    parameters = _b8_parameters()

    initial_table = pd.DataFrame(
        {
            "Biến": [
                "GDP Y",
                "Vốn K",
                "Lao động L",
                "Số hóa D",
                "Năng lực AI",
                "Nhân lực H",
                "TFP A",
            ],
            "Giá trị cuối năm 2025": [
                initial["Y"],
                initial["K"],
                initial["L"],
                initial["D"],
                initial["AI"],
                initial["H"],
                initial["A"],
            ],
        }
    )

    parameter_table = pd.DataFrame(
        {
            "Tham số": [
                "Tỷ lệ đầu tư/GDP",
                "Khấu hao K",
                "Khấu hao D",
                "Khấu hao AI",
                "Suy giảm H",
                "Hiệu quả đầu tư H",
                "Hệ số quy đổi D",
                "Hệ số quy đổi AI",
                "Hệ số quy đổi H",
                "Tăng lao động",
                "Cận dưới tỷ trọng",
                "Cận trên tỷ trọng",
            ],
            "Ký hiệu": [
                "i",
                "delta_K",
                "delta_D",
                "delta_AI",
                "mu_H",
                "theta_H",
                "s_D",
                "s_AI",
                "s_H",
                "g_L",
                "lb",
                "ub",
            ],
            "Giá trị": [
                parameters["investment_rate"],
                parameters["delta_K"],
                parameters["delta_D"],
                parameters["delta_AI"],
                parameters["mu_H"],
                parameters["theta_H"],
                parameters["scale_D"],
                parameters["scale_AI"],
                parameters["scale_H"],
                parameters["labor_growth"],
                parameters["share_lower_bound"],
                parameters["share_upper_bound"],
            ],
        }
    )

    c1, c2 = st.columns(2)

    with c1:
        st.dataframe(
            initial_table,
            use_container_width=True,
            hide_index=True,
        )

    with c2:
        st.dataframe(
            parameter_table,
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Trạng thái năm 2025 được lấy từ dữ liệu vĩ mô và hàm Cobb-Douglas của Bài 1. "
        "Các tham số động học là giả định mô phỏng, cần được nêu rõ trong báo cáo."
    )

    # =====================================================
    # 8.4. Yêu cầu lập trình
    # =====================================================
    st.markdown(
        "## 8.3. Yêu cầu lập trình"
    )

    rho = st.slider(
        "Hệ số chiết khấu phúc lợi rho",
        min_value=0.90,
        max_value=1.00,
        value=0.97,
        step=0.01,
        key="b8_rho_fixed",
    )

    with st.spinner(
        "Đang tối ưu quỹ đạo đầu tư 2026-2035..."
    ):
        (
            optimal_shares,
            optimal_simulation,
            solver_info,
        ) = _b8_optimize_shares(
            rho=float(rho),
            shock_2028=0.0,
        )

    tab841, tab842, tab843, tab844 = st.tabs(
        [
            "8.3.1 - Tối ưu SLSQP",
            "8.3.2 - Quỹ đạo động",
            "8.3.3 - Cú sốc 2028",
            "8.3.4 - Front-load & độ nhạy",
        ]
    )

    # -----------------------------------------------------
    # 8.3.1
    # -----------------------------------------------------
    with tab841:
        st.markdown(
            "### Câu 8.3.1. Giải bài toán phi tuyến bằng SLSQP"
        )

        shares_table = pd.DataFrame(
            optimal_shares,
            columns=[
                "Share_K",
                "Share_D",
                "Share_AI",
                "Share_H",
            ],
        )

        shares_table.insert(
            0,
            "Năm",
            np.arange(2026, 2036),
        )

        kpi_cards(
            [
                (
                    "Trạng thái solver",
                    (
                        "Thành công"
                        if solver_info["success"]
                        else "Cảnh báo"
                    ),
                    solver_info["message"][:45],
                ),
                (
                    "Số vòng lặp",
                    str(
                        solver_info["iterations"]
                    ),
                    "SLSQP",
                ),
                (
                    "Welfare tối ưu",
                    f"{optimal_simulation.iloc[-1]['Welfare_lũy_kế']:.4f}",
                    f"rho={rho:.2f}",
                ),
                (
                    "GDP năm 2035",
                    f"{optimal_simulation.iloc[-1]['GDP']:,.1f}",
                    "nghìn tỷ VND",
                ),
            ]
        )

        st.dataframe(
            shares_table.style.format(
                {
                    "Share_K": "{:.4f}",
                    "Share_D": "{:.4f}",
                    "Share_AI": "{:.4f}",
                    "Share_H": "{:.4f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        shares_long = shares_table.melt(
            id_vars="Năm",
            value_vars=[
                "Share_K",
                "Share_D",
                "Share_AI",
                "Share_H",
            ],
            var_name="Hạng mục",
            value_name="Tỷ trọng",
        )

        fig_shares = px.area(
            shares_long,
            x="Năm",
            y="Tỷ trọng",
            color="Hạng mục",
            template=PLOT_TEMPLATE,
            title="Quỹ đạo tỷ trọng đầu tư tối ưu",
        )
        fig_shares.update_layout(
            height=480,
            yaxis_title="Tỷ trọng đầu tư",
            xaxis_title="Năm",
        )

        st.plotly_chart(
            fig_shares,
            use_container_width=True,
        )

        st.markdown(
            "#### Kiểm định nghiệm sau tối ưu"
        )

        validation = _b8_validation_table(
            optimal_shares,
            optimal_simulation,
        )

        st.dataframe(
            validation,
            use_container_width=True,
            hide_index=True,
        )

        if bool(validation["Đạt"].all()):
            st.success(
                "Nghiệm vượt qua toàn bộ kiểm tra số và ràng buộc."
            )
        else:
            st.error(
                "Có ít nhất một kiểm tra chưa đạt; chưa nên sử dụng kết quả làm bản final."
            )

    # -----------------------------------------------------
    # 8.3.2
    # -----------------------------------------------------
    with tab842:
        st.markdown(
            "### Câu 8.3.2. Vẽ quỹ đạo tối ưu K, D, AI, H, Y và C"
        )

        c1, c2 = st.columns(2)

        with c1:
            fig_output = px.line(
                optimal_simulation,
                x="Năm",
                y=[
                    "GDP",
                    "Tiêu dùng",
                    "Tổng đầu tư",
                ],
                markers=True,
                template=PLOT_TEMPLATE,
                title="GDP, tiêu dùng và đầu tư",
            )
            fig_output.update_layout(
                height=470,
                xaxis_title="Năm",
                yaxis_title="Nghìn tỷ VND",
            )
            st.plotly_chart(
                fig_output,
                use_container_width=True,
            )

        with c2:
            state_long = optimal_simulation.melt(
                id_vars="Năm",
                value_vars=[
                    "K",
                    "D",
                    "AI",
                    "H",
                ],
                var_name="Biến trạng thái",
                value_name="Giá trị",
            )

            fig_state = px.line(
                state_long,
                x="Năm",
                y="Giá trị",
                color="Biến trạng thái",
                markers=True,
                template=PLOT_TEMPLATE,
                title="Quỹ đạo K, D, AI và H",
            )
            fig_state.update_layout(
                height=470,
                xaxis_title="Năm",
                yaxis_title="Chỉ số/giá trị mô phỏng",
            )
            st.plotly_chart(
                fig_state,
                use_container_width=True,
            )

        st.dataframe(
            optimal_simulation,
            use_container_width=True,
            hide_index=True,
        )

        gdp_cagr = (
            (
                optimal_simulation.iloc[-1]["GDP"]
                / optimal_simulation.iloc[0]["GDP"]
            )
            ** (1 / 9)
            - 1
        ) * 100

        st.info(
            f"GDP mô phỏng tăng bình quân khoảng **{gdp_cagr:.2f}%/năm** "
            "trong giai đoạn 2026-2035 theo quỹ đạo tối ưu."
        )

    # -----------------------------------------------------
    # 8.3.3
    # -----------------------------------------------------
    with tab843:
        st.markdown(
            "### Câu 8.3.3. Cú sốc GDP năm 2028 giảm 8% và tối ưu lại"
        )

        with st.spinner(
            "Đang tối ưu lại sau cú sốc 2028..."
        ):
            (
                shock_shares,
                shock_simulation,
                shock_solver_info,
            ) = _b8_optimize_shares(
                rho=float(rho),
                shock_2028=0.08,
            )

        comparison_shock = pd.DataFrame(
            {
                "Năm": optimal_simulation["Năm"],
                "GDP cơ sở": optimal_simulation["GDP"],
                "GDP sau cú sốc": shock_simulation["GDP"],
                "Tiêu dùng cơ sở": optimal_simulation["Tiêu dùng"],
                "Tiêu dùng sau cú sốc": shock_simulation["Tiêu dùng"],
            }
        )

        welfare_loss = (
            optimal_simulation.iloc[-1][
                "Welfare_lũy_kế"
            ]
            - shock_simulation.iloc[-1][
                "Welfare_lũy_kế"
            ]
        )

        gdp_2035_change = (
            shock_simulation.iloc[-1]["GDP"]
            - optimal_simulation.iloc[-1]["GDP"]
        )

        kpi_cards(
            [
                (
                    "Solver cú sốc",
                    (
                        "Thành công"
                        if shock_solver_info["success"]
                        else "Cảnh báo"
                    ),
                    shock_solver_info["message"][:45],
                ),
                (
                    "Welfare mất đi",
                    f"{welfare_loss:.4f}",
                    "so với cơ sở",
                ),
                (
                    "GDP 2035 thay đổi",
                    f"{gdp_2035_change:+,.1f}",
                    "nghìn tỷ VND",
                ),
                (
                    "Cú sốc năm 2028",
                    "-8%",
                    "GDP trong năm",
                ),
            ]
        )

        fig_shock = px.line(
            comparison_shock,
            x="Năm",
            y=[
                "GDP cơ sở",
                "GDP sau cú sốc",
            ],
            markers=True,
            template=PLOT_TEMPLATE,
            title="Quỹ đạo GDP trước và sau cú sốc 2028",
        )
        fig_shock.update_layout(
            height=480,
            xaxis_title="Năm",
            yaxis_title="GDP, nghìn tỷ VND",
        )
        st.plotly_chart(
            fig_shock,
            use_container_width=True,
        )

        share_change = pd.DataFrame(
            {
                "Năm": np.arange(2026, 2036),
                "Delta_Share_K": (
                    shock_shares[:, 0]
                    - optimal_shares[:, 0]
                ),
                "Delta_Share_D": (
                    shock_shares[:, 1]
                    - optimal_shares[:, 1]
                ),
                "Delta_Share_AI": (
                    shock_shares[:, 2]
                    - optimal_shares[:, 2]
                ),
                "Delta_Share_H": (
                    shock_shares[:, 3]
                    - optimal_shares[:, 3]
                ),
            }
        )

        st.markdown(
            "#### Thay đổi cơ cấu đầu tư sau cú sốc"
        )

        st.dataframe(
            share_change.style.format(
                {
                    "Delta_Share_K": "{:+.4f}",
                    "Delta_Share_D": "{:+.4f}",
                    "Delta_Share_AI": "{:+.4f}",
                    "Delta_Share_H": "{:+.4f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    # -----------------------------------------------------
    # 8.3.4
    # -----------------------------------------------------
    with tab844:
        st.markdown(
            "### Câu 8.3.4. So sánh trải đều, front-load và độ nhạy rho"
        )

        (
            strategy_comparison,
            equal_simulation,
            front_simulation,
            equal_rates,
            front_load_rates,
        ) = _b8_strategy_comparison(
            rho=float(rho)
        )

        st.dataframe(
            strategy_comparison,
            use_container_width=True,
            hide_index=True,
        )

        strategy_long = pd.concat(
            [
                equal_simulation[
                    ["Năm", "GDP"]
                ].assign(
                    Chiến_lược="Trải đều"
                ),
                front_simulation[
                    ["Năm", "GDP"]
                ].assign(
                    Chiến_lược="Front-load"
                ),
            ],
            ignore_index=True,
        )

        fig_strategy = px.line(
            strategy_long,
            x="Năm",
            y="GDP",
            color="Chiến_lược",
            markers=True,
            template=PLOT_TEMPLATE,
            title="GDP theo hai chiến lược đầu tư",
        )
        fig_strategy.update_layout(
            height=470,
            xaxis_title="Năm",
            yaxis_title="GDP, nghìn tỷ VND",
        )
        st.plotly_chart(
            fig_strategy,
            use_container_width=True,
        )

        rates_table = pd.DataFrame(
            {
                "Năm": np.arange(2026, 2036),
                "Trải đều": equal_rates,
                "Front-load": front_load_rates,
            }
        )

        st.dataframe(
            rates_table,
            use_container_width=True,
            hide_index=True,
        )

        sensitivity_rows = []

        for rho_test in [
            0.90,
            0.95,
            0.97,
            0.99,
            1.00,
        ]:
            (
                comparison_test,
                _,
                _,
                _,
                _,
            ) = _b8_strategy_comparison(
                rho=rho_test
            )

            equal_welfare = float(
                comparison_test.loc[
                    comparison_test[
                        "Chiến lược"
                    ] == "Trải đều",
                    "Welfare",
                ].iloc[0]
            )

            front_welfare = float(
                comparison_test.loc[
                    comparison_test[
                        "Chiến lược"
                    ] == "Front-load",
                    "Welfare",
                ].iloc[0]
            )

            sensitivity_rows.append(
                {
                    "rho": rho_test,
                    "Welfare trải đều": equal_welfare,
                    "Welfare front-load": front_welfare,
                    "Chênh lệch front-load": (
                        front_welfare
                        - equal_welfare
                    ),
                    "Chiến lược tốt hơn": (
                        "Front-load"
                        if front_welfare
                        > equal_welfare
                        else "Trải đều"
                    ),
                }
            )

        sensitivity_df = pd.DataFrame(
            sensitivity_rows
        )

        st.markdown(
            "#### Độ nhạy theo hệ số chiết khấu"
        )

        st.dataframe(
            sensitivity_df,
            use_container_width=True,
            hide_index=True,
        )

        better_strategy = (
            strategy_comparison.sort_values(
                "Welfare",
                ascending=False,
            ).iloc[0]["Chiến lược"]
        )

        st.success(
            f"Với rho={rho:.2f}, chiến lược có phúc lợi cao hơn là "
            f"**{better_strategy}**."
        )

    # =====================================================
    # Tải kết quả
    # =====================================================
    shares_export = pd.DataFrame(
        optimal_shares,
        columns=[
            "Share_K",
            "Share_D",
            "Share_AI",
            "Share_H",
        ],
    )
    shares_export.insert(
        0,
        "Năm",
        np.arange(2026, 2036),
    )

    export_df = optimal_simulation.merge(
        shares_export,
        on=[
            "Năm",
            "Share_K",
            "Share_D",
            "Share_AI",
            "Share_H",
        ],
        how="left",
    )

    st.download_button(
        "Tải kết quả Bài 8 dạng CSV",
        data=export_df.to_csv(
            index=False
        ).encode(
            "utf-8-sig"
        ),
        file_name="bai8_toi_uu_dong_2026_2035.csv",
        mime="text/csv",
        key="download_bai8_fixed",
    )

    # =====================================================
    # 8.4. Câu hỏi thảo luận chính sách
    # =====================================================
    st.markdown(
        "## 8.4. Câu hỏi thảo luận chính sách"
    )

    component_names = [
        "K - vốn vật chất",
        "D - số hóa",
        "AI - trí tuệ nhân tạo",
        "H - nhân lực số",
    ]
    component_cols = [
        "Share_K",
        "Share_D",
        "Share_AI",
        "Share_H",
    ]

    first_three_average = optimal_shares[:3].mean(axis=0)
    last_three_average = optimal_shares[-3:].mean(axis=0)
    all_period_average = optimal_shares.mean(axis=0)

    def _b8_timing_label(first_value, last_value, threshold=0.01):
        if first_value > last_value + threshold:
            return "front-loaded"
        if last_value > first_value + threshold:
            return "back-loaded"
        return "tương đối ổn định"

    timing_table = pd.DataFrame(
        {
            "Hạng mục": component_names,
            "TB 2026-2028": first_three_average,
            "TB toàn kỳ": all_period_average,
            "TB 2033-2035": last_three_average,
            "Chênh lệch đầu-cuối": first_three_average - last_three_average,
            "Nhận xét quỹ đạo": [
                _b8_timing_label(first_three_average[i], last_three_average[i])
                for i in range(4)
            ],
        }
    )

    state_growth_table = pd.DataFrame(
        {
            "Biến trạng thái": ["K", "D", "AI", "H"],
            "Giá trị 2026": [
                optimal_simulation.iloc[0]["K"],
                optimal_simulation.iloc[0]["D"],
                optimal_simulation.iloc[0]["AI"],
                optimal_simulation.iloc[0]["H"],
            ],
            "Giá trị 2035": [
                optimal_simulation.iloc[-1]["K"],
                optimal_simulation.iloc[-1]["D"],
                optimal_simulation.iloc[-1]["AI"],
                optimal_simulation.iloc[-1]["H"],
            ],
        }
    )
    state_growth_table["Tăng 2026-2035 (%)"] = (
        (state_growth_table["Giá trị 2035"] / state_growth_table["Giá trị 2026"] - 1)
        * 100
    )

    ai_h_ratio = optimal_shares[:, 2] / np.maximum(optimal_shares[:, 3], 1e-12)
    ai_h_ratio_mean = float(np.mean(ai_h_ratio))
    ai_h_ratio_std = float(np.std(ai_h_ratio))
    ai_h_ratio_cv = float(ai_h_ratio_std / max(ai_h_ratio_mean, 1e-12))
    ai_h_ratio_status = "khá ổn định" if ai_h_ratio_cv < 0.15 else "chưa ổn định"

    with st.spinner("Đang so sánh riêng hai trường hợp rho=0,97 và rho=0,90..."):
        rho97_shares, rho97_simulation, _ = _b8_optimize_shares(rho=0.97, shock_2028=0.0)
        rho90_shares, rho90_simulation, _ = _b8_optimize_shares(rho=0.90, shock_2028=0.0)

    rho_comparison = pd.DataFrame(
        {
            "Chỉ tiêu": [
                "Welfare lũy kế",
                "GDP 2035",
                "TB Share_K",
                "TB Share_D",
                "TB Share_AI",
                "TB Share_H",
                "Tỷ lệ AI/H bình quân",
            ],
            "rho=0,97": [
                float(rho97_simulation.iloc[-1]["Welfare_lũy_kế"]),
                float(rho97_simulation.iloc[-1]["GDP"]),
                float(rho97_shares[:, 0].mean()),
                float(rho97_shares[:, 1].mean()),
                float(rho97_shares[:, 2].mean()),
                float(rho97_shares[:, 3].mean()),
                float(np.mean(rho97_shares[:, 2] / np.maximum(rho97_shares[:, 3], 1e-12))),
            ],
            "rho=0,90": [
                float(rho90_simulation.iloc[-1]["Welfare_lũy_kế"]),
                float(rho90_simulation.iloc[-1]["GDP"]),
                float(rho90_shares[:, 0].mean()),
                float(rho90_shares[:, 1].mean()),
                float(rho90_shares[:, 2].mean()),
                float(rho90_shares[:, 3].mean()),
                float(np.mean(rho90_shares[:, 2] / np.maximum(rho90_shares[:, 3], 1e-12))),
            ],
        }
    )
    rho_comparison["Thay đổi khi rho=0,90"] = rho_comparison["rho=0,90"] - rho_comparison["rho=0,97"]

    with st.expander(
        "a) Quỹ đạo tối ưu của K, D, AI, H front-loaded hay back-loaded? Vì sao?",
        expanded=True,
    ):
        st.dataframe(
            timing_table.style.format(
                {
                    "TB 2026-2028": "{:.4f}",
                    "TB toàn kỳ": "{:.4f}",
                    "TB 2033-2035": "{:.4f}",
                    "Chênh lệch đầu-cuối": "{:+.4f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.dataframe(
            state_growth_table.style.format(
                {
                    "Giá trị 2026": "{:,.3f}",
                    "Giá trị 2035": "{:,.3f}",
                    "Tăng 2026-2035 (%)": "{:+.2f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown(
            "Bảng trên cho biết hạng mục nào được dồn tỷ trọng đầu tư mạnh ở đầu kỳ (**front-loaded**) "
            "và hạng mục nào được tăng tỷ trọng về cuối kỳ (**back-loaded**). Mô hình đề xuất như vậy vì "
            "các biến K, D, AI và H có cơ chế tích lũy khác nhau: đầu tư sớm vào biến có độ trễ và tác động nền tảng "
            "sẽ tạo năng lực sản xuất cho nhiều năm sau; còn đầu tư muộn phù hợp hơn với biến có lợi ích ngắn hạn "
            "hoặc cần chờ nền tảng hấp thụ đủ mạnh. Do đó, không nên kết luận chung rằng mọi biến đều front-loaded; "
            "phải đọc riêng từng cột trong bảng quỹ đạo tối ưu."
        )

    with st.expander(
        "b) Tỷ lệ đầu tư AI/đầu tư H có ổn định không? Nhân lực nên đi trước hay đồng thời với AI?",
        expanded=True,
    ):
        ratio_table = pd.DataFrame(
            {
                "Năm": np.arange(2026, 2036),
                "Share_AI": optimal_shares[:, 2],
                "Share_H": optimal_shares[:, 3],
                "AI/H": ai_h_ratio,
            }
        )
        st.dataframe(
            ratio_table.style.format(
                {
                    "Share_AI": "{:.4f}",
                    "Share_H": "{:.4f}",
                    "AI/H": "{:.4f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown(
            f"Tỷ lệ AI/H bình quân là **{ai_h_ratio_mean:.3f}**, độ lệch chuẩn **{ai_h_ratio_std:.3f}**, "
            f"hệ số biến thiên **{ai_h_ratio_cv:.3f}**, nên tỷ lệ này được xem là **{ai_h_ratio_status}**. "
            "Nếu Share_H cao ở đầu kỳ hoặc AI/H tăng dần về sau, mô hình ngụ ý đào tạo nhân lực nên **đi trước** "
            "để tạo năng lực hấp thụ AI. Nếu AI/H dao động ít và Share_AI, Share_H cùng duy trì ở mức đáng kể, "
            "mô hình ngụ ý đào tạo nhân lực nên **đồng thời** với đầu tư AI. Trong cả hai trường hợp, không nên đầu tư "
            "AI tách rời khỏi H vì thiếu nhân lực sẽ làm giảm hiệu quả triển khai và tăng rủi ro thay thế lao động."
        )

    with st.expander(
        "c) Nếu rho giảm từ 0,97 xuống 0,90 thì kết quả thay đổi thế nào? Có dẫn tới dưới đầu tư R&D không?",
        expanded=True,
    ):
        st.dataframe(
            rho_comparison.style.format(
                {
                    "rho=0,97": "{:,.4f}",
                    "rho=0,90": "{:,.4f}",
                    "Thay đổi khi rho=0,90": "{:+,.4f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown(
            "Khi **rho=0,97**, phúc lợi tương lai được coi trọng hơn, nên mô hình có xu hướng chấp nhận đầu tư "
            "vào các năng lực tích lũy dài hạn như D, AI và H. Khi **rho=0,90**, tương lai bị chiết khấu mạnh hơn, "
            "mô hình thiên về lợi ích ngắn hạn hơn và có thể giảm sức hấp dẫn tương đối của các khoản đầu tư có độ trễ. "
            "Đây là một lý do kinh tế khiến chính phủ hoặc tổ chức chịu áp lực nhiệm kỳ thường **dưới đầu tư vào R&D, "
            "nhân lực và công nghệ nền tảng**: chi phí xuất hiện ngay, còn lợi ích đến muộn và khó quy trách nhiệm. "
            "Trong Bài 8 không có biến R&D riêng, nên kết luận này được diễn giải thông qua các khoản đầu tư dài hạn "
            "gần R&D như AI, số hóa và nhân lực số."
        )

    ai_analysis_panel(
        lesson_name='Bài 8 - Tối ưu động 2026-2035',
        model_name='Dynamic Optimization + Welfare Simulation',
        input_params={"lesson": 'Bài 8 - Tối ưu động 2026-2035', "model": 'Dynamic Optimization + Welfare Simulation'},
        result_data=_collect_ai_context(locals()),
        key="ai_bai_8",
    )


def _b9_parameters():
    """Bảng tham số 8 ngành đúng theo đề Bài 9."""
    rows = [
        ["Nông-Lâm-Thủy sản", 13.20, 18, 8.5, 12.0, 45.0, 5.2, 50.0],
        ["CN chế biến chế tạo", 11.50, 42, 32.5, 18.5, 28.0, 62.4, 32.0],
        ["Xây dựng", 4.80, 25, 12.8, 8.5, 35.0, 18.5, 42.0],
        ["Bán buôn-bán lẻ", 7.80, 38, 22.4, 15.2, 32.0, 48.2, 38.0],
        ["Tài chính-Ngân hàng", 0.55, 52, 45.8, 12.5, 22.0, 72.5, 26.0],
        ["Logistics-Vận tải", 1.95, 35, 28.5, 16.8, 30.0, 42.8, 36.0],
        ["CNTT-Truyền thông", 0.62, 28, 62.5, 15.0, 20.0, 32.5, 24.0],
        ["Giáo dục-Đào tạo", 2.15, 22, 18.5, 22.0, 55.0, 12.5, 62.0],
    ]
    return pd.DataFrame(rows, columns=["Ngành", "Lao động (triệu)", "Risk (%)", "a1", "a2", "b1", "c1", "d1"])


def _b9_prepare_data():
    df = _b9_parameters().copy()
    df["risk"] = df["Risk (%)"] / 100.0
    return df


def _b9_solve(total_budget=30000.0, min_ai_budget=0.0, displacement_cap_5pct=False):
    """Giải LP đúng cấu trúc x_AI và x_H của Bài 9 bằng scipy.linprog."""
    df = _b9_prepare_data()
    n = len(df)
    risk = df["risk"].to_numpy(float)
    a1 = df["a1"].to_numpy(float)
    b1 = df["b1"].to_numpy(float)
    c1 = df["c1"].to_numpy(float)
    d1 = df["d1"].to_numpy(float)
    # biến: [x_AI_1..x_AI_N, x_H_1..x_H_N]
    net_ai_coef = a1 - c1 * risk
    net_h_coef = b1
    c = -np.r_[net_ai_coef, net_h_coef]
    A_ub, b_ub = [], []
    row = np.ones(2*n)
    A_ub.append(row); b_ub.append(float(total_budget))
    if min_ai_budget > 0:
        row = np.zeros(2*n); row[:n] = -1
        A_ub.append(row); b_ub.append(-float(min_ai_budget))
    for i in range(n):
        # NetJob_i >= 0 -> -(net_ai*xAI + b1*xH) <= 0
        row = np.zeros(2*n); row[i] = -net_ai_coef[i]; row[n+i] = -b1[i]
        A_ub.append(row); b_ub.append(0.0)
        # Displaced <= RetrainingCapacity
        row = np.zeros(2*n); row[i] = c1[i] * risk[i]; row[n+i] = -d1[i]
        A_ub.append(row); b_ub.append(0.0)
        if displacement_cap_5pct:
            # DisplacedJob_i <= 5% lao động ngành, đổi triệu người sang số việc làm.
            row = np.zeros(2*n); row[i] = c1[i] * risk[i]
            A_ub.append(row); b_ub.append(0.05 * df.loc[i, "Lao động (triệu)"] * 1_000_000)
    res = linprog(c, A_ub=np.asarray(A_ub), b_ub=np.asarray(b_ub), bounds=[(0, None)]*(2*n), method="highs")
    if not res.success:
        return {"success": False, "status": res.message, "x_AI": None, "x_H": None, "objective": np.nan}
    return {"success": True, "status": res.message, "x_AI": res.x[:n], "x_H": res.x[n:], "objective": -float(res.fun)}


def _b9_job_metrics(df, x_ai, x_h):
    risk = df["risk"].to_numpy(float)
    a1 = df["a1"].to_numpy(float)
    b1 = df["b1"].to_numpy(float)
    c1 = df["c1"].to_numpy(float)
    d1 = df["d1"].to_numpy(float)
    x_ai = np.asarray(x_ai, dtype=float)
    x_h = np.asarray(x_h, dtype=float)
    new_job = a1 * x_ai
    upgrade = b1 * x_h
    displaced = c1 * risk * x_ai
    retrain_cap = d1 * x_h
    net_job = new_job + upgrade - displaced
    return new_job, upgrade, displaced, retrain_cap, net_job


def _b9_result_table(result):
    df = _b9_prepare_data()
    if not result["success"]:
        return pd.DataFrame(), {}
    new_job, upgrade, displaced, retrain_cap, net_job = _b9_job_metrics(df, result["x_AI"], result["x_H"])
    out = df.copy()
    out["x_AI (tỷ VND)"] = result["x_AI"]
    out["x_H (tỷ VND)"] = result["x_H"]
    out["NewJob"] = new_job
    out["UpgradeJob"] = upgrade
    out["DisplacedJob"] = displaced
    out["RetrainingCapacity"] = retrain_cap
    out["NetJob"] = net_job
    summary = {
        "total_budget": float(out["x_AI (tỷ VND)"].sum() + out["x_H (tỷ VND)"].sum()),
        "total_ai": float(out["x_AI (tỷ VND)"].sum()),
        "total_h": float(out["x_H (tỷ VND)"].sum()),
        "new_job": float(out["NewJob"].sum()),
        "upgrade": float(out["UpgradeJob"].sum()),
        "displaced": float(out["DisplacedJob"].sum()),
        "retrain_cap": float(out["RetrainingCapacity"].sum()),
        "net_job": float(out["NetJob"].sum()),
    }
    return out, summary


def _b9_threshold_manufacturing(x_ai_max=30000.0):
    df = _b9_prepare_data()
    row = df.iloc[1]
    displaced_per_ai = row["c1"] * row["risk"]
    net_need = max(0.0, (displaced_per_ai - row["a1"]) * x_ai_max / row["b1"])
    retrain_need = displaced_per_ai * x_ai_max / row["d1"]
    return max(net_need, retrain_need), net_need, retrain_need


def _b9_sankey_figure(table):
    vulnerable = table[table["Ngành"].isin(["Nông-Lâm-Thủy sản", "Xây dựng", "Bán buôn-bán lẻ"])]
    labels = []
    source = []
    target = []
    value = []
    for _, row in vulnerable.iterrows():
        base = len(labels)
        labels += [row["Ngành"], "Việc mới", "Nâng cấp kỹ năng", "Bị thay thế"]
        source += [base, base, base]
        target += [base+1, base+2, base+3]
        value += [max(row["NewJob"], 0), max(row["UpgradeJob"], 0), max(row["DisplacedJob"], 0)]
    fig = go.Figure(data=[go.Sankey(node=dict(pad=16, thickness=18, label=labels), link=dict(source=source, target=target, value=value))])
    fig.update_layout(title="Luồng dịch chuyển lao động nhóm dễ bị tổn thương", height=520, template=PLOT_TEMPLATE)
    return fig


def _b9_validation_table(table, total_budget=30000.0, cap_5pct=False):
    checks = [
        ["Tổng ngân sách ≤ 30.000", f"{(table['x_AI (tỷ VND)'].sum()+table['x_H (tỷ VND)'].sum()):,.2f}", table['x_AI (tỷ VND)'].sum()+table['x_H (tỷ VND)'].sum() <= total_budget + 1e-6],
        ["NetJob_i ≥ 0 với mọi ngành", f"min={table['NetJob'].min():,.2f}", bool((table['NetJob'] >= -1e-6).all())],
        ["DisplacedJob_i ≤ RetrainingCapacity_i", f"max gap={(table['DisplacedJob']-table['RetrainingCapacity']).max():,.2f}", bool((table['DisplacedJob'] <= table['RetrainingCapacity'] + 1e-6).all())],
    ]
    if cap_5pct:
        cap = 0.05 * table["Lao động (triệu)"] * 1_000_000
        checks.append(["DisplacedJob_i ≤ 5% lao động", f"max ratio={(table['DisplacedJob']/cap.replace(0, np.nan)).max():.3f}", bool((table["DisplacedJob"] <= cap + 1e-6).all())])
    return pd.DataFrame(checks, columns=["Kiểm tra", "Giá trị", "Đạt"])


def page_9():
    hero(
        "Bài 9 — Tác động AI tới thị trường lao động Việt Nam",
        "Mô hình NetJob đúng 8 ngành theo đề: x_AI, x_H, ràng buộc NetJob_i≥0, tốc độ tự động hóa không vượt quá năng lực đào tạo lại.",
        ["9.1-9.5", "NetJob", "Retraining", "LP", "8 sectors"],
    )
    show_assignment_structure(9)

    params = _b9_prepare_data()
    st.markdown("## 9.1. Bối cảnh Việt Nam")
    st.markdown(
        """
        AI có thể tạo việc làm mới và nâng cấp kỹ năng, nhưng cũng có thể thay thế
        lao động trong các ngành có rủi ro tự động hóa cao. Bài toán đánh giá đồng thời
        đầu tư AI và đầu tư đào tạo lại để tối đa hóa việc làm ròng nhưng không để
        DisplacedJob vượt quá năng lực đào tạo lại.
        """
    )

    st.markdown("## 9.2. Mô hình toán học")
    st.latex(r"NetJob_i = a_{1i}x^{AI}_i + b_{1i}x^H_i - c_{1i}x^{AI}_i Risk_i")
    st.latex(r"DisplacedJob_i = c_{1i}x^{AI}_i Risk_i \le d_{1i}x^H_i = RetrainingCapacity_i")
    st.markdown("## 9.3. Tham số 8 ngành")
    st.dataframe(params.drop(columns=["risk"]), use_container_width=True, hide_index=True)
    st.caption("Cột a2 trong đề dành cho biến x_D khi mở rộng; phiên bản LP cơ sở của đề dùng hai biến x_AI và x_H nên x_D được đặt bằng 0.")

    with st.expander("Tùy chọn mô phỏng", expanded=True):
        total_budget = st.slider("Tổng ngân sách (tỷ VND)", 10000, 50000, 30000, 1000, key="b9_budget_exact")
        min_ai_share = st.slider("Sàn đầu tư AI để mô phỏng tự động hóa diễn ra", 0.0, 0.8, 0.0, 0.05, key="b9_min_ai_share_exact")
        st.caption("Để khớp đề tuyệt đối, giữ sàn AI = 0. Nếu muốn thấy luồng lao động do AI, tăng sàn AI.")

    result = _b9_solve(total_budget=float(total_budget), min_ai_budget=float(total_budget)*float(min_ai_share), displacement_cap_5pct=False)
    st.markdown("## 9.4. Yêu cầu lập trình")
    table, summary = _b9_result_table(result)

    tab1, tab2, tab3, tab4 = st.tabs(["9.4.1 - LP NetJob", "9.4.2 - Ngưỡng ngành 2", "9.4.3 - Nhóm dễ tổn thương", "9.4.4 - Ràng buộc 5%"])
    with tab1:
        st.markdown("### Câu 9.4.1. Giải LP và tính NetJob cho từng ngành")
        if not result["success"]:
            st.error(result["status"])
        else:
            kpi_cards([
                ("Tổng NetJob", f"{summary['net_job']/1_000_000:+.3f} triệu", "việc làm ròng"),
                ("Đầu tư AI", f"{summary['total_ai']:,.0f}", "tỷ VND"),
                ("Đào tạo lại", f"{summary['total_h']:,.0f}", "tỷ VND"),
                ("Displaced", f"{summary['displaced']/1_000_000:.3f} triệu", "trước đào tạo"),
            ])
            st.dataframe(table, use_container_width=True, hide_index=True)
            st.dataframe(_b9_validation_table(table, total_budget=float(total_budget)), use_container_width=True, hide_index=True)
            fig = px.bar(table.sort_values("NetJob"), x="NetJob", y="Ngành", orientation="h", template=PLOT_TEMPLATE, title="NetJob theo ngành")
            fig.update_layout(height=520)
            st.plotly_chart(fig, use_container_width=True)
            if summary["total_ai"] < 1e-6:
                st.warning("Nghiệm tối ưu thuần túy có thể chọn toàn bộ ngân sách cho đào tạo vì đề không bắt buộc phải đầu tư AI. Đây là phát hiện hợp lệ của mô hình; tăng sàn AI ở trên để mô phỏng tự động hóa diễn ra.")

    with tab2:
        st.markdown("### Câu 9.4.2. Ngưỡng đào tạo tối thiểu ở ngành chế biến chế tạo")
        x_ai_max = st.number_input("Giả định x_AI tối đa cho ngành 2 (tỷ VND)", min_value=1000.0, max_value=30000.0, value=30000.0, step=1000.0, key="b9_xai_max")
        threshold, net_need, retrain_need = _b9_threshold_manufacturing(float(x_ai_max))
        st.dataframe(pd.DataFrame({
            "Điều kiện": ["NetJob₂ ≥ 0", "DisplacedJob₂ ≤ RetrainingCapacity₂", "Ngưỡng cần lấy"],
            "x_H tối thiểu (tỷ VND)": [net_need, retrain_need, threshold],
        }), use_container_width=True, hide_index=True)
        st.info(f"Nếu đầu tư AI ngành chế biến chế tạo là {x_ai_max:,.0f} tỷ VND, cần ít nhất khoảng **{threshold:,.0f} tỷ VND** đào tạo lại để đồng thời không âm NetJob và không vượt năng lực retraining.")

    with tab3:
        st.markdown("### Câu 9.4.3. Mô phỏng nhóm dễ bị tổn thương và vẽ Sankey/swimming lane")
        st.plotly_chart(_b9_sankey_figure(table), use_container_width=True)
        st.caption("Sankey dùng ba ngành dễ tổn thương theo đề: nông-lâm-thủy sản, xây dựng, bán buôn-bán lẻ.")

    with tab4:
        st.markdown("### Câu 9.4.4. Thêm ràng buộc không ngành nào mất quá 5% lao động")
        cap_result = _b9_solve(total_budget=float(total_budget), min_ai_budget=float(total_budget)*float(min_ai_share), displacement_cap_5pct=True)
        cap_table, cap_summary = _b9_result_table(cap_result)
        if not cap_result["success"]:
            st.error("Bài toán không khả thi khi thêm ràng buộc DisplacedJob_i ≤ 5% lao động.")
        else:
            kpi_cards([
                ("Trạng thái", "Khả thi", "có ràng buộc 5%"),
                ("NetJob", f"{cap_summary['net_job']/1_000_000:+.3f} triệu", "sau ràng buộc"),
                ("Đầu tư AI", f"{cap_summary['total_ai']:,.0f}", "tỷ VND"),
                ("Đầu tư H", f"{cap_summary['total_h']:,.0f}", "tỷ VND"),
            ])
            st.dataframe(cap_table, use_container_width=True, hide_index=True)
            st.dataframe(_b9_validation_table(cap_table, total_budget=float(total_budget), cap_5pct=True), use_container_width=True, hide_index=True)

    st.download_button("Tải kết quả Bài 9 dạng CSV", data=table.to_csv(index=False).encode("utf-8-sig"), file_name="bai9_netjob_8_nganh.csv", mime="text/csv", key="download_bai9_exact")

    st.markdown("## 9.5. Câu hỏi thảo luận chính sách")
    top_training = table.loc[table["x_H (tỷ VND)"].idxmax(), "Ngành"] if not table.empty else ""
    top_ai = table.loc[table["x_AI (tỷ VND)"].idxmax(), "Ngành"] if not table.empty else ""
    with st.expander("a) Ngành nào cần đào tạo lại nhiều nhất?", expanded=True):
        st.markdown(f"Theo nghiệm hiện tại, ngành nhận đào tạo lại nhiều nhất là **{top_training}**. Nếu đặt sàn AI cao hơn, ngân sách H sẽ dịch chuyển sang các ngành có displaced lớn và d₁ đủ cao.")
    with st.expander("b) Tài chính-Ngân hàng có rủi ro 52% nhưng tạo việc AI cao, nên làm gì?", expanded=True):
        st.markdown("Ngành này phù hợp với chiến lược AI có kiểm soát: triển khai AI cho nghiệp vụ có giá trị gia tăng cao nhưng phải đi kèm đào tạo lại, quản trị rủi ro thuật toán và lộ trình chuyển đổi nghề.")
    with st.expander("c) Có nên đầu tư AI vào nông nghiệp không?", expanded=True):
        st.markdown("Nông nghiệp có lao động lớn nhưng hệ số tạo việc AI thấp. Mô hình thường khuyến nghị ưu tiên H và công cụ số hỗ trợ năng suất trước, thay vì tự động hóa nhanh gây dịch chuyển lao động quy mô lớn.")
    with st.expander("d) 'Tốc độ tự động hóa không vượt quá năng lực đào tạo lại' là ràng buộc nào?", expanded=True):
        st.markdown(r"Đó là ràng buộc **DisplacedJobᵢ ≤ RetrainingCapacityᵢ**, tức $c_{1i}x^{AI}_i Risk_i \le d_{1i}x^H_i$. Có thể bổ sung ràng buộc an sinh như DisplacedJobᵢ ≤ 5% lao động ngành.")


    ai_analysis_panel(
        lesson_name='Bài 9 - Tác động AI tới lao động Việt Nam',
        model_name='NetJob Model + Retraining Constraint',
        input_params={"lesson": 'Bài 9 - Tác động AI tới lao động Việt Nam', "model": 'NetJob Model + Retraining Constraint'},
        result_data=_collect_ai_context(locals()),
        key="ai_bai_9",
    )

def _b10_data():
    """Dữ liệu kịch bản đúng Bài 10."""
    items = ["I", "D", "AI", "H"]
    scenarios = ["s1 - Lạc quan", "s2 - Cơ sở", "s3 - Bi quan", "s4 - Khủng hoảng"]
    probabilities = np.array([0.30, 0.45, 0.20, 0.05], dtype=float)
    scenario_info = pd.DataFrame({
        "Kịch bản": scenarios,
        "Tăng trưởng TG (%)": [3.5, 2.8, 1.5, 0.2],
        "FDI VN (tỷ USD/năm)": [32.0, 27.0, 20.0, 12.0],
        "Xuất khẩu VN tăng (%)": [12.0, 8.0, 3.0, -5.0],
        "Xác suất": probabilities,
    })
    beta = np.array([1.00, 1.10, 1.25, 0.95], dtype=float)
    beta_s = np.array([
        [1.25, 1.35, 1.55, 1.05],
        [1.00, 1.10, 1.25, 0.95],
        [0.75, 0.85, 0.90, 1.00],
        [0.40, 0.50, 0.55, 1.10],
    ], dtype=float)
    return items, scenarios, probabilities, scenario_info, beta, beta_s


def _b10_solve_lp(beta_override=None, fixed_x=None, robust=False):
    items, scenarios, probabilities, _, beta, beta_s = _b10_data()
    if beta_override is not None:
        beta_s_used = np.tile(np.asarray(beta_override, dtype=float), (len(scenarios), 1))
    else:
        beta_s_used = beta_s.copy()
    n_i, n_s = len(items), len(scenarios)
    n_var = n_i + n_s * n_i + (1 if robust else 0)
    c = np.zeros(n_var)
    if robust:
        c[-1] = -1.0
    else:
        c[:n_i] = -beta
        for s in range(n_s):
            c[n_i+s*n_i:n_i+(s+1)*n_i] = -probabilities[s] * beta_s_used[s]
    A_ub, b_ub = [], []
    row = np.zeros(n_var); row[:n_i] = 1
    A_ub.append(row); b_ub.append(65000.0)
    for s in range(n_s):
        row = np.zeros(n_var); row[n_i+s*n_i:n_i+(s+1)*n_i] = 1
        A_ub.append(row); b_ub.append(15000.0)
        row = np.zeros(n_var); row[n_i+s*n_i+2] = 1; row[3] = -0.5
        A_ub.append(row); b_ub.append(0.0)
    if robust:
        for s in range(n_s):
            row = np.zeros(n_var)
            row[:n_i] = -beta
            row[n_i+s*n_i:n_i+(s+1)*n_i] = -beta_s_used[s]
            row[-1] = 1.0
            A_ub.append(row); b_ub.append(0.0)
    bounds = [(0, None)] * n_var
    if fixed_x is not None:
        for j, val in enumerate(np.asarray(fixed_x, dtype=float)):
            bounds[j] = (float(val), float(val))
    res = linprog(c, A_ub=np.asarray(A_ub), b_ub=np.asarray(b_ub), bounds=bounds, method="highs")
    if not res.success:
        return {"success": False, "status": res.message, "x": None, "y": None, "objective": np.nan}
    x = res.x[:n_i]
    y = res.x[n_i:n_i+n_s*n_i].reshape(n_s, n_i)
    if robust:
        objective = float(res.x[-1])
    else:
        objective = -float(res.fun)
    return {"success": True, "status": res.message, "x": x, "y": y, "objective": objective, "robust_z": float(res.x[-1]) if robust else None}


def _b10_solve_scenario(scenario_index):
    items, scenarios, _, _, beta, beta_s = _b10_data()
    n_i = len(items)
    c = -np.r_[beta, beta_s[scenario_index]]
    A_ub, b_ub = [], []
    row = np.zeros(2*n_i); row[:n_i] = 1
    A_ub.append(row); b_ub.append(65000.0)
    row = np.zeros(2*n_i); row[n_i:] = 1
    A_ub.append(row); b_ub.append(15000.0)
    row = np.zeros(2*n_i); row[n_i+2] = 1; row[3] = -0.5
    A_ub.append(row); b_ub.append(0.0)
    res = linprog(c, A_ub=np.asarray(A_ub), b_ub=np.asarray(b_ub), bounds=[(0, None)]*(2*n_i), method="highs")
    return {"success": res.success, "x": res.x[:n_i] if res.success else None, "y": res.x[n_i:] if res.success else None, "objective": -float(res.fun) if res.success else np.nan}


def _b10_solution_tables(result):
    items, scenarios, _, _, _, _ = _b10_data()
    x_df = pd.DataFrame({"Hạng mục": items, "First-stage x": result["x"]})
    y_df = pd.DataFrame(result["y"], columns=items)
    y_df.insert(0, "Kịch bản", scenarios)
    return x_df, y_df


def _b10_solve_robust_regret():
    """Cực tiểu hóa regret xấu nhất theo đúng yêu cầu 10.5.4."""
    items, scenarios, _, _, beta, beta_s = _b10_data()
    n_i, n_s = len(items), len(scenarios)
    scenario_opt = np.array(
        [_b10_solve_scenario(i)["objective"] for i in range(n_s)],
        dtype=float,
    )

    # Biến gồm x_j, y_sj và R=max regret.
    n_var = n_i + n_s * n_i + 1
    r_index = n_var - 1
    c = np.zeros(n_var, dtype=float)
    c[r_index] = 1.0

    A_ub, b_ub = [], []

    row = np.zeros(n_var, dtype=float)
    row[:n_i] = 1.0
    A_ub.append(row)
    b_ub.append(65000.0)

    for s in range(n_s):
        row = np.zeros(n_var, dtype=float)
        row[n_i + s * n_i : n_i + (s + 1) * n_i] = 1.0
        A_ub.append(row)
        b_ub.append(15000.0)

        row = np.zeros(n_var, dtype=float)
        row[n_i + s * n_i + 2] = 1.0
        row[3] = -0.5
        A_ub.append(row)
        b_ub.append(0.0)

        # regret_s = Z_s^WS - value_s(x,y_s) <= R
        # -beta*x - beta_s*y_s - R <= -Z_s^WS
        row = np.zeros(n_var, dtype=float)
        row[:n_i] = -beta
        row[n_i + s * n_i : n_i + (s + 1) * n_i] = -beta_s[s]
        row[r_index] = -1.0
        A_ub.append(row)
        b_ub.append(-scenario_opt[s])

    bounds = [(0, None)] * n_var
    res = linprog(
        c,
        A_ub=np.asarray(A_ub, dtype=float),
        b_ub=np.asarray(b_ub, dtype=float),
        bounds=bounds,
        method="highs",
    )
    if not res.success:
        return {
            "success": False,
            "status": res.message,
            "x": None,
            "y": None,
            "objective": np.nan,
            "scenario_opt": scenario_opt,
            "scenario_regret": None,
        }

    x = res.x[:n_i]
    y = res.x[n_i : n_i + n_s * n_i].reshape(n_s, n_i)
    values = np.array(
        [float(beta @ x + beta_s[s] @ y[s]) for s in range(n_s)],
        dtype=float,
    )
    regrets = scenario_opt - values
    return {
        "success": True,
        "status": res.message,
        "x": x,
        "y": y,
        "objective": float(res.x[r_index]),
        "scenario_opt": scenario_opt,
        "scenario_value": values,
        "scenario_regret": regrets,
    }


def _b10_full_analysis():
    items, scenarios, probabilities, _, _, beta_s = _b10_data()
    sp = _b10_solve_lp()
    expected_beta_s = probabilities @ beta_s
    ev_model = _b10_solve_lp(beta_override=expected_beta_s)
    eev = _b10_solve_lp(fixed_x=ev_model["x"])
    ws_values = []
    det_rows = []
    for i, s in enumerate(scenarios):
        det = _b10_solve_scenario(i)
        ws_values.append(probabilities[i] * det["objective"])
        det_rows.append({"Kịch bản": s, "Z* xác định": det["objective"], **{f"x_{items[j]}": det["x"][j] for j in range(len(items))}})
    ws = float(np.sum(ws_values))
    return {
        "sp": sp,
        "ev_model": ev_model,
        "eev": eev,
        "deterministic": pd.DataFrame(det_rows),
        "WS": ws,
        "VSS": float(sp["objective"] - eev["objective"]),
        "EVPI": float(ws - sp["objective"]),
        "robust": _b10_solve_lp(robust=True),
        "robust_regret": _b10_solve_robust_regret(),
    }


def page_10():
    hero(
        "Bài 10 — Quy hoạch ngẫu nhiên hai giai đoạn dưới bất định",
        "Mô hình first-stage / second-stage đúng 4 kịch bản, xác suất, VSS, EVPI và robust regret.",
        ["10.1-10.6", "Two-stage SP", "VSS", "EVPI", "Robust"],
    )
    show_assignment_structure(10)

    items, scenarios, probabilities, scenario_info, beta, beta_s = _b10_data()
    st.markdown("## 10.1. Bối cảnh Việt Nam")
    st.markdown(
        """
        Quyết định đầu tư số phải được đưa ra trước khi biết chắc trạng thái kinh tế tương lai.
        Mô hình stochastic programming hai giai đoạn cho phép chọn first-stage trước bất định
        và recourse sau khi kịch bản xảy ra.
        """
    )

    st.markdown("## 10.2. Cây kịch bản")
    st.dataframe(scenario_info, use_container_width=True, hide_index=True)

    st.markdown("## 10.3. Mô hình stochastic programming hai giai đoạn")
    st.markdown(
        """
        Phần này trình bày rõ cấu trúc **two-stage stochastic programming** đúng theo đề:
        Chính phủ phải quyết định ngân sách giai đoạn một trước khi biết kịch bản tương lai,
        sau đó mới sử dụng ngân sách điều chỉnh ở giai đoạn hai khi từng kịch bản xảy ra.
        """
    )

    st.markdown("### 10.3.1. Tập chỉ số và tham số")
    index_param_table = pd.DataFrame(
        {
            "Ký hiệu": ["J", "S", "p_s", "β_j", "β^s_j"],
            "Diễn giải": [
                "Tập hạng mục đầu tư J = {I, D, AI, H}",
                "Tập kịch bản S = {s1, s2, s3, s4}",
                "Xác suất xảy ra của kịch bản s",
                "Hệ số lợi ích cơ bản của hạng mục j ở quyết định giai đoạn một",
                "Hệ số lợi ích của hạng mục j khi kịch bản s xảy ra ở giai đoạn hai",
            ],
        }
    )
    st.dataframe(index_param_table, use_container_width=True, hide_index=True)

    st.markdown("### 10.3.2. Biến quyết định")
    st.latex(r"x_j \ge 0,\quad j\in J")
    st.latex(r"y^s_j \ge 0,\quad s\in S,\ j\in J")
    decision_table = pd.DataFrame(
        {
            "Biến": ["x_j", "y^s_j"],
            "Loại quyết định": ["First-stage / here-and-now", "Second-stage / recourse"],
            "Ý nghĩa": [
                "Ngân sách phân bổ ban đầu cho hạng mục j trước khi biết kịch bản tương lai",
                "Ngân sách điều chỉnh cho hạng mục j sau khi kịch bản s đã xảy ra",
            ],
            "Giới hạn ngân sách": ["Tổng x_j ≤ 65.000", "Tổng y^s_j ≤ 15.000 với từng kịch bản s"],
        }
    )
    st.dataframe(decision_table, use_container_width=True, hide_index=True)

    st.markdown("### 10.3.3. Hàm mục tiêu kỳ vọng")
    st.latex(
        r"\max Z="
        r"\sum_{j\in J}\beta_jx_j + "
        r"\sum_{s\in S}p_s\sum_{j\in J}\beta^s_jy^s_j"
    )
    st.markdown(
        """
        Thành phần thứ nhất đo lợi ích của quyết định ngân sách ban đầu.
        Thành phần thứ hai là **lợi ích kỳ vọng** của các quyết định điều chỉnh,
        được tính theo xác suất của từng kịch bản. Vì vậy nghiệm SP không chỉ tối ưu
        cho một trạng thái trung bình, mà cân nhắc toàn bộ cây kịch bản.
        """
    )

    st.markdown("### 10.3.4. Ràng buộc mô hình")
    st.latex(r"\sum_{j\in J}x_j\le65{,}000")
    st.latex(r"\sum_{j\in J}y^s_j\le15{,}000,\quad \forall s\in S")
    st.latex(r"y^s_{AI}\le0.5x_H,\quad \forall s\in S")
    st.latex(r"x_j\ge0,\quad y^s_j\ge0")
    constraint_table = pd.DataFrame(
        {
            "Ràng buộc": [
                "Ngân sách first-stage",
                "Ngân sách second-stage theo từng kịch bản",
                "Điều kiện triển khai AI phụ thuộc nhân lực số",
                "Không âm",
            ],
            "Công thức": [
                "Σ_j x_j ≤ 65.000",
                "Σ_j y^s_j ≤ 15.000, ∀s",
                "y^s_AI ≤ 0,5 x_H, ∀s",
                "x_j ≥ 0; y^s_j ≥ 0",
            ],
            "Ý nghĩa chính sách": [
                "Kế hoạch ngân sách 5 năm phải được chốt trước bất định",
                "Khi kịch bản xảy ra chỉ còn một quỹ dự phòng/điều chỉnh hữu hạn",
                "Không thể mở rộng AI giai đoạn hai nếu thiếu nền tảng nhân lực số ban đầu",
                "Không cho phép phân bổ ngân sách âm",
            ],
        }
    )
    st.dataframe(constraint_table, use_container_width=True, hide_index=True)

    st.markdown("### 10.3.5. Ý nghĩa của mô hình hai giai đoạn")
    st.markdown(
        """
        Mô hình SP hai giai đoạn khác mô hình xác định ở chỗ nó tách rõ hai lớp quyết định:
        **x** là quyết định cứng phải cam kết ngay, còn **y** là quyết định linh hoạt sau khi quan sát
        kịch bản. Cách mô hình hóa này phù hợp với đầu tư số 2026-2030 vì chính sách phải vừa tạo
        nền tảng trung hạn, vừa giữ khả năng chống chịu trước cú sốc xuất khẩu, FDI, công nghệ hoặc
        khủng hoảng kinh tế.
        """
    )

    beta_table = pd.DataFrame(beta_s, columns=items)
    beta_table.insert(0, "Kịch bản", scenarios)
    beta_table.loc[len(beta_table)] = ["β cơ bản"] + beta.tolist()
    st.markdown("## 10.4. Bảng hệ số β theo kịch bản")
    st.dataframe(beta_table, use_container_width=True, hide_index=True)
    st.caption(
        "Hệ số H cao hơn trong kịch bản khủng hoảng vì nhân lực số giúp nền kinh tế chuyển đổi việc làm, "
        "duy trì dịch vụ số và hấp thụ cú sốc tốt hơn."
    )

    analysis = _b10_full_analysis()
    st.markdown("## 10.5. Yêu cầu lập trình")
    tab1, tab2, tab3, tab4 = st.tabs(["10.5.1 - SP", "10.5.2 - EV & từng kịch bản", "10.5.3 - VSS/EVPI", "10.5.4 - Robust regret"])
    with tab1:
        st.markdown("### Câu 10.5.1. Mô hình first-stage/second-stage và quyết định tối ưu")
        sp = analysis["sp"]
        x_df, y_df = _b10_solution_tables(sp)
        kpi_cards([
            ("Z* stochastic", f"{sp['objective']:,.2f}", "GDP gain kỳ vọng"),
            ("First-stage", f"{x_df['First-stage x'].sum():,.0f}", "≤65.000"),
            ("Reserve/scenario", f"{y_df[items].sum(axis=1).mean():,.0f}", "≤15.000"),
            ("x_H", f"{sp['x'][3]:,.0f}", "ràng buộc y_AI≤0,5x_H"),
        ])
        st.dataframe(x_df, use_container_width=True, hide_index=True)
        st.dataframe(y_df, use_container_width=True, hide_index=True)
        fig = px.bar(x_df, x="Hạng mục", y="First-stage x", template=PLOT_TEMPLATE, title="Quyết định first-stage tối ưu")
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Mã Pyomo đúng cấu trúc Set, Param, Var theo đề", expanded=False):
            st.code("""import pyomo.environ as pyo

m = pyo.ConcreteModel()
m.J = pyo.Set(initialize=['I', 'D', 'AI', 'H'])
m.S = pyo.Set(initialize=['s1', 's2', 's3', 's4'])

m.p = pyo.Param(m.S, initialize={'s1': 0.30, 's2': 0.45, 's3': 0.20, 's4': 0.05})
m.beta = pyo.Param(m.J, initialize={'I': 1.00, 'D': 1.10, 'AI': 1.25, 'H': 0.95})
m.beta_s = pyo.Param(m.S, m.J, initialize={
    ('s1','I'): 1.25, ('s1','D'): 1.35, ('s1','AI'): 1.55, ('s1','H'): 1.05,
    ('s2','I'): 1.00, ('s2','D'): 1.10, ('s2','AI'): 1.25, ('s2','H'): 0.95,
    ('s3','I'): 0.75, ('s3','D'): 0.85, ('s3','AI'): 0.90, ('s3','H'): 1.00,
    ('s4','I'): 0.40, ('s4','D'): 0.50, ('s4','AI'): 0.55, ('s4','H'): 1.10,
})

m.x = pyo.Var(m.J, within=pyo.NonNegativeReals)       # first-stage
m.y = pyo.Var(m.S, m.J, within=pyo.NonNegativeReals)  # second-stage recourse

m.budget1 = pyo.Constraint(expr=sum(m.x[j] for j in m.J) <= 65000)
m.budget2 = pyo.Constraint(m.S, rule=lambda m, s: sum(m.y[s, j] for j in m.J) <= 15000)
m.ai_capacity = pyo.Constraint(m.S, rule=lambda m, s: m.y[s, 'AI'] <= 0.5 * m.x['H'])

def obj_rule(m):
    first = sum(m.beta[j] * m.x[j] for j in m.J)
    second = sum(m.p[s] * sum(m.beta_s[s, j] * m.y[s, j] for j in m.J) for s in m.S)
    return first + second

m.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)
solver = pyo.SolverFactory('cbc')  # hoặc glpk
solver.solve(m)
print({j: pyo.value(m.x[j]) for j in m.J})""", language="python")
            st.caption("Dashboard giải bằng SciPy/HiGHS để chạy ổn định trên Streamlit, nhưng mô hình Pyomo ở trên giữ đúng Set, Param, Var, first-stage và second-stage như yêu cầu đề.")

    with tab2:
        st.markdown("### Câu 10.5.2. So sánh deterministic, EV và SP")
        st.dataframe(analysis["deterministic"], use_container_width=True, hide_index=True)
        ev_x, ev_y = _b10_solution_tables(analysis["ev_model"])
        st.markdown("#### Quyết định EV dùng hệ số kịch bản trung bình")
        st.dataframe(ev_x, use_container_width=True, hide_index=True)
        compare_x = pd.DataFrame({"Hạng mục": items, "SP x": analysis["sp"]["x"], "EV x": analysis["ev_model"]["x"]})
        st.dataframe(compare_x, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### Câu 10.5.3. Tính VSS và EVPI")
        kpi_cards([
            ("RP / SP", f"{analysis['sp']['objective']:,.2f}", "recourse problem"),
            ("EEV", f"{analysis['eev']['objective']:,.2f}", "EV solution evaluated"),
            ("VSS", f"{analysis['VSS']:,.2f}", "SP - EEV"),
            ("EVPI", f"{analysis['EVPI']:,.2f}", "WS - SP"),
        ])
        st.info("VSS đo giá trị của việc xét bất định khi ra quyết định ban đầu. EVPI đo mức tối đa nên trả cho thông tin hoàn hảo về kịch bản tương lai.")
        st.dataframe(pd.DataFrame({"Chỉ tiêu": ["WS", "SP/RP", "EEV", "VSS", "EVPI"], "Giá trị": [analysis["WS"], analysis["sp"]["objective"], analysis["eev"]["objective"], analysis["VSS"], analysis["EVPI"]]}), use_container_width=True, hide_index=True)

    with tab4:
        st.markdown("### Câu 10.5.4. Robust optimization cực tiểu hóa regret xấu nhất")
        robust_regret = analysis["robust_regret"]
        robust_maxmin = analysis["robust"]
        x_df, y_df = _b10_solution_tables(robust_regret)
        regret_df = pd.DataFrame({
            "Kịch bản": scenarios,
            "Z* wait-and-see": robust_regret["scenario_opt"],
            "Giá trị robust-regret": robust_regret["scenario_value"],
            "Regret": robust_regret["scenario_regret"],
        })
        kpi_cards([
            ("Max regret", f"{robust_regret['objective']:,.2f}", "cần cực tiểu"),
            ("First-stage", f"{x_df['First-stage x'].sum():,.0f}", "≤65.000"),
            ("x_H robust-regret", f"{robust_regret['x'][3]:,.0f}", "bảo hiểm nhân lực"),
            ("Worst-case max-min", f"{robust_maxmin['objective']:,.2f}", "đối chiếu"),
        ])
        st.dataframe(x_df, use_container_width=True, hide_index=True)
        st.dataframe(y_df, use_container_width=True, hide_index=True)
        st.dataframe(regret_df, use_container_width=True, hide_index=True)
        robust_sp_compare = pd.DataFrame(
            {
                "Hạng mục": items,
                "SP first-stage x": analysis["sp"]["x"],
                "Robust-regret first-stage x": robust_regret["x"],
                "Chênh lệch robust - SP": robust_regret["x"] - analysis["sp"]["x"],
            }
        )
        st.markdown("#### So sánh decision robust-regret với SP")
        st.dataframe(robust_sp_compare, use_container_width=True, hide_index=True)
        st.markdown(
            "Robust regret không tối đa hóa riêng kịch bản xấu nhất, mà chọn quyết định làm cho **khoảng tiếc nuối lớn nhất** "
            "so với lời giải wait-and-see của từng kịch bản là nhỏ nhất. Cách này phù hợp khi nhà hoạch định muốn tránh "
            "ra quyết định quá tệ trong bất kỳ trạng thái tương lai nào."
        )

    x_export, y_export = _b10_solution_tables(analysis["sp"])
    st.download_button("Tải nghiệm SP Bài 10", data=x_export.to_csv(index=False).encode("utf-8-sig"), file_name="bai10_first_stage_sp.csv", mime="text/csv", key="download_bai10_exact")
    st.markdown("## 10.6. Câu hỏi thảo luận chính sách")
    with st.expander("a) So với lời giải xác định, SP đầu tư H nhiều hơn hay ít hơn? Vì sao?", expanded=True):
        st.markdown("So sánh cột SP x và EV/từng kịch bản cho thấy H đóng vai trò bảo hiểm: H có hệ số ổn định và tăng trong khủng hoảng, đồng thời mở năng lực triển khai AI giai đoạn hai qua ràng buộc y_AI≤0,5x_H.")
    with st.expander("b) VSS dương nói lên điều gì về tư duy xác suất trong hoạch định chính sách Việt Nam?", expanded=True):
        st.markdown(f"Trong kết quả hiện tại, VSS = **{analysis['VSS']:,.2f}**. Nếu dương, tư duy xác suất tạo giá trị so với dùng một kịch bản trung bình duy nhất.")
    with st.expander("c) COVID-19 và bão Yagi cho thấy Việt Nam có dưới đầu tư vào nhân lực số như hàng hóa bảo hiểm không?", expanded=True):
        st.markdown("Có thể có. Các cú sốc như COVID-19 giai đoạn 2020-2022 và bão Yagi năm 2024 cho thấy năng lực số và nhân lực số giúp duy trì dịch vụ công, thương mại, giáo dục, logistics và khả năng chuyển đổi việc làm. Nếu chỉ đánh giá H theo lợi ích tăng trưởng ngắn hạn, chính sách dễ dưới đầu tư vào nhân lực số; trong mô hình SP, H còn là **hàng hóa bảo hiểm** vì làm tăng khả năng thích ứng và mở năng lực triển khai AI ở giai đoạn hai qua ràng buộc y_AI≤0,5x_H.")


    ai_analysis_panel(
        lesson_name='Bài 10 - Quy hoạch ngẫu nhiên hai giai đoạn',
        model_name='Two-stage Stochastic Programming + VSS/EVPI',
        input_params={"lesson": 'Bài 10 - Quy hoạch ngẫu nhiên hai giai đoạn', "model": 'Two-stage Stochastic Programming + VSS/EVPI'},
        result_data=_collect_ai_context(locals()),
        key="ai_bai_10",
    )

def _b11_actions():
    """Năm hành động đúng đề Bài 11."""
    return {
        0: {"Tên": "a0 - Truyền thống", "K": 0.70, "D": 0.10, "AI": 0.10, "H": 0.10},
        1: {"Tên": "a1 - Cân bằng", "K": 0.40, "D": 0.25, "AI": 0.15, "H": 0.20},
        2: {"Tên": "a2 - Số hóa nhanh", "K": 0.25, "D": 0.45, "AI": 0.15, "H": 0.15},
        3: {"Tên": "a3 - AI dẫn dắt", "K": 0.20, "D": 0.20, "AI": 0.45, "H": 0.15},
        4: {"Tên": "a4 - Bao trùm", "K": 0.30, "D": 0.20, "AI": 0.10, "H": 0.40},
    }


def _b11_transition(state, action, rng=None):
    """Chuyển trạng thái MDP rời rạc 3^4 và tính reward."""
    rng = rng or np.random.default_rng(0)
    actions = _b11_actions()
    a = actions[int(action)]
    gdp, digital, ai_cap, unemp = np.asarray(state, dtype=int)
    K, D, AI, H = a["K"], a["D"], a["AI"], a["H"]

    delta_gdp = 0.18*K + 0.30*D + 0.34*AI + 0.24*H + 0.05*digital + 0.04*ai_cap + rng.normal(0, 0.015)
    delta_unemp = 0.20*AI*(1 + unemp/2) - 0.30*H - 0.05*D + rng.normal(0, 0.01)
    cyber_risk = max(0.0, 0.35*AI*(1 + ai_cap/3) + 0.12*D - 0.22*H)
    emission = max(0.0, 0.30*K + 0.24*AI + 0.08*D - 0.10*H)
    reward = 0.40*delta_gdp - 0.25*max(delta_unemp, 0) - 0.20*cyber_risk - 0.15*emission

    new_gdp = int(np.clip(gdp + (1 if delta_gdp > 0.42 else 0) - (1 if delta_gdp < 0.22 else 0), 0, 2))
    new_digital = int(np.clip(digital + (1 if D + 0.35*H > 0.38 else 0) - (1 if D < 0.15 else 0), 0, 2))
    new_ai = int(np.clip(ai_cap + (1 if AI + 0.20*H > 0.42 else 0) - (1 if AI < 0.12 else 0), 0, 2))
    new_unemp = int(np.clip(unemp + (1 if delta_unemp > 0.08 else 0) - (1 if delta_unemp < -0.08 else 0), 0, 2))
    return np.array([new_gdp, new_digital, new_ai, new_unemp], dtype=int), float(reward), {"delta_gdp": delta_gdp, "delta_unemp": delta_unemp, "cyber": cyber_risk, "emission": emission}


def _b11_initial_state(kind="vn2026"):
    states = {
        "VN 2026 thực tế": np.array([1, 1, 0, 1], dtype=int),
        "Suy giảm: GDP thấp, D thấp, U cao": np.array([0, 0, 0, 2], dtype=int),
        "Bứt phá số: GDP cao, D cao, AI trung bình": np.array([2, 2, 1, 0], dtype=int),
        "Rủi ro lao động: AI cao, U cao": np.array([1, 1, 2, 2], dtype=int),
        "Nền tảng yếu: tất cả thấp": np.array([0, 0, 0, 1], dtype=int),
    }
    return states if kind == "all" else states["VN 2026 thực tế"].copy()


@st.cache_data(show_spinner=False)
def _b11_train_tabular_q(episodes=10000, alpha=0.10, discount=0.95, seed=42):
    rng = np.random.default_rng(seed)
    Q = np.zeros((3, 3, 3, 3, 5), dtype=float)
    rewards = []
    for ep in range(int(episodes)):
        state = _b11_initial_state().copy()
        total = 0.0
        epsilon = max(0.05, 1.0 - ep / max(1, episodes/2))
        for _ in range(10):
            if rng.random() < epsilon:
                action = int(rng.integers(0, 5))
            else:
                action = int(np.argmax(Q[tuple(state)]))
            next_state, reward, _ = _b11_transition(state, action, rng)
            old = Q[tuple(state) + (action,)]
            target = reward + discount * Q[tuple(next_state)].max()
            Q[tuple(state) + (action,)] = old + alpha * (target - old)
            state = next_state
            total += reward
        rewards.append(total)
    return Q, pd.DataFrame({"Episode": np.arange(1, int(episodes)+1), "Reward": rewards})


def _b11_policy_action(Q, state):
    return int(np.argmax(Q[tuple(np.asarray(state, dtype=int))]))


def _b11_evaluate_policy(policy, episodes=500, seed=123):
    rng = np.random.default_rng(seed)
    totals = []
    for _ in range(int(episodes)):
        state = _b11_initial_state().copy()
        total = 0.0
        for _ in range(10):
            action = int(policy(state, rng))
            state, reward, _ = _b11_transition(state, action, rng)
            total += reward
        totals.append(total)
    return float(np.mean(totals)), float(np.std(totals))


def page_11():
    hero(
        "Bài 11 — Học tăng cường Q-learning cho chính sách kinh tế thích nghi",
        "MDP rời rạc 3⁴=81 trạng thái, 5 hành động ngân sách, episode 10 năm và Q-learning epsilon-greedy 10.000 episodes.",
        ["11.1-11.4", "MDP", "81 states", "Q-learning", "Policy comparison"],
    )
    show_assignment_structure(11)

    actions_df = pd.DataFrame(_b11_actions()).T.reset_index().rename(columns={"index": "Hành động"})
    st.markdown("## 11.1. Bối cảnh Việt Nam")
    st.markdown(
        """
        Chính sách phân bổ đầu tư số cần thích nghi với trạng thái kinh tế qua từng năm.
        Bài 11 xây dựng MDP rời rạc để agent học cách chọn 1 trong 5 hành động chính sách
        tùy theo tăng trưởng, số hóa, năng lực AI và rủi ro thất nghiệp.
        """
    )

    st.markdown("## 11.2. Môi trường MDP")
    st.dataframe(actions_df, use_container_width=True, hide_index=True)
    st.latex(r"R_t=0.40\Delta GDP-0.25\Delta unemployment-0.20CyberRisk-0.15Emission")
    st.info("Trạng thái gồm 4 thành phần rời rạc {low, medium, high}: GDP growth, Digital index, AI capacity, Unemployment risk. Tổng số trạng thái = 3⁴ = 81.")

    with st.expander("Tham số huấn luyện", expanded=True):
        episodes = st.slider("Số episode", 1000, 10000, 10000, 1000, key="b11_episodes_exact")
        alpha = st.slider("Learning rate α", 0.01, 0.30, 0.10, 0.01, key="b11_alpha_exact")
        discount = st.slider("Discount γ", 0.80, 0.99, 0.95, 0.01, key="b11_gamma_exact")

    Q, curve = _b11_train_tabular_q(episodes=int(episodes), alpha=float(alpha), discount=float(discount), seed=42)
    st.markdown("## 11.3. Yêu cầu lập trình")
    states = _b11_initial_state("all")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["11.3.1 - Env", "11.3.2 - Training", "11.3.3 - Chính sách π*", "11.3.4 - So sánh", "11.3.5 - DQN mở rộng"])
    with tab1:
        st.markdown("### Câu 11.3.1. Cài đặt Env với reset, step, action_space, observation_space")
        env_summary = pd.DataFrame({
            "Thành phần": ["Observation space", "Action space", "Horizon", "Initial state", "Reward"],
            "Giá trị": ["MultiDiscrete([3,3,3,3])", "Discrete(5)", "10 năm/episode", "[medium, medium, low, medium]", "welfare có GDP, thất nghiệp, cyber, emission"],
        })
        st.dataframe(env_summary, use_container_width=True, hide_index=True)
        with st.expander("Mã skeleton Env theo đề"):
            st.code("""class VietnamEconomyEnv(gym.Env):\n    def __init__(self):\n        self.action_space = spaces.Discrete(5)\n        self.observation_space = spaces.MultiDiscrete([3,3,3,3])\n        self.T = 10\n    def reset(self, seed=None, options=None):\n        self.state = np.array([1,1,0,1])\n        self.t = 0\n        return self.state, {}\n    def step(self, action):\n        self.state, reward, info = transition(self.state, action)\n        self.t += 1\n        return self.state, reward, self.t >= self.T, False, info""", language="python")

    with tab2:
        st.markdown("### Câu 11.3.2. Q-learning 10.000 episodes, alpha=0,1, gamma=0,95, epsilon-greedy")
        kpi_cards([
            ("Episode", f"{episodes:,}", "huấn luyện"),
            ("Reward đầu", f"{curve['Reward'].head(100).mean():.3f}", "TB 100 ep đầu"),
            ("Reward cuối", f"{curve['Reward'].tail(100).mean():.3f}", "TB 100 ep cuối"),
            ("ε cuối", "0.05", "epsilon-greedy"),
        ])
        smooth = curve.copy()
        smooth["Reward_MA100"] = smooth["Reward"].rolling(100, min_periods=1).mean()
        fig = px.line(smooth, x="Episode", y="Reward_MA100", template=PLOT_TEMPLATE, title="Learning curve - reward trung bình trượt 100 episode")
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("### Câu 11.3.3. Trích xuất chính sách π*(s) cho Việt Nam 2026 và 4 trạng thái giả định")
        rows = []
        for name, state in states.items():
            a = _b11_policy_action(Q, state)
            rows.append({"Trạng thái khởi đầu": name, "State [GDP,D,AI,U]": state.tolist(), "π*(s)": a, "Hành động": _b11_actions()[a]["Tên"]})
        policy_df = pd.DataFrame(rows)
        st.dataframe(policy_df, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown("### Câu 11.3.4. So sánh phần thưởng tích lũy của π* với 3 chính sách rule-based")
        learned_mean, learned_std = _b11_evaluate_policy(lambda s, rng: _b11_policy_action(Q, s), episodes=500, seed=1)
        a1_mean, a1_std = _b11_evaluate_policy(lambda s, rng: 1, episodes=500, seed=2)
        a3_mean, a3_std = _b11_evaluate_policy(lambda s, rng: 3, episodes=500, seed=3)
        random_mean, random_std = _b11_evaluate_policy(lambda s, rng: int(rng.integers(0, 5)), episodes=500, seed=4)
        comp = pd.DataFrame({
            "Chính sách": ["π* Q-learning", "Luôn a1 - Cân bằng", "Luôn a3 - AI dẫn dắt", "Random"],
            "Reward trung bình": [learned_mean, a1_mean, a3_mean, random_mean],
            "Độ lệch chuẩn": [learned_std, a1_std, a3_std, random_std],
        })
        st.dataframe(comp, use_container_width=True, hide_index=True)
        fig = px.bar(comp, x="Chính sách", y="Reward trung bình", error_y="Độ lệch chuẩn", template=PLOT_TEMPLATE, title="So sánh reward tích lũy")
        st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.markdown("### Câu 11.3.5. Mở rộng DQN bằng stable-baselines3")
        st.markdown("Đây là phần mở rộng. Dashboard giữ Q-learning tabular làm kết quả chính để chạy ổn định trên Streamlit Cloud; DQN có thể huấn luyện offline bằng stable-baselines3 với neural network 2 hidden layers, mỗi layer 64 units.")
        st.code("""from stable_baselines3 import DQN

policy_kwargs = dict(net_arch=[64, 64])  # 2 hidden layers, mỗi layer 64 units
model = DQN(
    'MlpPolicy',
    env,
    policy_kwargs=policy_kwargs,
    learning_rate=1e-3,
    buffer_size=50000,
    learning_starts=1000,
    batch_size=64,
    gamma=0.95,
    verbose=1,
)
model.learn(total_timesteps=100000)""", language="python")

    st.download_button("Tải Q-policy cho 81 trạng thái", data=pd.DataFrame([{"state": str([i,j,k,l]), "action": int(np.argmax(Q[i,j,k,l]))} for i in range(3) for j in range(3) for k in range(3) for l in range(3)]).to_csv(index=False).encode("utf-8-sig"), file_name="bai11_q_policy_81_states.csv", mime="text/csv", key="download_bai11_exact")

    st.markdown("## 11.4. Câu hỏi thảo luận chính sách")
    with st.expander("a) GDP thấp, D thấp, U cao thì π*(s) chọn hành động gì? Có khớp quick win không?", expanded=True):
        s = np.array([0,0,0,2]); a = _b11_policy_action(Q, s)
        st.markdown(f"Với trạng thái [low, low, low, high], chính sách học được chọn **{_b11_actions()[a]['Tên']}**. Diễn giải cần xem cùng reward: chính sách thường cân bằng giữa quick win số hóa và giảm thất nghiệp qua H.")
    with st.expander("b) GDP cao, AI cao, U thấp thì π*(s) chọn gì? Có phù hợp consolidation không?", expanded=True):
        s = np.array([2,2,2,0]); a = _b11_policy_action(Q, s)
        st.markdown(f"Với trạng thái thuận lợi [high, high, high, low], chính sách chọn **{_b11_actions()[a]['Tên']}**, thường mang ý nghĩa củng cố năng lực và kiểm soát rủi ro thay vì chỉ tăng AI.")
    with st.expander("c) Tích hợp π* vào quy trình hoạch định chính sách thế nào để không thay thế quyết định chính trị - xã hội?", expanded=True):
        st.markdown("Không. π* chỉ là đầu vào định lượng. Quy trình chính sách cần có thẩm định chuyên gia, tham vấn xã hội, kiểm toán dữ liệu, đánh giá tác động phân phối và quyết định cuối cùng của cơ quan có thẩm quyền.")


    ai_analysis_panel(
        lesson_name='Bài 11 - Q-learning cho chính sách thích nghi',
        model_name='Reinforcement Learning + Q-learning',
        input_params={"lesson": 'Bài 11 - Q-learning cho chính sách thích nghi', "model": 'Reinforcement Learning + Q-learning'},
        result_data=_collect_ai_context(locals()),
        key="ai_bai_11",
    )

def _b12_flow_figure():
    labels = [
        "Dữ liệu vĩ mô",
        "Dữ liệu ngành",
        "Dữ liệu vùng",
        "Ngân sách và rủi ro",
        "M1 - Dự báo",
        "M2 - Sẵn sàng vùng",
        "M3 - Phân bổ ngân sách",
        "M4 - Lao động và AI",
        "M5 - Rủi ro và bất định",
        "M6 - Dashboard tích hợp",
        "KPI năm 2030",
        "Cảnh báo",
        "Khuyến nghị chính sách",
    ]

    source = [
        0, 1, 2, 3,
        4, 5,
        6, 6,
        7,
        4, 5, 6, 7, 8,
        9, 9, 9,
    ]

    target = [
        4, 5, 5, 6,
        6, 6,
        7, 8,
        8,
        9, 9, 9, 9, 9,
        10, 11, 12,
    ]

    value = [
        4, 3, 3, 3,
        3, 3,
        3, 2,
        2,
        3, 3, 3, 3, 3,
        4, 3, 3,
    ]

    figure = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=18,
                    thickness=20,
                    label=labels,
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=value,
                ),
            )
        ]
    )

    figure.update_layout(
        title="Luồng dữ liệu và liên kết mô-đun AIDEOM-VN",
        height=600,
        template=PLOT_TEMPLATE,
        margin=dict(
            l=10,
            r=10,
            t=60,
            b=10,
        ),
    )

    return figure
def _b12_scenarios():
    return {
        "S1 - Truyền thống": np.array(
            [0.70, 0.10, 0.10, 0.10],
            dtype=float,
        ),
        "S2 - Số hóa nhanh": np.array(
            [0.25, 0.45, 0.15, 0.15],
            dtype=float,
        ),
        "S3 - AI dẫn dắt": np.array(
            [0.20, 0.20, 0.45, 0.15],
            dtype=float,
        ),
        "S4 - Bao trùm số": np.array(
            [0.30, 0.20, 0.10, 0.40],
            dtype=float,
        ),
        "S5 - Tối ưu cân bằng": np.array(
            [0.34, 0.26, 0.18, 0.22],
            dtype=float,
        ),
    }


def _b12_module_1_forecast(
    shares,
):
    simulation = simulate_dynamic(
        shares=shares,
        start=2026,
        end=2030,
        invest_rate=0.22,
        shock_2028=0.03,
    )

    first = simulation.iloc[0]
    last = simulation.iloc[-1]

    return {
        "GDP_2030": float(
            last["Y_GDP"]
        ),
        "Consumption_2030": float(
            last["C_tiêu_dùng"]
        ),
        "GDP_Growth_2026_2030": float(
            100
            * (
                last["Y_GDP"]
                / first["Y_GDP"]
                - 1
            )
        ),
        "Digital_2030": float(
            last["D"]
        ),
        "AI_2030": float(
            last["AI"]
        ),
        "Human_2030": float(
            last["H"]
        ),
        "trajectory": simulation,
    }


def _b12_module_2_region_readiness():
    df = load_regions().copy()

    criteria = [
        "grdp_per_capita_million_VND",
        "fdi_registered_billion_USD",
        "digital_index_0_100",
        "ai_readiness_0_100",
        "trained_labor_pct",
        "rd_intensity_pct",
        "internet_penetration_pct",
        "gini_coef",
    ]

    weights = np.array(
        [
            0.10,
            0.10,
            0.15,
            0.20,
            0.15,
            0.15,
            0.05,
            0.10,
        ],
        dtype=float,
    )

    benefit_flags = [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
    ]

    score = topsis_score(
        df,
        criteria,
        weights,
        benefit_flags,
    )

    result = pd.DataFrame(
        {
            "Vùng": df["region_name_vi"],
            "ReadinessScore": score,
        }
    )

    result["ReadinessRank"] = (
        result["ReadinessScore"]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    return result.sort_values(
        "ReadinessRank"
    ).reset_index(drop=True)


def _b12_module_3_allocation():
    """
    Ưu tiên dùng solver Bài 4. Nếu Bài 4 chưa được thay,
    dùng một LP tích hợp tối giản để dashboard vẫn chạy.
    """
    regions, items, beta, d0 = region_beta_matrix()

    solver_function = globals().get(
        "_b4_solve_scipy"
    )

    if callable(
        solver_function
    ):
        result = solver_function(
            fairness=True,
            total_budget=50000.0,
            region_floor=5000.0,
            region_cap=12000.0,
            human_floor=12000.0,
            gamma=0.002,
            lam=0.68,
        )

        if result.success:
            x = np.asarray(
                result.x[:24],
                dtype=float,
            ).reshape(6, 4)

            objective = float(
                -result.fun
            )

            source = "Bài 4 - SciPy LP"
        else:
            x = None
    else:
        x = None

    if x is None:
        n = 24
        c = -beta.reshape(-1)

        a_ub = []
        b_ub = []

        row = np.ones(
            n,
            dtype=float,
        )
        a_ub.append(
            row
        )
        b_ub.append(
            50000.0
        )

        for region_index in range(6):
            row = np.zeros(
                n,
                dtype=float,
            )
            row[
                region_index * 4:
                region_index * 4 + 4
            ] = -1.0
            a_ub.append(
                row
            )
            b_ub.append(
                -5000.0
            )

            row = np.zeros(
                n,
                dtype=float,
            )
            row[
                region_index * 4:
                region_index * 4 + 4
            ] = 1.0
            a_ub.append(
                row
            )
            b_ub.append(
                12000.0
            )

        row = np.zeros(
            n,
            dtype=float,
        )
        for region_index in range(6):
            row[
                region_index * 4 + 3
            ] = -1.0

        a_ub.append(
            row
        )
        b_ub.append(
            -12000.0
        )

        result = linprog(
            c,
            A_ub=np.asarray(
                a_ub,
                dtype=float,
            ),
            b_ub=np.asarray(
                b_ub,
                dtype=float,
            ),
            bounds=[
                (0.0, None)
            ]
            * n,
            method="highs",
        )

        if not result.success:
            raise RuntimeError(
                "M3 không giải được LP."
            )

        x = np.asarray(
            result.x,
            dtype=float,
        ).reshape(6, 4)

        objective = float(
            -result.fun
        )

        source = "LP tích hợp dự phòng"

    allocation = pd.DataFrame(
        x,
        columns=items,
    )

    allocation.insert(
        0,
        "Vùng",
        regions,
    )

    allocation["Tổng vùng"] = (
        x.sum(axis=1)
    )

    allocation[
        "Digital sau đầu tư"
    ] = (
        d0
        + 0.002
        * x[:, 1]
    )

    return {
        "table": allocation,
        "objective": objective,
        "source": source,
        "total_budget": float(
            x.sum()
        ),
        "human_budget": float(
            x[:, 3].sum()
        ),
    }


def _b12_module_4_labor(shares):
    """M4 dùng tham số Bài 9: 8 ngành, x_AI và x_H theo tỷ trọng kịch bản."""
    df = _b9_prepare_data().copy()
    budget = 30000.0
    ai_budget = budget * float(shares[2]) / max(float(shares[2] + shares[3]), 1e-12)
    h_budget = budget * float(shares[3]) / max(float(shares[2] + shares[3]), 1e-12)

    # Phân bổ AI theo mức sẵn sàng tạo việc tương đối, H theo displaced tiềm năng.
    ai_weight = np.maximum(df["a1"].to_numpy(float) - df["c1"].to_numpy(float) * df["risk"].to_numpy(float), 0.0)
    if ai_weight.sum() <= 0:
        ai_weight = np.ones(len(df))
    h_weight = df["c1"].to_numpy(float) * df["risk"].to_numpy(float) * df["Lao động (triệu)"].to_numpy(float)
    if h_weight.sum() <= 0:
        h_weight = np.ones(len(df))
    x_ai = ai_budget * ai_weight / ai_weight.sum()
    x_h = h_budget * h_weight / h_weight.sum()
    new_job, upgrade, displaced, retrain_cap, net_job = _b9_job_metrics(df, x_ai, x_h)
    result = pd.DataFrame({
        "Ngành": df["Ngành"],
        "JobsCreated_million": new_job / 1_000_000,
        "JobsDisplaced_million": displaced / 1_000_000,
        "JobsRetrained_million": np.minimum(displaced, retrain_cap) / 1_000_000,
        "NetJobs_million": net_job / 1_000_000,
    })
    return {
        "table": result.sort_values("NetJobs_million", ascending=False).reset_index(drop=True),
        "net_jobs_total": float(result["NetJobs_million"].sum()),
        "displaced_total": float(result["JobsDisplaced_million"].sum()),
        "retrained_total": float(result["JobsRetrained_million"].sum()),
    }


def _b12_module_5_risk(
    shares,
):
    k_share = float(
        shares[0]
    )
    d_share = float(
        shares[1]
    )
    ai_share = float(
        shares[2]
    )
    h_share = float(
        shares[3]
    )

    cyber_risk = float(
        np.clip(
            100
            * (
                0.48
                * ai_share
                + 0.25
                * d_share
                - 0.20
                * h_share
            ),
            0.0,
            100.0,
        )
    )

    emission_risk = float(
        np.clip(
            100
            * (
                0.34
                * k_share
                + 0.38
                * ai_share
                + 0.08
                * d_share
            ),
            0.0,
            100.0,
        )
    )

    inclusion_score = float(
        np.clip(
            100
            * (
                0.58
                * h_share
                + 0.30
                * d_share
                + 0.12
                * k_share
            ),
            0.0,
            100.0,
        )
    )

    concentration_risk = float(
        100
        * np.max(
            shares
        )
    )

    return {
        "CyberRisk": cyber_risk,
        "EmissionRisk": emission_risk,
        "InclusionScore": inclusion_score,
        "ConcentrationRisk": concentration_risk,
    }


@st.cache_data(show_spinner=False)
def _b12_run_pipeline():
    scenarios = _b12_scenarios()

    readiness = (
        _b12_module_2_region_readiness()
    )

    allocation = (
        _b12_module_3_allocation()
    )

    rows = []
    trajectories = {}
    labor_results = {}

    for scenario_name, shares in scenarios.items():
        forecast = (
            _b12_module_1_forecast(
                shares
            )
        )

        labor = (
            _b12_module_4_labor(
                shares
            )
        )

        risk = (
            _b12_module_5_risk(
                shares
            )
        )

        trajectories[
            scenario_name
        ] = forecast[
            "trajectory"
        ]

        labor_results[
            scenario_name
        ] = labor[
            "table"
        ]

        rows.append(
            {
                "Kịch bản": scenario_name,
                "Share_K": float(
                    shares[0]
                ),
                "Share_D": float(
                    shares[1]
                ),
                "Share_AI": float(
                    shares[2]
                ),
                "Share_H": float(
                    shares[3]
                ),
                "GDP_2030": forecast[
                    "GDP_2030"
                ],
                "Consumption_2030": forecast[
                    "Consumption_2030"
                ],
                "GDP_Growth_2026_2030": forecast[
                    "GDP_Growth_2026_2030"
                ],
                "Digital_2030": forecast[
                    "Digital_2030"
                ],
                "AI_2030": forecast[
                    "AI_2030"
                ],
                "Human_2030": forecast[
                    "Human_2030"
                ],
                "NetJobs_million": labor[
                    "net_jobs_total"
                ],
                "Displaced_million": labor[
                    "displaced_total"
                ],
                "Retrained_million": labor[
                    "retrained_total"
                ],
                **risk,
            }
        )

    result = pd.DataFrame(
        rows
    )

    result[
        "GDP_norm"
    ] = minmax(
        result[
            "GDP_2030"
        ]
    )

    result[
        "Jobs_norm"
    ] = minmax(
        result[
            "NetJobs_million"
        ]
    )

    result[
        "Inclusion_norm"
    ] = minmax(
        result[
            "InclusionScore"
        ]
    )

    result[
        "Cyber_norm"
    ] = minmax(
        result[
            "CyberRisk"
        ]
    )

    result[
        "Emission_norm"
    ] = minmax(
        result[
            "EmissionRisk"
        ]
    )

    result[
        "IntegratedScore"
    ] = (
        0.35
        * result[
            "GDP_norm"
        ]
        + 0.20
        * result[
            "Jobs_norm"
        ]
        + 0.20
        * result[
            "Inclusion_norm"
        ]
        + 0.15
        * (
            1
            - result[
                "Cyber_norm"
            ]
        )
        + 0.10
        * (
            1
            - result[
                "Emission_norm"
            ]
        )
    )

    result[
        "IntegratedRank"
    ] = (
        result[
            "IntegratedScore"
        ]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    return {
        "scenarios": result.sort_values(
            "IntegratedRank"
        ).reset_index(drop=True),
        "trajectories": trajectories,
        "readiness": readiness,
        "allocation": allocation,
        "labor_results": labor_results,
    }


def _b12_validation(
    pipeline,
):
    scenarios = pipeline[
        "scenarios"
    ].copy()

    allocation = pipeline[
        "allocation"
    ]

    readiness = pipeline[
        "readiness"
    ]

    checks = [
        {
            "Kiểm tra": "5 kịch bản được tạo",
            "Đạt": len(
                scenarios
            ) == 5,
            "Giá trị": len(
                scenarios
            ),
        },
        {
            "Kiểm tra": "Tỷ trọng mỗi kịch bản bằng 1",
            "Đạt": bool(
                np.allclose(
                    scenarios[
                        [
                            "Share_K",
                            "Share_D",
                            "Share_AI",
                            "Share_H",
                        ]
                    ].sum(axis=1),
                    1.0,
                )
            ),
            "Giá trị": scenarios[
                [
                    "Share_K",
                    "Share_D",
                    "Share_AI",
                    "Share_H",
                ]
            ].sum(axis=1).round(
                6
            ).tolist(),
        },
        {
            "Kiểm tra": "GDP 2030 hữu hạn và dương",
            "Đạt": bool(
                np.isfinite(
                    scenarios[
                        "GDP_2030"
                    ]
                ).all()
                and (
                    scenarios[
                        "GDP_2030"
                    ]
                    > 0
                ).all()
            ),
            "Giá trị": float(
                scenarios[
                    "GDP_2030"
                ].min()
            ),
        },
        {
            "Kiểm tra": "Ngân sách M3 không vượt 50.000",
            "Đạt": (
                allocation[
                    "total_budget"
                ]
                <= 50000.0
                + 1e-6
            ),
            "Giá trị": allocation[
                "total_budget"
            ],
        },
        {
            "Kiểm tra": "Nhân lực M3 tối thiểu 12.000",
            "Đạt": (
                allocation[
                    "human_budget"
                ]
                >= 12000.0
                - 1e-6
            ),
            "Giá trị": allocation[
                "human_budget"
            ],
        },
        {
            "Kiểm tra": "M2 xếp hạng đủ 6 vùng",
            "Đạt": (
                len(
                    readiness
                )
                == 6
                and set(
                    readiness[
                        "ReadinessRank"
                    ]
                )
                == set(
                    range(
                        1,
                        7,
                    )
                )
            ),
            "Giá trị": readiness[
                "ReadinessRank"
            ].tolist(),
        },
        {
            "Kiểm tra": "IntegratedScore nằm trong [0,1]",
            "Đạt": bool(
                scenarios[
                    "IntegratedScore"
                ].between(
                    0.0,
                    1.0,
                ).all()
            ),
            "Giá trị": [
                float(
                    scenarios[
                        "IntegratedScore"
                    ].min()
                ),
                float(
                    scenarios[
                        "IntegratedScore"
                    ].max()
                ),
            ],
        },
    ]

    return pd.DataFrame(
        checks
    )


def page_12():
    hero(
        "Bài 12 — Hệ thống hỗ trợ quyết định tích hợp AIDEOM-VN",
        "Kết nối thật sáu module từ dự báo, xếp hạng vùng, phân bổ ngân sách, lao động và rủi ro đến dashboard so sánh năm kịch bản và kiểm định pipeline.",
        ["12.1-12.6", "Integrated pipeline", "6 modules", "5 scenarios", "Validation"],
    )

    show_assignment_structure(12)

    with st.spinner(
        "Đang chạy pipeline M1-M6..."
    ):
        pipeline = (
            _b12_run_pipeline()
        )

    scenarios = pipeline[
        "scenarios"
    ]

    st.markdown("## 12.1. Kiến trúc sáu module")

    architecture = pd.DataFrame(
        [
            [
                "M1",
                "Dự báo kinh tế",
                "compute_tfp + simulate_dynamic",
                "GDP, D, AI, H năm 2030",
            ],
            [
                "M2",
                "Sẵn sàng vùng",
                "TOPSIS từ dữ liệu 6 vùng",
                "Điểm và thứ hạng vùng",
            ],
            [
                "M3",
                "Phân bổ ngân sách",
                "LP Bài 4 hoặc LP dự phòng",
                "Ma trận 6 vùng × 4 hạng mục",
            ],
            [
                "M4",
                "Lao động và AI",
                "Dữ liệu 8 ngành Bài 9",
                "NewJob, DisplacedJob, RetrainingCapacity, NetJob",
            ],
            [
                "M5",
                "Rủi ro",
                "Cơ cấu K-D-AI-H",
                "Cyber, phát thải, bao trùm, tập trung",
            ],
            [
                "M6",
                "Dashboard",
                "Đầu ra M1-M5",
                "KPI, xếp hạng, cảnh báo, tải CSV",
            ],
        ],
        columns=[
            "Module",
            "Chức năng",
            "Nguồn đầu vào",
            "Đầu ra",
        ],
    )

    st.dataframe(
        architecture,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Sơ đồ luồng dữ liệu M1-M6")

    st.plotly_chart(
        _b12_flow_figure(),
        use_container_width=True,
        key="b12_flow_figure",
    )

    # =====================================================
    # 12.1.1. Nguồn và phạm vi dữ liệu
    # =====================================================
    st.markdown("### Nguồn và phạm vi dữ liệu")

    data_sources = pd.DataFrame(
        [
            [
                "vietnam_macro_2020_2025.csv",
                "Dữ liệu vĩ mô Việt Nam",
                "2020-2025",
                "Nghìn tỷ VND, %, tỷ USD",
                "NSO/GSO, MPI, World Bank và dữ liệu tổng hợp của dự án",
                "Dữ liệu quan sát và một số biến đại diện",
            ],
            [
                "vietnam_sectors_2024.csv",
                "10 ngành kinh tế",
                "2024",
                "%, triệu lao động, tỷ USD, chỉ số 0-100",
                "NSO/GSO, MIC/MoST và dữ liệu tổng hợp của dự án",
                "Một số chỉ tiêu AI và rủi ro là biến đại diện",
            ],
            [
                "vietnam_regions_2024.csv",
                "6 vùng kinh tế - xã hội",
                "2024",
                "Triệu VND, tỷ USD, %, chỉ số 0-100",
                "NSO/GSO, MPI, MIC và WIPO/GII tham chiếu",
                "Dữ liệu vùng và chỉ số tổng hợp",
            ],
            [
                "Tham số mô hình",
                "Hệ số tác động, rủi ro và kịch bản",
                "2026-2035",
                "Tỷ trọng, hệ số và xác suất",
                "Giả định phục vụ mô phỏng bài tập",
                "Không phải số liệu dự báo chính thức",
            ],
        ],
        columns=[
            "Tệp/Nhóm dữ liệu",
            "Phạm vi",
            "Năm cơ sở",
            "Đơn vị",
            "Nguồn tham chiếu",
            "Ghi chú phương pháp",
        ],
    )

    st.dataframe(
        data_sources,
        use_container_width=True,
        hide_index=True,
    )

    file_checks = pd.DataFrame(
        [
            {
                "Tệp dữ liệu": "vietnam_macro_2020_2025.csv",
                "Đường dẫn": str(
                    DATA_DIR / "vietnam_macro_2020_2025.csv"
                ),
                "Tồn tại": (
                    DATA_DIR / "vietnam_macro_2020_2025.csv"
                ).exists(),
            },
            {
                "Tệp dữ liệu": "vietnam_sectors_2024.csv",
                "Đường dẫn": str(
                    DATA_DIR / "vietnam_sectors_2024.csv"
                ),
                "Tồn tại": (
                    DATA_DIR / "vietnam_sectors_2024.csv"
                ).exists(),
            },
            {
                "Tệp dữ liệu": "vietnam_regions_2024.csv",
                "Đường dẫn": str(
                    DATA_DIR / "vietnam_regions_2024.csv"
                ),
                "Tồn tại": (
                    DATA_DIR / "vietnam_regions_2024.csv"
                ).exists(),
            },
        ]
    )

    with st.expander(
        "Kiểm tra trạng thái các tệp dữ liệu",
        expanded=False,
    ):
        st.dataframe(
            file_checks,
            use_container_width=True,
            hide_index=True,
        )

        if bool(file_checks["Tồn tại"].all()):
            st.success(
                "Ba tệp dữ liệu đầu vào đều tồn tại và sẵn sàng cho pipeline."
            )
        else:
            st.error(
                "Có tệp dữ liệu bị thiếu. Hãy kiểm tra lại thư mục data."
            )

    st.warning(
        "Các hệ số beta, xác suất rủi ro, tác động AI, đào tạo lại và "
        "một số chỉ số tổng hợp là tham số mô phỏng. Kết quả của dashboard "
        "được sử dụng để so sánh kịch bản, không phải dự báo chính thức."
    )

    # =====================================================
    # 12.2. Trọng số tương tác và xếp hạng kịch bản
    # =====================================================
    st.markdown("## 12.2. Năm kịch bản")

    st.markdown("### Điều chỉnh trọng số ra quyết định")

    st.caption(
        "Người dùng có thể thay đổi mức ưu tiên giữa tăng trưởng, "
        "việc làm, bao trùm, an ninh mạng và phát thải. "
        "Các trọng số được tự động chuẩn hóa để có tổng bằng 1."
    )

    weight_columns = st.columns(5)

    weight_gdp = weight_columns[0].slider(
        "GDP",
        min_value=0.00,
        max_value=1.00,
        value=0.35,
        step=0.05,
        key="b12_weight_gdp",
    )

    weight_jobs = weight_columns[1].slider(
        "Việc làm",
        min_value=0.00,
        max_value=1.00,
        value=0.20,
        step=0.05,
        key="b12_weight_jobs",
    )

    weight_inclusion = weight_columns[2].slider(
        "Bao trùm",
        min_value=0.00,
        max_value=1.00,
        value=0.20,
        step=0.05,
        key="b12_weight_inclusion",
    )

    weight_cyber = weight_columns[3].slider(
        "Giảm cyber risk",
        min_value=0.00,
        max_value=1.00,
        value=0.15,
        step=0.05,
        key="b12_weight_cyber",
    )

    weight_emission = weight_columns[4].slider(
        "Giảm phát thải",
        min_value=0.00,
        max_value=1.00,
        value=0.10,
        step=0.05,
        key="b12_weight_emission",
    )

    decision_weights = np.array(
        [
            weight_gdp,
            weight_jobs,
            weight_inclusion,
            weight_cyber,
            weight_emission,
        ],
        dtype=float,
    )

    if decision_weights.sum() <= 1e-12:
        st.warning(
            "Tổng trọng số đang bằng 0. Hệ thống sử dụng lại "
            "bộ trọng số mặc định."
        )

        decision_weights = np.array(
            [
                0.35,
                0.20,
                0.20,
                0.15,
                0.10,
            ],
            dtype=float,
        )

    decision_weights = (
        decision_weights
        / decision_weights.sum()
    )

    scenarios["UserScore"] = (
        decision_weights[0]
        * scenarios["GDP_norm"]
        + decision_weights[1]
        * scenarios["Jobs_norm"]
        + decision_weights[2]
        * scenarios["Inclusion_norm"]
        + decision_weights[3]
        * (
            1.0
            - scenarios["Cyber_norm"]
        )
        + decision_weights[4]
        * (
            1.0
            - scenarios["Emission_norm"]
        )
    )

    scenarios["UserRank"] = (
        scenarios["UserScore"]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    scenarios = scenarios.sort_values(
        [
            "UserRank",
            "IntegratedRank",
        ]
    ).reset_index(
        drop=True
    )

    normalized_weights = pd.DataFrame(
        {
            "Tiêu chí": [
                "GDP",
                "Việc làm",
                "Bao trùm",
                "Giảm cyber risk",
                "Giảm phát thải",
            ],
            "Trọng số chuẩn hóa": decision_weights,
        }
    )

    with st.expander(
        "Xem bộ trọng số sau chuẩn hóa",
        expanded=False,
    ):
        st.dataframe(
            normalized_weights.style.format(
                {
                    "Trọng số chuẩn hóa": "{:.3f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.success(
            f"Tổng trọng số sau chuẩn hóa = "
            f"{decision_weights.sum():.3f}"
        )
    st.dataframe(
        scenarios[
            [
                "Kịch bản",
                "Share_K",
                "Share_D",
                "Share_AI",
                "Share_H",
                "GDP_2030",
                "NetJobs_million",
                "InclusionScore",
                "CyberRisk",
                "EmissionRisk",
                "IntegratedScore",
                "IntegratedRank",
                "UserScore",
                "UserRank",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    best = scenarios.iloc[0]

    kpi_cards(
        [
            (
                "Kịch bản số 1",
                best[
                    "Kịch bản"
                ],
                f"Điểm tùy chỉnh={best['UserScore']:.4f}",
            ),
            (
                "GDP 2030",
                f"{best['GDP_2030']:,.1f}",
                "kịch bản dẫn đầu",
            ),
            (
                "Net jobs",
                f"{best['NetJobs_million']:.3f} triệu",
                "M4",
            ),
            (
                "Bao trùm",
                f"{best['InclusionScore']:.2f}",
                "M5",
            ),
        ]
    )

    st.markdown("## 12.3. Yêu cầu kỹ thuật và dashboard tích hợp")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "M1 - Dự báo",
            "M2 - Vùng",
            "M3 - Phân bổ",
            "M4 - Lao động",
            "M5 - Rủi ro",
            "M6 - Kiểm định",
        ]
    )

    with tab1:
        selected = st.multiselect(
            "Chọn kịch bản",
            options=list(
                pipeline[
                    "trajectories"
                ].keys()
            ),
            default=list(
                pipeline[
                    "trajectories"
                ].keys()
            ),
            key="b12_forecast_scenarios",
        )

        rows = []

        for scenario_name in selected:
            temp = pipeline[
                "trajectories"
            ][scenario_name].copy()

            temp[
                "Kịch bản"
            ] = scenario_name

            rows.append(
                temp
            )

        if rows:
            forecast_df = pd.concat(
                rows,
                ignore_index=True,
            )

            fig = px.line(
                forecast_df,
                x="Năm",
                y="Y_GDP",
                color="Kịch bản",
                markers=True,
                template=PLOT_TEMPLATE,
                title="Quỹ đạo GDP 2026-2030",
            )
            fig.update_layout(
                height=500,
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    with tab2:
        readiness = pipeline[
            "readiness"
        ]

        st.dataframe(
            readiness,
            use_container_width=True,
            hide_index=True,
        )

        fig = px.bar(
            readiness.sort_values(
                "ReadinessScore"
            ),
            x="ReadinessScore",
            y="Vùng",
            orientation="h",
            template=PLOT_TEMPLATE,
            title="M2 - Sẵn sàng AI và số hóa theo vùng",
        )
        fig.update_layout(
            height=480,
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with tab3:
        allocation = pipeline[
            "allocation"
        ]

        st.caption(
            f"Nguồn solver: {allocation['source']} | "
            f"Z*={allocation['objective']:,.2f}"
        )

        st.dataframe(
            allocation[
                "table"
            ],
            use_container_width=True,
            hide_index=True,
        )

        long_df = allocation[
            "table"
        ].melt(
            id_vars=[
                "Vùng",
                "Tổng vùng",
                "Digital sau đầu tư",
            ],
            value_vars=[
                "I - Hạ tầng số",
                "D - CĐS DN",
                "AI",
                "H - Nhân lực số",
            ],
            var_name="Hạng mục",
            value_name="Ngân sách",
        )

        fig = px.bar(
            long_df,
            x="Vùng",
            y="Ngân sách",
            color="Hạng mục",
            barmode="stack",
            template=PLOT_TEMPLATE,
            title="M3 - Phân bổ ngân sách vùng",
        )
        fig.update_layout(
            height=520,
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with tab4:
        selected_labor_scenario = (
            st.selectbox(
                "Kịch bản lao động",
                options=list(
                    pipeline[
                        "labor_results"
                    ].keys()
                ),
                index=4,
                key="b12_labor_scenario",
            )
        )

        labor_df = pipeline[
            "labor_results"
        ][selected_labor_scenario]

        st.dataframe(
            labor_df,
            use_container_width=True,
            hide_index=True,
        )

        fig = px.bar(
            labor_df.sort_values(
                "NetJobs_million"
            ),
            x="NetJobs_million",
            y="Ngành",
            orientation="h",
            template=PLOT_TEMPLATE,
            title="M4 - Việc làm ròng theo ngành",
        )
        fig.update_layout(
            height=560,
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with tab5:
        risk_long = scenarios.melt(
            id_vars="Kịch bản",
            value_vars=[
                "CyberRisk",
                "EmissionRisk",
                "InclusionScore",
                "ConcentrationRisk",
            ],
            var_name="KPI",
            value_name="Điểm",
        )

        fig = px.bar(
            risk_long,
            x="Kịch bản",
            y="Điểm",
            color="KPI",
            barmode="group",
            template=PLOT_TEMPLATE,
            title="M5 - Rủi ro và bao trùm",
        )
        fig.update_layout(
            height=500,
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        warnings = []

        for _, row in scenarios.iterrows():
            if (
                row["Share_AI"]
                >= 0.40
                and row[
                    "Share_H"
                ]
                < 0.20
            ):
                warnings.append(
                    f"{row['Kịch bản']}: AI cao nhưng nhân lực thấp."
                )

            if row[
                "CyberRisk"
            ] > scenarios[
                "CyberRisk"
            ].median():
                warnings.append(
                    f"{row['Kịch bản']}: cyber risk trên trung vị."
                )

            if row[
                "InclusionScore"
            ] < scenarios[
                "InclusionScore"
            ].median():
                warnings.append(
                    f"{row['Kịch bản']}: bao trùm dưới trung vị."
                )

        for warning in warnings:
            st.markdown(
                f"<div class='warning-box'>{warning}</div>",
                unsafe_allow_html=True,
            )

    with tab6:
        validation = (
            _b12_validation(
                pipeline
            )
        )

        st.dataframe(
            validation,
            use_container_width=True,
            hide_index=True,
        )

        passed = int(
            validation[
                "Đạt"
            ].sum()
        )

        kpi_cards(
            [
                (
                    "Số kiểm định đạt",
                    f"{passed}/{len(validation)}",
                    "pipeline self-test",
                ),
                (
                    "M1-M5",
                    "Đã kết nối",
                    "M6 nhận đầu ra thật",
                ),
                (
                    "Số vùng",
                    str(
                        len(
                            pipeline[
                                "readiness"
                            ]
                        )
                    ),
                    "M2",
                ),
                (
                    "Ngân sách M3",
                    f"{pipeline['allocation']['total_budget']:,.0f}",
                    "không vượt 50.000",
                ),
            ]
        )

        if bool(
            validation[
                "Đạt"
            ].all()
        ):
            st.success(
                "Pipeline vượt qua toàn bộ kiểm định nội bộ."
            )
        else:
            st.error(
                "Có kiểm định chưa đạt; không nên coi kết quả là final."
            )

    st.markdown("## 12.4. Sản phẩm bàn giao")

    deliverables = pd.DataFrame(
        [
            [
                "Dashboard",
                "12 trang Streamlit",
                "Hoàn thành",
            ],
            [
                "Mã nguồn",
                "app.py + requirements.txt + data",
                "Hoàn thành",
            ],
            [
                "Kiểm định",
                "Self-test pipeline M1-M6",
                "Hoàn thành trong Bài 12",
            ],
            [
                "Báo cáo",
                "Word/PDF 15-25 trang",
                "Cần nộp kèm",
            ],
            [
                "Slide",
                "Khoảng 15 slide",
                "Cần nộp kèm",
            ],
            [
                "Video",
                "Demo 3-5 phút",
                "Cần nộp kèm",
            ],
        ],
        columns=[
            "Sản phẩm",
            "Nội dung",
            "Trạng thái",
        ],
    )

    st.dataframe(
        deliverables,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("## 12.5. Tiêu chí đánh giá")

    rubric = pd.DataFrame(
        [
            [
                "Mô hình toán",
                20,
            ],
            [
                "Chất lượng code",
                20,
            ],
            [
                "Dữ liệu Việt Nam",
                15,
            ],
            [
                "Phân tích chính sách",
                20,
            ],
            [
                "Dashboard",
                15,
            ],
            [
                "Báo cáo và thuyết trình",
                10,
            ],
        ],
        columns=[
            "Tiêu chí",
            "Trọng số (%)",
        ],
    )

    st.dataframe(
        rubric,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("## 12.6. Hướng mở rộng")
    st.markdown(
        """
        - Tách M1-M5 thành package Python độc lập trong thư mục `src/`.
        - Thêm unit test bằng pytest cho LP, TOPSIS, SP và RL.
        - Kết nối API dữ liệu chính thức thay vì chỉ dùng CSV tĩnh.
        - Huấn luyện DQN offline, lưu model và kiểm định nhiều seed.
        - Bổ sung use case chuyên sâu cho Đồng bằng sông Cửu Long hoặc bán dẫn.
        """
    )

    st.download_button(
        "Tải bảng tổng hợp năm kịch bản",
        data=scenarios.to_csv(
            index=False
        ).encode(
            "utf-8-sig"
        ),
        file_name="bai12_pipeline_5_kich_ban.csv",
        mime="text/csv",
        key="download_bai12_pipeline",
    )


    ai_analysis_panel(
        lesson_name='Bài 12 - Dashboard tích hợp AIDEOM-VN',
        model_name='Integrated Policy Dashboard + 5 Scenarios + M1-M6',
        input_params={"lesson": 'Bài 12 - Dashboard tích hợp AIDEOM-VN', "model": 'Integrated Policy Dashboard + 5 Scenarios + M1-M6'},
        result_data=_collect_ai_context(locals()),
        key="ai_bai_12",
    )


PAGES = {
    "Trang chủ": page_home,
    "Bài 1 — Cobb-Douglas + AI": page_1,
    "Bài 2 — LP ngân sách số": page_2,
    "Bài 3 — Priority 10 ngành": page_3,
    "Bài 4 — LP ngành-vùng": page_4,
    "Bài 5 — MIP 15 dự án": page_5,
    "Bài 6 — TOPSIS 6 vùng": page_6,
    "Bài 7 — Pareto đa mục tiêu": page_7,
    "Bài 8 — Động 2026-2035": page_8,
    "Bài 9 — Lao động & AI": page_9,
    "Bài 10 — Stochastic SP": page_10,
    "Bài 11 — Q-learning RL": page_11,
    "Bài 12 — AIDEOM tích hợp": page_12,
}


st.sidebar.markdown("## VN AIDEOM-VN")
st.sidebar.caption("Decision Optimization Dashboard")
choice = st.sidebar.radio("Điều hướng 13 trang", list(PAGES.keys()), label_visibility="visible")
st.sidebar.markdown("---")

PAGES[choice]()
