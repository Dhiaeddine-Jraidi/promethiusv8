import ccxt
import requests
from datetime import datetime, timedelta
import pandas as pd
import os
import time
import numpy as np
import random
import string
import csv
import json
from ML import predict_probability

BOT_TOKEN_key = "6566859554:AAHN0ZeuI4Ojrd5II60lcH6y8-hIJ4OLXMk"
open_trade_csv = "files/download/open_trades.csv"
open_trade_columns = ['trade_id', 'symbol', 'entry_time_str', 'side', 'entry_price', 'last_price','take_profit_percent', 'stop_loss_percent', 'exit_price_TP', 'exit_price_SL','timeframe', 'strategy', 'pnl', 'period_hours', 'entry_day_of_week' , 'entry_hour', 'aroon_up', 'aroon_down','ema_short', 'ema_middle', 'ema_long', 'rsi', 'macd', '24h_volume', 'probability']
temporary_finished_trades_csv= "files/download/temporary_finished_trade.csv"
output_final_trades = "files/download/output_final_trades.csv"
output_final_trades2 = "files/download/output_final_trades2.csv"


def generate_random_id(length=5):
    allowed_characters = string.ascii_letters + string.digits
    random_id = ''.join(random.choice(allowed_characters) for _ in range(length))
    return random_id


def remove_row_by_trade_id(csv_file, trade_id):
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
    index_to_remove = None
    for i, row in enumerate(rows):
        if row['trade_id'] == trade_id:
            index_to_remove = i
            break
    del rows[index_to_remove]
    fieldnames = reader.fieldnames
    with open(csv_file, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_dataframe(csv_filepath, columns):
    if os.path.exists(csv_filepath):
        trade_data_df = pd.read_csv(csv_filepath)
    else:
        trade_data_df = pd.DataFrame(columns=columns)

    return trade_data_df


def write_to_csv(filepath, columns, data):
    file_exists = os.path.isfile(filepath)
    with open(filepath, 'a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(columns)
        writer.writerow(data)

def routine(strategy, timeframe, symbol, take_profit_percent, stop_loss_percent, side, calibration_perc):
    def count_dp(symbol):
        while True:    
            try:
                response = requests.get("https://fapi.binance.com/fapi/v1/ticker/price", params={"symbol": symbol})
                data = response.json()
                real_price =  float(data['price'])
                return int(len(str(real_price).split('.')[-1]))
            
            except Exception as e:
                print("An error occurred in count_dp:", e)
                time.sleep(2)

    trade_ID = generate_random_id()

    last_price = get_real_price(symbol)
    dp = count_dp (symbol)
    
    if side == "BUY":
        entry_price = round(last_price - (last_price * (calibration_perc / 100)), dp)
        exit_price_TP = round(last_price + (last_price * (take_profit_percent / 100)), dp)
        exit_price_SL = round(last_price - (last_price * (stop_loss_percent / 100)), dp)
    else:
        entry_price = round(last_price + (last_price * (calibration_perc / 100)), dp)
        exit_price_TP = round(last_price - (last_price * (take_profit_percent / 100)), dp)
        exit_price_SL = round(last_price + (last_price * (stop_loss_percent / 100)), dp)

    entry_time_str = (datetime.now() + timedelta(hours=1)).strftime("%d-%m-%Y %I:%M%p")
    entry_hour = int(pd.to_datetime(entry_time_str, format='%d-%m-%Y %I:%M%p').strftime('%H'))
    entry_day_of_week = pd.to_datetime(entry_time_str, format='%d-%m-%Y %I:%M%p').strftime('%A')
    
    df = extract_information(symbol, timeframe, 300)

    df['aroon_up'] , df['aroon_down']= calculate_aroon(df)
    df['ema_short'] = ema(df, 21)
    df['ema_middle'] = ema(df, 50)
    df['ema_long'] = ema(df, 200)
    df['rsi'] = calculate_rsi(df, 14)
    df['macd'] = macd(df)

    _24_hour_volume = calculate_24_hour_volume(symbol)
    
    
    trade_data = [trade_ID,symbol,entry_time_str,side,entry_price,last_price,take_profit_percent/100,stop_loss_percent/100,exit_price_TP,exit_price_SL,timeframe,strategy,0 ,0, entry_day_of_week , entry_hour, df['aroon_up'].iloc[-1],df['aroon_down'].iloc[-1],df['ema_short'].iloc[-1],df['ema_middle'].iloc[-1],df['ema_long'].iloc[-1],df['rsi'].iloc[-1],df['macd'].iloc[-1],_24_hour_volume]
    data_dict = dict(zip(open_trade_columns, trade_data))
    probability = predict_probability(data_dict)
    trade_data.append(probability)
    write_to_csv(open_trade_csv, open_trade_columns, trade_data)
    message = f"{strategy} Opportunity !!!\nProbability: {round(probability*100,0)}%\n\nTrade ID: {trade_ID}\nSymbol: {symbol}\nLast Price: {last_price}\nEntry Price: {entry_price}\nPosition: {side}\nTake Profit: {exit_price_TP} || ({round(take_profit_percent,2)}%)\nStop Loss: {exit_price_SL} || ({round(stop_loss_percent,2)}%)\nTime: {entry_time_str}\nTimeframe: {timeframe}"
    send_message(message)


def calculate_24_hour_volume(symbol):

    df = extract_information(symbol, "1d", 1)

    return df['volume'].iloc[-1] * df['close'].iloc[-1]


def calculate_rsi(df, window=14):
    close_prices = df['close']
    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()

    return 100 - (100 / (1 + (avg_gain / avg_loss)))

def ema(df, period):
    return df['close'].ewm(span=period, min_periods=period - 1).mean()


def macd(df):
    short_period = 12
    long_period = 26
    signal_period = 9  

    return ((df['close'].ewm(span=short_period, adjust=False).mean()) - (df['close'].ewm(span=long_period, adjust=False).mean())) - ((df['close'].ewm(span=short_period, adjust=False).mean()) - (df['close'].ewm(span=long_period, adjust=False).mean())).ewm(span=signal_period, adjust=False).mean()


def calculate_aroon(df):
    def highestbars(data, length):
        return np.argmax(data[-length:]) + length

    def lowestbars(data, length):
        return np.argmin(data[-length:]) + length
    length = 14 
    df['aroon_up'] = 0  # Initialize Aroon_Up column
    df['aroon_down'] = 0  # Initialize Aroon_Down column
    
    for i in range(length, len(df)):
        high_window = df['high'][i-length:i]
        low_window = df['low'][i-length:i]
        upper_value = ((100 * (highestbars(high_window, length) + length) / length)-200)/100
        lower_value = ((100 * (lowestbars(low_window, length) + length) / length)-200)/100
        df.at[df.index[i], 'aroon_up'] = upper_value
        df.at[df.index[i], 'aroon_down'] = lower_value
    
    return df['aroon_up'], df['aroon_down']


def extract_information(symbol, timeframe, number_of_bars):
    while True:
        try:
            exchange = ccxt.binance()
            ohlcv_data = exchange.fetch_ohlcv(symbol, timeframe, limit=number_of_bars)
            data = []
            for candle in ohlcv_data:
                timestamp, open_price, high_price, low_price, close_price, volume = candle
                data.append([timestamp, open_price, high_price, low_price, close_price, volume])
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            return df
        
        except Exception as e:
            print("error in extract_information: ",e)
            time.sleep(60)


def get_real_price(symbol):
    while True:
        try:
            base_url = "https://fapi.binance.com"
            endpoint = "/fapi/v1/ticker/price"
            params = {"symbol": symbol}
            response = requests.get(base_url + endpoint, params=params)
            data = response.json()
            real_price =  float(data['price'])
            return real_price
        
        except Exception as e:
            print("An error occurred in get_real_price:", e)
            time.sleep(2)

def send_message(message):
    chat_id = '1545111998'
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN_key}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message
    }
    requests.post(url, data=data)


def delete_coin_from_file(strategy, coin_to_delete):
    try:
        with open(f'files/{strategy}_coins.txt', 'r') as file:
            lines = file.readlines()
        updated_lines = [line for line in lines if line.strip() != coin_to_delete]

        with open(f'files/{strategy}_coins.txt', 'w') as file:
            file.writelines(updated_lines)

        send_message(f"{coin_to_delete} will not be used again with {strategy} strategy.")

    except FileNotFoundError:
        send_message(f"File '{f'files/{strategy}_coins.txt'}' not found.")

    except Exception as e:
        send_message(f"An error occurred: {e}")



def indicators(symbol):
    df = extract_information(symbol, "1h",1000)
    lengthMA = 34
    lengthSignal = 9
    
    def calc_smma(src, length):
        smma = np.empty(len(src))
        smma[0] = np.nan
        for i in range(1, len(src)):
            if np.isnan(smma[i-1]):
                smma[i] = np.mean(src[:i+1])
            else:
                smma[i] = (smma[i-1] * (length - 1) + src[i]) / length
        return smma
    
    def calc_zlema(src, length):
        ema1 = pd.Series(src).ewm(span=length).mean()
        ema2 = ema1.ewm(span=length).mean()
        d = ema1 - ema2
        return ema1 + d
    
    src = df['close']
    hi = calc_smma(df['high'], lengthMA)
    lo = calc_smma(df['low'], lengthMA)
    mi = calc_zlema(src, lengthMA)
    md = np.where(mi > hi, mi - hi, np.where(mi < lo, mi - lo, 0))
    sb = pd.Series(md).rolling(window=lengthSignal).mean()
    sh = md - sb
    df['ImpulseMACD'] = md
    df['ImpulseHisto'] = sh
    df['ImpulseMACDCDSignal'] = sb
    period = 20 
    std = df['close'].rolling(window=period).std()
    df['BollingerMid'] = df['close'].rolling(window=period).mean()
    df['BollingerUpper'] = df['BollingerMid'] + 2 * std
    df['Bollingerlower'] = df['BollingerMid'] - 2 * std
    
    return df


def write_json_file(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    
def read_json_file(file_path):
    with open(file_path, "r") as file:
        return json.load(file)
    

def calculate_sl(symbol, timeframe):
    df  = extract_information(symbol, timeframe, 25)
    current_price = get_real_price(symbol) 
    df['tr'] = np.max([
        df['high'] - df['low'],
        np.abs(df['high'] - df['close'].shift()),
        np.abs(df['low'] - df['close'].shift())
    ], axis=0)

    df['atr'] = df['tr'].rolling(window=14, min_periods=1).mean()

    return df['atr'].iloc[-1] / current_price