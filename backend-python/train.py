import argparse
import os
from grracing.data import load_telemetry
from grracing.models import train_simple_model

# Very small example trainer that finds numeric columns and uses them to predict 'LapTime' or first numeric column after filtering.

parser = argparse.ArgumentParser()
parser.add_argument('--csv', required=True)
parser.add_argument('--out', default='models/model.joblib')
args = parser.parse_args()

print('Loading', args.csv)
df = load_telemetry(args.csv)
# pick numeric columns
numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
if not numeric_cols:
    raise SystemExit('No numeric columns found in CSV')

# naive target selection: column named 'lap_time' or last numeric
target = None
for c in ['lap_time', 'LapTime', 'LAP_TIME', 'lapTime', 'lap_time_seconds']:
    if c in numeric_cols:
        target = c
        break
if target is None:
    target = numeric_cols[-1]

features = [c for c in numeric_cols if c != target]
if not features:
    # fallback: use an index-derived feature
    df['idx_feat'] = df.index.to_series()
    features = ['idx_feat']

print('Training model predicting', target, 'using', len(features), 'features')
model = train_simple_model(df, features, target, out_path=args.out)
print('Saved model to', args.out)
