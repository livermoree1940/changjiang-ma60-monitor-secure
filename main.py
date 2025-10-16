import os
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from utils_email import send_email_if_signal
import adata  # 获取股票行情数据
import exchange_calendars as ecals
import matplotlib as mpl

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 强化字体配置（放在所有其他导入之后）
mpl.rcParams['font.sans-serif'] = ['SimHei']  # 仅保留Windows字体
mpl.rcParams['axes.unicode_minus'] = False
mpl.use('Agg')  # 必须在其他matplotlib操作之前设置

# 修改字体配置部分（移除中文字体设置）
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 跨平台兼容字体
plt.rcParams['axes.unicode_minus'] = False

def plot_stock_ma60(df, stock_name, filename):
    """绘制股票收盘价与60日均线"""
    plt.figure(figsize=(15, 8))
    plt.plot(df['trade_date'], df['close'], label='Close', linewidth=2)
    plt.plot(df['trade_date'], df['ma60'], label='60MA', linestyle='--', linewidth=2)
    above_mask = df['above']
    plt.fill_between(df['trade_date'], df['close'], df['ma60'], where=above_mask, facecolor='green', alpha=0.3)
    plt.fill_between(df['trade_date'], df['close'], df['ma60'], where=~above_mask, facecolor='red', alpha=0.3)
    plt.title(f"{stock_name} - Price and 60-day Moving Average", fontsize=16)
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.title(f'{stock_name} MA60 Monitor', fontsize=14)  # 英文标题避免中文
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# ----------------- 函数 -----------------
def is_trade_day():
    """判断今天是否交易日"""
    today = pd.Timestamp(datetime.now().date())
    return today in XSHG.sessions_in_range(today, today)

# ----------------- 主逻辑 -----------------
def main():
    # 在生成图表前添加后端设置
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端
    if not is_trade_day():
        print("非交易日，跳过执行。")
        return

    for stock in STOCK_LIST:
        code = stock["code"]
        name = stock["name"]
        asset_type = stock["type"]
        
        # 根据类型选择不同的数据获取函数
        if asset_type == "etf":
            df = get_etf_data(code)
        else:
            df = get_stock_data(code)
            
        if df is None:
            continue

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        if not prev['above'] and latest['above']:
            print(f"✅ {name} 今日新站上60日线，生成买入信号。")
            # 修改文件名为中文名 + 代码
            chart_file = f"{name}_{code}.png"
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
