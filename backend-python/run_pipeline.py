import os
import sys
import json
import traceback

# Ensure backend-python package path is importable
backend_pkg = os.path.abspath(os.path.dirname(__file__))
if backend_pkg not in sys.path:
    sys.path.insert(0, backend_pkg)

def main():
    try:
        from grracing.preprocess import merge_lap_and_telemetry
        from grracing.models import train_simple_model, load_model_meta
        import joblib
        import matplotlib.pyplot as plt
    except Exception as e:
        print('Failed to import project helpers:', e)
        traceback.print_exc()
        return 2

    root = os.path.abspath(os.path.join(backend_pkg, '..'))
    lap_csv = os.path.join(root, 'road-america', 'road-america', 'Road America', 'Race 1', 'road_america_lap_time_R1.csv')
    telemetry_csv = os.path.join(root, 'road-america', 'road-america', 'Road America', 'Race 1', 'R1_road_america_telemetry_data.csv')

    if not os.path.exists(lap_csv) or not os.path.exists(telemetry_csv):
        print('Input CSVs not found:')
        print('  lap_csv ->', lap_csv, os.path.exists(lap_csv))
        print('  telemetry_csv ->', telemetry_csv, os.path.exists(telemetry_csv))
        return 3

    models_dir = os.path.join(backend_pkg, 'models')
    os.makedirs(models_dir, exist_ok=True)

    merged_out = os.path.join(models_dir, 'merged_road_america.csv')
    model_out = os.path.join(models_dir, 'merged_road_model.joblib')
    shap_out = os.path.join(models_dir, 'shap_summary.png')

    print('Merging lap and telemetry...')
    merged_df = merge_lap_and_telemetry(lap_csv, telemetry_csv, out_csv=merged_out)
    print('Merged rows:', len(merged_df))

    print('Selecting features and training model...')
    df = merged_df
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    target = 'value' if 'value' in df.columns else (numeric_cols[-1] if numeric_cols else None)
    features = [c for c in numeric_cols if c != target]
    if not features:
        df['idx_feat'] = df.index
        features = ['idx_feat']

    model = train_simple_model(df, features, target, out_path=model_out)
    print('Model saved to', model_out)

    # Try SHAP explainability
    try:
        import shap
        print('Running SHAP (small sample)...')
        meta = load_model_meta(model_out)
        features_used = meta['feature_names'] if meta else features
        sample_X = df[features_used].fillna(0).values[:200]
        explainer = shap.Explainer(model)
        shap_values = explainer(sample_X)
        plt.figure(figsize=(8,6))
        shap.summary_plot(shap_values, features=sample_X, feature_names=features_used, show=False)
        plt.tight_layout()
        plt.savefig(shap_out)
        print('Saved SHAP summary to', shap_out)
    except Exception as e:
        print('SHAP step failed (continue):', e)
        traceback.print_exc()

    print('\nArtifacts created:')
    for p in (merged_out, model_out, shap_out):
        print(' -', p, os.path.exists(p))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
