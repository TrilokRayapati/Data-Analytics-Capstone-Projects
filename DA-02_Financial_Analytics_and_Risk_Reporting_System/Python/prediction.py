import pandas as pd
import joblib

# Load trained model
model = joblib.load("Python/loan_default_model.pkl")

# New loan details
new_loan = pd.DataFrame([{
    "LoanAmount": 50000,
    "InterestRate": 8.5,
    "TermMonths": 36,
    "CreditScore": 700,
    "DebtToIncomeRatio": 0.3,
    "PriorDelinquencies": 0,
    "AnnualIncome": 60000,
    "IssueYear": 2026,
    "IssueMonth": 11,
    "LoanDurationDays": 1095,
    "LoanType_Auto": 0,
    "LoanType_Business": 0,
    "LoanType_Education": 0,
    "LoanType_Home": 0,
    "LoanType_Personal": 1
}])

# Ensure feature order matches training
new_loan = new_loan[model.feature_names_in_]

# Predict
prediction = model.predict(new_loan)

# Prediction probability
probability = model.predict_proba(new_loan)[0][1]

if prediction[0] == 1:
    print("Prediction: Loan Default")
else:
    print("Prediction: No Loan Default")

print(f"Default Probability: {probability:.2%}")