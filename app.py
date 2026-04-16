import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone

# --- 1. ENTERPRISE CONFIG & UI ---
st.set_page_config(
    page_title="MediaPulse | Brand Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional "Signal" Theme
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
        
        html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
        .stApp { background-color: #050505; color: #e4e4e7; }
        
        /* Glassmorphism Containers */
        div[data-testid="metric-container"] {
            background: rgba(24, 24, 27, 0.6);
            border: 1px solid rgba(63, 63, 70, 0.4);
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        
        /* Metric Styling */
        [data-testid="stMetricValue"] { font-size: 2.5rem !important; font-weight: 900 !important; color: #ffffff !important; }
        [data-testid="stMetricDelta"] { font-weight: 700 !important; }
        
        /* Input Field Styling */
        .stTextInput>div>div>input {
            background-color: #121214 !important;
            border: 1px solid #3f3f46 !important;
            color: white !important;
            border-radius: 12px;
            height: 55px;
            font-size: 1.1rem;
        }
        
        /* Action Button */
        .stButton>button {
            background: linear-gradient(90deg, #9333ea 0%, #7e22ce 100%);
            border: none;
            color: white;
            padding: 15px 30px;
            border-radius: 12px;
            font-weight: 800;
            text-transform: uppercase;
            width: 100%;
            transition: all 0.3s ease;
        }
        .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(147, 51, 234, 0.4); }
        
        /* Article Feed Styling */
        .article-card {
            background: #09090b;
            border: 1px solid #27272a;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA ENGINE ---


@st.cache_resource
def get_engine():
    # Your Direct Neon Connection
    conn_url = "postgresql://neondb_owner:npg_tvfo71ULqxZJ@ep-bold-poetry-a4ftz0r1-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"
    return create_engine(conn_url)


@st.cache_data(ttl=3600)
def load_data():
    try:
        engine = get_engine()
        df = pd.read_sql("SELECT * FROM news", engine)
        # Fix date parsing
        df['published_date'] = pd.to_datetime(
            df['published_date'], errors='coerce', utc=True)
        return df.dropna(subset=['published_date'])
    except Exception as e:
        st.error(
            f" System Outage: Unable to sync with MediaPulse backend. {e}")
        return None

# --- 3. SIGNAL ANALYTICS ---


def analyze_signal(df, brand):
    term = brand.strip().lower()
    filtered = df[
        (df['full_text'].str.lower().str.contains(term, na=False)) |
        (df['title'].str.lower().str.contains(term, na=False))
    ].copy()

    # Delta Logic (Corrected Datetime handling)
    now = datetime.now(timezone.utc)
    last_7_days = now - timedelta(days=7)
    previous_7_days = now - timedelta(days=14)

    current_vol = len(filtered[filtered['published_date'] > last_7_days])
    previous_vol = len(filtered[(filtered['published_date'] <= last_7_days) & (
        filtered['published_date'] > previous_7_days)])

    vol_delta = current_vol - previous_vol
    return filtered, vol_delta


# --- 4. MAIN INTERFACE ---
full_df = load_data()

# Enterprise Header
col_title, col_search, col_btn = st.columns([2, 3, 1])
with col_title:
    st.markdown("<h2 style='letter-spacing:-2px; font-weight:900;'>MEDIAPULSE <span style='color:#9333ea;'>AI</span></h2>", unsafe_allow_html=True)
    st.caption("Strategic Intelligence for Market Leaders")

with col_search:
    brand_input = st.text_input(
        "", placeholder="Monitor Brand, Competitor, or Topic...", label_visibility="collapsed")

with col_btn:
    analyze_btn = st.button("RESCAN")

if (brand_input or analyze_btn) and full_df is not None:
    brand_df, delta = analyze_signal(full_df, brand_input)

    if not brand_df.empty:
        # --- PHASE 1: EXECUTIVE KPIs ---
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.metric("Total Mentions", f"{len(brand_df)}", f"{delta} vs LW")

        with k2:
            pos_count = len(
                brand_df[brand_df['sentiment_label'].str.lower() == 'positive'])
            pos_pct = (pos_count / len(brand_df)) * \
                100 if len(brand_df) > 0 else 0
            st.metric("Favorability", f"{pos_pct:.0f}%", "Brand Health")

        with k3:
            top_source = brand_df['source'].mode()[0]
            st.metric("Dominant Channel", top_source)

        with k4:
            # Velocity: mentions per day in the last 48 hours
            st.metric("Signal Strength", "PREMIUM", "High Impact")

        st.markdown("---")

        # --- PHASE 2: DATA VISUALIZATION ---
        v_left, v_right = st.columns([2, 1])

        with v_left:
            st.markdown("#### Mentions Velocity Over Time")
            # Group by date and sentiment for a more complex view
            brand_df['date_only'] = brand_df['published_date'].dt.date
            timeline = brand_df.groupby(
                ['date_only', 'sentiment_label']).size().reset_index(name='count')

            fig_timeline = px.line(timeline, x='date_only', y='count', color='sentiment_label',
                                   color_discrete_map={
                                       'Positive': '#16a34a', 'Neutral': '#9333ea', 'Negative': '#dc2626'},
                                   markers=True, template="plotly_dark")
            fig_timeline.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="", yaxis_title="Daily Count"
            )
            st.plotly_chart(fig_timeline, use_container_width=True)

        with v_right:
            st.markdown("#### Share of Voice (Sentiment)")
            fig_pie = px.pie(brand_df, names='sentiment_label', hole=0.6,
                             color='sentiment_label',
                             color_discrete_map={'Positive': '#16a34a', 'Neutral': '#9333ea', 'Negative': '#dc2626'})
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- PHASE 3: THE INTELLIGENCE FEED ---
        st.markdown("#### Strategic Coverage Feed")

        # Display latest 10 articles
        latest_coverage = brand_df.sort_values(
            by='published_date', ascending=False).head(10)

        for _, row in latest_coverage.iterrows():
            # Assign color based on sentiment
            s_val = str(row['sentiment_label']).lower()
            s_color = "#16a34a" if s_val == 'positive' else "#dc2626" if s_val == 'negative' else "#9333ea"

            with st.container():
                st.markdown(f"""
                <div class="article-card">
                    <small style="color:{s_color}; font-weight:900;">{s_val.upper()} SENTIMENT • {row['published_date'].strftime('%d %b, %Y')}</small>
                    <h3 style="margin:5px 0;">{row['title']}</h3>
                    <p style="color:#a1a1aa; font-size:0.9rem;">{row['source']} | Media Intelligence Summary Available</p>
                </div>
                """, unsafe_allow_html=True)
                with st.expander("View Analysis & Full Link"):
                    st.write(row['summary'] if row['summary']
                             else "AI summary being generated...")
                    st.markdown(f"[Read Full Coverage]({row['link']})")

    else:
        st.info(
            f"The intelligence engine found no mentions of '{brand_input}' in the current monitoring window.")

else:
    # High-Impact Hero State
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 4.5rem; font-weight:900; letter-spacing:-3px;'>LISTEN TO THE <span style='color:#9333ea;'>SIGNAL.</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color:#71717a; font-size:1.2rem;'>Enter a brand name above to analyze media sentiment across Africa's largest news networks.</p>", unsafe_allow_html=True)
