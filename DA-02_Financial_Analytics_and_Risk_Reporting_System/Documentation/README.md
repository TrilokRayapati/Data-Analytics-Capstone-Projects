# Financial Analytics & Risk Reporting System

## About the Project

I built this project to explore how data analytics and machine learning can be used in the financial and lending domain.

The project covers different stages of an analytics workflow, starting with synthetic data generation and SQL analysis, followed by Power BI reporting and loan default prediction using machine learning.

The main goal was to understand loan portfolio performance, explore factors related to loan defaults, and build a model that predicts whether a loan is likely to be classified as default or non-default.

**Note:** All datasets used in this project are synthetic and created for learning and demonstration purposes.

## Tools & Technologies

- Python
- Pandas and NumPy
- PostgreSQL
- Power BI
- Scikit-learn
- Joblib

## What I Worked On

### 1. Data Generation and Preparation
- Generated synthetic lending and financial datasets using Python.
- Worked with loan, customer, payment, and financial transaction data.
- Checked missing values, duplicate records, and data types.

### 2. SQL Analysis
- Used PostgreSQL to analyze loan and financial data.
- Wrote SQL queries to explore loan portfolios and financial metrics.
- Used SQL to support reporting and analytical insights.

### 3. Power BI Dashboard
- Built interactive dashboards for financial and loan portfolio reporting.
- Created KPIs and visualizations to explore financial performance and loan-related trends.

### 4. Loan Default Prediction

I used Python and Scikit-learn to build a machine learning model for predicting loan default status.

The target column was `DefaultFlag`:

- `0` — Non-default
- `1` — Default

During preprocessing, I:
- Removed identifier columns and potential target leakage columns.
- Converted date columns into datetime format.
- Extracted issue year and month.
- Created a loan duration feature.
- Encoded loan types using one-hot encoding.
- Split the data into training and testing sets using an 80:20 split.

I tested the following classification algorithms:

| Algorithm | Accuracy |
|---|---:|
| Decision Tree | 69.17% |
| Random Forest | 76% |
| Logistic Regression | 76% |
| Gradient Boosting | 75% |
| K-Nearest Neighbors | 61% |

Random Forest was selected as the preliminary model based on the recorded results.

### 5. Model Prediction

After training the model, I saved it using Joblib and loaded it in a separate Python script.

I tested the saved model with sample loan details and generated a prediction for default or non-default status.

## Project Files

| File | Purpose |
|---|---|
| `dataset_generation.py` | Generates synthetic datasets |
| `loan_default_prediction.py` | Preprocessing, model training, and evaluation |
| `prediction.py` | Loads the trained model and predicts loan default |
| `loan_default_model.pkl` | Saved Random Forest model |
| `requirements.txt` | Python dependencies |

## How to Run the Project

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Run the model training script:

```bash
python loan_default_prediction.py
```

Run the prediction script:

```bash
python prediction.py
```

## What I Learned

Through this project, I practiced working with financial datasets, SQL-based analysis, Power BI reporting, feature engineering, model training, and model evaluation.

It also helped me understand how different machine learning algorithms perform on the same dataset and how a trained model can be saved and reused for predictions.

## Limitations

This project uses synthetic data, so the results should not be considered representative of real-world lending or credit risk.

The model is intended for learning and demonstration purposes only and should not be used for actual financial or lending decisions.

## Author

**Trilok Rayapati**

[LinkedIn](https://www.linkedin.com/in/trilok-rayapati) | [GitHub](https://github.com/TrilokRayapati)