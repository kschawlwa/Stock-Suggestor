# Source: @DeepCharts Youtube Channel (https://www.youtube.com/@DeepCharts)

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import ta

##########################################################################################
## PART 1: Define Functions for Pulling, Processing, and Creating Techincial Indicators ##
##########################################################################################

# Fetch stock data based on the ticker, period, and interval


def fetch_stock_data(ticker, period, interval):
    end_date = datetime.now()
    if period == '1wk':
        start_date = end_date - timedelta(days=7)
        data = yf.download(ticker, start=start_date,
                           end=end_date, interval=interval)
    else:
        data = yf.download(ticker, period=period, interval=interval)
    return data

# Process data to ensure it is timezone-aware and has the correct format


def process_data(data):
    if data.index.tzinfo is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert('Asia/Kolkata')
    data.reset_index(inplace=True)
    data.rename(columns={'Date': 'Datetime'}, inplace=True)
    return data

# Calculate basic metrics from the stock data


def calculate_metrics(data):
    last_close = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[0]
    change = last_close - prev_close
    pct_change = (change / prev_close) * 100
    high = data['High'].max()
    low = data['Low'].min()
    volume = data['Volume'].sum()
    return last_close, change, pct_change, high, low, volume

# Add simple moving average (SMA) and exponential moving average (EMA) indicators


def add_technical_indicators(data):
    data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
    data['SMA_50'] = ta.trend.sma_indicator(data['Close'], window=50)
    data['SMA_200'] = ta.trend.sma_indicator(data['Close'], window=200)
    data['EMA_20'] = ta.trend.ema_indicator(data['Close'], window=20)
    return data

###############################################
## PART 2: Creating the Dashboard App layout ##
###############################################


# Set up Streamlit page layout
st.set_page_config(layout="wide")
st.title('Real Time Stock Dashboard')


# 2A: SIDEBAR PARAMETERS ############

# Sidebar for user input parameters
st.sidebar.header('Chart Parameters')
ticker = st.sidebar.text_input('Ticker', 'RELIANCE.NS')
time_period = st.sidebar.selectbox(
    'Time Period', ['1d', '1wk', '1mo', '1y', '2y', '3y', '5y', '10y', 'max'])
chart_type = st.sidebar.selectbox('Chart Type', ['Candlestick', 'Line'])
indicators = st.sidebar.multiselect(
    'Technical Indicators', ['SMA 20', 'SMA 50', 'SMA 200', 'EMA 20'])

# Mapping of time periods to data intervals
interval_mapping = {
    '1d': '1m',
    '1wk': '30m',
    '1mo': '1d',
    '1y': '1d',
    '2y': '1d',
    '3y': '1d',
    '5y': '1d',
    '10y': '1d',
    'max': '1d'
}


# 2B: MAIN CONTENT AREA ############

# Define to 0 so it dosent popop a NameError
sma_20 = 0
sma_200 = 0
sma_50 = 0
data = {}

if ((sma_200 and sma_20 and sma_50) == 0):
    st.toast("**Click 'Update' to fetch the latest data.**")

# Update the dashboard based on user input
if st.sidebar.button('Update'):
    st.success("**Strategy recommendations are shown at the bottom.**")
    data = fetch_stock_data(ticker, time_period, interval_mapping[time_period])
    data.columns = data.columns.droplevel(1)
    data = process_data(data)
    data = add_technical_indicators(data)
    last_close, change, pct_change, high, low, volume = calculate_metrics(data)

    # Extract SMA values
    sma_20 = data['SMA_20'].iloc[-1]  # Latest SMA 20 value
    sma_50 = data['SMA_50'].iloc[-1]  # Latest SMA 50 value
    sma_200 = data['SMA_200'].iloc[-1]  # Latest SMA 200 value

    # Display main metrics
    st.metric(label=f"{ticker} Last Price", value=f"{last_close:.2f} ₹",
              delta=f"{change:.2f} ({pct_change:.2f}%)")

    col1, col2, col3 = st.columns(3)
    col1.metric("High", f"{high:.2f} ₹")
    col2.metric("Low", f"{low:.2f} ₹")
    col3.metric("Volume", f"{volume:,}")

    # Plot the stock price chart
    fig = go.Figure()
    if chart_type == 'Candlestick':
        fig.add_trace(go.Candlestick(x=data['Datetime'],
                                     open=data['Open'],
                                     high=data['High'],
                                     low=data['Low'],
                                     close=data['Close']))
    else:
        fig = px.line(data, x='Datetime', y='Close')

    # Add selected technical indicators to the chart
    for indicator in indicators:
        if indicator == 'SMA 20':
            fig.add_trace(go.Scatter(
                x=data['Datetime'], y=data['SMA_20'], name='SMA 20'))
        elif indicator == 'SMA 50':
            fig.add_trace(go.Scatter(
                x=data['Datetime'], y=data['SMA_50'], name='SMA 50'))
        elif indicator == 'SMA 200':
            fig.add_trace(go.Scatter(
                x=data['Datetime'], y=data['SMA_200'], name='SMA 200'))
        elif indicator == 'EMA 20':
            fig.add_trace(go.Scatter(
                x=data['Datetime'], y=data['EMA_20'], name='EMA 20'))

    # Format graph
    fig.update_layout(title=f'{ticker} {time_period.upper()} Chart',
                      xaxis_title='Time',
                      yaxis_title='Price (₹)',
                      height=700)
    st.plotly_chart(fig, use_container_width=True)

    # Display historical data and technical indicators
    st.subheader('Historical Data')
    st.dataframe(data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']])
    st.subheader('Technical Indicators')
    st.dataframe(data[['Datetime', 'SMA_20', 'SMA_50', 'SMA_200', 'EMA_20']])
    # Print SMA vlaues
    st.subheader("Latest SMA Values")
    st.write(f"SMA 20: {sma_20:.2f} ₹")
    st.write(f"SMA 50: {sma_50:.2f} ₹")
    st.write(f"SMA 200: {sma_200:.2f} ₹")

# 2C: SIDEBAR PRICES ############

# Sidebar section for real-time stock prices of selected symbols
st.sidebar.header('Real-Time Stock Prices')
stock_symbols = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS']
for symbol in stock_symbols:
    real_time_data = fetch_stock_data(symbol, '1d', '1m')
    if not real_time_data.empty:
        real_time_data = process_data(real_time_data)
        last_price = float(real_time_data['Close'].iloc[-1])
        change = float(last_price - real_time_data['Open'].iloc[0])
        pct_change = float((change / real_time_data['Open'].iloc[0]) * 100)
        st.sidebar.metric(f"{symbol}", f"{last_price:.2f} ₹",
                          f"{change:.2f} ({pct_change:.2f}%)")

# Get only date and format to words
# data['Datetime'] = data['Datetime'].dt.strftime('%B %d, %Y')

# Clickable subheader, mimics st.subheader() but makes it a clickable link
st.markdown(
    "<h3><a href='https://youtu.be/QwZIbSiENMI?feature=shared' target='_blank' style='text-decoration: none; color: inherit;'>EMA Strategy</a></h3>",
    unsafe_allow_html=True
)


# EMA Strategy Conditions
def buyConditon(data, i):
    return (
        data['Close'][i] < data['SMA_200'][i]
        and data['Close'][i] < data['SMA_50'][i]
        and data['Close'][i] < data['SMA_20'][i]
        and data['SMA_200'][i] > data['SMA_50'][i]
        and data['SMA_50'][i] > data['SMA_20'][i]
    )


def sellCondition(data, j):
    return (
        data['Close'][j] > data['SMA_200'][j]
        and data['Close'][j] > data['SMA_50'][j]
        and data['Close'][j] > data['SMA_20'][j]
        and data['SMA_20'][j] > data['SMA_50'][j]
        and data['SMA_50'][j] > data['SMA_200'][j]
    )


def calculate_ROI(buy, sell):
    return (((sell - buy) / buy) * 100)


# Variables for EMA strategy
def ema_strategy():
    buy_index = 0
    buying_price = 0
    count = 1

    i = 0
    while i < len(data):
        buy_signal_found = False
        for a in range(i, len(data)):
            if buyConditon(data, a):
                buy_index = a
                st.info(
                    f"✅ Buy Condition **{count}** Met!\\\n**Date: {data['Datetime'][a]}** \\\n**Buying Price: {data['Close'][a]:.2f}** ")
                buying_price = data['Close'][a]
                buy_signal_found = True
                break

        if not buy_signal_found:
            st.error("OOPS NO BUY SIGNAL")
            break

        sell_signal_found = False
        for j in range(buy_index + 1, len(data)):
            if sellCondition(data, j):
                sell_index = j
                selling_price = data['Close'][j]
                st.error(
                    f"❌ Sell Condition **{count}** Met!\\\n**Date: {data['Datetime'][j]}** \\\n**Selling Price: {data['Close'][j]:.2f}** \\\n **Total Return On Investment (ROI) : {calculate_ROI(buying_price, selling_price):.2f}%**")
                count += 1
                i = sell_index + 1
                sell_signal_found = True
                break

        if not sell_signal_found:
            st.warning("⚠️ Waiting for sell signal.")
            break


with st.expander("Signals"):
    ema_strategy()

# Sidebar information section
st.sidebar.subheader('About')
st.sidebar.info(
    'This dashboard provides stock data and technical indicators for various time periods. Use the sidebar to customize your view.')
