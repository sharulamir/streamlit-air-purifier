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

# Step 1: Generate Synthetic Data
def generate_synthetic_data(n_samples=2000, noise_level=5):
    np.random.seed(42)  # For reproducibility
    runtime = np.random.uniform(100, 10000, n_samples)      # Runtime in hours
    pm25 = np.random.uniform(10, 200, n_samples)           # PM2.5 levels
    fan_speed = np.random.choice([1, 2, 3, 4], n_samples)  # Fan speed levels
    odor_level = np.random.uniform(0, 100, n_samples)      # Odor sensor readings
    dust_level = np.random.uniform(0, 100, n_samples)      # Dust sensor readings

    # Target: Remaining days before cleaning
    remaining_days = 60 - (
        odor_level / 2 +
        dust_level / 2 +
        runtime / 300 +
        pm25 / 10
    ) + np.random.normal(0, noise_level, n_samples)

    data = pd.DataFrame({
        'runtime': runtime,
        'pm25': pm25,
        'fan_speed': fan_speed,
        'odor_level': odor_level,
        'dust_level': dust_level,
        'remaining_days': remaining_days
    })
    return data

# Step 2: Optimize Hyperparameters with Optuna
def optimize_xgboost(data):
    """
    Optimize XGBoost hyperparameters using Optuna.
    """
    def objective(trial):
        # Define the hyperparameter space
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 300),
            'max_depth': trial.suggest_int('max_depth', 3, 15),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'random_state': 42
        }

        # Split the data
        X = data[['runtime', 'pm25', 'fan_speed', 'odor_level', 'dust_level']]
        y = data['remaining_days']
        X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the model
        model = XGBRegressor(**params)
        model.fit(X_train, y_train)

        # Evaluate on validation set
        predictions = model.predict(X_valid)
        mse = mean_squared_error(y_valid, predictions)
        return mse

    # Run the optimization
    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=50)

    # Best hyperparameters
    print("Best Hyperparameters:", study.best_params)
    return study.best_params

# Step 3: Train Model with Best Hyperparameters
def train_model(data, best_params):
    """
    Train an XGBoost Regressor with the best hyperparameters.
    """
    # Features and target
    X = data[['runtime', 'pm25', 'fan_speed', 'odor_level', 'dust_level']]
    y = data['remaining_days']

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train XGBoost Regressor
    model = XGBRegressor(**best_params)
    model.fit(X_train, y_train)

    # Predictions
    predictions = model.predict(X_test)

    # Evaluate the model
    mse = mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    print(f"Model Performance: MSE = {mse:.2f}, R^2 = {r2:.2f}")

    return model, X_test, y_test, predictions

# Step 4: Streamlit Dashboard
def air_purifier_dashboard(data, model):
    st.title("Air Purifier Real-Time Monitoring and Forecasting Dashboard")

    # Display live data
    st.write("### Live Sensor Data")
    st.dataframe(data.head())

    # Predict remaining days for live data
    X_live = data[['runtime', 'pm25', 'fan_speed', 'odor_level', 'dust_level']]
    data['predicted_remaining_days'] = model.predict(X_live)

    # Display predictions
    st.write("### Predicted Remaining Days for Cleaning")
    st.dataframe(data[['runtime', 'pm25', 'odor_level', 'dust_level', 'predicted_remaining_days']])

    # Visualization: Remaining Days Distribution
    st.write("### Predicted Remaining Days Distribution")
    fig, ax = plt.subplots()
    sns.histplot(data['predicted_remaining_days'], kde=True, bins=30, ax=ax, color='blue')
    ax.set_title("Predicted Remaining Days Distribution")
    st.pyplot(fig)

# Main Function
def main():
    # Generate synthetic training data
    training_data = generate_synthetic_data(n_samples=2000)

    # Optimize hyperparameters
    best_params = optimize_xgboost(training_data)

    # Train the model with best hyperparameters
    model, X_test, y_test, predictions = train_model(training_data, best_params)

    # Generate live data for real-time monitoring
    live_data = generate_synthetic_data(n_samples=100)

    # Launch the dashboard
    air_purifier_dashboard(live_data, model)

if __name__ == "__main__":
    main()
