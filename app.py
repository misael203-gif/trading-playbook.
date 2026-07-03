import streamlit as st
import streamlit.components.v1 as components
import math

# Set mobile-friendly page config
st.set_page_config(page_title="Trading Playbook", layout="centered")

st.title("⚡ Momentum Trading Playbook")
st.write("Pre-Market Checklist & Risk Calculator")

st.markdown("---")

# ==========================================
# SECTION 1: LIVE TRADINGVIEW CHARTS
# ==========================================
st.header("1. Live Charts")

# Single input controls both charts
ticker = st.text_input("Ticker Symbol", "AAPL").upper()

# --- Daily Chart ---
st.subheader("Daily Chart")
tv_daily_html = f"""
<div class="tradingview-widget-container">
  <div id="tv_daily"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
  "autosize": true,
  "symbol": "{ticker}",
  "interval": "D",
  "timezone": "America/New_York",
  "theme": "dark",
  "style": "1",
  "locale": "en",
  "enable_publishing": false,
  "allow_symbol_change": true,
  "container_id": "tv_daily"
}});
  </script>
</div>
"""
# Height set to 400px for a clean mobile view
components.html(tv_daily_html, height=400)

# --- Intraday Chart ---
st.subheader("Intraday Chart")
timeframe = st.radio("Select Intraday Timeframe", ["1 Minute", "5 Minute", "15 Minute", "30 Minute"], horizontal=True)

interval_map = {"1 Minute": "1", "5 Minute": "5", "15 Minute": "15", "30 Minute": "30"}
interval = interval_map[timeframe]

tv_intraday_html = f"""
<div class="tradingview-widget-container">
  <div id="tv_intraday"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
  "autosize": true,
  "symbol": "{ticker}",
  "interval": "{interval}",
  "timezone": "America/New_York",
  "theme": "dark",
  "style": "1",
  "locale": "en",
  "enable_publishing": false,
  "allow_symbol_change": true,
  "container_id": "tv_intraday"
}});
  </script>
</div>
"""
components.html(tv_intraday_html, height=400)

st.markdown("---")

# ==========================================
# SECTION 2: PLAYBOOK CHECKLIST (100 PTS)
# ==========================================
st.header("2. Playbook Criteria Checklist")

col1, col2 = st.columns(2)

with col1:
    news_grade = st.slider("News Catalyst Grade (1-5)", 1, 5, 3, 
                           help="5=FDA/Earnings, 4=Strong PR, 3=Neutral, 2=Fluff, 1=Dilution/Bad")
    float_check = st.checkbox("Low Float (< 10M shares)", value=False)
    chart_check = st.checkbox("Clean Daily Chart / Near Breakout", value=False)
    rvol_check = st.checkbox("Unusual Volume (RVOL > 3x)", value=False)
    gap_check = st.checkbox("Pre-Market Gap > 15%", value=False)

with col2:
    pm_vol_check = st.checkbox("Pre-Market Volume > 500k", value=False)
    dilution_check = st.checkbox("No Active Dilution (S-3/ATM)", value=False)
    time_check = st.checkbox("Peak Time (9:30 AM - 10:30 AM)", value=False)
    rr_check = st.checkbox("2:1 Upside Available Before Resistance", value=False)
    support_check = st.checkbox("Holding VWAP / Key Level", value=False)

# Calculate Score
score = 0
if news_grade >= 4: score += 20
if float_check: score += 15
if chart_check: score += 15
if rvol_check: score += 10
if gap_check: score += 10
if pm_vol_check: score += 10
if dilution_check: score += 5
if time_check: score += 5
if rr_check: score += 5
if support_check: score += 5

# Grade Assignment
if score >= 90:
    grade, color = "A-Setup (Full Sizing Allowed)", "#2ecc71"
elif score >= 75:
    grade, color = "B-Setup (Half Sizing Allowed)", "#f1c40f"
elif score >= 60:
    grade, color = "C-Setup (Quarter Sizing / Scalp)", "#e67e22"
else:
    grade, color = "F-Setup (NO TRADE / WATCH ONLY)", "#e74c3c"

st.markdown(f"### Playbook Score: <span style='color:{color}'>{score} / 100 ({grade})</span>", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# SECTION 3: DUAL-INPUT POSITION CALCULATOR
# ==========================================
st.header("3. Position Sizing & 2:1 Calculator")

entry_price = st.number_input("Entry Price ($)", min_value=0.01, value=2.00, step=0.01)
stop_loss = st.number_input("Stop Loss ($)", min_value=0.01, value=1.85, step=0.01)

risk_per_share = entry_price - stop_loss

if risk_per_share <= 0:
    st.error("Stop Loss must be lower than the Entry Price!")
else:
    # Toggle for input type
    calc_mode = st.radio("How do you want to size this trade?", ("By Cash Amount ($)", "By Number of Shares"))
    
    shares = 0
    cash_used = 0.0
    
    if calc_mode == "By Cash Amount ($)":
        cash_input = st.number_input("Enter Cash Investment ($)", min_value=0.0, value=2000.0, step=100.0)
        shares = math.floor(cash_input / entry_price) if entry_price > 0 else 0
        cash_used = shares * entry_price
    else:
        shares_input = st.number_input("Enter Number of Shares", min_value=0, value=1000, step=100)
        shares = shares_input
        cash_used = shares * entry_price

    # 2:1 Target Calculation
    target_price = entry_price + (2 * risk_per_share)
    total_risk = shares * risk_per_share
    potential_reward = shares * (target_price - entry_price)

    # Output Results
    st.markdown("### 📊 Trade Plan Metrics")
    
    col_out1, col_out2 = st.columns(2)
    with col_out1:
        st.metric(label="Shares to Buy", value=f"{shares:,}")
        st.metric(label="Total Cash Required", value=f"${cash_used:,.2f}")
        st.metric(label="Total Capital at Risk", value=f"${total_risk:,.2f}")
        
    with col_out2:
        st.metric(label="Strict 2:1 Profit Target", value=f"${target_price:.2f}")
        st.metric(label="Potential Max Reward", value=f"${potential_reward:,.2f}")
        st.metric(label="Reward-to-Risk Ratio", value="2.0 : 1")

    # Real-time warnings based on setup quality
    if score < 60:
        st.error("⚠️ Playbook Rule Broken: This is an F-Setup. Execution is locked based on your criteria.")
    elif score < 75 and total_risk > 50:
        st.warning("⚠️ Warning: This is a C-Setup. Consider reducing your size/risk further.")
