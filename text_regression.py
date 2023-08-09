from catboost import CatBoostRegressor
import pandas as pd
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('--model_path', type=str, default='C:/Deep Learning/ml_analytics/data/catboost_text_regressor')
parser.add_argument('--json_path', type=str, default='C:/Deep Learning/ml_analytics/resule_parsing.json')
args = parser.parse_args()

model = CatBoostRegressor()      # parameters not required.
model.load_model(args.model_path)

with open(args.json_path, encoding='utf-8') as f:
    text = json.load(f)[0]['description']

inputs = pd.DataFrame({'descriptions':[text]})
predict = abs(round(model.predict(inputs)[0], 2))
print(predict)
