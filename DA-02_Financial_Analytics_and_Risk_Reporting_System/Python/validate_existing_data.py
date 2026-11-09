import os
import traceback
from pathlib import Path
import numpy as np
import pandas as pd
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# VALIDATE EXISTING FINANCIAL ANALYTICS CSV FILES
# Put this file beside the "output" folder and run it.
# It reads existing CSVs only; it does NOT modify them.
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TOLERANCE = 0.02

FILES = {
    "Departments": "Departments.csv",
    "ChartOfAccounts": "ChartOfAccounts.csv",
    "Customers": "Customers.csv",
    "Loans": "Loans.csv",
    "LoanPayments": "LoanPayments.csv",
    "GeneralLedger": "GeneralLedger.csv",
    "Budget": "Budget.csv",
}

REQUIRED_COLUMNS = {
    "Departments": ["DepartmentID", "DepartmentName", "Location"],
    "ChartOfAccounts": [
        "AccountID", "AccountName", "AccountType",
        "FinancialStatement", "NormalBalance"
    ],
    "Customers": [
        "CustomerID", "CustomerName", "Age", "AnnualIncome",
        "EmploymentType", "CustomerSince"
    ],
    "Loans": [
        "LoanID", "CustomerID", "IssueDate", "LoanAmount",
        "InterestRate", "TermMonths", "CreditScore",
        "DebtToIncomeRatio", "PriorDelinquencies",
        "DefaultFlag"
    ],
    "LoanPayments": [
        "PaymentID", "LoanID", "PaymentDate", "InstallmentNo",
        "ScheduledPayment", "AmountPaid", "PrincipalPaid",
        "InterestPaid", "OutstandingBalance", "PaymentStatus"
    ],
    "GeneralLedger": [
        "GLLineID", "JournalEntryID", "TransactionDate",
        "AccountID", "Debit", "Credit", "DepartmentID"
    ],
    "Budget": [
        "BudgetID", "BudgetMonth", "AccountID",
        "DepartmentID", "BudgetAmount"
    ],
}

PRIMARY_KEYS = {
    "Departments": "DepartmentID",
    "ChartOfAccounts": "AccountID",
    "Customers": "CustomerID",
    "Loans": "LoanID",
    "LoanPayments": "PaymentID",
    "GeneralLedger": "GLLineID",
    "Budget": "BudgetID",
}


def section(title):
    print("\n" + "=" * 65)
    print(title)
    print("=" * 65)


def report_check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))


# ------------------------------------------------------------
# 1. LOAD THE EXISTING CSV FILES
# ------------------------------------------------------------

section("1. FILE CHECK")

data = {}
missing_files = []

for table_name, filename in FILES.items():
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not os.path.isfile(filepath):
        missing_files.append(filename)
        report_check(f"{filename} exists", False, "File not found")
        continue

    try:
        data[table_name] = pd.read_csv(filepath)
        report_check(
            f"{filename} loaded",
            True,
            f"{len(data[table_name]):,} rows, {len(data[table_name].columns)} columns"
        )
    except Exception as error:
        report_check(f"{filename} loaded", False, str(error))

if missing_files or len(data) != len(FILES):
    print("\nCannot complete validation because one or more files are missing or unreadable.")
    print("Expected folder:", OUTPUT_DIR)
    raise SystemExit(1)


# ------------------------------------------------------------
# 2. REQUIRED COLUMN CHECK
# ------------------------------------------------------------

section("2. REQUIRED COLUMNS")

schema_ok = True

for table_name, required in REQUIRED_COLUMNS.items():
    actual = set(data[table_name].columns)
    missing_columns = sorted(set(required) - actual)
    passed = len(missing_columns) == 0
    schema_ok = schema_ok and passed
    report_check(
        f"{table_name} columns",
        passed,
        "All required columns exist" if passed else f"Missing: {missing_columns}"
    )


# ------------------------------------------------------------
# 3. ROW COUNTS, MISSING VALUES, DUPLICATE PRIMARY KEYS
# ------------------------------------------------------------

section("3. TABLE QUALITY")

for table_name, df in data.items():
    print(f"{table_name}: {len(df):,} rows")

print("\nMissing values:")
for table_name, df in data.items():
    missing_count = int(df.isna().sum().sum())
    report_check(
        f"{table_name} missing values",
        missing_count == 0,
        f"{missing_count:,} missing cells"
    )

print("\nDuplicate primary keys:")
for table_name, key in PRIMARY_KEYS.items():
    df = data[table_name]
    duplicate_count = int(df[key].duplicated().sum())
    null_key_count = int(df[key].isna().sum())
    report_check(
        f"{table_name}.{key}",
        duplicate_count == 0 and null_key_count == 0,
        f"{duplicate_count} duplicates; {null_key_count} null keys"
    )


# ------------------------------------------------------------
# 4. FOREIGN KEY RELATIONSHIPS
# ------------------------------------------------------------

section("4. FOREIGN KEY CHECKS")

departments = data["Departments"]
accounts = data["ChartOfAccounts"]
customers = data["Customers"]
loans = data["Loans"]
payments = data["LoanPayments"]
ledger = data["GeneralLedger"]
budget = data["Budget"]

foreign_key_checks = [
    (
        "Loans.CustomerID -> Customers.CustomerID",
        loans["CustomerID"].isin(customers["CustomerID"])
    ),
    (
        "LoanPayments.LoanID -> Loans.LoanID",
        payments["LoanID"].isin(loans["LoanID"])
    ),
    (
        "GeneralLedger.AccountID -> ChartOfAccounts.AccountID",
        ledger["AccountID"].isin(accounts["AccountID"])
    ),
    (
        "GeneralLedger.DepartmentID -> Departments.DepartmentID",
        ledger["DepartmentID"].isin(departments["DepartmentID"])
    ),
    (
        "Budget.AccountID -> ChartOfAccounts.AccountID",
        budget["AccountID"].isin(accounts["AccountID"])
    ),
    (
        "Budget.DepartmentID -> Departments.DepartmentID",
        budget["DepartmentID"].isin(departments["DepartmentID"])
    ),
]

for label, valid_mask in foreign_key_checks:
    invalid_count = int((~valid_mask).sum())
    report_check(label, invalid_count == 0, f"{invalid_count} invalid references")


# ------------------------------------------------------------
# 5. LOAN DATA CHECKS
# ------------------------------------------------------------

section("5. LOAN DATA CHECKS")

loans["IssueDate"] = pd.to_datetime(loans["IssueDate"], errors="coerce")
if "MaturityDate" in loans.columns:
    loans["MaturityDate"] = pd.to_datetime(loans["MaturityDate"], errors="coerce")

loan_numeric_checks = {
    "LoanAmount must be positive": loans["LoanAmount"] > 0,
    "InterestRate must be non-negative": loans["InterestRate"] >= 0,
    "TermMonths must be positive": loans["TermMonths"] > 0,
    "CreditScore must be between 300 and 900": loans["CreditScore"].between(300, 900),
    "DebtToIncomeRatio must be between 0 and 1": loans["DebtToIncomeRatio"].between(0, 1),
    "DefaultFlag must be 0 or 1": loans["DefaultFlag"].isin([0, 1]),
    "IssueDate must be valid": loans["IssueDate"].notna(),
}

for label, mask in loan_numeric_checks.items():
    failures = int((~mask).sum())
    report_check(label, failures == 0, f"{failures} invalid loan records")


# ------------------------------------------------------------
# 6. LOAN PAYMENT CHECKS
# ------------------------------------------------------------

section("6. LOAN PAYMENT CHECKS")

payments["PaymentDate"] = pd.to_datetime(payments["PaymentDate"], errors="coerce")

payment_checks = {
    "Payment amount cannot be negative": payments["AmountPaid"] >= 0,
    "Principal paid cannot be negative": payments["PrincipalPaid"] >= 0,
    "Interest paid cannot be negative": payments["InterestPaid"] >= 0,
    "Outstanding balance cannot be negative": payments["OutstandingBalance"] >= -TOLERANCE,
    "Payment date must be valid": payments["PaymentDate"].notna(),
    "Installment number must be positive": payments["InstallmentNo"] > 0,
    "Payment status must be Paid, Late or Missed": payments["PaymentStatus"].isin(
        ["Paid", "Late", "Missed"]
    ),
    "Missed payments must have zero amount paid": (
        (payments["PaymentStatus"] != "Missed") | (payments["AmountPaid"].abs() <= TOLERANCE)
    ),
}

for label, mask in payment_checks.items():
    failures = int((~mask).sum())
    report_check(label, failures == 0, f"{failures} invalid payment records")

reconciliation = (
    payments["PrincipalPaid"]
    + payments["InterestPaid"]
    - payments["AmountPaid"]
).abs() <= TOLERANCE

report_check(
    "PrincipalPaid + InterestPaid = AmountPaid",
    bool(reconciliation.all()),
    f"{int((~reconciliation).sum())} mismatches"
)

duplicate_installments = payments.duplicated(
    subset=["LoanID", "InstallmentNo"]
).sum()

report_check(
    "No duplicate installment number per loan",
    int(duplicate_installments) == 0,
    f"{int(duplicate_installments)} duplicate loan/installment pairs"
)

# Check payment chronology against loan issue dates.
loan_issue_dates = loans.set_index("LoanID")["IssueDate"]
payment_issue_dates = payments["LoanID"].map(loan_issue_dates)
date_order_valid = (
    payments["PaymentDate"].notna()
    & payment_issue_dates.notna()
    & (payments["PaymentDate"] > payment_issue_dates)
)

report_check(
    "Payment date occurs after loan issue date",
    bool(date_order_valid.all()),
    f"{int((~date_order_valid).sum())} invalid payment dates"
)


# ------------------------------------------------------------
# 7. GENERAL LEDGER CHECKS
# ------------------------------------------------------------

section("7. GENERAL LEDGER CHECKS")

ledger["TransactionDate"] = pd.to_datetime(
    ledger["TransactionDate"], errors="coerce"
)

debit_nonnegative = ledger["Debit"] >= 0
credit_nonnegative = ledger["Credit"] >= 0
not_both_sides = ~((ledger["Debit"] > TOLERANCE) & (ledger["Credit"] > TOLERANCE))
valid_gl_dates = ledger["TransactionDate"].notna()

report_check(
    "Debit values are non-negative",
    bool(debit_nonnegative.all()),
    f"{int((~debit_nonnegative).sum())} invalid rows"
)
report_check(
    "Credit values are non-negative",
    bool(credit_nonnegative.all()),
    f"{int((~credit_nonnegative).sum())} invalid rows"
)
report_check(
    "A ledger line is not both debit and credit",
    bool(not_both_sides.all()),
    f"{int((~not_both_sides).sum())} invalid rows"
)
report_check(
    "Transaction dates are valid",
    bool(valid_gl_dates.all()),
    f"{int((~valid_gl_dates).sum())} invalid rows"
)

journal_totals = ledger.groupby("JournalEntryID")[["Debit", "Credit"]].sum()
journal_difference = (journal_totals["Debit"] - journal_totals["Credit"]).abs()
unbalanced_count = int((journal_difference > TOLERANCE).sum())

report_check(
    "Every journal entry balances",
    unbalanced_count == 0,
    f"{unbalanced_count} unbalanced journal entries"
)

total_debit = float(ledger["Debit"].sum())
total_credit = float(ledger["Credit"].sum())

print(f"Total debit:  {total_debit:,.2f}")
print(f"Total credit: {total_credit:,.2f}")
print(f"Difference:   {total_debit - total_credit:,.2f}")


# ------------------------------------------------------------
# 8. BUDGET CHECKS
# ------------------------------------------------------------

section("8. BUDGET CHECKS")

budget["BudgetMonth"] = pd.to_datetime(budget["BudgetMonth"], errors="coerce")

report_check(
    "Budget amounts are non-negative",
    bool((budget["BudgetAmount"] >= 0).all()),
    f"{int((budget['BudgetAmount'] < 0).sum())} negative values"
)
report_check(
    "Budget months are valid",
    bool(budget["BudgetMonth"].notna().all()),
    f"{int(budget['BudgetMonth'].isna().sum())} invalid dates"
)

duplicate_budget_rows = budget.duplicated(
    subset=["BudgetMonth", "AccountID", "DepartmentID", "BudgetVersion"]
).sum()

report_check(
    "No duplicate monthly budget combination",
    int(duplicate_budget_rows) == 0,
    f"{int(duplicate_budget_rows)} duplicate combinations"
)


# ------------------------------------------------------------
# 9. ACCOUNTING SUMMARY (NOT A FULL AUDIT)
# ------------------------------------------------------------

section("9. ACCOUNT BALANCES")

account_balances = ledger.groupby("AccountID").agg(
    TotalDebit=("Debit", "sum"),
    TotalCredit=("Credit", "sum")
)
account_balances["NetDebitBalance"] = (
    account_balances["TotalDebit"] - account_balances["TotalCredit"]
)

account_summary = account_balances.merge(
    accounts[["AccountID", "AccountName", "AccountType", "NormalBalance"]],
    left_index=True,
    right_on="AccountID",
    how="left"
)

print(
    account_summary[
        ["AccountID", "AccountName", "AccountType",
         "TotalDebit", "TotalCredit", "NetDebitBalance"]
    ].to_string(index=False)
)

print(
    "\nNote: These are ledger movements/net debit balances, not by themselves "
    "a finalized Balance Sheet or P&L. Opening balances, retained earnings, "
    "and period-end adjustments must be assessed separately."
)


# ------------------------------------------------------------
# 10. FINAL SUMMARY
# ------------------------------------------------------------

section("10. FINAL VALIDATION SUMMARY")

all_foreign_keys_valid = all(
    int((~mask).sum()) == 0 for _, mask in foreign_key_checks
)
all_primary_keys_valid = all(
    int(data[table_name][key].duplicated().sum()) == 0
    and int(data[table_name][key].isna().sum()) == 0
    for table_name, key in PRIMARY_KEYS.items()
)

overall_checks = {
    "All seven CSV files loaded": len(data) == 7,
    "Required columns exist": schema_ok,
    "Primary keys are unique and non-null": all_primary_keys_valid,
    "Foreign keys are valid": all_foreign_keys_valid,
    "Journal entries balance": unbalanced_count == 0,
    "Payment reconciliation passes": bool(reconciliation.all()),
    "No negative payment balances": bool((payments["OutstandingBalance"] >= -TOLERANCE).all()),
}

for label, passed in overall_checks.items():
    report_check(label, passed)

if all(overall_checks.values()):
    print("\nRESULT: All included validation checks passed.")
else:
    print("\nRESULT: One or more checks failed. Review the FAIL rows above.")

print("\nThis script validates existing files only. It does not modify the CSV files.")
# ============================================================
# 11. ADVANCED ACCOUNTING AND BUSINESS VALIDATION
# ============================================================

print("\n" + "=" * 65)
print("11. ADVANCED ACCOUNTING VALIDATION")
print("=" * 65)

# Load account classifications
accounts = data["ChartOfAccounts"].copy()
ledger = data["GeneralLedger"].copy()
loans = data["Loans"].copy()
payments = data["LoanPayments"].copy()
budget = data["Budget"].copy()

# ------------------------------------------------------------
# A. TRIAL BALANCE
# ------------------------------------------------------------

trial = ledger.groupby("AccountID").agg(
    TotalDebit=("Debit", "sum"),
    TotalCredit=("Credit", "sum")
).reset_index()

trial = trial.merge(accounts, on="AccountID", how="left")

trial["NetDebit"] = trial["TotalDebit"] - trial["TotalCredit"]

trial["DebitBalance"] = trial["NetDebit"].clip(lower=0)
trial["CreditBalance"] = (-trial["NetDebit"]).clip(lower=0)

trial_debit = trial["DebitBalance"].sum()
trial_credit = trial["CreditBalance"].sum()

report_check(
    "Trial Balance",
    abs(trial_debit - trial_credit) <= TOLERANCE,
    f"Debit={trial_debit:.2f}, Credit={trial_credit:.2f}"
)

trial.to_csv(
    os.path.join(OUTPUT_DIR, "Trial_Balance.csv"),
    index=False
)

# ------------------------------------------------------------
# B. PROFIT AND LOSS
# ------------------------------------------------------------

trial["AccountType"] = trial["AccountType"].astype(str).str.lower()
trial["NormalBalance"] = trial["NormalBalance"].astype(str).str.lower()

trial["SignedBalance"] = (
    trial["TotalDebit"] - trial["TotalCredit"]
)

trial.loc[
    trial["NormalBalance"] == "credit",
    "SignedBalance"
] *= -1

revenue = trial.loc[
    trial["AccountType"] == "revenue",
    "SignedBalance"
].sum()

expenses = trial.loc[
    trial["AccountType"] == "expense",
    "SignedBalance"
].sum()

net_profit = revenue - expenses

print(f"Total Revenue: {revenue:.2f}")
print(f"Total Expenses: {expenses:.2f}")
print(f"Net Profit/Loss: {net_profit:.2f}")

# ------------------------------------------------------------
# C. BALANCE SHEET
# ------------------------------------------------------------

asset_types = ["asset", "contra asset"]

asset_rows = trial[
    trial["AccountType"].isin(asset_types)
]

liability_rows = trial[
    trial["AccountType"] == "liability"
]

equity_rows = trial[
    trial["AccountType"] == "equity"
]

# Contra assets reduce total assets.
normal_assets = trial.loc[
    trial["AccountType"] == "asset",
    "SignedBalance"
].sum()

contra_assets = trial.loc[
    trial["AccountType"] == "contra asset",
    "SignedBalance"
].sum()

assets = normal_assets - contra_assets
liabilities = liability_rows["SignedBalance"].sum()
equity = equity_rows["SignedBalance"].sum()

adjusted_equity = equity + net_profit

balance_difference = (
    assets - liabilities - adjusted_equity
)

print(f"Total Assets: {assets:.2f}")
print(f"Total Liabilities: {liabilities:.2f}")
print(f"Recorded Equity: {equity:.2f}")
print(f"Net Profit/Loss: {net_profit:.2f}")
print(f"Balance Sheet Difference: {balance_difference:.2f}")

report_check(
    "Balance Sheet Equation",
    abs(balance_difference) <= TOLERANCE,
    f"Difference={balance_difference:.2f}"
)

# ------------------------------------------------------------
# D. LOAN PORTFOLIO RECONCILIATION
# ------------------------------------------------------------

loan_principal = loans["LoanAmount"].sum()

principal_paid = payments.groupby(
    "LoanID"
)["PrincipalPaid"].sum()

loan_reconciliation = loans[
    ["LoanID", "LoanAmount"]
].copy()

loan_reconciliation["PrincipalPaid"] = (
    loan_reconciliation["LoanID"]
    .map(principal_paid)
    .fillna(0)
)

loan_reconciliation["ExpectedOutstanding"] = (
    loan_reconciliation["LoanAmount"]
    - loan_reconciliation["PrincipalPaid"]
).clip(lower=0)

latest_balance = (
    payments.sort_values("PaymentDate")
    .groupby("LoanID")["OutstandingBalance"]
    .last()
)

loan_reconciliation["ActualOutstanding"] = (
    loan_reconciliation["LoanID"]
    .map(latest_balance)
    .fillna(loan_reconciliation["LoanAmount"])
)

loan_reconciliation["Difference"] = (
    loan_reconciliation["ActualOutstanding"]
    - loan_reconciliation["ExpectedOutstanding"]
)

loan_errors = (
    loan_reconciliation["Difference"].abs() > 1
).sum()

report_check(
    "Loan Portfolio Reconciliation",
    loan_errors == 0,
    f"{loan_errors} mismatched loans"
)

loan_reconciliation.to_csv(
    os.path.join(OUTPUT_DIR, "Loan_Reconciliation.csv"),
    index=False
)

# ------------------------------------------------------------
# E. CREDIT RISK DISTRIBUTION
# ------------------------------------------------------------

default_rate = loans["DefaultFlag"].mean() * 100

print(f"Total Loans: {len(loans)}")
print(f"Defaulted Loans: {loans['DefaultFlag'].sum()}")
print(f"Default Rate: {default_rate:.2f}%")

print("\nDefault Distribution:")
print(loans["DefaultFlag"].value_counts())

report_check(
    "Credit Risk Target Contains Both Classes",
    loans["DefaultFlag"].nunique() == 2,
    "DefaultFlag must contain both 0 and 1"
)

# ------------------------------------------------------------
# F. TARGET LEAKAGE WARNING
# ------------------------------------------------------------

leakage_columns = [
    "DefaultProbability",
    "LoanStatus"
]

present_leakage = [
    col for col in leakage_columns
    if col in loans.columns
]

print("\nPotential ML leakage columns:", present_leakage)

# ------------------------------------------------------------
# G. BUDGET VS ACTUAL
# ------------------------------------------------------------

ledger["Month"] = pd.to_datetime(
    ledger["TransactionDate"]
).dt.to_period("M").astype(str)

budget["Month"] = pd.to_datetime(
    budget["BudgetMonth"]
).dt.to_period("M").astype(str)

actual = ledger.groupby(
    ["Month", "AccountID", "DepartmentID"]
).agg(
    ActualDebit=("Debit", "sum"),
    ActualCredit=("Credit", "sum")
).reset_index()

actual["ActualNetDebit"] = (
    actual["ActualDebit"] - actual["ActualCredit"]
)

budget_actual = budget.merge(
    actual,
    on=["Month", "AccountID", "DepartmentID"],
    how="outer"
)

budget_actual.to_csv(
    os.path.join(OUTPUT_DIR, "Budget_vs_Actual.csv"),
    index=False
)

print("\nBudget vs Actual report generated.")

# ------------------------------------------------------------
# H. FINAL ADVANCED SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 65)
print("ADVANCED VALIDATION COMPLETED")
print("=" * 65)

print("Trial Balance:", trial_debit, trial_credit)
print("Revenue:", revenue)
print("Expenses:", expenses)
print("Net Profit/Loss:", net_profit)
print("Balance Sheet Difference:", balance_difference)
print("Loan Reconciliation Errors:", loan_errors)

print("\nReports saved in:", OUTPUT_DIR)