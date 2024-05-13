from bot_functions import *

filepath_kerberos = "files/kerberos_coins.txt"


def processing(symbol, timeframe):
    numberofrows = 6
    extracted_rows = 205
    df = extract_information(symbol, timeframe,extracted_rows)
    df['ema_short'] = ema(df, 21)
    df['ema_middle'] = ema(df, 50)
    df['ema_long'] = ema(df, 200)
    df['rsi'] = calculate_rsi(df, 14)
    if all(df["close"].iloc[-i] > df['ema_short'].iloc[-i] and df["close"].iloc[-i] > df['ema_middle'].iloc[-i] and df["close"].iloc[-i] > df['ema_long'].iloc[-i] for i in range(1, numberofrows-1)) and (df["close"].iloc[-numberofrows] < df['ema_short'].iloc[-numberofrows]) and (df["ema_middle"].iloc[-1] < df['ema_short'].iloc[-1]) and (df["ema_long"].iloc[-1] < df['ema_middle'].iloc[-1]) and df['rsi'].iloc[-1] > 50:
        return "BUY", symbol
        
    elif all(df["close"].iloc[-i] < df['ema_short'].iloc[-i] and df["close"].iloc[-i] < df['ema_middle'].iloc[-i] and df["close"].iloc[-i] < df['ema_long'].iloc[-i] for i in range(1, numberofrows-1))   and (df["close"].iloc[-numberofrows] > df['ema_short'].iloc[-numberofrows]) and (df["ema_middle"].iloc[-1] > df['ema_short'].iloc[-1]) and (df["ema_long"].iloc[-1] > df['ema_middle'].iloc[-1]) and df['rsi'].iloc[-1] < 50 :
        return "SELL", symbol
    else:
        return None, None