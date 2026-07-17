import streamlit as st
import streamlit.components.v1 as components
import math
import yfinance as yf
import pandas as pd
import datetime
import time
import calendar

# Set mobile-friendly page config
st.set_page_config(page_title="Trading Playbook", layout="wide")

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

# ==========================================
# MASTER DATA LOADER (Runs in background)
# ==========================================
@st.cache_data(ttl=60) # Caches data for 60 seconds to keep app blazing fast while staying real-time
def load_trade_data():
    try:
        sheet_id = "1Xvlszud1_o6F-SWEfP_ckcL9yWnEs40Hm75DYgnwY7o"
        tab_id = "1620057635" 
        
        # Adding a time-based cache-buster to the URL forces Google to send a fresh file
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={tab_id}&t={int(time.time())}"
        
        df = pd.read_csv(csv_url)
        df = df.iloc[:, :17] # Stop loading at Column Q
        
        # Clean the Date and P/L columns so the computer can do math on them
        if 'Date' in df.columns:
            # Strip out any invisible spaces or non-breaking characters
            clean_date = df['Date'].astype(str).str.replace(r'\xa0', ' ', regex=True).str.strip()
            df['Date_Parsed'] = pd.to_datetime(clean_date, errors='coerce')
            
        if 'P/L' in df.columns:
            # Strip out dollar signs, commas, and handle negative accounting formats
            clean_pl = df['P/L'].astype(str).str.replace(r'[\$,\s]', '', regex=True).str.replace(r'^\((.*)\)$', r'-\1', regex=True)
            df['P/L_Num'] = pd.to_numeric(clean_pl, errors='coerce').fillna(0.0)
            
        return df
    except Exception as e:
        return pd.DataFrame()

# Load the data once for the whole app
df_trades = load_trade_data()

st.title("⚡ Momentum Trading Playbook")
st.write("Pre-Market Checklist & Risk Calculator")

# Input for multiple tickers (No default values)
tickers_input = st.text_input("Enter up to 5 Tickers (separated by commas)", "").upper()
tickers = [t.strip() for t in tickers_input.split(",") if t.strip()][:5]

st.markdown("---")

# Initialize session states for storing persistent data
if 'scores_data' not in st.session_state:
    st.session_state.scores_data = {}
if 'ticker_stats' not in st.session_state:
    st.session_state.ticker_stats = {}

# Cleanup memory: Remove any tickers from session state that are no longer in the search box
keys_to_delete_scores = [k for k in st.session_state.scores_data.keys() if k not in tickers]
for k in keys_to_delete_scores:
    del st.session_state.scores_data[k]

keys_to_delete_stats = [k for k in st.session_state.ticker_stats.keys() if k not in tickers]
for k in keys_to_delete_stats:
    del st.session_state.ticker_stats[k]

# Stop execution if no tickers are entered to keep the screen clean
if not tickers:
    st.info("Enter a ticker symbol above to start building your playbook.")
    st.stop()

# Create tabs for each ticker + Comparison + Risk Monitor + Calendar + Trade Log
tabs = st.tabs(tickers + ["🏆 Compare Best Setups", "🛡️ Risk & Drawdown Monitor", "📅 P/L Calendar", "📝 Trade Log"])

def get_live_price(t):
    try:
        data = yf.Ticker(t).history(period="1d")
        if not data.empty:
            st.session_state[f"share_price_{t}"] = float(data['Close'].iloc[-1])
    except:
        pass

# Render Playbook for each ticker in its respective tab
for i, ticker in enumerate(tickers):
    if ticker not in st.session_state.ticker_stats:
        st.session_state.ticker_stats[ticker] = {
            "Float": "N/A", "Volume": "N/A", "Short %": "N/A", "52w High": "N/A", "VWAP": "N/A"
        }
    
    if f"manual_float_{ticker}" not in st.session_state:
        st.session_state[f"manual_float_{ticker}"] = ""

    with tabs[i]:
        # ==========================================
        # SECTION 1: LIVE TRADINGVIEW CHARTS
        # ==========================================
        st.header(f"1. Live Charts: {ticker}")

        st.subheader("Daily Chart")
        tv_daily_html = f"""
        <div class="tradingview-widget-container" style="height: 550px; width: 100%;">
          <div id="tv_daily_{ticker}" style="height: 100%; width: 100%;"></div>
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
          "container_id": "tv_daily_{ticker}"
        }});
          </script>
        </div>
        """
        components.html(tv_daily_html, height=550)

        st.subheader("Intraday Chart")
        timeframe = st.radio("Select Intraday Timeframe", ["1 Minute", "5 Minute", "15 Minute", "30 Minute"], horizontal=True, key=f"tf_{ticker}")

        interval_map = {"1 Minute": "1", "5 Minute": "5", "15 Minute": "15", "30 Minute": "30"}
        interval = interval_map[timeframe]

        tv_intraday_html = f"""
        <div class="tradingview-widget-container" style="height: 550px; width: 100%;">
          <div id="tv_intraday_{ticker}" style="height: 100%; width: 100%;"></div>
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
          "container_id": "tv_intraday_{ticker}"
        }});
          </script>
        </div>
        """
        components.html(tv_intraday_html, height=550)

        st.markdown("---")

        # ==========================================
        # SECTION 2: LIVE STOCK STATS
        # ==========================================
        st.header("2. Live Stock Stats")

        with st.expander(f"📉 Click to Show/Hide Live Stats for {ticker}", expanded=False):
            if st.button(f"📊 Fetch / Refresh Stats for {ticker}", key=f"fetch_{ticker}"):
                with st.spinner(f"Pulling market data for {ticker}..."):
                    try:
                        t = yf.Ticker(ticker)
                        info = t.info
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
                        
                        float_val = info.get('floatShares', info.get('sharesOutstanding', 'N/A'))
                        float_str = format_number(float_val)
                        st.session_state[f"manual_float_{ticker}"] = float_str
                        
                        high_52 = info.get('fiftyTwoWeekHigh', 0)
                        if c_price and high_52:
                            if c_price >= high_52: dist_52h = f"${high_52:.2f} (AT HIGH)"
                            else: dist_52h = f"${high_52:.2f} (-{((high_52 - c_price) / high_52) * 100:.0f}%)"
                        else: dist_52h = "N/A"

                        low_52 = info.get('fiftyTwoWeekLow', 0)
                        if c_price and low_52:
                            if c_price <= low_52: dist_52l = f"${low_52:.2f} (AT LOW)"
                            else: dist_52l = f"${low_52:.2f} (+{((c_price - low_52) / low_52) * 100:.0f}%)"
                        else: dist_52l = "N/A"
                            
                        shares_short = format_number(info.get('sharesShort'))
                        short_pct = info.get('shortPercentOfFloat')
                        short_pct_str = f"{short_pct * 100:.2f}%" if short_pct else "N/A"
                        short_ratio = info.get('shortRatio', 'N/A')

                        if not hist.empty and hist['Volume'].sum() > 0:
                            hist['Typical'] = (hist['High'] + hist['Low'] + hist['Close']) / 3
                            vwap = (hist['Typical'] * hist['Volume']).sum() / hist['Volume'].sum()
                            above_vwap = "Yes 🟢" if c_price > vwap else "No 🔴"
                        else: above_vwap = "N/A"

                        st.session_state.ticker_stats[ticker] = {
                            "Float": float_str, "Volume": vol, "Short %": short_pct_str, 
                            "52w High": dist_52h, "VWAP": above_vwap
                        }

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
            ("🔥 Active Runner (Surging Volume & Liquidity)", "💤 Illiquid Former Runner (Boring/Consolidating)"),
            key=f"dist_{ticker}"
        )

        if distraction_check == "💤 Illiquid Former Runner (Boring/Consolidating)":
            st.error("🛑 Playbook is locked for this ticker.")
            st.session_state.scores_data[ticker] = {
                "Score": 0, "Grade": "LOCK", "Status": "❌ Locked",
                "Float": "N/A", "Volume": "N/A", "Short %": "N/A", "52w High": "N/A", "VWAP": "N/A"
            }
            continue

        st.markdown("---")

        # ==========================================
        # SECTION 4: PLAYBOOK CRITERIA CHECKLIST
        # ==========================================
        st.header("4. Playbook Criteria Checklist")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Long Attributes...")
            up_10 = st.radio("Up more than 10%", ["Y", "N"], horizontal=True, key=f"up_{ticker}")
            unusual_vol = st.radio("Have Unusual Volume", ["Y", "N"], horizontal=True, key=f"uvol_{ticker}")
            former_runner = st.radio("Former Runner", ["Y", "N"], horizontal=True, key=f"fr_{ticker}")
            catalyst_yn = st.radio("Catalyst (News/PR)", ["Y", "N"], horizontal=True, key=f"catyn_{ticker}")
            dollar_break = st.radio("Whole/Half $ Break", ["Y", "N"], horizontal=True, key=f"brk_{ticker}")
            clear_support = st.radio("Clear support to set risk", ["Y", "N"], horizontal=True, key=f"suppck_{ticker}")

        with col2:
            st.subheader("Quality of the setup?")
            float_category = st.selectbox("Float Category", ["Micro Float (< 1M) [10 pts]", "Low Float (1M - 10M) [8 pts]", "Medium Float (10M - 50M) [6 pts]", "High Float (50M+) [4 pts]"], key=f"fcat_{ticker}")
            setup_float = st.text_input("Actual Float Size", key=f"manual_float_{ticker}")
            support_area = st.text_input("Support area (for risk)", key=f"sarea_{ticker}")
            rating_catalyst = st.number_input("Rating of Catalyst (1-5)", min_value=1, max_value=5, value=3, key=f"rcat_{ticker}")

        score = 0
        if "Micro" in float_category: score += 10
        elif "Low" in float_category: score += 8
        elif "Medium" in float_category: score += 6
        elif "High" in float_category: score += 4

        if up_10 == "Y": score += 10
        if unusual_vol == "Y": score += 20 
        if former_runner == "Y": score += 10
        if catalyst_yn == "Y": score += 10
        if dollar_break == "Y": score += 10
        if clear_support == "Y": score += 10
        
        score += (rating_catalyst * 4)

        if score >= 90: grade, color, status = "A-Setup", "#2ecc71", "✅ Prime"
        elif score >= 75: grade, color, status = "B-Setup", "#f1c40f", "⚠️ Viable"
        elif score >= 60: grade, color, status = "C-Setup", "#e67e22", "⚠️ High Risk"
        else: grade, color, status = "F-Setup", "#e74c3c", "❌ Skip"

        st.markdown(f"### Score: <span style='color:{color}'>{score} / 100 ({grade})</span>", unsafe_allow_html=True)
        
        st.session_state.scores_data[ticker] = {
            "Score": score, "Grade": grade, "Status": status,
            "Float": st.session_state.ticker_stats[ticker]["Float"],
            "Volume": st.session_state.ticker_stats[ticker]["Volume"],
            "Short %": st.session_state.ticker_stats[ticker]["Short %"],
            "52w High": st.session_state.ticker_stats[ticker]["52w High"],
            "VWAP": st.session_state.ticker_stats[ticker]["VWAP"]
        }

        st.markdown("---")

        # ==========================================
        # SECTION 5: STOCK PROFIT CALCULATOR
        # ==========================================
        st.header("5. Stock Profit Calculator")
        if f"share_price_{ticker}" not in st.session_state: st.session_state[f"share_price_{ticker}"] = 3.50

        st.subheader("BUY")
        col_price, col_btn = st.columns([2, 1])
        with col_price:
            share_price = st.number_input("Share Price ($)", min_value=0.0001, step=0.01, format="%.4f", key=f"sp_input_{ticker}", value=st.session_state[f"share_price_{ticker}"])
            st.session_state[f"share_price_{ticker}"] = share_price
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True) 
            st.button("🔄 Auto-Fill Live Price", on_click=get_live_price, args=(ticker,), key=f"btn_{ticker}")

        calc_mode = st.radio("Sizing Method", ("# of Shares", "Cash Outlay ($)"), horizontal=True, key=f"cmode_{ticker}")
        shares = 0.0
        cash_outlay = 0.0

        if calc_mode == "# of Shares":
            shares = st.number_input("# of Shares", min_value=0.0, value=1000.0, step=100.0, key=f"shares_{ticker}")
            cash_outlay = shares * share_price
            st.info(f"Calculated Cash Outlay: **${cash_outlay:,.2f}**")
        else:
            cash_input = st.number_input("Cash Outlay ($)", min_value=0.0, value=1000.0, step=100.0, key=f"cashin_{ticker}")
            shares = cash_input / share_price if share_price > 0 else 0
            cash_outlay = cash_input
            st.info(f"Calculated # of Shares: **{shares:,.4f}**")

        st.subheader("SELL")
        selling_price = st.number_input("Selling Price ($)", min_value=0.0001, value=5.00, step=0.01, format="%.4f", key=f"sell_{ticker}")
        commission = st.number_input("Commission Included ($)", min_value=0.0, value=0.0, step=1.0, key=f"comm_{ticker}")

        gross_proceeds = shares * selling_price
        net_profit = (gross_proceeds - cash_outlay) - commission
        percent_return = (net_profit / cash_outlay) * 100 if cash_outlay > 0 else 0.0

        col_out1, col_out2 = st.columns(2)
        with col_out1: st.metric("Net Profit", f"${net_profit:,.2f}")
        with col_out2: st.metric("% of Return", f"{percent_return:,.2f}%")

        st.markdown("---")
        st.subheader("Playbook Risk Check")
        stop_loss = st.number_input("Planned Stop Loss ($)", min_value=0.0001, value=share_price * 0.85, step=0.01, format="%.4f", key=f"sl_{ticker}")
        risk_per_share = share_price - stop_loss

        if risk_per_share > 0:
            target_price = share_price + (2 * risk_per_share)
            total_risk = shares * risk_per_share
            st.write(f"**Strict 2:1 Target (30.00% minimum):** ${target_price:,.4f}")
            st.write(f"**Total Capital at Risk:** ${total_risk:,.2f}")
            
            if cash_outlay > 466.00: st.error("🛑 Playbook Rule Broken: Cash outlay exceeds your strict $466 limit.")
            if total_risk > 70.00: st.error("🛑 Playbook Rule Broken: Dollar amount at risk exceeds your strict $70 max loss per trade.")
            if selling_price < target_price: st.warning(f"⚠️ Your Selling Price is below your strict 2:1 target.")
            if score < 60: st.error("🛑 Playbook Rule Broken: This is an F-Setup.")
        else: st.error("Stop Loss must be lower than the Share Price.")

# ==========================================
# COMPARISON TAB LOGIC
# ==========================================
with tabs[-4]:
    st.header("🏆 Morning Leaderboard")
    st.write("Compare setups side-by-side. Focus on low floats and high relative volume to spot maximum volatility.")
    
    if st.session_state.scores_data:
        df = pd.DataFrame.from_dict(st.session_state.scores_data, orient='index')
        df.index.name = 'Ticker'
        df.reset_index(inplace=True)
        df = df.sort_values(by='Score', ascending=False).reset_index(drop=True)
        st.table(df)
        
        top_ticker = df.iloc[0]['Ticker']
        top_score = df.iloc[0]['Score']
        
        if top_score >= 75: st.success(f"🚀 **Top Focus:** {top_ticker} leads with a playbook score of {top_score}.")
        elif top_score >= 60: st.warning(f"⚠️ **Caution:** {top_ticker} is your highest scoring ticker, but it's high risk ({top_score} pts).")
        else: st.error("🛑 **No Play:** No tickers passed minimum guidelines.")
    else:
        st.info("Fill out your ticker checklists to update the master grid.")

# ==========================================
# RISK & DRAWDOWN MONITOR TAB LOGIC
# ==========================================
with tabs[-3]:
    st.header("🛡️ 6-Month Account Survival Dashboard")
    st.write("Track metrics to preserve your capital over a six-month trading horizon.")
    
    # Static Rules Sidebar/Section
    st.markdown("### 📌 Rule Mandates")
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    col_r1.metric("Starting Balance", "$3,500")
    col_r2.metric("Max Size Per Trade", "$466", "13.3% of Account")
    col_r3.metric("Max Loss Per Trade", "$70", "15% Position Stop")
    col_r4.metric("Max Daily Trades", "3")
    
    st.markdown("---")
    
    # 🗓️ LIVE CALENDAR SYNC
    st.markdown("### 🗓️ Sync with Trade Log")
    st.write("Select the dates below to automatically calculate your Intraday and Weekly P/L from your Google Sheet.")
    
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    
    col_cal1, col_cal2 = st.columns(2)
    with col_cal1:
        start_of_week = st.date_input("Start of Trading Week", value=monday)
    with col_cal2:
        current_day = st.date_input("Today's Date", value=today)

    daily_pl = 0.0
    weekly_pl = 0.0
    
    if not df_trades.empty and 'Date_Parsed' in df_trades.columns and 'P/L_Num' in df_trades.columns:
        mask_week = (df_trades['Date_Parsed'].dt.date >= start_of_week) & (df_trades['Date_Parsed'].dt.date <= current_day)
        mask_today = (df_trades['Date_Parsed'].dt.date == current_day)
        
        weekly_pl = float(df_trades[mask_week]['P/L_Num'].sum())
        daily_pl = float(df_trades[mask_today]['P/L_Num'].sum())

    st.markdown("### 📊 Active P/L Trackers (Live Synced)")
    col_in1, col_in2 = st.columns(2)
    col_in1.metric("Current Intraday P/L", f"${daily_pl:,.2f}")
    col_in2.metric("Current Weekly P/L", f"${weekly_pl:,.2f}")
    
    st.markdown("---")
    
    max_daily_drawdown = 140.00
    max_weekly_drawdown = 350.00
    
    remaining_daily = max_daily_drawdown + daily_pl if daily_pl < 0 else max_daily_drawdown
    remaining_weekly = max_weekly_drawdown + weekly_pl if weekly_pl < 0 else max_weekly_drawdown
    
    st.markdown("### 📉 Remaining Drawdown Buffers")
    col_m1, col_m2 = st.columns(2)
    
    if daily_pl <= -max_daily_drawdown:
        col_m1.metric("Daily Limit Status", f"${daily_pl:,.2f}", "⚠️ BREACHED", delta_color="inverse")
        st.error("🛑 **DAILY LOSS LIMIT BREACHED:** Shut down your platform immediately. Do not attempt another trade.")
    else:
        col_m1.metric("Daily Room Left", f"${remaining_daily:,.2f}", f"Current Daily P/L: ${daily_pl:,.2f}")
        
    if weekly_pl <= -max_weekly_drawdown:
        col_m2.metric("Weekly Limit Status", f"${weekly_pl:,.2f}", "🚨 SYSTEM LOCKED", delta_color="inverse")
        st.error("🛑 **WEEKLY DRAWDOWN CIRCUIT BREAKER HIT:** Market context is toxic for your playbook. You are locked out until next Monday.")
    else:
        col_m2.metric("Weekly Room Left", f"${remaining_weekly:,.2f}", f"Current Weekly P/L: ${weekly_pl:,.2f}")

    st.markdown("---")
    st.markdown("### 🧠 Self-Discipline Checklist")
    st.checkbox("I am executing outlays below $466 and utilizing strict 15% stops.")
    st.checkbox("I am refusing to average down on standard setups that go against my entry point.")
    st.checkbox("I am taking partial profits between 20% and 30% instead of holding for micro-cap home runs.")

# ==========================================
# P/L CALENDAR TAB LOGIC
# ==========================================
with tabs[-2]:
    st.header("📅 Daily P/L Calendar")
    
    today = datetime.date.today()
    col_y, col_m = st.columns(2)
    with col_y:
        selected_year = st.selectbox("Select Year", range(2023, 2035), index=range(2023, 2035).index(today.year))
    with col_m:
        selected_month = st.selectbox("Select Month", range(1, 13), index=today.month - 1, format_func=lambda x: calendar.month_name[x])
        
    st.markdown("---")
    
    daily_sums = {}
    if not df_trades.empty and 'Date_Parsed' in df_trades.columns:
        cal_df = df_trades.dropna(subset=['Date_Parsed'])
        cal_df = cal_df[(cal_df['Date_Parsed'].dt.year == selected_year) & (cal_df['Date_Parsed'].dt.month == selected_month)]
        daily_sums = cal_df.groupby(cal_df['Date_Parsed'].dt.day)['P/L_Num'].sum().to_dict()
        
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7)
    for i, day_name in enumerate(weekdays):
        cols[i].markdown(f"<div style='text-align:center; font-weight:bold; font-size:16px;'>{day_name}</div>", unsafe_allow_html=True)
        
    cal_matrix = calendar.monthcalendar(selected_year, selected_month)
    
    for week in cal_matrix:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
                else:
                    pl = daily_sums.get(day, 0.0)
                    if pl > 0:
                        color = "#2ecc71" 
                        pl_str = f"+${pl:,.2f}"
                    elif pl < 0:
                        color = "#e74c3c" 
                        pl_str = f"-${abs(pl):,.2f}"
                    else:
                        color = "gray"
                        pl_str = "$0.00"
                        
                    st.markdown(
                        f"""
                        <div style="border: 1px solid rgba(128, 128, 128, 0.3); border-radius: 8px; padding: 10px; margin-bottom: 10px; text-align: center; height: 80px;">
                            <div style="font-size: 14px; font-weight: bold; color: gray;">{day}</div>
                            <div style="font-size: 16px; font-weight: bold; color: {color}; margin-top: 5px;">{pl_str}</div>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

# ==========================================
# TRADE LOG TAB LOGIC (GOOGLE SHEETS)
# ==========================================
with tabs[-1]:
    st.header("📝 Google Sheets Trade Log")
    
    if not df_trades.empty:
        # Drop the background math columns so the table looks clean
        clean_df = df_trades.drop(columns=['Date_Parsed', 'P/L_Num'], errors='ignore')
        st.dataframe(clean_df, use_container_width=True)
    else:
        st.error("Could not load data from Google Sheets. Check your link and permissions.")
        
    # Button clears the 60-second cache and forces an immediate redownload
    if st.button("🔄 Refresh Trade Log"):
        st.cache_data.clear()
        st.rerun()
