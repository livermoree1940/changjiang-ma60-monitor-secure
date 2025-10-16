import os
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from utils_email import send_email_if_signal
import adata  # 获取股票行情数据
import exchange_calendars as ecals

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# ----------------- 配置 -----------------
STOCK_LIST = [
    {"code": "600900", "name": "长江电力", "type": "stock"},
    {"code": "601336", "name": "新华保险", "type": "stock"},
    {"code": "601728", "name": "中国电信", "type": "stock"},
    {"code": "600030", "name": "中信证券", "type": "stock"},
    {"code": "600028", "name": "中国石化", "type": "stock"},
    {"code": "563300", "name": "中证2000etf", "type": "etf"},
    {"code": "513950", "name": "恒生红利etf", "type": "etf"},
    {"code": "510300", "name": "沪深300ETF", "type": "etf"}  # 添加510300 ETF
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

def get_etf_data(code):
    try:
        adata.set_config()
        df = adata.fund.market.get_market_etf(
            fund_code=code,
            k_type=1,
            start_date="20230101",
            end_date=datetime.now().strftime("%Y%m%d")
        )
        # 添加数据验证
        if df.empty or 'close' not in df.columns:
            raise ValueError("Invalid ETF data returned")
        return df
    except Exception as e:
        print(f"获取ETF数据失败: {str(e)}")
        # 添加详细的错误日志
        print(f"API返回数据格式可能有变化，请检查接口响应")
        return pd.DataFrame()

def plot_stock_ma60(df, stock_name, filename):
    """绘制股票收盘价与60日均线"""
    plt.figure(figsize=(15, 8))
    plt.plot(df['trade_date'], df['close'], label='Close Price', linewidth=2)
    plt.plot(df['trade_date'], df['ma60'], label='60-day MA', linestyle='--', linewidth=2)
    above_mask = df['above']
    plt.fill_between(df['trade_date'], df['close'], df['ma60'], where=above_mask, facecolor='green', alpha=0.3)
    plt.fill_between(df['trade_date'], df['close'], df['ma60'], where=~above_mask, facecolor='red', alpha=0.3)
    plt.title(f"{stock_name} - Price and 60-day Moving Average", fontsize=16)
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.title('长江电力 60日线监控', fontsize=14)  # 确保使用配置的中文字体
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

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
