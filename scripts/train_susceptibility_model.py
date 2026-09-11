import pandas as pd
import numpy as np
import joblib

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score
)

BASE = Path(__file__).resolve().parents[1]

DATA_FILE = BASE / "data/processed/final_training_dataset.csv"
MODEL_FILE = BASE / "model/landslide_susceptibility_model.pkl"

print("=" * 60)
print("LANDSLIDE SUSCEPTIBILITY MODEL")
print("=" * 60)

# ---------------------------------------------------------
# 1. Load dataset
# ---------------------------------------------------------

df = pd.read_csv(DATA_FILE)

print(f"Dataset size: {len(df)}")

# ---------------------------------------------------------
# 2. Select features
# ---------------------------------------------------------

features = [
    "elevation_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos"
]

X = df[features]
y = df["label"]

print("\nFeatures:")
print(features)

print("\nClass distribution:")
print(y.value_counts())

# ---------------------------------------------------------
# 3. Train / test split
# ---------------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# ---------------------------------------------------------
# 4. Random Forest
# ---------------------------------------------------------

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    min_samples_leaf=3,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1
)

print("\nTraining Random Forest...")

model.fit(
    X_train,
    y_train
)

print("Training complete.")

# ---------------------------------------------------------
# 5. Predictions
# ---------------------------------------------------------

y_pred = model.predict(X_test)

y_probability = model.predict_proba(
    X_test
)[:, 1]

# ---------------------------------------------------------
# 6. Evaluation
# ---------------------------------------------------------

accuracy = accuracy_score(
    y_test,
    y_pred
)

auc = roc_auc_score(
    y_test,
    y_probability
)

print("\n" + "=" * 60)
print("MODEL PERFORMANCE")
print("=" * 60)

print(f"\nAccuracy: {accuracy:.4f}")
print(f"ROC-AUC:  {auc:.4f}")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred
    )
)

print("\nConfusion Matrix:")
print(
    confusion_matrix(
        y_test,
        y_pred
    )
)

# ---------------------------------------------------------
# 7. Feature importance
# ---------------------------------------------------------

importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\nFeature Importance:")
print(importance.to_string(index=False))

# ---------------------------------------------------------
# 8. Save model
# ---------------------------------------------------------

joblib.dump(
    model,
    MODEL_FILE
)

print("\n" + "=" * 60)
print("MODEL SAVED")
print("=" * 60)

print(MODEL_FILE)

print("=" * 60)