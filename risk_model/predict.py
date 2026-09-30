import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

FEATURES = ["vol5", "vol21", "vol63"]

def _build_feature_frame(ticker, returns):
    df = pd.DataFrame({"ret": returns})
    df["vol5"] = df["ret"].rolling(5).std() * np.sqrt(252)
    df["vol21"] = df["ret"].rolling(21).std() * np.sqrt(252)
    df["vol63"] = df["ret"].rolling(63).std() * np.sqrt(252)
    df["target"] = df["ret"].rolling(21).std().shift(-21) * np.sqrt(252)
    df = df.dropna()
    df["ticker"] = ticker
    return df

def predict_next_volatility(all_data, test_fraction=0.2):

    frames = [_build_feature_frame(d["ticker"], d["returns"]) for d in all_data]
    full = pd.concat(frames)

    split = int(len(full) * (1 - test_fraction))
    train, test = full.iloc[:split], full.iloc[split:]

    model = Ridge(alpha=1.0)
    model.fit(train[FEATURES], train["target"])

    test_pred = model.predict(test[FEATURES])
    mae = float(np.mean(np.abs(test_pred - test["target"])))
    print(f"Volatility prediction test MAE: {mae:.4f} (annualized vol units)")

    predictions = {}
    for d in all_data:
        r = d["returns"]
        latest = pd.DataFrame({
            "vol5": [r.tail(5).std() * np.sqrt(252)],
            "vol21": [r.tail(21).std() * np.sqrt(252)],
            "vol63": [r.tail(63).std() * np.sqrt(252)],
        })
        pred_vol = model.predict(latest[FEATURES])[0]
        predictions[d["ticker"]] = max(float(pred_vol), 0.0)

    return predictions, mae
