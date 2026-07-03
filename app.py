Here is the updated code.

I added the extended hours parameter to both charts. Note that **Daily charts do not physically show pre-market action** because a daily candle aggregates the entire day into one bar. However, your **Intraday chart (1m, 5m, 15m, 30m)** will now display all the pre-market and after-hours data.

*(If you ever don't see it on a specific ticker, just click the little "EXT" button at the bottom right of the chart to toggle it on/off).*

Replace your `app.py` code in GitHub with this block and commit the changes:

```python
import streamlit as st
import streamlit.components.v1 as components
import math
import yfinance as yf

# Set mobile-friendly page config
st.set_page_config(page_title="Trading Playbook", layout="centered")

def format_number(num):
    if num is None or num == 'N/A': return "N/A"
    try:
        num = float(num)
        if num >= 1_000_000_000: return f"{num/1_000_000_000:.2f}B"
        elif num >= 1_000_000: return f"{num/1_000_000:.2f}M"
        elif num >= 1_000: return f"{num/1_000:.2f}K"
        else: return f"{num:.2f}"
    except:
        return "N/A"

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
  "extended_hours": true,
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
  "extended_hours": true,
  "container_id": "tv_intraday"
}});
  </script>
</div>
"""
components.html(tv_intraday_html, height=550)

st.markdown("---")

# ==========================================
# SECTION 2: LIVE STOCK STATS (COLLAPSIBLE)
# ==========================================
st.header("2. Live Stock Stats")

with st.expander(f"📉 Click to Show/Hide Live Stats for {ticker}", expanded=False):
    if st.button(f"📊 Fetch / Refresh Stats"):
        with st.spinner("Pulling market data..."):
            try:
                t = yf.Ticker(ticker)
                info = t.info
                
                # Fetch intraday data to calculate VWAP
                hist = t.history(period="1d", interval="1m")
                
                c_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                op = info.get('open', 'N/A')
                day_low = info.get('dayLow', 'N/A')
                day_high = info.get('dayHigh', 'N/A')
                day_range = f"{day_low} - {day_high}" if day_low != 'N/A' else "N/A"
                vol = format_number(info.get('volume'))
                prev_close = info.get('previousClose', 'N/A')
                mcap = format_number(info.get('marketCap'))
                avg_vol = format_number(info.get('averageVolume'))
                
                # Float fallback
                float_val = info.get('floatShares', info.get('sharesOutstanding', 'N/A'))
                float_str = format_number(float_val)
                
                # 52w High Logic
                high_52 = info.get('fiftyTwoWeekHigh', 0)
                if c_price and high_52:
                    if c_price >= high_52:
                        dist_52h = f"${high_52:.2f} (AT HIGH)"
                    else:
                        diff_pct = ((high_52 - c_price) / high_52) * 100
                        dist_52h = f"${high_52:.2f} (-{diff_pct:.0f}%)"
                else:
                    dist_52h = "N/A"

                # 52w Low Logic
                low_52 = info.get('fiftyTwoWeekLow', 0)
                if c_price and low_52:
                    if c_price <= low_52:
                        dist_52l = f"${low_52:.2f} (AT LOW)"
                    else:
                        diff_pct = ((c_price - low_52) / low_52) * 100
                        dist_52l = f"${low_52:.2f} (+{diff_pct:.0f}%)"
                else:
                    dist_52l = "N/A"
                    
                # Short Interest Logic
                shares_short = format_number(info.get('sharesShort'))
                short_pct = info.get('shortPercentOfFloat')
                short_pct_str = f"{short_pct * 100:.2f}%" if short_pct else "N/A"
                short_ratio = info.get('shortRatio', 'N/A')

                # VWAP Logic
                if not hist.empty and hist['Volume'].sum() > 0:
                    hist['Typical'] = (hist['High'] + hist['Low'] + hist['Close']) / 3
                    vwap = (hist['Typical'] * hist['Volume']).sum() / hist['Volume'].sum()
                    above_vwap = "Yes 🟢" if c_price > vwap else "No 🔴"
                else:
                    above_vwap = "N/A"

                # Display Metrics Grid
                c1, c2, c3 = st.columns(3)
                c1.metric("Open", op)
                c2.metric("Day's Range", day_range)
                c3.metric("Volume", vol)
                
                c1.metric("Prev Close", prev_close)
                c2.metric("Market Cap", mcap)
                c3.metric("AVG Vol (3m)", avg_vol)
                
                c1.metric("Shares Short", shares_short)
                c2.metric("Float", float_str)
                c3.metric("52w High", dist_52h)
                
                c1.metric("Short % of Float", short_pct_str)
                c2.metric("Short Ratio", short_ratio)
                c3.metric("52w Low", dist_52l)
                
                st.markdown("---")
                st.metric("Above VWAP", above_vwap)

            except Exception as e:
                st.error("Data fetch failed. Verify ticker symbol.")

st.markdown("---")

# ==========================================
# SECTION 3: TRADER DISCIPLINE CHECK
# ==========================================
st.header("3. Discipline Check")
distraction_check = st.radio(
    "Is this stock the active volume leader, or a slow distraction?",
    ("🔥 Active Runner (Surging Volume & Liquidity)", "💤 Illiquid Former Runner (Boring/Consolidating)")
)

if distraction_check == "💤 Illiquid Former Runner (Boring/Consolidating)":
    st.error("🛑 WAKE UP: Stop watching dead tickers. Go find the active volume leader. Playbook is locked.")
    st.stop() 

st.markdown("---")

# ==========================================
# SECTION 4: PLAYBOOK CHECKLIST (100 PTS)
# ==========================================
st.header("4. Playbook Criteria Checklist")

col1, col2 = st.columns(2)

with col1:
    news_grade = st.slider("News Catalyst Grade (1-5)", 1, 5, 3, 
                           help="5=FDA/Earnings, 4=Strong PR, 3=Neutral, 2=Fluff, 1=Dilution/Bad")
    float_check = st.checkbox("Low Float (< 10M shares)", value=False)
    chart_check = st.checkbox("Clean Daily Chart / Near Breakout", value=False)
    open_skies = st.checkbox("🌌 Open Skies (No Daily Overhead Resistance)", value=False)
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
if float_check: score += 10
if chart_check: score += 10
if open_skies: score += 10
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
# SECTION 5: STOCK PROFIT CALCULATOR
# ==========================================
st.header("5. Stock Profit Calculator")

if "share_price_input" not in st.session_state:
    st.session_state.share_price_input = 3.50

def get_live_price():
    try:
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
    st.markdown("<br>", unsafe_allow_html=True) 
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

```
