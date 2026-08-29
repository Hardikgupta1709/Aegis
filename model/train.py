import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss, classification_report
import os
import joblib

def train_core_model():
    print("Loading synthetic data...")
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), '../data/synthetic_orders.csv'))
    
    print("Preprocessing features...")
    X = df.drop(columns=['order_id', 'outcome_label'])
    y = df['outcome_label']
    
    # Convert categorical columns to numeric codes
    X['sector'] = X['sector'].astype('category').cat.codes
    X['payment_method'] = X['payment_method'].astype('category').cat.codes
    
    # --- The 3-Way Split (60% Train, 20% Validate, 20% Test) ---
    print("Performing Train/Validate/Test split...")
    # First split: 80% Train+Val, 20% Test
    X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Second split: Of that 80%, split 75/25 to get 60% Train, 20% Val overall
    X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp)
    
    print(f"Data Shapes -> Train: {X_train.shape[0]}, Validate: {X_val.shape[0]}, Test: {X_test.shape[0]}")

    # Train XGBoost with Early Stopping on the Validation Set
    print("\nTraining XGBoost Multiclass model...")
    model = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        n_estimators=150,
        learning_rate=0.1,
        max_depth=5,
        subsample=0.8,
        random_state=42,
        eval_metric='mlogloss',
        early_stopping_rounds=10 # Prevents overfitting using the Val set!
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    print("\n--- Model Evaluation (On Unseen Test Set) ---")
    y_pred_proba = model.predict_proba(X_test)
    y_pred = model.predict(X_test)
    
    loss = log_loss(y_test, y_pred_proba)
    print(f"Log-Loss: {loss:.4f} (Closer to 0 is better)")
    
    print("\nClassification Report (0=Safe, 1=Fraud, 2=RTO):")
    print(classification_report(y_test, y_pred))
    
    # Save Artifacts
    os.makedirs(os.path.join(os.path.dirname(__file__), 'artifacts'), exist_ok=True)
    joblib.dump(model, os.path.join(os.path.dirname(__file__), 'artifacts/xgboost_model.pkl'))
    
    # Save Validation Set (For tomorrow's threshold sweep)
    val_data = X_val.copy()
    val_data['true_label'] = y_val
    val_data.to_csv(os.path.join(os.path.dirname(__file__), 'artifacts/val_set.csv'), index=False)

    # Save Test Set (For final honest presentation metrics)
    test_data = X_test.copy()
    test_data['true_label'] = y_test
    test_data.to_csv(os.path.join(os.path.dirname(__file__), 'artifacts/test_set.csv'), index=False)
    
    print(f"\nModel, Validation Set, and Test Set saved to model/artifacts/")

if __name__ == "__main__":
    train_core_model()