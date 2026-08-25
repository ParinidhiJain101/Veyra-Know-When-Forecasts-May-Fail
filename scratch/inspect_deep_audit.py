"""
Deep inspection script for all 15 audit questions.
"""
import pandas as pd
import json
import numpy as np

# Load training dataset
df_feat = pd.read_parquet("data/features/training_dataset.parquet")
print("=== TRAINING DATASET ===")
print("Shape:", df_feat.shape)
print("Bust label counts:\n", df_feat["bust_label"].value_counts())
print("Bust count by variable:")
print(df_feat.groupby("variable")["bust_label"].value_counts())

# Load bust thresholds
with open("configs/bust_thresholds.json") as f:
    thresh = json.load(f)
print("\n=== THRESHOLDS ===")
print(json.dumps(thresh, indent=2))

# Check revision features calculation
print("\n=== REVISION FEATURES SAMPLE ===")
print(df_feat[["variable", "valid_time", "lead_hours", "forecast_value", "forecast_delta_6h", "forecast_delta_24h", "ensemble_std", "ensemble_spread_delta_6h"]].head(15))
