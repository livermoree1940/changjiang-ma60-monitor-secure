import pandas as pd
from datetime import datetime
import adata
from utils_email import send_email_if_signal
import exchange_calendars as ecals
import matplotlib.pyplot as plt

STOCK_LIST = [
    {"code": "600900", "name": "长江电力"},
    {"code": "601336", "name": "新华保险"},
    {"code": "603586", "name": "森麒麟"},
]

XSHG = ecals.get_calendar("XSHG")

def is_trade_day():
    today = pd.Timestamp(datetime.now().date())
    return today in XSHG.sessions_in_range(today, today)

def get_stock_data(stock_code, days=120):
    df = adata.stock.market.get_market(stock_code=stock_code, k_type=1, adjust_type=1)
    if df is None or df.empty or len(df) < 60:
        return None
    for col in ["close", "open", "high", "low", "volume", "amount"]:
        df[col] = df[col].astype(float)
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.sort_values("trade_date")
    df["ma60"] = df["close"].rolling(window=60, min_periods=1).mean()
    df["above"] = df["close"] > df["ma60"]
    return df.tail(days)

def plot_ma60(df, name, filename):
    plt.figure(figsize=(15,8))
    plt.plot(df['trade_date'], df['close'], label='收盘价', linewidth=2)
    plt.plot(df['trade_date'], df['ma60'], label='60日均线', linestyle='--', linewidth=2)
    above_mask = df['above']
    plt.fill_between(df['trade_date'], df['close'], df['ma60'], where=above_mask, facecolor='green', alpha=0.3)
    plt.fill_between(df['trade_date'], df['close'], df['ma60'], where=~above_mask, facecolor='red', alpha=0.3)
    plt.title(f"{name} - 收盘价与60日均线", fontsize=16)
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def run_ma60():
    if not is_trade_day():
        print("非交易日，跳过 MA60 执行")
        return
    for stock in STOCK_LIST:
        df = get_stock_data(stock["code"])
        if df is None:
            continue
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        if not prev["above"] and latest["above"]:
            print(f"✅ 股票 {stock['name']} 今日站上60日线")
            chart_file = f"{stock['name']}_{stock['code']}.png"
            plot_ma60(df, stock['name'], chart_file)
            msg = f"""【买入信号】股票 {stock['name']} 站上60日线
检测时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
当前价格：{latest['close']:.2f}
60日均线：{latest['ma60']:.2f}"""
            send_email_if_signal(msg, chart_file)
