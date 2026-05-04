import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Customer Behavior Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── DARK THEME CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    [data-testid="stSidebar"] * { color: #e6edf3 !important; }

    /* Cards */
    .kpi-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        margin-bottom: 12px;
    }
    .kpi-label { font-size: 13px; color: #8b949e; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.06em; }
    .kpi-value { font-size: 32px; font-weight: 700; color: #58a6ff; }
    .kpi-sub   { font-size: 12px; color: #3fb950; margin-top: 4px; }

    /* Section headers */
    .section-title {
        font-size: 16px; font-weight: 600; color: #e6edf3;
        margin: 24px 0 12px; border-left: 3px solid #58a6ff;
        padding-left: 10px;
    }

    /* Plotly chart bg */
    .js-plotly-plot .plotly { background: transparent !important; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }

    /* Streamlit widget overrides */
    .stSelectbox > div > div { background-color: #161b22 !important; border-color: #30363d !important; color: #e6edf3 !important; }
    .stMultiSelect > div > div { background-color: #161b22 !important; }
    label, .stRadio label { color: #8b949e !important; }
    h1, h2, h3 { color: #e6edf3 !important; }
    .stDataFrame { background: #161b22; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

CHART_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8b949e", size=12),
    margin=dict(l=10, r=10, t=30, b=10),
)
GRID = dict(gridcolor="#21262d", zerolinecolor="#21262d")
BLUE    = "#58a6ff"
GREEN   = "#3fb950"
PURPLE  = "#bc8cff"
ORANGE  = "#f78166"
TEAL    = "#39d353"
COLORS  = [BLUE, GREEN, PURPLE, ORANGE, TEAL, "#ffa657", "#ff7b72"]

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    customers = pd.read_csv(BASE_DIR / "customers.csv")
    orders    = pd.read_csv(BASE_DIR / "orders.csv")
    payments  = pd.read_csv(BASE_DIR / "payments.csv")
    products  = pd.read_csv(BASE_DIR / "products.csv")

    orders["order_date"]    = pd.to_datetime(orders["order_date"],    format="mixed")
    payments["payment_date"]= pd.to_datetime(payments["payment_date"], format="mixed", errors="coerce")
    customers["signup_date"]= pd.to_datetime(customers["signup_date"], format="mixed", errors="coerce")

    orders["month"]     = orders["order_date"].dt.to_period("M").astype(str)
    orders["month_num"] = orders["order_date"].dt.to_period("M")

    merged = orders.merge(customers, on="customer_id")\
                   .merge(products,  on="product_id")\
                   .merge(payments,  on="order_id", how="left")

    bins   = [18, 25, 30, 35, 40, 45]
    labels = ["18-24", "25-29", "30-34", "35-39", "40-44"]
    customers["age_group"] = pd.cut(customers["age"], bins=bins, labels=labels, right=False)

    opc = orders.groupby("customer_id").size()
    customers["order_count"] = customers["customer_id"].map(opc).fillna(0).astype(int)
    customers["customer_type"] = customers["order_count"].apply(lambda x: "Returning" if x > 1 else "New")

    return customers, orders, payments, products, merged

customers, orders, payments, products, merged = load_data()

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Filters")
    st.markdown("---")

    all_cities = ["All"] + sorted(customers["city"].unique().tolist())
    selected_city = st.selectbox("🏙️ City", all_cities)

    all_genders = ["All", "M", "F"]
    selected_gender = st.radio("👤 Gender", all_genders, horizontal=True)

    age_range = st.slider("🎂 Age Range", int(customers["age"].min()), int(customers["age"].max()),
                          (int(customers["age"].min()), int(customers["age"].max())))

    st.markdown("---")
    st.markdown("#### 📁 About")
    st.markdown(f"**Customers:** {len(customers):,}")
    st.markdown(f"**Orders:** {len(orders):,}")
    st.markdown(f"**Products:** {len(products):,}")
    st.markdown(f"**Date range:** Apr 2023 – Dec 2024")

# ─── APPLY FILTERS ───────────────────────────────────────────────────────────
fc = customers.copy()
if selected_city   != "All":    fc = fc[fc["city"]   == selected_city]
if selected_gender != "All":    fc = fc[fc["gender"] == selected_gender]
fc = fc[(fc["age"] >= age_range[0]) & (fc["age"] <= age_range[1])]

filtered_orders = orders[orders["customer_id"].isin(fc["customer_id"])]
filtered_merged = merged[merged["customer_id"].isin(fc["customer_id"])]

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style='font-size:28px; font-weight:700; margin-bottom:4px;'>
    📊 Customer Behavior Analytics
</h1>
<p style='color:#8b949e; font-size:14px; margin-bottom:24px;'>
    E-Commerce Business Analytics Dashboard &nbsp;|&nbsp; Apr 2023 – Dec 2024
</p>
""", unsafe_allow_html=True)

# ─── KPI CARDS ───────────────────────────────────────────────────────────────
total_customers  = len(fc)
total_orders     = len(filtered_orders)
avg_orders       = round(filtered_orders.groupby("customer_id").size().mean(), 2) if total_orders else 0
new_customers    = len(fc[fc["customer_type"] == "New"])
returning        = len(fc[fc["customer_type"] == "Returning"])
ret_pct          = round(returning / total_customers * 100, 1) if total_customers else 0
total_revenue    = int(filtered_merged[filtered_merged["payment_status"] == "Success"]["amount"].sum())
avg_age          = round(fc["age"].mean(), 1) if total_customers else 0

k1, k2, k3, k4, k5 = st.columns(5)
for col, label, value, sub in [
    (k1, "Total Customers",  f"{total_customers:,}",    f"{len(customers):,} overall"),
    (k2, "Total Orders",     f"{total_orders:,}",       f"Avg {avg_orders} / customer"),
    (k3, "Total Revenue",    f"₹{total_revenue:,.0f}",  "Successful payments"),
    (k4, "Returning Rate",   f"{ret_pct}%",             f"{returning:,} returning"),
    (k5, "Average Age",      f"{avg_age}",              "Years old"),
]:
    col.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value'>{value}</div>
        <div class='kpi-sub'>{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── ROW 1: Monthly Orders + Revenue by Category ─────────────────────────────
st.markdown("<div class='section-title'>Orders & Revenue Over Time</div>", unsafe_allow_html=True)
c1, c2 = st.columns([3, 2])

with c1:
    monthly_orders = filtered_orders.groupby("month_num").size().reset_index()
    monthly_orders.columns = ["period", "orders"]
    monthly_orders["period_str"] = monthly_orders["period"].astype(str)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly_orders["period_str"], y=monthly_orders["orders"],
        mode="lines+markers",
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=5, color=BLUE),
        fill="tozeroy",
        fillcolor="rgba(88,166,255,0.08)",
        name="Orders"
    ))
    fig.update_layout(**CHART_THEME, height=260,
                      xaxis=dict(**GRID, title=""),
                      yaxis=dict(**GRID, title="Orders"),
                      title=dict(text="Monthly Orders", font=dict(color="#e6edf3", size=14)))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    cat_rev = filtered_merged[filtered_merged["payment_status"] == "Success"]\
        .groupby("category")["amount"].sum().sort_values(ascending=True).reset_index()
    fig2 = go.Figure(go.Bar(
        x=cat_rev["amount"], y=cat_rev["category"],
        orientation="h",
        marker=dict(color=COLORS[:len(cat_rev)]),
        text=[f"₹{v:,.0f}" for v in cat_rev["amount"]],
        textposition="outside",
        textfont=dict(color="#8b949e", size=10),
    ))
    fig2.update_layout(**CHART_THEME, height=260,
                       xaxis=dict(**GRID, title="Revenue (₹)"),
                       yaxis=dict(gridcolor="rgba(0,0,0,0)"),
                       title=dict(text="Revenue by Category", font=dict(color="#e6edf3", size=14)))
    st.plotly_chart(fig2, use_container_width=True)

# ─── ROW 2: City + Age + Gender ──────────────────────────────────────────────
st.markdown("<div class='section-title'>Customer Demographics</div>", unsafe_allow_html=True)
c3, c4, c5 = st.columns(3)

with c3:
    city_data = fc["city"].value_counts().head(8).reset_index()
    city_data.columns = ["city", "count"]
    fig3 = go.Figure(go.Bar(
        x=city_data["count"], y=city_data["city"],
        orientation="h",
        marker=dict(color=BLUE, opacity=0.85),
        text=city_data["count"],
        textposition="outside",
        textfont=dict(color="#8b949e", size=10),
    ))
    fig3.update_layout(**CHART_THEME, height=300,
                       xaxis=dict(**GRID),
                       yaxis=dict(gridcolor="rgba(0,0,0,0)", autorange="reversed"),
                       title=dict(text="Top Cities", font=dict(color="#e6edf3", size=14)))
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    age_data = fc["age_group"].value_counts().sort_index().reset_index()
    age_data.columns = ["age_group", "count"]
    fig4 = go.Figure(go.Bar(
        x=age_data["age_group"], y=age_data["count"],
        marker=dict(color=PURPLE, opacity=0.85),
        text=age_data["count"],
        textposition="outside",
        textfont=dict(color="#8b949e", size=10),
    ))
    fig4.update_layout(**CHART_THEME, height=300,
                       xaxis=dict(**GRID, title="Age Group"),
                       yaxis=dict(**GRID, title="Customers"),
                       title=dict(text="Age Distribution", font=dict(color="#e6edf3", size=14)))
    st.plotly_chart(fig4, use_container_width=True)

with c5:
    gender_map  = {"M": "Male", "F": "Female"}
    gender_data = fc["gender"].map(gender_map).value_counts().reset_index()
    gender_data.columns = ["gender", "count"]
    fig5 = go.Figure(go.Pie(
        labels=gender_data["gender"],
        values=gender_data["count"],
        hole=0.55,
        marker=dict(colors=[BLUE, ORANGE]),
        textinfo="percent+label",
        textfont=dict(color="#e6edf3", size=12),
    ))
    fig5.update_layout(**CHART_THEME, height=300,
                       title=dict(text="Gender Split", font=dict(color="#e6edf3", size=14)),
                       legend=dict(font=dict(color="#8b949e")))
    st.plotly_chart(fig5, use_container_width=True)

# ─── ROW 3: New vs Returning + Buying Frequency + Payment Mode ───────────────
st.markdown("<div class='section-title'>Buying Behavior & Payments</div>", unsafe_allow_html=True)
c6, c7, c8 = st.columns(3)

with c6:
    nr_data = fc["customer_type"].value_counts().reset_index()
    nr_data.columns = ["type", "count"]
    fig6 = go.Figure(go.Pie(
        labels=nr_data["type"], values=nr_data["count"],
        hole=0.55,
        marker=dict(colors=[GREEN, TEAL]),
        textinfo="percent+label",
        textfont=dict(color="#e6edf3", size=12),
    ))
    fig6.update_layout(**CHART_THEME, height=280,
                       title=dict(text="New vs Returning", font=dict(color="#e6edf3", size=14)),
                       legend=dict(font=dict(color="#8b949e")))
    st.plotly_chart(fig6, use_container_width=True)

with c7:
    opc = filtered_orders.groupby("customer_id").size()
    freq_bins   = [1, 2, 4, 7, 11, 999]
    freq_labels = ["1 order", "2-3 orders", "4-6 orders", "7-10 orders", "10+ orders"]
    freq_series = pd.cut(opc, bins=freq_bins, labels=freq_labels, right=False).value_counts().sort_index()
    fig7 = go.Figure(go.Bar(
        x=freq_series.index.tolist(), y=freq_series.values,
        marker=dict(color=ORANGE, opacity=0.85),
        text=freq_series.values,
        textposition="outside",
        textfont=dict(color="#8b949e", size=10),
    ))
    fig7.update_layout(**CHART_THEME, height=280,
                       xaxis=dict(**GRID, title="Frequency"),
                       yaxis=dict(**GRID, title="Customers"),
                       title=dict(text="Buying Frequency", font=dict(color="#e6edf3", size=14)))
    st.plotly_chart(fig7, use_container_width=True)

with c8:
    pay_data = filtered_merged[filtered_merged["payment_status"] == "Success"]\
        ["payment_mode"].value_counts().reset_index()
    pay_data.columns = ["mode", "count"]
    fig8 = go.Figure(go.Pie(
        labels=pay_data["mode"], values=pay_data["count"],
        hole=0.55,
        marker=dict(colors=[BLUE, GREEN, PURPLE]),
        textinfo="percent+label",
        textfont=dict(color="#e6edf3", size=12),
    ))
    fig8.update_layout(**CHART_THEME, height=280,
                       title=dict(text="Payment Mode", font=dict(color="#e6edf3", size=14)),
                       legend=dict(font=dict(color="#8b949e")))
    st.plotly_chart(fig8, use_container_width=True)

# ─── ROW 4: Top Products ──────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Top Products</div>", unsafe_allow_html=True)
top_p = filtered_merged.groupby("product_name").size().sort_values(ascending=False).head(10).reset_index()
top_p.columns = ["product", "orders"]
fig9 = go.Figure(go.Bar(
    x=top_p["product"], y=top_p["orders"],
    marker=dict(color=COLORS * 2),
    text=top_p["orders"],
    textposition="outside",
    textfont=dict(color="#8b949e", size=10),
))
fig9.update_layout(**CHART_THEME, height=280,
                   xaxis=dict(**GRID, title="", tickangle=-20),
                   yaxis=dict(**GRID, title="Orders"),
                   title=dict(text="Top 10 Products by Orders", font=dict(color="#e6edf3", size=14)))
st.plotly_chart(fig9, use_container_width=True)

# ─── RAW DATA TABLE ──────────────────────────────────────────────────────────
with st.expander("📋 View Raw Customer Data"):
    show_cols = ["customer_id", "name", "age", "gender", "city", "signup_date", "order_count", "customer_type"]
    st.dataframe(
        fc[show_cols].sort_values("order_count", ascending=False).reset_index(drop=True),
        use_container_width=True,
        height=300,
    )

st.markdown("<br><p style='text-align:center;color:#30363d;font-size:12px;'>Customer Behavior Analytics Dashboard · Built with Streamlit & Plotly</p>", unsafe_allow_html=True)
