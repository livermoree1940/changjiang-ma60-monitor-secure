from ma60_strategy import run_ma60
from boll_strategy import run_boll

def main():
    print("==== 执行 MA60 股票策略 ====")
    run_ma60()
    
    print("\n==== 执行 BOLL 股票/ETF策略 ====")
    run_boll()

if __name__ == "__main__":
    main()
