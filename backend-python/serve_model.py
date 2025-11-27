import argparse
import json
import os
from grracing.data import load_telemetry
from grracing.models import load_model, predict

parser = argparse.ArgumentParser()
parser.add_argument('--csv', help='CSV path to use for a sample prediction')
parser.add_argument('--model', default='models/model.joblib')
args = parser.parse_args()

model_path = args.model
if not os.path.exists(model_path):
    print(json.dumps({'error': 'model not found', 'model_path': model_path}))
    raise SystemExit(2)

model = load_model(model_path)

if args.csv:
    df = load_telemetry(args.csv, nrows=1)
    # attempt to pick same features used for training heuristically
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if not numeric_cols:
        print(json.dumps({'error': 'no numeric columns in csv'}))
        raise SystemExit(3)
    # choose all numeric as features
    X = df[numeric_cols].fillna(0).values[0].tolist()
    preds = predict(model, X)
    print(json.dumps({'prediction': preds, 'features': numeric_cols}))
else:
    print(json.dumps({'error': 'no csv provided'}))
