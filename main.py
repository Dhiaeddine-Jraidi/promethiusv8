# Project Promethius V8

from bot_functions import *
from STRATEGY_kerberos import *
from STRATEGY_recession import *
from STRATEGY_syfer import *
from STRATEGY_abnormality import *
from sql_integration import extract_trade_from_sql, table_name1
from ml_train import train_models



last_recession_check_time = 0
last_ml_train_check_time = 0
calibration_perc = 0.00


def main_bot():
    
    ######################### train models
    global last_ml_train_check_time
    current_time = time.time()
    if current_time - last_ml_train_check_time >= 72 * 3600:
        train_models()
        last_ml_train_check_time = current_time
   
    ######################### reading opened trades

    trade_data_df = read_dataframe(open_trade_csv, open_trade_columns)
    
    ######################### Strategy 1

    if len(trade_data_df[trade_data_df['strategy'] == 'Abnormality']) < 2:
        signal, side = detect_abnormal_volatility(0.0048, 0.011)
        if signal :
            strategy = "Abnormality"
            timeframe = "15m"
            symbol = "BTCUSDT"
            take_profit_percent = 2
            stop_loss_percent = 2
            routine(strategy, timeframe, symbol, take_profit_percent, stop_loss_percent, side, calibration_perc)
    
    ######################### Strategy 2    
    
    ratio  = 1.5

    timeframes = [
        {'timeframe': '1m', 'atr_timeframe': '2h', 'calibration_perc': 0.00},
        {'timeframe': '15m', 'atr_timeframe': '6h','calibration_perc': 0.00},
        {'timeframe': '30m', 'atr_timeframe': '12h', 'calibration_perc':0.00},]

    with open(filepath_kerberos, "r") as file:
        coins = file.read().splitlines()

    for timeframe in timeframes:
        strategy = f"Kerberos_{timeframe['timeframe']}"

        for symbol in coins:
            if trade_data_df[(trade_data_df['symbol'] == symbol) & (trade_data_df['strategy'] == strategy)].empty:
                side, symbol = processing(symbol, timeframe['timeframe'])
                if side is not None:
                    stop_loss_percent = round(calculate_sl(symbol, timeframe['atr_timeframe']) * 100,2)
                    take_profit_percent = round(stop_loss_percent * ratio,2)
                    routine(strategy, timeframe['timeframe'], symbol,take_profit_percent, stop_loss_percent,side, timeframe['calibration_perc'])  
            else:
                continue
                
    ######################### Strategy 3
    global last_recession_check_time
    number_of_successive_zeros = 8
    pct_decrease_to_sell = 3  # pct
    pct_increase_to_buy = 3  # pct
    
    current_time = time.time()

    if current_time - last_recession_check_time >= number_of_successive_zeros * 3600:
        number_of_successive_zeros = 8
        pct_decrease_to_sell = 3
        pct_increase_to_buy = 3
        recession_check(number_of_successive_zeros, pct_decrease_to_sell, pct_increase_to_buy)
        last_recession_check_time = current_time


    if check_pending_orders_recession() is not None:
        timeframe = "1h"
        strategy = f"Impulse MACD // {number_of_successive_zeros}"
        symbol = "BTCUSDT"
        take_profit_percent = 3
        stop_loss_percent = 3
        side = check_pending_orders_recession()
        routine(strategy, timeframe, symbol, take_profit_percent, stop_loss_percent, side, calibration_perc)
        os.remove(recession_file_path)

    ######################### Strategy 4
        
    project_syfer(1.5)
    symbol, side = check_pending_orders_project_syfer()
    strategy = "syfer"
    
    if symbol is not None:
        timeframe = "15m"
        TP = 3.5
        SL = 3.5
        
        routine(strategy, timeframe, symbol, TP, SL, side, calibration_perc)
        coins_data = read_json_file(syfer_file_path)
        if symbol in coins_data:
            coins_data.pop(symbol)

        write_json_file(syfer_file_path, coins_data)

    time.sleep(5)


if __name__ == "__main__":
    df = extract_trade_from_sql(table_name1)
    df.to_csv("files/download/output_final_trades.csv", index = False)
    while True:
        main_bot()

