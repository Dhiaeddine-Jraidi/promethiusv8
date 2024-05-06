from bot_functions import *


def detect_abnormal_volatility(threshold_volatility,threshold_pctchange):
    df = extract_information("BTCUSDT", "15m",16)
    df['daily_return'] = df['close'].pct_change()
    df['volatility'] = df['daily_return'].rolling(window=15).std()
    last_row = df.iloc[-1]
    if (last_row['volatility'] > threshold_volatility) and ((last_row['daily_return'] > threshold_pctchange) or (last_row['daily_return'] < (-1 * threshold_pctchange))):
        if last_row['daily_return'] > 0:
            return True , "SELL"
        else: 
            return True, "BUY"
    else:
        return False, None