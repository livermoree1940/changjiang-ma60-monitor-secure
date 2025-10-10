import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import adata
from utils_email import send_email_if_signal
import exchange_calendars as ecals

STOCK_LIST = [
    {"code": "600519", "name": "贵州茅台"},
    {"code": "601318", "name": "中国平安"},
]

ETF_LIST = [
    {"code": "515080", "name": "华夏上证50ETF"},
    {"code": "515450", "name": "标普500ETF"},
]

XSHG = ecals.get_calendar("XSHG")

def is_trade_day():
    today = pd.Timestamp(datetime.now().date())
    return today in XSHG.sessions_in_range(today, today)

def get_stock_data(stock_code, days=120):
    df = adata.stock.market.get_market(stock_code=stock_code, k_type=1, adjust_type=1)
    if df is None or df.empty or len(df) < 20:
        return None
    for col in ["close", "open", "high", "low", "volume", "amount"]:
        df[col] = df[col].astype(float)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.sort_values("trade_date")
    df["ma20"] = df["close"].rolling(window=20).mean()
    df["std"] = df["close"].rolling(window=20).std()
    df["upper"] = df["ma20"] + 2 * df["std"]
    df["lower"] = df["ma20"] - 2 * df["std"]
    return df.tail(days)

def get_etf_data(etf_code, days=120):
    df = adata.fund.market.get_market_etf(fund_code=etf_code, k_type=1)
    if df is None or df.empty or len(df) < 20:
        return None
    for col in ["close", "open", "high", "low", "volume", "amount"]:
        df[col] = df[col].astype(float)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.sort_values("trade_date")
    df["ma20"] = df["close"].rolling(window=20).mean()
    df["std"] = df["close"].rolling(window=20).std()
    df["upper"] = df["ma20"] + 2 * df["std"]
    df["lower"] = df["ma20"] - 2 * df["std"]
    return df.tail(days)

def plot_boll(df, name, filename):
    plt.figure(figsize=(15,8))
    plt.plot(df["trade_date"], df["close"], label="收盘价", linewidth=2)
    plt.plot(df["trade_date"], df["upper"], label="上轨", linestyle="--")
    plt.plot(df["trade_date"], df["ma20"], label="中轨", linestyle="--")
    plt.plot(df["trade_date"], df["lower"], label="下轨", linestyle="--")
    plt.fill_between(df["trade_date"], df["close"], df["lower"], where=df["close"] < df["lower"], facecolor="red", alpha=0.3)
    plt.title(f"{name} - 收盘价与BOLL")
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def run_boll():
    if not is_trade_day():
        print("非交易日，跳过 BOLL 执行")
        return

    # 股票
    for stock in STOCK_LIST:
        df = get_stock_data(stock["code"])
        if df is None:
            continue
        latest = df.iloc[-1]
        if latest["close"] < latest["lower"]:
            print(f"✅ 股票 {stock['name']} 跌破BOLL下轨，生成买入信号")
            chart_file = f"{stock['name']}_{stock['code']}.png"
            plot_boll(df, stock['name'], chart_file)
            msg = f"""【买入信号】股票 {stock['name']} 跌破BOLL下轨
检测时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
当前价格：{latest['close']:.2f}
BOLL下轨：{latest['lower']:.2f}"""
            send_email_if_signal(msg, chart_file)

    # ETF
    for etf in ETF_LIST:
        df = get_etf_data(etf["code"])
        if df is None:
            continue
        latest = df.iloc[-1]
        if latest["close"] < latest["lower"]:
            print(f"✅ ETF {etf['name']} 跌破BOLL下轨，生成买入信号")
            chart_file = f"{etf['name']}_{etf['code']}.png"
            plot_boll(df, etf['name'], chart_file)
            msg = f"""【买入信号】ETF {etf['name']} 跌破BOLL下轨
检测时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
当前价格：{latest['close']:.2f}
BOLL下轨：{latest['lower']:.2f}"""
            send_email_if_signal(msg, chart_file)
