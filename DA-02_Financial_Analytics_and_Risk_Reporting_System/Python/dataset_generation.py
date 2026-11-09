import os
import random
import numpy as np
import pandas as pd
from faker import Faker

# ============================================================
# FINANCIAL ANALYTICS AND RISK REPORTING SYSTEM
# Fictional Indian lending company | INR | Jan-2023 to Dec-2025
# Generates seven CSV tables in the output folder.
# ============================================================

Faker.seed(42)
random.seed(42)
np.random.seed(42)
fake = Faker("en_IN")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
AS_OF_DATE = pd.Timestamp("2025-12-31")

# 1. DEPARTMENTS
df_departments = pd.DataFrame([
    [1, "Sales", "Hyderabad"],
    [2, "Finance", "Hyderabad"],
    [3, "Operations", "Bengaluru"],
    [4, "Technology", "Bengaluru"],
    [5, "Marketing", "Chennai"],
    [6, "Customer Support", "Chennai"],
], columns=["DepartmentID", "DepartmentName", "Location"])

# 2. CHART OF ACCOUNTS
accounts = [
    [1000, "Cash", "Asset", "Balance Sheet", "Debit"],
    [1100, "Accounts Receivable", "Asset", "Balance Sheet", "Debit"],
    [1300, "Equipment", "Asset", "Balance Sheet", "Debit"],
    [1400, "Loans Receivable", "Asset", "Balance Sheet", "Debit"],
    [1500, "Interest Receivable", "Asset", "Balance Sheet", "Debit"],
    [2000, "Accounts Payable", "Liability", "Balance Sheet", "Credit"],
    [2100, "Bank Borrowings", "Liability", "Balance Sheet", "Credit"],
    [2300, "Loan Loss Allowance", "Contra Asset", "Balance Sheet", "Credit"],
    [3000, "Share Capital", "Equity", "Balance Sheet", "Credit"],
    [3100, "Retained Earnings", "Equity", "Balance Sheet", "Credit"],
    [4000, "Interest Income", "Revenue", "P&L", "Credit"],
    [4100, "Fee and Service Income", "Revenue", "P&L", "Credit"],
    [4200, "Other Operating Income", "Revenue", "P&L", "Credit"],
    [5000, "Salaries Expense", "Expense", "P&L", "Debit"],
    [5100, "Rent Expense", "Expense", "P&L", "Debit"],
    [5200, "Marketing Expense", "Expense", "P&L", "Debit"],
    [5300, "Technology Expense", "Expense", "P&L", "Debit"],
    [5400, "Interest Expense", "Expense", "P&L", "Debit"],
    [5500, "Credit Loss Expense", "Expense", "P&L", "Debit"],
    [5600, "General and Administrative Expense", "Expense", "P&L", "Debit"],
]
df_accounts = pd.DataFrame(accounts, columns=[
    "AccountID", "AccountName", "AccountType", "FinancialStatement", "NormalBalance"
])

# 3. CUSTOMERS
customers = []
employment_types = ["Salaried", "Self-Employed", "Business Owner"]
for i in range(1, 2001):
    age = random.randint(21, 60)
    customers.append({
        "CustomerID": f"CUST{i:05d}",
        "CustomerName": fake.name(),
        "Age": age,
        "Gender": random.choice(["Male", "Female"]),
        "AnnualIncome": random.randint(240000, 2400000),
        "EmploymentType": random.choice(employment_types),
        "EmploymentYears": random.randint(0, age - 18),
        "City": fake.city(),
        "State": fake.state(),
        "CustomerSince": fake.date_between(start_date="-8y", end_date=pd.Timestamp("2025-12-31").date()),
    })
df_customers = pd.DataFrame(customers)

# 4. LOANS
loans = []
loan_types = ["Personal", "Home", "Auto", "Education", "Business"]
loan_terms = [12, 24, 36, 48, 60]
latest_issue_date = pd.Timestamp("2024-06-30")

for i in range(1, 3001):
    customer = random.choice(customers)
    issue_date = pd.Timestamp(fake.date_between(
        start_date=pd.Timestamp("2023-01-01").date(), end_date=latest_issue_date.date()
    ))
    loan_amount = random.choice([50000, 100000, 150000, 200000, 300000, 500000, 750000, 1000000])
    credit_score = random.randint(500, 850)
    dti = round(random.uniform(0.05, 0.70), 2)
    delinquencies = random.randint(0, 4)
    interest_rate = round(max(6, min(
        30, 12 + (700 - credit_score) * 0.04 + dti * 8 + delinquencies * 1.5
    )), 2)
    term = random.choice(loan_terms)

    # Synthetic label-generation rule. Do not use DefaultProbability as a model predictor.
    logit = -4 + (700 - credit_score) * 0.012 + dti * 4 + delinquencies * 0.55
    default_probability = float(1 / (1 + np.exp(-logit)))
    default_flag = int(random.random() < default_probability)
    maturity_date = issue_date + pd.DateOffset(months=term)
    status = "Defaulted" if default_flag else ("Active" if maturity_date > AS_OF_DATE else "Matured")

    loans.append({
        "LoanID": f"LN{i:05d}",
        "CustomerID": customer["CustomerID"],
        "LoanType": random.choice(loan_types),
        "IssueDate": issue_date,
        "LoanAmount": float(loan_amount),
        "InterestRate": interest_rate,
        "TermMonths": term,
        "MaturityDate": maturity_date,
        "CreditScore": credit_score,
        "DebtToIncomeRatio": dti,
        "PriorDelinquencies": delinquencies,
        "AnnualIncome": customer["AnnualIncome"],
        "DefaultProbability": round(default_probability, 4),
        "DefaultFlag": default_flag,
        "LoanStatus": status,
    })
df_loans = pd.DataFrame(loans)

# 5. LOAN PAYMENTS
payments = []
for loan in loans:
    principal = float(loan["LoanAmount"])
    monthly_rate = float(loan["InterestRate"]) / 1200
    term = int(loan["TermMonths"])
    issue_date = pd.Timestamp(loan["IssueDate"])
    factor = (1 + monthly_rate) ** term
    emi = principal * monthly_rate * factor / (factor - 1) if monthly_rate else principal / term

    months_to_cutoff = (AS_OF_DATE.year - issue_date.year) * 12 + AS_OF_DATE.month - issue_date.month
    installment_limit = max(0, min(term, 18, months_to_cutoff))
    default_month = random.randint(3, installment_limit) if loan["DefaultFlag"] and installment_limit >= 3 else None
    balance = principal

    for month in range(1, installment_limit + 1):
        payment_date = issue_date + pd.DateOffset(months=month)
        interest_due = balance * monthly_rate

        if default_month is not None and month >= default_month:
            payment_status, amount_paid = "Missed", 0.0
        else:
            payment_status = random.choices(["Paid", "Late"], weights=[90, 10])[0]
            amount_paid = emi if payment_status == "Paid" else emi * 0.75

        interest_paid = min(amount_paid, interest_due)
        principal_paid = min(balance, max(0.0, amount_paid - interest_paid))

        # Round the components first, then derive cash paid from those
        # rounded components so each payment reconciles exactly to the ledger.
        interest_paid = round(interest_paid, 2)
        principal_paid = round(principal_paid, 2)
        amount_paid = round(interest_paid + principal_paid, 2)
        balance = max(0.0, balance - principal_paid)

        payments.append({
            "PaymentID": f"PAY{len(payments)+1:07d}",
            "LoanID": loan["LoanID"],
            "PaymentDate": payment_date,
            "InstallmentNo": month,
            "ScheduledPayment": round(emi, 2),
            "AmountPaid": amount_paid,
            "PrincipalPaid": principal_paid,
            "InterestPaid": interest_paid,
            "OutstandingBalance": round(balance, 2),
            "PaymentStatus": payment_status,
        })

df_payments = pd.DataFrame(payments, columns=[
    "PaymentID", "LoanID", "PaymentDate", "InstallmentNo", "ScheduledPayment",
    "AmountPaid", "PrincipalPaid", "InterestPaid", "OutstandingBalance", "PaymentStatus"
])

# 6. GENERAL LEDGER
ledger = []
journal_counter = 0

def create_journal(date_value, description, postings, department_id):
    """Create one balanced journal from (AccountID, Debit, Credit) postings."""
    global journal_counter
    clean = []
    for account_id, debit, credit in postings:
        debit, credit = round(float(debit), 2), round(float(credit), 2)
        if debit < 0 or credit < 0:
            raise ValueError("Debit/Credit cannot be negative.")
        if debit > 0 or credit > 0:
            clean.append((int(account_id), debit, credit))
    total_debit = round(sum(x[1] for x in clean), 2)
    total_credit = round(sum(x[2] for x in clean), 2)
    if abs(total_debit - total_credit) > 0.01:
        raise ValueError(f"Unbalanced journal {description}: {total_debit} != {total_credit}")
    if not clean:
        return

    journal_counter += 1
    journal_id = f"JE{journal_counter:07d}"
    department_name = df_departments.loc[
        df_departments["DepartmentID"] == department_id, "DepartmentName"
    ].iloc[0]

    for account_id, debit, credit in clean:
        ledger.append({
            "GLLineID": f"GL{len(ledger)+1:08d}",
            "JournalEntryID": journal_id,
            "TransactionDate": pd.Timestamp(date_value),
            "Description": description,
            "AccountID": account_id,
            "Debit": debit,
            "Credit": credit,
            "DepartmentID": department_id,
            "DepartmentName": department_name,
        })

# Opening share capital and borrowing facility.
create_journal("2023-01-01", "Initial share capital contribution",
               [(1000, 50000000, 0), (3000, 0, 50000000)], 2)

loan_book_value = float(df_loans["LoanAmount"].sum())
borrowing_funding = loan_book_value + 25000000
create_journal("2023-01-02", "Initial bank borrowing facility",
               [(1000, borrowing_funding, 0), (2100, 0, borrowing_funding)], 2)

# Loan disbursements: Dr Loans Receivable, Cr Cash.
for loan in loans:
    create_journal(loan["IssueDate"], "Loan disbursement",
                   [(1400, loan["LoanAmount"], 0), (1000, 0, loan["LoanAmount"])], 2)

# Repayments: Dr Cash, Cr Loans Receivable (principal), Cr Interest Income.
for payment in payments:
    amount = float(payment["AmountPaid"])
    principal = float(payment["PrincipalPaid"])
    interest = float(payment["InterestPaid"])
    if amount > 0:
        create_journal(payment["PaymentDate"], "Loan repayment received",
                       [(1000, amount, 0), (1400, 0, principal), (4000, 0, interest)], 2)

# Provision once per defaulted loan at its first missed installment.
if not df_payments.empty:
    missed = df_payments[df_payments["PaymentStatus"] == "Missed"].copy()
    first_missed = missed.sort_values(["LoanID", "InstallmentNo"]).drop_duplicates("LoanID")
    for _, payment in first_missed.iterrows():
        provision = float(payment["OutstandingBalance"])
        if provision > 0:
            create_journal(payment["PaymentDate"], "Expected credit loss provision",
                           [(5500, provision, 0), (2300, 0, provision)], 2)

# Monthly lending-company operating transactions.
months = pd.period_range("2023-01", "2025-12", freq="M")
for month in months:
    transaction_date = month.to_timestamp() + pd.Timedelta(days=14)
    growth = 1 + (month.year - 2023) * 0.05
    fee_income = random.uniform(150000, 300000) * growth
    operating_costs = [
        (5000, random.uniform(260000, 340000) * growth, 2, "Monthly salaries"),
        (5100, random.uniform(65000, 90000) * growth, 3, "Monthly rent"),
        (5200, random.uniform(35000, 75000) * growth, 5, "Monthly marketing"),
        (5300, random.uniform(40000, 85000) * growth, 4, "Monthly technology"),
        (5400, random.uniform(80000, 140000) * growth, 2, "Monthly borrowing interest"),
        (5600, random.uniform(25000, 60000) * growth, 2, "Monthly general and administrative"),
    ]
    create_journal(transaction_date, "Monthly loan processing and service fees",
                   [(1000, fee_income, 0), (4100, 0, fee_income)], 1)
    for account_id, amount, dept_id, description in operating_costs:
        create_journal(transaction_date, description,
                       [(account_id, amount, 0), (1000, 0, amount)], dept_id)

df_ledger = pd.DataFrame(ledger)

# 7. BUDGET
budget_accounts = [
    (4000, 2, "Interest Income", 900000),
    (4100, 1, "Fee and Service Income", 220000),
    (5000, 2, "Salaries Expense", 300000),
    (5100, 3, "Rent Expense", 78000),
    (5200, 5, "Marketing Expense", 55000),
    (5300, 4, "Technology Expense", 62000),
    (5400, 2, "Interest Expense", 110000),
    (5500, 2, "Credit Loss Expense", 80000),
    (5600, 2, "General and Administrative Expense", 42000),
]
budgets = []
for month in months:
    growth = 1 + (month.year - 2023) * 0.05
    for account_id, dept_id, account_name, base_amount in budget_accounts:
        dept_name = df_departments.loc[
            df_departments["DepartmentID"] == dept_id, "DepartmentName"
        ].iloc[0]
        budgets.append({
            "BudgetID": f"BUD{len(budgets)+1:07d}",
            "BudgetMonth": month.to_timestamp(),
            "AccountID": account_id,
            "AccountName": account_name,
            "DepartmentID": dept_id,
            "DepartmentName": dept_name,
            "BudgetAmount": round(base_amount * growth * random.uniform(0.94, 1.06), 2),
            "BudgetVersion": "Approved",
        })
df_budget = pd.DataFrame(budgets)

# EXPORT ALL SEVEN CSV FILES
tables = {
    "Departments": df_departments,
    "ChartOfAccounts": df_accounts,
    "Customers": df_customers,
    "Loans": df_loans,
    "LoanPayments": df_payments,
    "GeneralLedger": df_ledger,
    "Budget": df_budget,
}
for name, dataframe in tables.items():
    dataframe.to_csv(os.path.join(OUTPUT_DIR, f"{name}.csv"), index=False)

# BUILT-IN VALIDATION
print("\n" + "=" * 60)
print("DATASET GENERATION COMPLETED")
print("Output folder:", OUTPUT_DIR)

print("\nROW COUNTS")
for name, dataframe in tables.items():
    print(f"{name}: {len(dataframe):,}")

print("\nMISSING VALUES")
for name, dataframe in tables.items():
    print(f"{name}: {int(dataframe.isna().sum().sum()):,}")

keys = {
    "Departments": (df_departments, "DepartmentID"),
    "ChartOfAccounts": (df_accounts, "AccountID"),
    "Customers": (df_customers, "CustomerID"),
    "Loans": (df_loans, "LoanID"),
    "LoanPayments": (df_payments, "PaymentID"),
    "GeneralLedger": (df_ledger, "GLLineID"),
    "Budget": (df_budget, "BudgetID"),
}
print("\nDUPLICATE PRIMARY KEYS")
for name, (dataframe, key) in keys.items():
    print(f"{name}: {int(dataframe[key].duplicated().sum()):,}")

fk_checks = {
    "Loans -> Customers": (~df_loans["CustomerID"].isin(df_customers["CustomerID"])).sum(),
    "LoanPayments -> Loans": (~df_payments["LoanID"].isin(df_loans["LoanID"])).sum(),
    "GeneralLedger -> Accounts": (~df_ledger["AccountID"].isin(df_accounts["AccountID"])).sum(),
    "GeneralLedger -> Departments": (~df_ledger["DepartmentID"].isin(df_departments["DepartmentID"])).sum(),
    "Budget -> Accounts": (~df_budget["AccountID"].isin(df_accounts["AccountID"])).sum(),
    "Budget -> Departments": (~df_budget["DepartmentID"].isin(df_departments["DepartmentID"])).sum(),
}
print("\nFOREIGN KEY CHECKS")
for name, count in fk_checks.items():
    print(f"{name}: {int(count):,} invalid references")

journal_totals = df_ledger.groupby("JournalEntryID")[["Debit", "Credit"]].sum()
unbalanced = ((journal_totals["Debit"] - journal_totals["Credit"]).abs() > 0.01).sum()
debits, credits = float(df_ledger["Debit"].sum()), float(df_ledger["Credit"].sum())

print("\nGENERAL LEDGER CHECK")
print("Journal entries:", len(journal_totals))
print("Unbalanced journal entries:", int(unbalanced))
print("Total debit:", round(debits, 2))
print("Total credit:", round(credits, 2))
print("Difference:", round(debits - credits, 2))

print("\nLOAN PAYMENT CHECKS")
print("Negative amounts:", int((df_payments["AmountPaid"] < 0).sum()))
print("Negative outstanding balances:", int((df_payments["OutstandingBalance"] < -0.01).sum()))
reconciliation_errors = (
    df_payments["PrincipalPaid"] + df_payments["InterestPaid"] - df_payments["AmountPaid"]
).abs() > 0.02
print("Payment amount reconciliation errors:", int(reconciliation_errors.sum()))
print("Payment dates after 2025-12-31:",
      int((pd.to_datetime(df_payments["PaymentDate"]) > AS_OF_DATE).sum()))

print("\nDATE COVERAGE")
print("Loan issue dates:", df_loans["IssueDate"].min(), "to", df_loans["IssueDate"].max())
if not df_payments.empty:
    print("Payment dates:", df_payments["PaymentDate"].min(), "to", df_payments["PaymentDate"].max())
print("Ledger dates:", df_ledger["TransactionDate"].min(), "to", df_ledger["TransactionDate"].max())
print("Budget months:", df_budget["BudgetMonth"].min(), "to", df_budget["BudgetMonth"].max())

print("\nFILES CREATED")
for filename in sorted(os.listdir(OUTPUT_DIR)):
    if filename.endswith(".csv"):
        print(filename)

print("\nMODELING NOTES")
print("- Exclude DefaultProbability from model predictors to avoid target leakage.")
print("- Defaults are provisioned to Loan Loss Allowance; this is not a direct write-off.")
print("- Dataset is synthetic demonstration data, not audited real-world financial data.")
print("- Validate financial statement balances before using them in reports.")
print("=" * 60)

