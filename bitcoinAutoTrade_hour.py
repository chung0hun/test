import time
import pyupbit
import datetime
import numpy as np
import pickle

access = "41KdMvNE6qWl8Qomu0x0IsxvImrF3TbXBNGhvmFU"
secret = "3gVPPd0yNuLzfBDa6B8R3En9GvViuCzQrwDbZyXA"


def get_daily_ohlcv_from_base(n):
    try:
        df = pyupbit.get_ohlcv("KRW-BTC", interval="minute60", count=504)
        basetime = str(n) + 'h'
        df = df.resample(rule='24H', offset=basetime).agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
        return df
    except Exception as x:
        return None


def get_best_k(n):
    df = get_daily_ohlcv_from_base(n)
    max_crr = 0
    best_k = 0.36
    for k in np.arange(0.0, 1.0, 0.01):
        df['range'] = df['high'].shift(1) - df['low'].shift(1)
        df['targetPrice'] = df['open'] + df['range'] * k
        df['drr'] = np.where(df['high'] > df['targetPrice'], (df['close'] * .9995) / (df['targetPrice'] * 1.0005), 1)
        crr = df['drr'].cumprod()[-2]
        if crr > max_crr:
            max_crr = crr
            best_k = k
    return best_k


def get_target_price(n):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = get_daily_ohlcv_from_base(n)
    target_price = df.iloc[-2]['close'] + (df.iloc[-2]['high'] - df.iloc[-2]['low']) * get_best_k(n)
    return target_price


# 로그인


upbit = pyupbit.Upbit(access, secret)

print("autotrade start")
with open("BTC.bin", "rb") as f:
    BTC = pickle.load(f)
for n in range(24):
    print(f'{n:>2} : {BTC[n][0]:>6} , {BTC[n][1]:.8f} , {BTC[n][2]:>8}')

# 자동매매 시작
while True:
    try:
        time.sleep(1)
        now = datetime.datetime.now()
        pre_time = now + datetime.timedelta(seconds=-30)

        if now.hour != pre_time.hour:   # 시간이 바뀌면
            n = now.hour - 1
            if n < 0:
                n = 23
            if BTC[n][1] > 0.00008:
                upbit.sell_market_order("KRW-BTC", BTC[n][1])  # 매도
                time.sleep(10)
                ret = upbit.get_order("KRW-BTC", "done")
                print(f'<70>  {n:>2} : {BTC[n][0]:>6} , {BTC[n][1]:.8f} , {BTC[n][2]:>8}')
                print(ret)
                if str(ret[0]['side']) == 'ask':
                    BTC[n][0] = int(float(ret[0]['paid_fee']) / float(ret[0]['executed_volume']) * .9995 * 2000 * BTC[n][1])
                    BTC[n][1] = 0
                    print(f'<75>  {n:>2} : {BTC[n][0]:>6} , {BTC[n][1]:.8f} , {BTC[n][2]:>8}')
            time.sleep(30)  # df가 전날 것까지만 나오는 것 방지
            n = now.hour
            BTC[n][2] = get_target_price(n)
            print(f'<79>  {n:>2} : {BTC[n][0]:>6} , {BTC[n][1]:.8f} , {BTC[n][2]:>8}')
            with open("BTC.bin", "wb") as f:
                pickle.dump(BTC, f)
            time.sleep(10)

        for n in range(24):
            time.sleep(1)
            current_price = pyupbit.get_current_price("KRW-BTC")
            if BTC[n][1] == 0 and BTC[n][2] < current_price and BTC[n][0] > 5050:
                upbit.buy_market_order("KRW-BTC", BTC[n][0] * 0.9995)  # 매수
#                time.sleep(10)
#                ret = upbit.get_order("KRW-BTC", state="done")
#                if str(ret[0]['side']) == 'bid':
                print(f'<92>  {n:>2} : {BTC[n][0]:>6} , {BTC[n][1]:.8f} , {BTC[n][2]:>8}')
                BTC[n][1] = round(BTC[n][0]/current_price,8)
                BTC[n][2] = current_price
                BTC[n][0] = 0
                print(f'<96>  {n:>2} : {BTC[n][0]:>6} , {BTC[n][1]:.8f} , {BTC[n][2]:>8}')
                with open("BTC.bin", "wb") as f:
                    pickle.dump(BTC, f)

    except Exception as e:
        print(e)
