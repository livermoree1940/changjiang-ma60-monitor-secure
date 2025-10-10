# -*- coding:utf-8 -*-
import akshare as ak
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from utils_email import send_email_if_signal
from trade_calendar import is_trade_day

STOCK_CODE = "601336.XSHG"  # 长江电力
STOCK_NAME = "长江电力"

def get_stock_data(stock_code, days=120):
    # AKShare 股票代码需要小写、交易所前缀
    if stock_code.endswith(".XSHG"):
        symbol = "sh" + stock_code.replace(".XSHG", "")
    elif stock_code.endswith(".XSHE"):
        symbol = "sz" + stock_code.replace(".XSHE", "")
    else:
        symbol = stock_code

    # 获取历史日线前复权数据
    df = ak.stock_zh_a_hist(symbol=symbol, adjust="qfq", start_date="2024-01-01", end_date=datetime.now().strftime("%Y-%m-%d"))

    if df is None or df.empty or len(df) < 60:
        print(f"无法获取股票 {stock_code} 的数据")
        return None

    # 日期列处理
    df['日期'] = pd.to_datetime(df['日期'])
    df.sort_values('日期', inplace=True)
    df.set_index('日期', inplace=True)
    df.rename(columns={'收盘':'close'}, inplace=True)

    # 取最近 days+60 日数据
    df = df.tail(days+60).copy()

    # 获取今日最新分时价（如果有）
    try:
        df_tick = ak.stock_zh_a_tick_tx(symbol)  # 腾讯分时
        if not df_tick.empty:
            latest_price = df_tick.iloc[-1]['成交价']
            latest_time = datetime.now()
            # 用最新分时价覆盖或追加到最后一行
            df.loc[latest_time] = df.iloc[-1]
            df.iloc[-1, df.columns.get_loc('close')] = latest_price
    except Exception as e:
        print("分时价获取失败，使用日线收盘价:", e)

    # 计算 60 日均线
    df['ma60'] = df['close'].rolling(window=60).mean()
    df['above'] = df['close'] > df['ma60']

    # 打印最近 60 日收盘价与均线
    print("\n最近60日收盘价与60日均线对照：")
    print(df[['close', 'ma60']].tail(60))

    return df.tail(days)

def plot_stock_ma60(df, filename="ma60_chart.png"):
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

    print(f"\n最新收盘价: {latest['close']:.2f}  日期: {df.index[-1]}")
    print(f"最新60日均线: {latest['ma60']:.2f}")

    if not prev['above'] and latest['above']:
        print("✅ 今日新站上60日线，生成买入信号。")
        plot_stock_ma60(df)
        msg = f"""【买入信号】{STOCK_NAME} 站上60日线

检测时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
当前价格：{latest['close']:.2f}
60日均线：{latest['ma60']:.2f}
状态：✅ 站上60日线（建议关注买入机会）
"""
        send_email_if_signal(msg, "ma60_chart.png")
    else:
        print("未触发买入信号。")

if __name__ == "__main__":
    main()
