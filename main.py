import os
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from utils_email import send_email_if_signal
import adata  # 获取股票行情数据
import exchange_calendars as ecals

# ----------------- 配置 -----------------
STOCK_LIST = [
    {"code": "600900", "name": "长江电力"},
    {"code": "601336", "name": "新华保险"},
    {"code": "603586", "name": "森麒麟"}
]

# 初始化上交所交易日历
XSHG = ecals.get_calendar("XSHG")

# ----------------- 函数 -----------------
def is_trade_day():
    """判断今天是否交易日"""
    today = pd.Timestamp(datetime.now().date())
    return today in XSHG.sessions_in_range(today, today)

def get_stock_data(stock_code, days=120):
    """获取股票日K线数据并计算60日均线"""
    total_days = days + 60
    df = adata.stock.market.get_market(
        stock_code=stock_code,
        k_type=1,       # 日K
        adjust_type=1   # 前复权
    )
    if df is None or df.empty or len(df) < 60:
        print(f"无法获取股票 {stock_code} 的数据")
        return None

    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values('trade_date')
    df['ma60'] = df['close'].rolling(window=60, min_periods=1).mean()
    df['above'] = df['close'] > df['ma60']
    return df.tail(days)

def plot_stock_ma60(df, stock_name, filename):
    """绘制股票收盘价与60日均线"""
    plt.figure(figsize=(15, 8))
    plt.plot(df['trade_date'], df['close'], label='收盘价', linewidth=2)
    plt.plot(df['trade_date'], df['ma60'], label='60日均线', linestyle='--', linewidth=2)
    above_mask = df['above']
    plt.fill_between(df['trade_date'], df['close'], df['ma60'], where=above_mask, facecolor='green', alpha=0.3)
    plt.fill_between(df['trade_date'], df['close'], df['ma60'], where=~above_mask, facecolor='red', alpha=0.3)
    plt.title(f"{stock_name} - 股价与60日均线", fontsize=16)
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# ----------------- 主逻辑 -----------------
def main():
    if not is_trade_day():
        print("非交易日，跳过执行。")
        return

    for stock in STOCK_LIST:
        code = stock["code"]
        name = stock["name"]
        df = get_stock_data(code)
        if df is None:
            continue

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        if not prev['above'] and latest['above']:
            print(f"✅ {name} 今日新站上60日线，生成买入信号。")
            chart_file = f"ma60_{code}.png"
            plot_stock_ma60(df, name, chart_file)

            msg = f"""【买入信号】{name} 站上60日线

检测时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
当前价格：{latest['close']:.2f}
60日均线：{latest['ma60']:.2f}
状态：✅ 站上60日线（建议关注买入机会）
"""
            send_email_if_signal(msg, chart_file)
        else:
            print(f"{name} 未触发买入信号。")

# ----------------- 执行 -----------------
if __name__ == "__main__":
    main()
