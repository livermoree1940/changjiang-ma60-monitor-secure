import matplotlib.pyplot as plt
from matplotlib import font_manager
import os

def plot_ma60(df, name, filename):
    """绘制股价和60日均线图"""
    try:
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Arial Unicode MS']  # 备用字体
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        plt.figure(figsize=(15,8))
        plt.plot(df['trade_date'], df['close'], label='Close Price', linewidth=2)
        plt.plot(df['trade_date'], df['ma60'], label='60-day MA', linestyle='--', linewidth=2)
        above_mask = df['above']
        plt.fill_between(df['trade_date'], df['close'], df['ma60'], where=above_mask, facecolor='green', alpha=0.3)
        plt.fill_between(df['trade_date'], df['close'], df['ma60'], where=~above_mask, facecolor='red', alpha=0.3)
        
        # 使用英文标题避免字体问题
        plt.title(f"{name} - Price vs 60-day Moving Average", fontsize=16)
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
