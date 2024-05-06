from bot_functions import *

syfer_file_path = "files/download/syfer_PendingTrades.json"
syfer_coin_file_path = "files/syfer_coins.txt"

def project_syfer(pct):

    def isSupport(df, i):
        support = df['low'][i] < df['low'][i-1] and df['low'][i] < df['low'][i+1] and df['low'][i+1] < df['low'][i+2] and df['low'][i-1] < df['low'][i-2]
        return support

    def isResistance(df, i):
        resistance = df['high'][i] > df['high'][i-1] and df['high'][i] > df['high'][i+1] and df['high'][i+1] > df['high'][i+2] and df['high'][i-1] > df['high'][i-2]
        return resistance

    def isFarFromLevel(l, levels, s):
        return np.sum([abs(l - x) < s for x in levels]) == 0

    def detect_key_levels(df, pct):
        s = np.mean(df['high'] - df['low'])

        levels = []
        for i in range(2, df.shape[0] - 2):
            if isSupport(df, i):
                l = df['low'][i]
                if isFarFromLevel(l, levels, s):
                    levels.append(l)
            elif isResistance(df, i):
                l = df['high'][i]
                if isFarFromLevel(l, levels, s):
                    levels.append(l)
        levels.sort()
        current_price = df['close'].iloc[-1]
        supportlevel = levels[0]
        resistancelevel= levels[-1]
        pricetosell = supportlevel - (supportlevel * (pct/100))
        pricetobuy = resistancelevel + (resistancelevel * (pct/100))

        return pricetosell , current_price, pricetobuy
    
    last_execution_time = 0
    if os.path.exists(syfer_file_path):
        data = read_json_file(syfer_file_path)
        last_execution_time = data.get("last_execution_time", 0)

    current_time = time.time()
    elapsed_time_since_last_project_syfer = current_time - last_execution_time

    if elapsed_time_since_last_project_syfer >= 72 * 3600 :  # schedule every 72 hours
        coins_dict = {}

        with open(syfer_coin_file_path) as f:
            coins = f.read().splitlines()

        for coin in coins:
            try:
                df = extract_information(coin, '15m', 500)
                pricetosell, current_price, pricetobuy = detect_key_levels(df, pct)
                coins_dict[coin] = {'pricetosell': pricetosell, 'current_price': current_price, 'pricetobuy': pricetobuy}
            
            except Exception as e:
                print(f"An error occurred for {coin}: {e}")

        coins_dict["last_execution_time"] = current_time
        
        write_json_file(syfer_file_path, coins_dict)


def check_pending_orders_project_syfer():
    coins_data = read_json_file(syfer_file_path)

    for symbol, data in coins_data.items():
        if symbol == "last_execution_time":
            continue

        pricetosell = data["pricetosell"]
        current_price = get_real_price(symbol)
        pricetobuy = data["pricetobuy"]

        if current_price >= pricetobuy:
            return symbol, "BUY"

        if current_price <= pricetosell:
            return symbol, "SELL"

    return None, None