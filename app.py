# -*- coding: utf-8 -*-
"""Test_1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1P8RcXWoBTP6TMHbJUfImIiyfY_f5NSUB
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import optuna

# Step 1: Load Real Data or Use Synthetic Data
def load_real_data(file_path=None, n_samples=20000, use_synthetic=True):
    """
    Load real-world sensor data or generate synthetic data.

    Parameters:
        file_path (str): Path to the real sensor data file.
        n_samples (int): Number of synthetic data points to generate.
        use_synthetic (bool): Whether to generate synthetic data.

    Returns:
        pd.DataFrame: The dataset (real or synthetic).
    """
    if not use_synthetic and file_path:
        # Load real data
        return pd.read_csv(file_path)
    else:
        # Generate synthetic data
        np.random.seed(42)
        runtime = np.random.uniform(100, 10000, n_samples)
        pm25 = np.random.uniform(10, 200, n_samples)
        fan_speed = np.random.choice([1, 2, 3, 4], n_samples)
        odor_level = np.random.uniform(0, 100, n_samples)
        dust_level = np.random.uniform(0, 100, n_samples)
        remaining_days = 60 - (
            odor_level / 2 + dust_level / 2 + runtime / 300 + pm25 / 10
        ) + np.random.normal(0, 5, n_samples)
        return pd.DataFrame({
            'runtime': runtime,
            'pm25': pm25,
            'fan_speed': fan_speed,
            'odor_level': odor_level,
            'dust_level': dust_level,
            'remaining_days': remaining_days
        })

# Step 2: Optimize Hyperparameters with Optuna
def optimize_xgboost(data):
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 300),
            'max_depth': trial.suggest_int('max_depth', 3, 15),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'random_state': 42
        }
        X = data[['runtime', 'pm25', 'fan_speed', 'odor_level', 'dust_level']]
        y = data['remaining_days']
        X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=0.2, random_state=42)
        model = XGBRegressor(**params)
        model.fit(X_train, y_train)
        predictions = model.predict(X_valid)
        return mean_squared_error(y_valid, predictions)

    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=50)
    print("Best Hyperparameters:", study.best_params)
    return study.best_params

# Step 3: Train the Model
def train_model(data, best_params):
    X = data[['runtime', 'pm25', 'fan_speed', 'odor_level', 'dust_level']]
    y = data['remaining_days']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBRegressor(**best_params)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    print(f"Model Performance: MSE = {mse:.2f}, R^2 = {r2:.2f}")
    return model, X_test, y_test, predictions

# Step 4: Notify User
def notify_user(predicted_remaining_days):
    if predicted_remaining_days <= 0:
        return "Needs Cleaning"
    elif 1 <= predicted_remaining_days <= 3:
        return "Prepare for Cleaning"
    else:
        return "Good"

# Step 5: Streamlit Dashboard
def air_purifier_dashboard(data, model):
    st.title("Air Purifier Real-Time Monitoring and Forecasting Dashboard")
    st.write("### Live Sensor Data")
    st.dataframe(data.head())
    X_live = data[['runtime', 'pm25', 'fan_speed', 'odor_level', 'dust_level']]
    data['predicted_remaining_days'] = model.predict(X_live)
    data['status'] = data['predicted_remaining_days'].apply(notify_user)
    st.write("### Predicted Remaining Days for Cleaning")
    st.dataframe(data[['runtime', 'pm25', 'odor_level', 'dust_level', 'predicted_remaining_days', 'status']])
    st.write("### Predicted Remaining Days Distribution")
    fig, ax = plt.subplots()
    sns.histplot(data['predicted_remaining_days'], kde=True, bins=30, ax=ax, color='blue')
    ax.set_title("Predicted Remaining Days Distribution")
    st.pyplot(fig)

# Main Function
def main():
    # Step 1: Train the model with synthetic data
    use_synthetic = True
    file_path = None
    training_data = load_real_data(file_path, n_samples=20000, use_synthetic=use_synthetic)

    # Optimize hyperparameters and train the model
    best_params = optimize_xgboost(training_data)
    model, X_test, y_test, predictions = train_model(training_data, best_params)

    # Step 2: Custom Input for Testing
    custom_data = pd.DataFrame({
        'runtime': [500],
        'pm25': [100],
        'fan_speed': [3],
        'odor_level': [60],
        'dust_level': [50]
    })

    # Make prediction for the custom input
    custom_data['predicted_remaining_days'] = model.predict(custom_data)
    custom_data['status'] = custom_data['predicted_remaining_days'].apply(notify_user)

    # Step 3: Generate Live Data for Monitoring (Synthetic)
    live_data = load_real_data(file_path, n_samples=100, use_synthetic=use_synthetic)
    live_data['predicted_remaining_days'] = model.predict(live_data)
    live_data['status'] = live_data['predicted_remaining_days'].apply(notify_user)

    # Step 4: Combine Custom Input and Live Data for Dashboard
    combined_data = pd.concat([custom_data, live_data], ignore_index=True)

    # Launch the dashboard
    air_purifier_dashboard(combined_data, model)

if __name__ == "__main__":
    main()
