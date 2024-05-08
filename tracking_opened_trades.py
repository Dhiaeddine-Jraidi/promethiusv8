from sql_integration import write_to_mysql
from bot_functions import time,requests, get_real_price, os, send_message, write_to_csv, open_trade_csv, temporary_finished_trades_csv, output_final_trades, output_final_trades2
from datetime import datetime, timedelta
import pandas as pd
import concurrent.futures



def checking_trade(pnl, stop_loss_percent, take_profit_percent):
    if pnl >= take_profit_percent:
        return "WIN"
    elif pnl <= (-1 * stop_loss_percent):
        return "LOSS"
    else :
        return None
    
def calc_multiple_pct(symbol, start_date_str, opening_price):

    def calculate_percentage_change(df, opening_price, n):
        min_low = df['low'][:n*60].min()
        max_high = df['high'][:n*60].max()
        
        pct_decrease = (opening_price - min_low) / opening_price
        if pct_decrease < 0:
            pct_decrease = 0
        pct_increase = (max_high - opening_price) / opening_price
        if pct_increase < 0:
            pct_increase = 0
        return pct_decrease, pct_increase

    def extracting_information_profitability(symbol, start_date_str):
        period_hours = 36
        timeframe = "1m"
        api_url = "https://api.binance.com/api/v3/klines"
        start_date_str = datetime.strptime(start_date_str, "%d-%m-%Y %I:%M%p")
        end_date_str = (start_date_str + timedelta(hours=period_hours)).strftime("%d-%m-%Y %I:%M%p")
        start_timestamp = int(start_date_str.timestamp()) * 1000
        end_date_str = datetime.strptime(end_date_str, "%d-%m-%Y %I:%M%p")
        end_timestamp = int(end_date_str.timestamp()) * 1000
        
        all_data = []
        while start_timestamp < end_timestamp:
            try:
                limit = 1000
                params = {'symbol': symbol, 'interval': timeframe, 'startTime': start_timestamp, 'endTime': end_timestamp, 'limit': limit}
                response = requests.get(api_url, params=params)
                data = response.json()
                if not data: 
                    break
                all_data.extend(data)
                start_timestamp = int(data[-1][0]) + 1
            except Exception as e: 
                print("problem occured in calc_multiple percentage", e)
                time.sleep(1)
        df = pd.DataFrame(all_data, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df = df[['high', 'low']]
        df= df.apply(pd.to_numeric)
        return df
    df = extracting_information_profitability(symbol, start_date_str)
    pct_decrease_6hours, pct_increase_6hours = calculate_percentage_change(df, opening_price, 6)
    pct_decrease_12hours, pct_increase_12hours = calculate_percentage_change(df, opening_price, 12)
    pct_decrease_24hours, pct_increase_24hours = calculate_percentage_change(df, opening_price, 24)
    pct_decrease_36hours, pct_increase_36hours = calculate_percentage_change(df, opening_price, 36)
    
    
    return pct_decrease_6hours, pct_increase_6hours,pct_decrease_12hours,pct_increase_12hours,pct_decrease_24hours,pct_increase_24hours,pct_decrease_36hours,pct_increase_36hours



def updater(trade_id, pnl, period_hours, df):
    df.at[trade_id, 'pnl'] = pnl
    df.at[trade_id, 'period_hours'] = period_hours



def process_trade(trade_id, trade_data, trade_to_remove, open_trades):
    symbol = trade_data['symbol']
    side = trade_data['side']
    current_price = get_real_price(symbol)
    trade_data['current_price'] = current_price
    entry_price = trade_data['entry_price']

    if side == 'BUY':
        pnl = round((current_price - entry_price) / entry_price, 5)
    else:
        pnl = round((entry_price - current_price) / current_price, 5)

    period_hours = round(((datetime.now() + timedelta(hours=1)) - (datetime.strptime(trade_data['entry_time_str'], "%d-%m-%Y %I:%M%p"))).total_seconds() / 3600, 2)
    updater(trade_id, pnl, period_hours, open_trades)

    take_profit_percent = trade_data['take_profit_percent']
    stop_loss_percent = trade_data['stop_loss_percent']
    trade_result = checking_trade(pnl, stop_loss_percent, take_profit_percent)

    if trade_result is not None:
        exit_time_str = (datetime.now() + timedelta(hours=1)).strftime("%d-%m-%Y %I:%M%p")
        trade_data['exit_time_str'] = exit_time_str
        trade_data['trade_result'] = trade_result
        trade_data['formated_exit_time'] = (pd.to_datetime(exit_time_str, format='%d-%m-%Y %I:%M%p')).strftime('%d %B')
        gb_classifier = int(trade_data['gradientboostingclassifier'] * 100) if not pd.isna(trade_data['gradientboostingclassifier']) else None
        rf_classifier = int(trade_data['randomforestclassifier'] * 100) if not pd.isna(trade_data['randomforestclassifier']) else None
        xgb_classifier = int(trade_data['xgbclassifier'] * 100) if not pd.isna(trade_data['xgbclassifier']) else None
        send_message(f"Order result of: {trade_data['trade_id']}\n\nGradientBoostingClassifier: {gb_classifier}\nRandomForestClassifier: {rf_classifier}\nXGBClassifier: {xgb_classifier}\nStrategy: {trade_data['strategy']}\nPosition period: {trade_data['period_hours']:.2f} hours\nSymbol: {symbol}\nEntry price: {entry_price}\nPosition: {side}\nTake Profit: {trade_data['exit_price_TP']} || ({round(take_profit_percent*100,2)}%)\nStop Loss: {trade_data['exit_price_SL']} || ({round(stop_loss_percent*100,2)}%)\nResult: {trade_result}\nEntry Time: {trade_data['entry_time_str']}\nExit time: {exit_time_str}\nTimeframe: {trade_data['timeframe']}\nPNL: {(trade_data['pnl']*100):.2f}%")
        finishedtrades_columns = list(trade_data.index)
        trade_data_to_write = trade_data.values.tolist()
        write_to_csv(temporary_finished_trades_csv, finishedtrades_columns, trade_data_to_write)
        trade_to_remove.append(trade_data['trade_id'])

def process_finished_trade(trade_data, trade_to_remove1):
    entry_time_str = trade_data['entry_time_str']
    period_hours = round(((datetime.now() + timedelta(hours=1)) - (datetime.strptime(entry_time_str, "%d-%m-%Y %I:%M%p"))).total_seconds() / 3600, 2)
    if period_hours >= 37:
        trade_data2 = trade_data[['trade_id','gradientboostingclassifier','randomforestclassifier','xgbclassifier']]
        trade_data = trade_data.drop(['gradientboostingclassifier', 'randomforestclassifier','xgbclassifier'], axis=1)
        pct_decrease_6hours, pct_increase_6hours, pct_decrease_12hours, pct_increase_12hours, pct_decrease_24hours, pct_increase_24hours, pct_decrease_36hours, pct_increase_36hours = calc_multiple_pct(trade_data['symbol'], entry_time_str, trade_data['entry_price'])
        finialtrades_columns = list(trade_data.index) + ['pct_decrease_6hours', 'pct_increase_6hours', 'pct_decrease_12hours', 'pct_increase_12hours', 'pct_decrease_24hours', 'pct_increase_24hours', 'pct_decrease_36hours', 'pct_increase_36hours']
        trade_data_to_write = list(trade_data.values) + [pct_decrease_6hours, pct_increase_6hours, pct_decrease_12hours, pct_increase_12hours, pct_decrease_24hours, pct_increase_24hours, pct_decrease_36hours, pct_increase_36hours]
        finialtrades_columns2 = list(trade_data2.index)
        trade_data_to_write2 = list(trade_data2.values)
        write_to_csv(output_final_trades, columns=finialtrades_columns, data=trade_data_to_write)
        write_to_csv(output_final_trades2, columns=finialtrades_columns2, data=trade_data_to_write2)
        write_to_mysql(table_name="tradeswithfeatures_table", sql_columns = finialtrades_columns, data = trade_data_to_write )
        write_to_mysql(table_name="probability_table", sql_columns = finialtrades_columns2 , data = trade_data_to_write2 )
        trade_to_remove1.append(trade_data['trade_id'])


def tracking():
    if os.path.exists(open_trade_csv):
        open_trades = pd.read_csv(open_trade_csv)
        trade_to_remove = []
        if not open_trades.empty:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(process_trade, trade_id, trade_data, trade_to_remove, open_trades): (trade_id, trade_data) for trade_id, trade_data in open_trades.iterrows()}
                for future in concurrent.futures.as_completed(futures):
                    trade_id = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Exception occurred for trade {trade_id}: {e}")
            
            latest_version = pd.read_csv(open_trade_csv)
            new_trades = latest_version[~latest_version['trade_id'].isin(open_trades['trade_id'])]
            open_trades = pd.concat([open_trades, new_trades], ignore_index=True)
            
            for trade_id in trade_to_remove:
                open_trades = open_trades[open_trades['trade_id'] != trade_id]
            open_trades.to_csv(open_trade_csv, index=False)

    if os.path.exists(temporary_finished_trades_csv):
        finished_trades = pd.read_csv(temporary_finished_trades_csv)
        trade_to_remove1 = []
        if not finished_trades.empty:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(process_finished_trade, trade_data, trade_to_remove1): (trade_id, trade_data) for trade_id, trade_data in finished_trades.iterrows()}
                for future in concurrent.futures.as_completed(futures):
                    future.result()

            latest_version = pd.read_csv(temporary_finished_trades_csv)
            new_trades = latest_version[~latest_version['trade_id'].isin(finished_trades['trade_id'])]
            finished_trades = pd.concat([finished_trades, new_trades], ignore_index=True)
            
            
            for trade_id in trade_to_remove1:
                finished_trades = finished_trades[finished_trades['trade_id'] != trade_id]
            
            finished_trades.to_csv(temporary_finished_trades_csv, index=False)

    if not os.path.exists(temporary_finished_trades_csv) and not os.path.exists(open_trade_csv):
        time.sleep(30)

    

if __name__ == "__main__":
    while True:
        tracking()