import pandas as pd
import numpy as np
import joblib


encode_csv_path = 'files/ml/encoder_data.csv'
output_final_trades = 'files/download/output_final_trades.csv'

def predict_probability(dict, model_path, number_of_previous_trades):

    def decode_dict_features(input_dict, encoder_data):
        def decode_feature(encoded_value, encoder_data):
            filtered_data = encoder_data[encoder_data['key'] == encoded_value] 
            if not filtered_data.empty:
                decoded_value = filtered_data['value'].values[0]
                return int(decoded_value)
            else:
                return None
            
        decoded_dict = {}
        for key, value in input_dict.items():
            if isinstance(value, (float,int)):
                decoded_dict[key] = value
            else:
                decoded_value = decode_feature(value, encoder_data)
                decoded_dict[key] = decoded_value
        return decoded_dict


    def scale_dict_values(output_trades_data, symbol, data_dict):
        scaled_dict = {}
        for column, value in data_dict.items():
            if isinstance(value, float):
                symbol_data = output_trades_data[output_trades_data['symbol'] == symbol]
                max_value = symbol_data[column].max()
                min_value = symbol_data[column].min()
                scaled_value = (value - min_value) / (max_value - min_value) if (max_value - min_value) != 0 else 0  # Avoid division by zero
                scaled_dict[column] = scaled_value
            else:
                scaled_dict[column] = value
        return scaled_dict
    try:
        keys_to_keep = ['symbol','side','take_profit_percent', 'stop_loss_percent','strategy', 'timeframe','entry_day_of_week','entry_hour', 'aroon_up','aroon_down', 'rsi','macd','24h_volume']
        dict = {key: dict[key] for key in keys_to_keep}
        print(f"dict:{dict}")
        output_trades_data = pd.read_csv(output_final_trades)
        filtered_df = output_trades_data[(output_trades_data['symbol'] == dict['symbol']) & (output_trades_data['strategy'] == dict['strategy'])]
        if len(filtered_df) >= number_of_previous_trades : 
            scaled_dict = scale_dict_values(output_trades_data, dict['symbol'], dict)    
            encoder_data = pd.read_csv(encode_csv_path)
            scaled_decoded_dict = decode_dict_features(scaled_dict, encoder_data)
            feature_names = list(scaled_decoded_dict.keys())
            features = list(scaled_decoded_dict.values())
            with open(model_path, 'rb') as file:
                model = joblib.load(file)
            input_data = {feature: features[i] for i, feature in enumerate(feature_names)}
            input_array = np.array([[input_data[feature] for feature in feature_names]])
            probability = model.predict_proba(input_array)[:, 1]
            return probability[0]
        else: 
            return ''
        
    except Exception as e:
        
        print(f"An error occurred: {e}")
        
        return ''
