import os
import sys
import numpy as np
import pandas as pd

# UTF-8 output for Windows terminals
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
AS_OF_DATE = pd.Timestamp("2025-12-31")
TOL = 0.02

FILES = {
    "Departments": "Departments.csv",
    "ChartOfAccounts": "ChartOfAccounts.csv",
    "Customers": "Customers.csv",
    "Loans": "Loans.csv",
    "LoanPayments": "LoanPayments.csv",
    "GeneralLedger": "GeneralLedger.csv",
    "Budget": "Budget.csv",
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
REQUIRED_COLUMNS = {
    "Departments": ["DepartmentID", "DepartmentName", "Location"],
    "ChartOfAccounts": ["AccountID", "AccountName", "AccountType",
                        "FinancialStatement", "NormalBalance"],
    "Customers": ["CustomerID", "CustomerName", "Age", "AnnualIncome",
                  "EmploymentType", "CustomerSince"],
    "Loans": ["LoanID", "CustomerID", "IssueDate", "LoanAmount",
              "InterestRate", "TermMonths", "CreditScore",
              "DebtToIncomeRatio", "PriorDelinquencies", "DefaultFlag"],
    "LoanPayments": ["PaymentID", "LoanID", "PaymentDate", "InstallmentNo",
                     "ScheduledPayment", "AmountPaid", "PrincipalPaid",
                     "InterestPaid", "OutstandingBalance", "PaymentStatus"],
    "GeneralLedger": ["GLLineID", "JournalEntryID", "TransactionDate",
                      "AccountID", "Debit", "Credit", "DepartmentID"],
    "Budget": ["BudgetID", "BudgetMonth", "AccountID",
               "DepartmentID", "BudgetAmount"],
}

results = []

def section(title):
    print("\n" + "=" * 76)
    print(title)
    print("=" * 76)

def check(label, status, detail=""):
    # status must be PASS, FAIL, or REVIEW
    results.append((label, status))
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")

def count_bad(mask):
    return int((~pd.Series(mask).fillna(False)).sum())

# ---------------------------------------------------------------------
# 1. LOAD AND SCHEMA
# ---------------------------------------------------------------------
section("1. FILES AND SCHEMA")
data = {}
missing = []
for table, filename in FILES.items():
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.isfile(path):
        missing.append(filename)
        check(f"{filename} exists and loads", "FAIL", "File not found")
        continue
    try:
        data[table] = pd.read_csv(path)
        check(f"{filename} exists and loads", "PASS",
              f"{len(data[table]):,} rows x {len(data[table].columns)} columns")
    except Exception as exc:
        check(f"{filename} exists and loads", "FAIL", str(exc))

if missing or len(data) != len(FILES):
    print("\nSTOP: all seven source CSVs must be present and readable.")
    raise SystemExit(1)

schema_ok = True
for table, required in REQUIRED_COLUMNS.items():
    absent = sorted(set(required) - set(data[table].columns))
    ok = not absent
    schema_ok &= ok
    check(f"{table} required columns", "PASS" if ok else "FAIL",
          "All required columns exist" if ok else f"Missing: {absent}")

# Work on copies. Source CSVs are never changed.
departments = data["Departments"].copy()
accounts = data["ChartOfAccounts"].copy()
customers = data["Customers"].copy()
loans = data["Loans"].copy()
payments = data["LoanPayments"].copy()
ledger = data["GeneralLedger"].copy()
budget = data["Budget"].copy()

# Parse date columns
date_columns = {
    "Customers": (customers, ["CustomerSince"]),
    "Loans": (loans, ["IssueDate", "MaturityDate"]),
    "LoanPayments": (payments, ["PaymentDate"]),
    "GeneralLedger": (ledger, ["TransactionDate"]),
    "Budget": (budget, ["BudgetMonth"]),
}
for _, (frame, cols) in date_columns.items():
    for col in cols:
        if col in frame.columns:
            frame[col] = pd.to_datetime(frame[col], errors="coerce")

# ---------------------------------------------------------------------
# 2. TABLE QUALITY AND RELATIONSHIPS
# ---------------------------------------------------------------------
section("2. TABLE QUALITY AND RELATIONSHIPS")
for table, frame in data.items():
    missing_cells = int(frame.isna().sum().sum())
    check(f"{table} missing cells", "PASS" if missing_cells == 0 else "FAIL",
          f"{missing_cells:,} missing cells")
    key = PRIMARY_KEYS[table]
    dup = int(frame[key].duplicated().sum())
    nulls = int(frame[key].isna().sum())
    check(f"{table}.{key} unique and non-null",
          "PASS" if dup == 0 and nulls == 0 else "FAIL",
          f"{dup} duplicates; {nulls} nulls")

fk_tests = [
    ("Loans.CustomerID -> Customers", loans["CustomerID"].isin(customers["CustomerID"])),
    ("LoanPayments.LoanID -> Loans", payments["LoanID"].isin(loans["LoanID"])),
    ("GeneralLedger.AccountID -> ChartOfAccounts", ledger["AccountID"].isin(accounts["AccountID"])),
    ("GeneralLedger.DepartmentID -> Departments", ledger["DepartmentID"].isin(departments["DepartmentID"])),
    ("Budget.AccountID -> ChartOfAccounts", budget["AccountID"].isin(accounts["AccountID"])),
    ("Budget.DepartmentID -> Departments", budget["DepartmentID"].isin(departments["DepartmentID"])),
]
for label, mask in fk_tests:
    bad = count_bad(mask)
    check(label, "PASS" if bad == 0 else "FAIL", f"{bad} invalid references")

# ---------------------------------------------------------------------
# 3. CUSTOMER, LOAN AND PAYMENT QUALITY
# ---------------------------------------------------------------------
section("3. CUSTOMER, LOAN AND PAYMENT QUALITY")
customer_tests = {
    "Customer age between 18 and 100": customers["Age"].between(18, 100),
    "Annual income positive": customers["AnnualIncome"] > 0,
    "Customer-since dates valid": customers["CustomerSince"].notna(),
    "Customer-since not after as-of date": customers["CustomerSince"] <= AS_OF_DATE,
}
for label, mask in customer_tests.items():
    bad = count_bad(mask)
    check(label, "PASS" if bad == 0 else "FAIL", f"{bad} invalid records")

loan_tests = {
    "Loan amount positive": loans["LoanAmount"] > 0,
    "Interest rate non-negative": loans["InterestRate"] >= 0,
    "Loan term positive": loans["TermMonths"] > 0,
    "Credit score between 300 and 900": loans["CreditScore"].between(300, 900),
    "DTI between 0 and 1": loans["DebtToIncomeRatio"].between(0, 1),
    "Prior delinquencies non-negative": loans["PriorDelinquencies"] >= 0,
    "DefaultFlag is binary": loans["DefaultFlag"].isin([0, 1]),
    "Loan issue dates valid": loans["IssueDate"].notna(),
    "Loan issue dates not after as-of date":
        loans["IssueDate"].notna() & (loans["IssueDate"] <= AS_OF_DATE),
}
if "MaturityDate" in loans.columns:
    loan_tests["MaturityDate is not before IssueDate"] = (
        loans["MaturityDate"].notna() &
        (loans["MaturityDate"] >= loans["IssueDate"])
    )
for label, mask in loan_tests.items():
    bad = count_bad(mask)
    check(label, "PASS" if bad == 0 else "FAIL", f"{bad} invalid loans")

payment_tests = {
    "Payment dates valid": payments["PaymentDate"].notna(),
    "Payment amounts non-negative": payments["AmountPaid"] >= 0,
    "Principal paid non-negative": payments["PrincipalPaid"] >= 0,
    "Interest paid non-negative": payments["InterestPaid"] >= 0,
    "Outstanding balance non-negative": payments["OutstandingBalance"] >= -TOL,
    "Scheduled payment non-negative": payments["ScheduledPayment"] >= 0,
    "Installment numbers positive": payments["InstallmentNo"] > 0,
    "Payment status in allowed set": payments["PaymentStatus"].isin(["Paid", "Late", "Missed"]),
    "Missed payment has zero paid amount":
        (payments["PaymentStatus"] != "Missed") | (payments["AmountPaid"].abs() <= TOL),
    "Payment dates not after as-of date":
        payments["PaymentDate"].notna() & (payments["PaymentDate"] <= AS_OF_DATE),
}
for label, mask in payment_tests.items():
    bad = count_bad(mask)
    check(label, "PASS" if bad == 0 else "FAIL", f"{bad} invalid payment rows")

payment_split = (
    payments["PrincipalPaid"] + payments["InterestPaid"] - payments["AmountPaid"]
).abs() <= TOL
bad = count_bad(payment_split)
check("PrincipalPaid + InterestPaid = AmountPaid",
      "PASS" if bad == 0 else "FAIL", f"{bad} mismatches")

dups = int(payments.duplicated(["LoanID", "InstallmentNo"]).sum())
check("No duplicate installment per loan", "PASS" if dups == 0 else "FAIL",
      f"{dups} duplicate pairs")

issue_map = loans.set_index("LoanID")["IssueDate"]
mapped_issue = payments["LoanID"].map(issue_map)
chronology = payments["PaymentDate"].notna() & mapped_issue.notna() & (
    payments["PaymentDate"] > mapped_issue
)
bad = count_bad(chronology)
check("Every payment occurs after its loan issue date",
      "PASS" if bad == 0 else "FAIL", f"{bad} chronology errors")

# ---------------------------------------------------------------------
# 4. DEFAULT LABEL CONSISTENCY AND ML LEAKAGE
# ---------------------------------------------------------------------
section("4. DEFAULT LABEL CONSISTENCY AND ML LEAKAGE")
missed_by_loan = payments.assign(
    IsMissed=payments["PaymentStatus"].eq("Missed")
).groupby("LoanID")["IsMissed"].any()

loan_check = loans[["LoanID", "DefaultFlag"]].copy()
loan_check["HasMissedPayment"] = loan_check["LoanID"].map(missed_by_loan).fillna(False)
loan_check["DefaultFlag"] = loan_check["DefaultFlag"].astype(int)

false_default = loan_check[(loan_check["DefaultFlag"] == 1) &
                           (~loan_check["HasMissedPayment"])]
missed_nondefault = loan_check[(loan_check["DefaultFlag"] == 0) &
                               loan_check["HasMissedPayment"]]
label_mismatch_count = len(false_default) + len(missed_nondefault)
check("DefaultFlag agrees with missed-payment history",
      "PASS" if label_mismatch_count == 0 else "FAIL",
      f"{len(false_default)} flagged defaults without missed payments; "
      f"{len(missed_nondefault)} non-default loans with missed payments")

print("\nDefaultFlag x HasMissedPayment:")
print(pd.crosstab(loan_check["DefaultFlag"], loan_check["HasMissedPayment"]).to_string())

if "LoanStatus" in loans.columns:
    status_default = loans["LoanStatus"].astype(str).eq("Defaulted")
    flag_default = loans["DefaultFlag"].astype(int).eq(1)
    status_mismatch = int((status_default != flag_default).sum())
    check("LoanStatus='Defaulted' agrees with DefaultFlag",
          "PASS" if status_mismatch == 0 else "FAIL",
          f"{status_mismatch} mismatches")
else:
    check("LoanStatus consistency", "REVIEW", "LoanStatus column not present")

leakage = [c for c in ["DefaultProbability", "LoanStatus"] if c in loans.columns]
check("ML leakage columns identified", "REVIEW" if leakage else "PASS",
      f"Exclude from predictors: {leakage}" if leakage else "No known leakage columns found")
print("Model target: DefaultFlag. Do not use DefaultProbability or LoanStatus as predictors.")

# ---------------------------------------------------------------------
# 5. GENERAL LEDGER, TRIAL BALANCE AND ACCOUNTING RECONCILIATIONS
# ---------------------------------------------------------------------
section("5. GENERAL LEDGER AND ACCOUNTING")
gl_tests = {
    "Debit values non-negative": ledger["Debit"] >= 0,
    "Credit values non-negative": ledger["Credit"] >= 0,
    "A GL line is not both debit and credit":
        ~((ledger["Debit"] > TOL) & (ledger["Credit"] > TOL)),
    "GL transaction dates valid": ledger["TransactionDate"].notna(),
    "GL transaction dates not after as-of date":
        ledger["TransactionDate"].notna() & (ledger["TransactionDate"] <= AS_OF_DATE),
}
for label, mask in gl_tests.items():
    bad = count_bad(mask)
    check(label, "PASS" if bad == 0 else "FAIL", f"{bad} invalid rows")

journal = ledger.groupby("JournalEntryID")[["Debit", "Credit"]].sum()
unbalanced = int(((journal["Debit"] - journal["Credit"]).abs() > TOL).sum())
check("Every journal entry balances", "PASS" if unbalanced == 0 else "FAIL",
      f"{unbalanced} unbalanced journal entries")

total_debit = float(ledger["Debit"].sum())
total_credit = float(ledger["Credit"].sum())
check("Total GL debits equal total GL credits",
      "PASS" if abs(total_debit - total_credit) <= TOL else "FAIL",
      f"Debit={total_debit:,.2f}; Credit={total_credit:,.2f}; "
      f"Difference={total_debit-total_credit:,.2f}")

# Trial balance by account
trial = ledger.groupby("AccountID").agg(
    TotalDebit=("Debit", "sum"), TotalCredit=("Credit", "sum")
).reset_index().merge(accounts, on="AccountID", how="left")
trial["NetDebit"] = trial["TotalDebit"] - trial["TotalCredit"]
trial["DebitBalance"] = trial["NetDebit"].clip(lower=0)
trial["CreditBalance"] = (-trial["NetDebit"]).clip(lower=0)
tb_debit = float(trial["DebitBalance"].sum())
tb_credit = float(trial["CreditBalance"].sum())
check("Trial balance debit balances equal credit balances",
      "PASS" if abs(tb_debit - tb_credit) <= TOL else "FAIL",
      f"Debit={tb_debit:,.2f}; Credit={tb_credit:,.2f}")

# Independent GL Loans Receivable reconciliation
account_name_to_id = accounts.set_index("AccountName")["AccountID"].to_dict()
loans_receivable_id = account_name_to_id.get("Loans Receivable")
if loans_receivable_id is not None:
    gl_loan_net = float(
        ledger.loc[ledger["AccountID"] == loans_receivable_id, "Debit"].sum()
        - ledger.loc[ledger["AccountID"] == loans_receivable_id, "Credit"].sum()
    )
    total_principal_paid = float(payments["PrincipalPaid"].sum())
    expected_gl_loan = float(loans["LoanAmount"].sum() - total_principal_paid)
    gl_loan_diff = gl_loan_net - expected_gl_loan
    check("GL Loans Receivable agrees with loan/payment records",
          "PASS" if abs(gl_loan_diff) <= 1.00 else "FAIL",
          f"GL={gl_loan_net:,.2f}; Expected={expected_gl_loan:,.2f}; "
          f"Difference={gl_loan_diff:,.2f}")
else:
    check("GL Loans Receivable reconciliation", "FAIL",
          "Chart of Accounts has no 'Loans Receivable' account")

# Provision check: first missed installment outstanding balance
if "Loan Loss Allowance" in account_name_to_id and "Credit Loss Expense" in account_name_to_id:
    first_missed = (
        payments[payments["PaymentStatus"].eq("Missed")]
        .sort_values(["LoanID", "InstallmentNo"])
        .drop_duplicates("LoanID")
    )
    expected_provision = float(first_missed["OutstandingBalance"].sum())
    allowance_id = account_name_to_id["Loan Loss Allowance"]
    expense_id = account_name_to_id["Credit Loss Expense"]
    allowance_credit = float(ledger.loc[ledger["AccountID"] == allowance_id, "Credit"].sum()
                             - ledger.loc[ledger["AccountID"] == allowance_id, "Debit"].sum())
    credit_loss_debit = float(ledger.loc[ledger["AccountID"] == expense_id, "Debit"].sum()
                              - ledger.loc[ledger["AccountID"] == expense_id, "Credit"].sum())
    provision_ok = (abs(allowance_credit - expected_provision) <= 1.00 and
                    abs(credit_loss_debit - expected_provision) <= 1.00)
    check("Credit-loss provision agrees with first missed balances",
          "PASS" if provision_ok else "FAIL",
          f"Expected={expected_provision:,.2f}; Allowance={allowance_credit:,.2f}; "
          f"Expense={credit_loss_debit:,.2f}")
else:
    check("Credit-loss provision reconciliation", "REVIEW",
          "Required allowance/expense accounts not found")

# P&L and Balance Sheet sign convention
trial["AccountTypeNorm"] = trial["AccountType"].astype(str).str.strip().str.lower()
trial["NormalBalanceNorm"] = trial["NormalBalance"].astype(str).str.strip().str.lower()
trial["SignedBalance"] = trial["TotalDebit"] - trial["TotalCredit"]
trial.loc[trial["NormalBalanceNorm"].eq("credit"), "SignedBalance"] *= -1

revenue = float(trial.loc[trial["AccountTypeNorm"].eq("revenue"), "SignedBalance"].sum())
expenses = float(trial.loc[trial["AccountTypeNorm"].eq("expense"), "SignedBalance"].sum())
net_profit = revenue - expenses
normal_assets = float(trial.loc[trial["AccountTypeNorm"].eq("asset"), "SignedBalance"].sum())
contra_assets = float(trial.loc[trial["AccountTypeNorm"].eq("contra asset"), "SignedBalance"].sum())
liabilities = float(trial.loc[trial["AccountTypeNorm"].eq("liability"), "SignedBalance"].sum())
equity_recorded = float(trial.loc[trial["AccountTypeNorm"].eq("equity"), "SignedBalance"].sum())
assets_net = normal_assets - contra_assets
equity_including_current_result = equity_recorded + net_profit
bs_diff = assets_net - liabilities - equity_including_current_result

print(f"\nP&L: Revenue={revenue:,.2f}; Expenses={expenses:,.2f}; "
      f"Net profit/(loss)={net_profit:,.2f}")
print(f"Balance sheet arithmetic: Assets={assets_net:,.2f}; "
      f"Liabilities={liabilities:,.2f}; Equity incl. current result="
      f"{equity_including_current_result:,.2f}; Difference={bs_diff:,.6f}")
check("Balance sheet arithmetic after including current-period result",
      "PASS" if abs(bs_diff) <= 1.00 else "FAIL",
      f"Difference={bs_diff:,.6f}")

# This dataset has no period-end closing entry for current P&L into retained earnings.
retained_id = account_name_to_id.get("Retained Earnings")
retained_used = False
if retained_id is not None:
    retained_used = bool((ledger["AccountID"] == retained_id).any())
check("Retained earnings / period-end closing entry",
      "PASS" if retained_used else "REVIEW",
      "Retained Earnings account has ledger activity" if retained_used else
      "No closing entry found; current P&L is added to equity analytically, not posted")

# ---------------------------------------------------------------------
# 6. LOAN PORTFOLIO RECONCILIATION
# ---------------------------------------------------------------------
section("6. LOAN PORTFOLIO RECONCILIATION")
principal_by_loan = payments.groupby("LoanID")["PrincipalPaid"].sum()
loan_rec = loans[["LoanID", "LoanAmount"]].copy()
loan_rec["PrincipalPaid"] = loan_rec["LoanID"].map(principal_by_loan).fillna(0)
loan_rec["ExpectedOutstanding"] = (
    loan_rec["LoanAmount"] - loan_rec["PrincipalPaid"]
).clip(lower=0)

latest_bal = (
    payments.sort_values(["PaymentDate", "InstallmentNo"])
    .groupby("LoanID")["OutstandingBalance"].last()
)
loan_rec["LatestScheduleBalance"] = loan_rec["LoanID"].map(latest_bal).fillna(loan_rec["LoanAmount"])
loan_rec["Difference"] = loan_rec["LatestScheduleBalance"] - loan_rec["ExpectedOutstanding"]
loan_rec_errors = int((loan_rec["Difference"].abs() > 1.00).sum())
check("Per-loan schedule balance equals principal less principal paid",
      "PASS" if loan_rec_errors == 0 else "FAIL",
      f"{loan_rec_errors} mismatched loans")

# ---------------------------------------------------------------------
# 7. BUDGET, DATES AND PERIOD COVERAGE
# ---------------------------------------------------------------------
section("7. BUDGET VS ACTUAL AND DATE COVERAGE")
if "BudgetVersion" in budget.columns:
    budget_dups = int(budget.duplicated(
        ["BudgetMonth", "AccountID", "DepartmentID", "BudgetVersion"]
    ).sum())
else:
    budget_dups = int(budget.duplicated(
        ["BudgetMonth", "AccountID", "DepartmentID"]
    ).sum())
check("No duplicate budget month/account/department/version",
      "PASS" if budget_dups == 0 else "FAIL", f"{budget_dups} duplicates")

budget_tests = {
    "Budget amounts non-negative": budget["BudgetAmount"] >= 0,
    "Budget months valid": budget["BudgetMonth"].notna(),
    "Budget months are first day of month":
        budget["BudgetMonth"].notna() & budget["BudgetMonth"].dt.day.eq(1),
}
for label, mask in budget_tests.items():
    bad = count_bad(mask)
    check(label, "PASS" if bad == 0 else "FAIL", f"{bad} invalid rows")

expected_months = pd.period_range("2023-01", "2025-12", freq="M")
actual_months = pd.PeriodIndex(budget["BudgetMonth"].dropna(), freq="M").unique().sort_values()
missing_months = expected_months.difference(actual_months)
extra_months = actual_months.difference(expected_months)
check("Budget covers every month from Jan-2023 through Dec-2025",
      "PASS" if len(missing_months) == 0 and len(extra_months) == 0 else "FAIL",
      f"{len(actual_months)} distinct months; missing={list(missing_months)}; "
      f"outside range={list(extra_months)}")

# Build a meaningful budget-vs-actual report using normal-balance-positive actuals.
ledger_join = ledger.merge(
    accounts[["AccountID", "AccountType", "NormalBalance"]],
    on="AccountID", how="left"
)
ledger_join["Month"] = ledger_join["TransactionDate"].dt.to_period("M").astype(str)
ledger_join["ActualNet"] = ledger_join["Debit"] - ledger_join["Credit"]
credit_normal = ledger_join["NormalBalance"].astype(str).str.lower().eq("credit")
ledger_join.loc[credit_normal, "ActualNet"] *= -1
actual = ledger_join.groupby(
    ["Month", "AccountID", "DepartmentID"], as_index=False
)["ActualNet"].sum()

budget_copy = budget.copy()
budget_copy["Month"] = budget_copy["BudgetMonth"].dt.to_period("M").astype(str)
budget_keys = ["Month", "AccountID", "DepartmentID"]
bva = budget_copy.merge(actual, on=budget_keys, how="outer")
bva["BudgetAmount"] = bva["BudgetAmount"].fillna(0)
bva["ActualNet"] = bva["ActualNet"].fillna(0)
bva["Variance"] = bva["ActualNet"] - bva["BudgetAmount"]
bva.to_csv(os.path.join(OUTPUT_DIR, "Budget_vs_Actual_Validated.csv"), index=False)
print(f"Budget-vs-actual rows exported: {len(bva):,}")
check("Budget vs Actual report generated", "PASS",
      "Uses credit-normal-positive actuals for revenue and debit-normal-positive for expenses")

# ---------------------------------------------------------------------
# 8. OUTLIERS, ACCOUNT USAGE AND DOCUMENTED LIMITATIONS
# ---------------------------------------------------------------------
section("8. OUTLIERS, ACCOUNT USAGE AND MODEL READINESS")
print("\nKey numeric ranges:")
for col in ["LoanAmount", "InterestRate", "CreditScore", "DebtToIncomeRatio",
            "PriorDelinquencies"]:
    if col in loans.columns:
        print(f"{col}: min={loans[col].min()}, median={loans[col].median()}, "
              f"max={loans[col].max()}")

# Plausibility checks based on the generator's explicit bounds.
plausibility = {
    "Loan amounts within generated range ₹50,000–₹1,000,000":
        loans["LoanAmount"].between(50000, 1000000),
    "Interest rates within generated range 6%–30%":
        loans["InterestRate"].between(6, 30),
    "Credit scores within generated range 500–850":
        loans["CreditScore"].between(500, 850),
    "DTI within generated range 0.05–0.70":
        loans["DebtToIncomeRatio"].between(0.05, 0.70),
    "Customer ages within generated range 21–60":
        customers["Age"].between(21, 60),
    "Annual incomes within generated range ₹240,000–₹2,400,000":
        customers["AnnualIncome"].between(240000, 2400000),
}
for label, mask in plausibility.items():
    bad = count_bad(mask)
    check(label, "PASS" if bad == 0 else "REVIEW", f"{bad} outside generated range")

used_accounts = set(ledger["AccountID"].dropna().unique())
unused = accounts.loc[~accounts["AccountID"].isin(used_accounts),
                      ["AccountID", "AccountName", "AccountType"]]
print("\nUnused chart-of-accounts rows:")
print(unused.to_string(index=False) if len(unused) else "None")
check("Unused chart-of-accounts entries reviewed",
      "REVIEW" if len(unused) else "PASS",
      f"{len(unused)} accounts have no GL activity; confirm intentional")

default_rate = float(loans["DefaultFlag"].mean() * 100)
print(f"\nLoans: {len(loans):,}; defaults: {int(loans['DefaultFlag'].sum()):,}; "
      f"default rate: {default_rate:.2f}%")
print("Payment status counts:")
print(payments["PaymentStatus"].value_counts(dropna=False).to_string())

# Important methodological limitations identified from generator source.
check("Accounting methodology documentation",
      "REVIEW",
      "Synthetic data; interest income recorded on cash receipts; full outstanding "
      "balance provisioned at first missed installment; no write-off/recovery model; "
      "borrowing interest is expensed monthly without a detailed accrual schedule")

# ---------------------------------------------------------------------
# 9. EXPORT AUDIT SUPPORT AND FINAL SUMMARY
# ---------------------------------------------------------------------
section("9. EXPORTS AND FINAL RESULT")
trial.to_csv(os.path.join(OUTPUT_DIR, "Trial_Balance_Validated.csv"), index=False)
loan_rec.to_csv(os.path.join(OUTPUT_DIR, "Loan_Reconciliation_Validated.csv"), index=False)

summary = pd.DataFrame(results, columns=["Check", "Status"])
summary.to_csv(os.path.join(OUTPUT_DIR, "Validation_Summary.csv"), index=False)

pass_count = int((summary["Status"] == "PASS").sum())
fail_count = int((summary["Status"] == "FAIL").sum())
review_count = int((summary["Status"] == "REVIEW").sum())

print(f"PASS: {pass_count}")
print(f"FAIL: {fail_count}")
print(f"REVIEW: {review_count}")
print("\nChecks requiring attention:")
attention = summary[summary["Status"].isin(["FAIL", "REVIEW"])]
print(attention.to_string(index=False) if len(attention) else "None")

if fail_count:
    print("\nFINAL RESULT: NOT READY — fix FAIL items and rerun.")
elif review_count:
    print("\nFINAL RESULT: TECHNICAL CHECKS PASSED WITH REVIEW ITEMS — "
          "resolve/document REVIEW items before freezing the dataset.")
else:
    print("\nFINAL RESULT: ALL INCLUDED CHECKS PASSED — dataset can be frozen.")

print("\nSource CSV files were read only and were not modified.")
print("Validation reports saved in:", OUTPUT_DIR)
