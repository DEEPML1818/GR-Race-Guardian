import os
import json
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')


def train_simple_model(df, feature_cols, target_col, out_path=None):
    """Train a simple regressor and optionally save model + metadata.

    Writes a companion JSON file with feature names and target when out_path provided.
    """
    X = df[feature_cols].fillna(0).values
    y = df[target_col].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = GradientBoostingRegressor(n_estimators=50)
    model.fit(X_train, y_train)
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        joblib.dump(model, out_path)
        # save metadata next to model
        meta = {'feature_names': feature_cols, 'target': target_col}
        meta_path = out_path + '.meta.json'
        with open(meta_path, 'w', encoding='utf-8') as fh:
            json.dump(meta, fh)
    return model


def load_model(path):
    return joblib.load(path)


def load_model_meta(path):
    meta_path = path + '.meta.json'
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    return None


def predict(model, X):
    Xarr = np.asarray(X)
    if Xarr.ndim == 1:
        Xarr = Xarr.reshape(1, -1)
    preds = model.predict(Xarr)
    return preds.tolist()
