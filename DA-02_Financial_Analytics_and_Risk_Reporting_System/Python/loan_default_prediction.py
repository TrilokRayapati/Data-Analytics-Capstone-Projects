import pandas as pd

df = pd.read_csv("Dataset/generated_data/output/Loans.csv")
print(df.shape)
print(df.head())
print("Dataset Shape:", df.shape)
print("\nColumn Names:")
print(df.columns.tolist())
print("\nData Types:")
print(df.dtypes)
print("\nFirst 5 Rows:")
print(df.head())
print("\nMissing Values:")
print(df.isnull().sum())
print("\nDefault Distribution:")
print(df["DefaultFlag"].value_counts())

print("\nDefault Percentage:")
print(df["DefaultFlag"].value_counts(normalize=True) * 100)
print("Duplicate rows:", df.duplicated().sum())

print("Duplicate LoanIDs:", df["LoanID"].duplicated().sum())
X = df.drop(columns=[
    "LoanID",
    "CustomerID",
    "DefaultProbability",
    "DefaultFlag",
    "LoanStatus"
])

# Target variable
y = df["DefaultFlag"]

print("Features:")
print(X.columns.tolist())

print("\nTarget:")
print(y.name)

print("\nFeature shape:", X.shape)
print("Target shape:", y.shape)
X["IssueDate"] = pd.to_datetime(X["IssueDate"])
X["MaturityDate"] = pd.to_datetime(X["MaturityDate"])
X["IssueYear"] = X["IssueDate"].dt.year
X["IssueMonth"] = X["IssueDate"].dt.month
X["LoanDurationDays"] = (
    X["MaturityDate"] - X["IssueDate"]
).dt.days
X = X.drop(columns=["IssueDate", "MaturityDate"])
X = pd.get_dummies(X, columns=["LoanType"], dtype=int)
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("X_train:", X_train.shape)
print("X_test:", X_test.shape)

print("y_train:", y_train.shape)
print("y_test:", y_test.shape)
print(X.head())
print(X.dtypes)
from sklearn.ensemble import RandomForestClassifier
model =  RandomForestClassifier(random_state=42)



model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("Model training completed")
# Feature Importance
importance = model.feature_importances_

feature_importance = pd.DataFrame({
    "Feature": X_train.columns,
    "Importance": importance
})

feature_importance = feature_importance.sort_values(
    by="Importance",
    ascending=False
)

print("\nFeature Importance:")
print(feature_importance)

print("Predictions:")
print(y_pred)
from sklearn.metrics import accuracy_score

accuracy = accuracy_score(y_test, y_pred)

print("Model Accuracy:", accuracy)
print("Accuracy Percentage:", accuracy * 100, "%")
from sklearn.metrics import confusion_matrix, classification_report

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))
results = pd.DataFrame({
    "Algorithm": [
        "Decision Tree",
        "Random Forest",
        "Logistic Regression",
        "Gradient Boosting",
        "KNN"
    ],
    "Accuracy": [
        69.17,
        76,
        76,
        75,
        61
    ]
})

print(results.sort_values(by="Accuracy", ascending=False))

import os

print("Current working directory:")
print(os.getcwd())

print("\nFiles and folders here:")
print(os.listdir())
print("Exact model features:")
print(X.columns.tolist())
import joblib

joblib.dump(model, "Python/loan_default_model.pkl")

print("Model saved successfully!")
