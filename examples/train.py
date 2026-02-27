"""
Example training script for ML Jobs.

This demonstrates a simple ML workflow that can be submitted to Snowflake compute.
"""

import os
print(f"Running on Snowflake compute!")
print(f"Working directory: {os.getcwd()}")

# Example: Simple sklearn model
try:
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score

    print("\nLoading Iris dataset...")
    X, y = load_iris(return_X_y=True)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training RandomForest model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\nModel accuracy: {accuracy:.2%}")
    print("Training complete!")

except ImportError:
    print("sklearn not available - running basic test")
    print("Hello from Snowflake ML Jobs!")
    print("Training simulation complete!")
