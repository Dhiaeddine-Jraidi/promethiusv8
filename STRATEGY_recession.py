from bot_functions import *

recession_file_path = "files/download/recession.csv"
symbol = 'BTCUSDT'
columns = ['symbol','target_price_to_buy', 'target_price_to_sell', 'current_price']



def recession_check(number_of_successive_zeros, pct_increase_to_buy, pct_decrease_to_sell):
    if not os.path.exists(recession_file_path):
        recent_rows = indicators(symbol).tail(number_of_successive_zeros)
        zeros = recent_rows['ImpulseMACDCDSignal'] == 0     
        if zeros.all():
            df = indicators(symbol)
            midprice = df.at[df.index[-1], 'BollingerMid']
            target_price_to_buy = midprice + (midprice * (pct_increase_to_buy / 100))
            target_price_to_sell = midprice - (midprice * (pct_decrease_to_sell / 100))
            current_price = get_real_price(symbol)
            data_to_save = [symbol,target_price_to_buy,target_price_to_sell,current_price]
            write_to_csv(recession_file_path, columns, data_to_save)    

def check_pending_orders_recession():
    if os.path.exists(recession_file_path):
        df = read_dataframe(recession_file_path, columns)
    
        pricetosell = df["target_price_to_sell"].iloc[-1]
        current_price = get_real_price(symbol)
        pricetobuy = df["target_price_to_buy"].iloc[-1]

        if current_price >= pricetobuy:
            return "BUY"

        elif current_price <= pricetosell:
            return "SELL"
        
        else:
            return None