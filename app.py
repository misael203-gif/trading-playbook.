import streamlit as st
import streamlit.components.v1 as components
import math
import yfinance as yf

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
ticker = st.text_input("Ticker Symbol", "CWD").upper()

# --- Daily Chart ---
st.subheader("Daily Chart")
tv_daily_html = f"""
<div class="tradingview-widget-container" style="height: 550px; width: 100%;">
  <div id="tv_daily" style="height: 100%; width: 100%;"></div>
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
components.html(tv_daily_html, height=550)

# --- Intraday Chart ---
st.subheader("Intraday Chart")
timeframe = st.radio("Select Intraday Timeframe", ["1 Minute", "5 Minute", "15 Minute", "30 Minute"], horizontal=True)

interval_map = {"1 Minute": "1", "5 Minute": "5", "15 Minute": "15", "30 Minute": "30"}
interval = interval_map[timeframe]

tv_intraday_html = f"""
<div class="tradingview-widget-container" style="height: 550px; width: 100%;">
  <div id="tv_intraday" style="height: 100%; width: 100%;"></div>
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
components.html(tv_intraday_html, height=550)

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
    grade, color = "A-Setup (Full Sizing)", "#2ecc71"
elif score >= 75:
    grade, color = "B-Setup (Half Sizing)", "#f1c40f"
elif score >= 60:
    grade, color = "C-Setup (Quarter Sizing / Scalp)", "#e67e22"
else:
    grade, color = "F-Setup (NO TRADE / WATCH ONLY)", "#e74c3c"

st.markdown(f"### Score: <span style='color:{color}'>{score} / 100 ({grade})</span>", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# SECTION 3: STOCK PROFIT CALCULATOR
# ==========================================
st.header("3. Stock Profit Calculator")

# Initialize session state for the share price so the button can update it
if "share_price_input" not in st.session_state:
    st.session_state.share_price_input = 3.50

def get_live_price():
    try:
        # Fetch the last day's data for the ticker and grab the closing price
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            st.session_state.share_price_input = float(data['Close'].iloc[-1])
    except:
        pass

# --- BUY SECTION ---
st.subheader("BUY")

col_price, col_btn = st.columns([2, 1])
with col_price:
    share_price = st.number_input("Share Price ($)", min_value=0.0001, step=0.01, format="%.4f", key="share_price_input")
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True) # Adds vertical spacing to align the button with the input box
    st.button("🔄 Auto-Fill Live Price", on_click=get_live_price)

calc_mode = st.radio("Sizing Method", ("# of Shares", "Cash Outlay ($)"), horizontal=True)

shares = 0.0
cash_outlay = 0.0

if calc_mode == "# of Shares":
    shares = st.number_input("# of Shares", min_value=0.0, value=1000.0, step=100.0)
    cash_outlay = shares * share_price
    st.info(f"Calculated Cash Outlay: **${cash_outlay:,.2f}**")
else:
    cash_input = st.number_input("Cash Outlay ($)", min_value=0.0, value=1000.0, step=100.0)
    shares = cash_input / share_price if share_price > 0 else 0
    cash_outlay = cash_input
    st.info(f"Calculated # of Shares: **{shares:,.4f}**")

# --- SELL SECTION ---
st.subheader("SELL")
selling_price = st.number_input("Selling Price ($)", min_value=0.0001, value=5.00, step=0.01, format="%.4f")
commission = st.number_input("Commission Included ($)", min_value=0.0, value=0.0, step=1.0)

# Calculations
gross_proceeds = shares * selling_price
net_profit = (gross_proceeds - cash_outlay) - commission
percent_return = (net_profit / cash_outlay) * 100 if cash_outlay > 0 else 0.0

col_out1, col_out2 = st.columns(2)
with col_out1:
    st.metric("Net Profit", f"${net_profit:,.2f}")
with col_out2:
    st.metric("% of Return", f"{percent_return:,.2f}%")

st.markdown("---")

# --- PLAYBOOK RISK CHECK ---
st.subheader("Playbook Risk Check")
stop_loss = st.number_input("Planned Stop Loss ($)", min_value=0.0001, value=share_price * 0.95, step=0.01, format="%.4f")
risk_per_share = share_price - stop_loss

if risk_per_share > 0:
    target_price = share_price + (2 * risk_per_share)
    total_risk = shares * risk_per_share
    
    st.write(f"**Strict 2:1 Target:** ${target_price:,.4f}")
    st.write(f"**Total Capital at Risk:** ${total_risk:,.2f}")
    
    if selling_price < target_price:
        st.warning(f"⚠️ Your Selling Price (${selling_price}) is below your strict 2:1 target (${target_price:,.4f}).")
    if score < 60:
        st.error("🛑 Playbook Rule Broken: This is an F-Setup. Do not execute.")
else:
    st.error("Stop Loss must be lower than the Share Price.")
