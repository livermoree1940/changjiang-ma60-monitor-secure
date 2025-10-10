import os
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from utils_email import send_email_if_signal
import adata
import exchange_calendars as ecals

# ----------------- 配置 -----------------
STOCK_LIST = [
    {"code": "600900", "name": "长江电力"},
    {"code": "601336", "name": "新华保险"},
    {"code": "603586", "name": "森麒麟"},
]

ETF_LIST = [
    {"code": "515080", "name": "华夏上证50ETF"},
    {"code": "515450", "name": "标普500ETF"},
    {"code": "512880", "name": "中证500ETF"},
]

XSHG = ecals.get_calendar("XSHG")


# ----------------- 函数 -----------------
def is_trade_day():
    today = pd.Timestamp(datetime.now().date())
    return today in XSHG.sessions_in_range(today, today)


def get_stock_data(stock_code, days=120):
    df = adata.stock.market.get_market(stock_code=stock_code, k_type=1, adjust_type=1)
    if df is None or df.empty or len(df) < 60:
        print(f"无法获取股票 {stock_code} 数据")
        return None

    # 转换为数值类型
    for col in ["close", "open", "high", "low", "volume", "amount"]:
        df[col] = df[col].astype(float)

    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.sort_values("trade_date")
    df["ma60"] = df["close"].rolling(window=60, min_periods=1).mean()
    df["above"] = df["close"] > df["ma60"]
    return df.tail(days)


def get_etf_data(etf_code, days=120):
    df = adata.fund.market.get_market_etf(fund_code=etf_code, k_type=1)
    if df is None or df.empty or len(df) < 60:
        print(f"无法获取ETF {etf_code} 数据")
        return None

    # 转换为数值类型
    for col in ["close", "open", "high", "low", "volume", "amount"]:
        df[col] = df[col].astype(float)

    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df = df.sort_values("trade_date")
    df["ma60"] = df["close"].rolling(window=60, min_periods=1).mean()
    df["above"] = df["close"] > df["ma60"]
    return df.tail(days)


def plot_ma60(df, name, filename):
    plt.figure(figsize=(15, 8))
    plt.plot(df["trade_date"], df["close"], label="收盘价", linewidth=2)
    plt.plot(
        df["trade_date"], df["ma60"], label="60日均线", linestyle="--", linewidth=2
    )
    above_mask = df["above"]
    plt.fill_between(
        df["trade_date"],
        df["close"],
        df["ma60"],
        where=above_mask,
        facecolor="green",
        alpha=0.3,
    )
    plt.fill_between(
        df["trade_date"],
        df["close"],
        df["ma60"],
        where=~above_mask,
        facecolor="red",
        alpha=0.3,
    )
    plt.title(f"{name} - 收盘价与60日均线", fontsize=16)
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


# ----------------- 主逻辑 -----------------
def main():
    if not is_trade_day():
        print("非交易日，跳过执行。")
        return

    # 先遍历股票
    for stock in STOCK_LIST:
        code = stock["code"]
        name = stock["name"]
        df = get_stock_data(code)
        if df is None:
            continue

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        if not prev["above"] and latest["above"]:
            print(f"✅ 股票 {name} 今日站上60日线，生成买入信号。")
            chart_file = f"{name}_{code}.png"
            plot_ma60(df, name, chart_file)

            msg = f"""【买入信号】股票 {name} 站上60日线
检测时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
当前价格：{latest['close']:.2f}
60日均线：{latest['ma60']:.2f}
状态：✅ 站上60日线
"""
            send_email_if_signal(msg, chart_file)
        else:
            print(f"股票 {name} 未触发买入信号。")

    # 再遍历ETF
    for etf in ETF_LIST:
        code = etf["code"]
        name = etf["name"]
        df = get_etf_data(code)
        if df is None:
            continue

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        if not prev["above"] and latest["above"]:
            print(f"✅ ETF {name} 今日站上60日线，生成买入信号。")
            chart_file = f"{name}_{code}.png"
            plot_ma60(df, name, chart_file)

            msg = f"""【买入信号】ETF {name} 站上60日线
检测时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
当前价格：{latest['close']:.2f}
60日均线：{latest['ma60']:.2f}
状态：✅ 站上60日线
"""
            send_email_if_signal(msg, chart_file)
        else:
            print(f"ETF {name} 未触发买入信号。")


if __name__ == "__main__":
    main()
