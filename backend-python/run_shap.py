"""Run SHAP explainability on the merged model and save summary PNG.

Usage (Windows cmd.exe):
  cd backend-python
  .venv\Scripts\activate  # if using venv
  python run_shap.py --model models/merged_road_model.joblib --merged models/merged_road_america.csv --out models/shap_summary.png
"""
import argparse
import os
import sys
import json
import traceback

try:
    import joblib
    import pandas as pd
    import shap
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from grracing.models import load_model_meta
except Exception as e:
    print('Missing dependency:', e)
    raise

parser = argparse.ArgumentParser()
parser.add_argument('--model', required=True)
parser.add_argument('--merged', required=True)
parser.add_argument('--out', default='models/shap_summary.png')
args = parser.parse_args()

if not os.path.exists(args.model):
    print('Model file not found:', args.model)
    sys.exit(2)
if not os.path.exists(args.merged):
    print('Merged CSV not found:', args.merged)
    sys.exit(3)

try:
    print('Loading model:', args.model)
    model = joblib.load(args.model)
    meta = load_model_meta(args.model)
    df = pd.read_csv(args.merged)
    if meta and 'feature_names' in meta:
        features = meta['feature_names']
    else:
        features = df.select_dtypes(include=['number']).columns.tolist()
        # heuristic: drop last numeric if it's the target
        if len(features) > 1:
            features = features[:-1]

    print('Features used:', features)
    X = df[features].fillna(0).values[:200]
    print('Sample shape:', X.shape)

    explainer = shap.Explainer(model)
    shap_values = explainer(X)

    plt.figure(figsize=(10,6))
    shap.summary_plot(shap_values, features=X, feature_names=features, show=False)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    plt.tight_layout()
    plt.savefig(args.out)
    print('Saved SHAP summary to', args.out)
except Exception:
    print('Error running SHAP:')
    traceback.print_exc()
    sys.exit(4)
