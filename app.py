import streamlit as st
import streamlit.components.v1 as components
import math
import yfinance as yf
import pandas as pd

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

# Create tabs for each ticker + 1 comparison tab
tabs = st.tabs(tickers + ["🏆 Compare Best Setups"])

def get_live_price(t):
    try:
        data = yf.Ticker(t).history(period="1d")
        if not data.empty:
            st.session_state[f"share_price_{t}"] = float(data['Close'].iloc[-1])
    except:
        pass

# Render Playbook for each ticker in its respective tab
for i, ticker in enumerate(tickers):
    # Initialize default blank stats for the leaderboard if not fetched yet
    if ticker not in st.session_state.ticker_stats:
        st.session_state.ticker_stats[ticker] = {
            "Float": "N/A",
            "Volume": "N/A",
            "Short %": "N/A",
            "52w High": "N/A",
            "VWAP": "N/A"
        }

    with tabs[i]:
        # ==========================================
        # SECTION 1: LIVE TRADINGVIEW CHARTS
        # ==========================================
        st.header(f"1. Live Charts: {ticker}")

        # --- Daily Chart ---
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

        # --- Intraday Chart ---
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
                        
                        high_52 = info.get('fiftyTwoWeekHigh', 0)
                        if c_price and high_52:
                            if c_price >= high_52:
                                dist_52h = f"${high_52:.2f} (AT HIGH)"
                            else:
                                diff_pct = ((high_52 - c_price) / high_52) * 100
                                dist_52h = f"${high_52:.2f} (-{diff_pct:.0f}%)"
                        else:
                            dist_52h = "N/A"

                        low_52 = info.get('fiftyTwoWeekLow', 0)
                        if c_price and low_52:
                            if c_price <= low_52:
                                dist_52l = f"${low_52:.2f} (AT LOW)"
                            else:
                                diff_pct = ((c_price - low_52) / low_52) * 100
                                dist_52l = f"${low_52:.2f} (+{diff_pct:.0f}%)"
                        else:
                            dist_52l = "N/A"
                            
                        shares_short = format_number(info.get('sharesShort'))
                        short_pct = info.get('shortPercentOfFloat')
                        short_pct_str = f"{short_pct * 100:.2f}%" if short_pct else "N/A"
                        short_ratio = info.get('shortRatio', 'N/A')

                        if not hist.empty and hist['Volume'].sum() > 0:
                            hist['Typical'] = (hist['High'] + hist['Low'] + hist['Close']) / 3
                            vwap = (hist['Typical'] * hist['Volume']).sum() / hist['Volume'].sum()
                            above_vwap = "Yes 🟢" if c_price > vwap else "No 🔴"
                        else:
                            above_vwap = "N/A"

                        # Save crucial metrics for Leaderboard visibility
                        st.session_state.ticker_stats[ticker] = {
                            "Float": float_str,
                            "Volume": vol,
                            "Short %": short_pct_str,
                            "52w High": dist_52h,
                            "VWAP": above_vwap
                        }

                        # Display Dashboard Grids
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
                "Score": 0, 
                "Grade": "LOCK", 
                "Status": "❌ Locked",
                "Float": "N/A", "Volume": "N/A", "Short %": "N/A", "52w High": "N/A", "VWAP": "N/A"
            }
            continue

        st.markdown("---")

        # ==========================================
        # SECTION 4: PLAYBOOK CHECKLIST (100 PTS)
        # ==========================================
        st.header("4. Playbook Criteria Checklist")

        col1, col2 = st.columns(2)

        with col1:
            news_grade = st.slider("News Catalyst Grade (1-5)", 1, 5, 3, key=f"news_{ticker}")
            float_check = st.checkbox("Low Float (< 10M shares)", value=False, key=f"float_{ticker}")
            chart_check = st.checkbox("Clean Daily Chart / Near Breakout", value=False, key=f"chart_{ticker}")
            open_skies = st.checkbox("🌌 Open Skies (No Daily Overhead Resistance)", value=False, key=f"skies_{ticker}")
            rvol_check = st.checkbox("Unusual Volume (RVOL > 3x)", value=False, key=f"rvol_{ticker}")
            gap_check = st.checkbox("Pre-Market Gap > 15%", value=False, key=f"gap_{ticker}")

        with col2:
            pm_vol_check = st.checkbox("Pre-Market Volume > 500k", value=False, key=f"pmvol_{ticker}")
            dilution_check = st.checkbox("No Active Dilution (S-3/ATM)", value=False, key=f"dilution_{ticker}")
            time_check = st.checkbox("Peak Time (9:30 AM - 10:30 AM)", value=False, key=f"time_{ticker}")
            rr_check = st.checkbox("2:1 Upside Available Before Resistance", value=False, key=f"rr_{ticker}")
            support_check = st.checkbox("Holding VWAP / Key Level", value=False, key=f"supp_{ticker}")

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

        if score >= 90: grade, color, status = "A-Setup", "#2ecc71", "✅ Prime"
        elif score >= 75: grade, color, status = "B-Setup", "#f1c40f", "⚠️ Viable"
        elif score >= 60: grade, color, status = "C-Setup", "#e67e22", "⚠️ High Risk"
        else: grade, color, status = "F-Setup", "#e74c3c", "❌ Skip"

        st.markdown(f"### Score: <span style='color:{color}'>{score} / 100 ({grade})</span>", unsafe_allow_html=True)
        
        # Combine Score + Fetched Stats for the Leaderboard mapping
        st.session_state.scores_data[ticker] = {
            "Score": score,
            "Grade": grade,
            "Status": status,
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

        if f"share_price_{ticker}" not in st.session_state:
            st.session_state[f"share_price_{ticker}"] = 3.50

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
        with col_out1:
            st.metric("Net Profit", f"${net_profit:,.2f}")
        with col_out2:
            st.metric("% of Return", f"{percent_return:,.2f}%")

        st.markdown("---")

        st.subheader("Playbook Risk Check")
        stop_loss = st.number_input("Planned Stop Loss ($)", min_value=0.0001, value=share_price * 0.95, step=0.01, format="%.4f", key=f"sl_{ticker}")
        risk_per_share = share_price - stop_loss

        if risk_per_share > 0:
            target_price = share_price + (2 * risk_per_share)
            total_risk = shares * risk_per_share
            st.write(f"**Strict 2:1 Target:** ${target_price:,.4f}")
            st.write(f"**Total Capital at Risk:** ${total_risk:,.2f}")
            if selling_price < target_price:
                st.warning(f"⚠️ Your Selling Price is below your strict 2:1 target.")
            if score < 60:
                st.error("🛑 Playbook Rule Broken: This is an F-Setup.")
        else:
            st.error("Stop Loss must be lower than the Share Price.")

# ==========================================
# COMPARISON TAB LOGIC
# ==========================================
with tabs[-1]:
    st.header("🏆 Morning Leaderboard")
    st.write("Compare setups side-by-side. Focus on low floats and high relative volume to spot maximum volatility.")
    
    if st.session_state.scores_data:
        df = pd.DataFrame.from_dict(st.session_state.scores_data, orient='index')
        df.index.name = 'Ticker'
        df.reset_index(inplace=True)
        
        # Sort by Playbook Score first
        df = df.sort_values(by='Score', ascending=False).reset_index(drop=True)
        
        # Display the complete matrix
        st.table(df)
        
        top_ticker = df.iloc[0]['Ticker']
        top_score = df.iloc[0]['Score']
        
        if top_score >= 75:
            st.success(f"🚀 **Top Focus:** {top_ticker} leads with a playbook score of {top_score}.")
        elif top_score >= 60:
            st.warning(f"⚠️ **Caution:** {top_ticker} is your highest scoring ticker, but it's high risk ({top_score} pts).")
        else:
            st.error("🛑 **No Play:** No tickers passed minimum guidelines.")
    else:
        st.info("Fill out your ticker checklists to update the master grid.")
