import pandas as pd
from datetime import datetime, timedelta
import adata
from utils_email import send_email_if_signal
import exchange_calendars as ecals
import matplotlib.pyplot as plt
import os

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
    """获取股票数据并计算60日均线"""
    print(f"正在获取 {stock_code} 的数据...")
    
    # 计算开始日期，确保有足够数据
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days+100)).strftime('%Y-%m-%d')
    
    try:
        df = adata.stock.market.get_market(
            stock_code=stock_code, 
            start_date=start_date,
            end_date=end_date,
            k_type=1, 
            adjust_type=1
        )
        
        if df is None or df.empty:
            print(f"❌ 获取 {stock_code} 数据失败：数据为空")
            return None
            
        if len(df) < 60:
            print(f"❌ 获取 {stock_code} 数据失败：数据量不足，只有 {len(df)} 条")
            return None
        
        # 数据清洗和转换
        for col in ["close", "open", "high", "low", "volume", "amount"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df = df.sort_values("trade_date")
        
        # 计算60日均线
        df["ma60"] = df["close"].rolling(window=60, min_periods=60).mean()
        df["above"] = df["close"] > df["ma60"]
        
        print(f"✅ 成功获取 {stock_code} 数据，共 {len(df)} 条，最新日期: {df['trade_date'].iloc[-1].strftime('%Y-%m-%d')}")
        return df.tail(days)
        
    except Exception as e:
        print(f"❌ 获取 {stock_code} 数据异常: {e}")
        return None

def plot_ma60(df, name, filename):
    """绘制股价和60日均线图"""
    try:
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
        print(f"✅ 成功生成图表: {filename}")
        return True
    except Exception as e:
        print(f"❌ 生成图表失败: {e}")
        return False

def run_ma60():
    """运行60日均线策略"""
    print("=" * 50)
    print("开始执行 MA60 策略检测")
    print("=" * 50)
    
    if not is_trade_day():
        print("⏸️ 非交易日，跳过 MA60 执行")
        return
    
    signal_count = 0
    
    for stock in STOCK_LIST:
        print(f"\n🔍 检测股票: {stock['name']}({stock['code']})")
        
        df = get_stock_data(stock["code"])
        if df is None:
            continue
            
        if len(df) < 2:
            print(f"⚠️  {stock['name']} 数据不足，无法判断")
            continue
            
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        print(f"📊 {stock['name']} 最新数据:")
        print(f"   当前日期: {latest['trade_date'].strftime('%Y-%m-%d')}, 收盘价: {latest['close']:.2f}, 60日线: {latest['ma60']:.2f}")
        print(f"   前一日期: {prev['trade_date'].strftime('%Y-%m-%d')}, 收盘价: {prev['close']:.2f}, 60日线: {prev['ma60']:.2f}")
        print(f"   前一日位置: {'60日线上方' if prev['above'] else '60日线下方'}")
        print(f"   当前日位置: {'60日线上方' if latest['above'] else '60日线下方'}")
        
        # 检查是否站上60日线
        if not prev["above"] and latest["above"]:
            print(f"🎯 ✅ 发现信号: {stock['name']} 今日站上60日线！")
            
            # 生成图表
            chart_file = f"{stock['name']}_{stock['code']}.png"
            plot_success = plot_ma60(df, stock['name'], chart_file)
            
            # 准备邮件内容
            msg = f"""【买入信号】{stock['name']} 站上60日线

检测时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
股票代码：{stock['code']}
当前价格：{latest['close']:.2f}元
60日均线：{latest['ma60']:.2f}元
涨跌幅：{((latest['close'] - prev['close']) / prev['close'] * 100):.2f}%

技术信号：
- 前一日位置：60日线{'上方' if prev['above'] else '下方'}
- 当前日位置：60日线{'上方' if latest['above'] else '下方'}
- 信号类型：站上60日线

投资建议：建议关注买入机会，结合其他指标综合判断。
"""
            
            # 发送邮件
            email_success = send_email_if_signal(msg, chart_file if plot_success else None)
            
            if email_success:
                signal_count += 1
                print(f"📧 邮件发送成功！")
            else:
                print(f"❌ 邮件发送失败")
        else:
            print(f"➖ 未触发买入信号")
    
    print(f"\n📈 MA60策略检测完成，共发现 {signal_count} 个买入信号")

# 测试函数
def test_ma60_strategy():
    """测试MA60策略"""
    print("🧪 开始测试MA60策略...")
    
    # 测试环境变量
    sender = os.getenv("QQ_EMAIL")
    password = os.getenv("AUTH_CODE")
    receiver = os.getenv("RECEIVER")
    
    print(f"环境变量检查:")
    print(f"QQ_EMAIL: {'✅ 已设置' if sender else '❌ 未设置'}")
    print(f"AUTH_CODE: {'✅ 已设置' if password else '❌ 未设置'}")
    print(f"RECEIVER: {'✅ 已设置' if receiver else '❌ 未设置'}")
    
    # 测试数据获取
    test_stock = STOCK_LIST[0]
    df = get_stock_data(test_stock["code"], days=10)
    
    if df is not None:
        print(f"✅ 数据获取测试成功")
        print(f"数据样例:")
        print(df[['trade_date', 'close', 'ma60', 'above']].tail())
    else:
        print(f"❌ 数据获取测试失败")
    
    print("🧪 测试完成")

if __name__ == "__main__":
    test_ma60_strategy()
