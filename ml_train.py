from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import pandas as pd, xgboost as xgb , joblib



data_to_train = "files/download/output_final_trades.csv"
encode_csv_path = 'files/ml/encoder_data.csv'

models = {
    'GradientBoostingClassifier': (GradientBoostingClassifier(random_state=42), {
        'loss': ['log_loss', 'exponential'],
        'criterion': ['friedman_mse', 'squared_error'],
        'n_estimators': [100, 200, 300],  # Number of boosting stages
        'learning_rate': [0.1, 0.01, 0.001],  # Learning rate shrinks the contribution of each tree
        'max_depth': [3, 5, 7]  # Maximum depth of the individual regression estimators
    }),

    'XGBClassifier': (xgb.XGBClassifier(random_state=42), {
        'learning_rate': [0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3],
        'n_estimators': [50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 350, 400],
        'max_depth': [20,21,22,23,24,25,26,27,28,29,30],
        'min_child_weight': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
        'colsample_bytree': [0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        'gamma': [0, 0.1, 0.2, 0.3, 0.4, 0.5],
        'scale_pos_weight': [1, 2, 3, 4, 5, 6],
        'reg_alpha': [0, 0.001, 0.01, 0.1, 1, 10],
        'reg_lambda': [0, 0.001, 0.01, 0.1, 1, 10]
    }),

    'RandomForestClassifier': (RandomForestClassifier(random_state=42), {
        'n_estimators': [50, 100, 150, 200, 250, 300],
        'criterion': ['gini', 'entropy', 'log_loss'],  # Number of trees in the forest
        'max_depth': [None, 5, 10, 15, 20, 25],  # Maximum depth of the tree
        'min_samples_split': [15, 20],  # Minimum number of samples required to split an internal node
        'min_samples_leaf': [1, 2, 4, 6], # Minimum number of samples required to be at a leaf node
        'max_leaf_nodes': [None, 10, 20, 30, 40],
        'min_weight_fraction_leaf': [0.0, 0.1, 0.2],
        'max_features': ['sqrt', 'log2', None]  # Grow trees with max_leaf_nodes in best-first fashion
    }),

}


def train_models():
    def encode_categorical_columns(df):
        label_encoders = {}
        try:
            encoder_df = pd.read_csv(encode_csv_path)
            for _, row in encoder_df.iterrows():
                column = row['column']
                key = row['key']
                value = row['value']
                if column not in label_encoders:
                    label_encoders[column] = {}
                label_encoders[column][key] = value
        except FileNotFoundError:
            pass
        
        encoded_columns = []
        for column in df.select_dtypes(include=['object']).columns:
            if column == 'trade_id':
                continue
            if column not in label_encoders:
                label_encoders[column] = {}
            new_values = set(df[column]) - set(label_encoders[column].keys())
            if new_values:
                new_mapping = {value: len(label_encoders[column]) + i for i, value in enumerate(new_values)}
                label_encoders[column].update(new_mapping)

                for key, value in new_mapping.items():
                    encoded_columns.append({'column': column, 'key': key, 'value': value})

            df[column] = df[column].map(label_encoders[column])

        encoder_df = pd.DataFrame(encoded_columns)
        encoder_df.to_csv(encode_csv_path, mode='a', header=True, index=False)

        return df



    df = pd.read_csv(data_to_train)
    df = df[["trade_id","symbol","side", "take_profit_percent","stop_loss_percent","strategy","timeframe", "entry_day_of_week", "entry_hour", "aroon_up","aroon_down", "rsi", "macd", "24h_volume","trade_result"]]
    df[["take_profit_percent","stop_loss_percent", "aroon_up","aroon_down", "rsi", "macd", "24h_volume"]] = df[["take_profit_percent","stop_loss_percent", "aroon_up","aroon_down", "rsi", "macd", "24h_volume"]].astype("float")
    df = encode_categorical_columns(df)

    columns_to_normalize = ["take_profit_percent","stop_loss_percent","aroon_up","aroon_down", "rsi", "macd", "24h_volume"]
    scaler = MinMaxScaler()
    normalized_data = []

    for coin_id, group_data in df.groupby('symbol'):
        group_data[columns_to_normalize] = scaler.fit_transform(group_data[columns_to_normalize])
        normalized_data.append(group_data)

    normalized_data = pd.concat(normalized_data, ignore_index=True)
    normalized_data = normalized_data.drop(columns=['trade_id'])
    X = normalized_data.drop(columns=['trade_result'])
    y = normalized_data['trade_result']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)




    for model_name, (model, param_grid) in models.items():
        search = RandomizedSearchCV(model, param_distributions=param_grid, n_iter=10, scoring='accuracy', cv=3, verbose=2, random_state=42)
        search.fit(X_train, y_train)
        best_params = search.best_params_
        best_model = model.set_params(**best_params)
        best_model.fit(X_train, y_train)
        filename = f'files/ml/{model_name}.pkl'
        joblib.dump(best_model, filename)





