import os
import matplotlib.pyplot as plt
import pandas as pd
from Ashare import get_price
from datetime import datetime
from utils_email import send_email_if_signal
from trade_calendar import is_trade_day

STOCK_CODE = "000300.XSHG"  # 长江电力
STOCK_NAME = "长江电力"

def get_stock_data(stock_code, days=120):
    total_days = days + 60
    df = get_price(stock_code, frequency='1d', count=total_days)
    if df is None or df.empty or len(df) < 60:
        print(f"无法获取股票 {stock_code} 的数据")
        return None
    df['ma60'] = df['close'].rolling(window=60, min_periods=1).mean()
    df['above'] = df['close'] > df['ma60']
    return df.tail(days)

def plot_stock_ma60(df, filename):
    plt.figure(figsize=(15, 8))
    plt.plot(df.index, df['close'], label='收盘价', linewidth=2)
    plt.plot(df.index, df['ma60'], label='60日均线', linestyle='--', linewidth=2)
    above_mask = df['above']
    plt.fill_between(df.index, df['close'], df['ma60'], where=above_mask, facecolor='green', alpha=0.3)
    plt.fill_between(df.index, df['close'], df['ma60'], where=~above_mask, facecolor='red', alpha=0.3)
    plt.title(f"{STOCK_NAME} - 股价与60日均线", fontsize=16)
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def main():
    if not is_trade_day():
        print("非交易日，跳过执行。")
        return

    df = get_stock_data(STOCK_CODE)
    if df is None:
        return

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    if not prev['above'] and latest['above']:
        print("✅ 今日新站上60日线，生成买入信号。")
        chart_file = "ma60_chart.png"
        plot_stock_ma60(df, chart_file)

        msg = f"""【买入信号】{STOCK_NAME} 站上60日线

检测时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
当前价格：{latest['close']:.2f}
60日均线：{latest['ma60']:.2f}
状态：✅ 站上60日线（建议关注买入机会）
"""
        send_email_if_signal(msg, chart_file)
    else:
        print("未触发买入信号。")

if __name__ == "__main__":
    main()
