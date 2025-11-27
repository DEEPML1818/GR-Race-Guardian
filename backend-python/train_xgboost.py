"""
XGBoost Model Training Script

Trains XGBoost models for race predictions with enhanced performance.
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
import joblib
import json
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from grracing.data import load_telemetry
from grracing.preprocess import merge_lap_and_telemetry


def train_xgboost_model(df, feature_cols, target_col, out_path=None, **kwargs):
    """
    Train an XGBoost model for race predictions.
    
    Args:
        df: DataFrame with training data
        feature_cols: List of feature column names
        target_col: Target column name
        out_path: Path to save model
        **kwargs: Additional XGBoost parameters
    
    Returns:
        Trained XGBoost model
    """
    # Prepare data
    X = df[feature_cols].fillna(0).values
    y = df[target_col].values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # XGBoost parameters
    params = {
        'n_estimators': kwargs.get('n_estimators', 100),
        'max_depth': kwargs.get('max_depth', 6),
        'learning_rate': kwargs.get('learning_rate', 0.1),
        'subsample': kwargs.get('subsample', 0.8),
        'colsample_bytree': kwargs.get('colsample_bytree', 0.8),
        'objective': 'reg:squarederror',
        'random_state': 42
    }
    
    # Train model
    print(f'Training XGBoost model with {len(X_train)} samples...')
    model = xgb.XGBRegressor(**params)
    model.fit(X_train, y_train)
    
    # Evaluate
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    
    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    train_r2 = r2_score(y_train, train_pred)
    test_r2 = r2_score(y_test, test_pred)
    
    print(f'\nTraining RMSE: {train_rmse:.4f}')
    print(f'Test RMSE: {test_rmse:.4f}')
    print(f'Training R²: {train_r2:.4f}')
    print(f'Test R²: {test_r2:.4f}')
    
    # Save model
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        joblib.dump(model, out_path)
        
        # Save metadata
        meta = {
            'feature_names': feature_cols,
            'target': target_col,
            'train_rmse': float(train_rmse),
            'test_rmse': float(test_rmse),
            'train_r2': float(train_r2),
            'test_r2': float(test_r2),
            'n_samples': len(X_train),
            'n_features': len(feature_cols),
            'model_type': 'xgboost',
            'params': params
        }
        
        meta_path = out_path + '.meta.json'
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2)
        
        print(f'\nModel saved to: {out_path}')
        print(f'Metadata saved to: {meta_path}')
    
    return model


def main():
    parser = argparse.ArgumentParser(description='Train XGBoost model for race predictions')
    parser.add_argument('--csv', required=True, help='Path to training CSV file')
    parser.add_argument('--out', default='models/xgboost_model.joblib', help='Output model path')
    parser.add_argument('--target', help='Target column name (auto-detect if not provided)')
    parser.add_argument('--n-estimators', type=int, default=100, help='Number of estimators')
    parser.add_argument('--max-depth', type=int, default=6, help='Max depth')
    parser.add_argument('--learning-rate', type=float, default=0.1, help='Learning rate')
    
    args = parser.parse_args()
    
    print(f'Loading data from: {args.csv}')
    df = load_telemetry(args.csv)
    
    # Select numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if not numeric_cols:
        raise SystemExit('No numeric columns found in CSV')
    
    # Auto-detect target
    if args.target:
        target = args.target
    else:
        target_candidates = ['lap_time', 'LapTime', 'LAP_TIME', 'lap_time_seconds', 'value']
        target = None
        for candidate in target_candidates:
            if candidate in numeric_cols:
                target = candidate
                break
        
        if target is None:
            target = numeric_cols[-1]
    
    # Features are all numeric columns except target
    features = [c for c in numeric_cols if c != target]
    if not features:
        df['idx_feat'] = df.index
        features = ['idx_feat']
    
    print(f'Training model predicting {target} using {len(features)} features')
    
    # Train model
    model = train_xgboost_model(
        df,
        features,
        target,
        out_path=args.out,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate
    )
    
    print('\n✅ Training complete!')


if __name__ == '__main__':
    main()

