from datetime import datetime

def is_trade_day():
    today = datetime.now().weekday()
    return today < 5  # 周一至周五
