-- ============================================
-- 1. DEPARTMENTS
-- ============================================

CREATE TABLE departments (
    "DepartmentID" INTEGER PRIMARY KEY,
    "DepartmentName" VARCHAR(100) NOT NULL,
    "Location" VARCHAR(100) NOT NULL
);


-- ============================================
-- 2. CHART OF ACCOUNTS
-- ============================================

CREATE TABLE chart_of_accounts (
    "AccountID" INTEGER PRIMARY KEY,
    "AccountName" VARCHAR(150) NOT NULL,
    "AccountType" VARCHAR(50) NOT NULL,
    "FinancialStatement" VARCHAR(50) NOT NULL,
    "NormalBalance" VARCHAR(10) NOT NULL
);


-- ============================================
-- 3. CUSTOMERS
-- ============================================

CREATE TABLE customers (
    "CustomerID" VARCHAR(15) PRIMARY KEY,
    "CustomerName" VARCHAR(150) NOT NULL,
    "Age" INTEGER NOT NULL,
    "Gender" VARCHAR(20),
    "AnnualIncome" NUMERIC(15,2) NOT NULL,
    "EmploymentType" VARCHAR(50),
    "EmploymentYears" INTEGER,
    "City" VARCHAR(100),
    "State" VARCHAR(100),
    "CustomerSince" DATE
);


-- ============================================
-- 4. LOANS
-- ============================================

CREATE TABLE loans (
    "LoanID" VARCHAR(15) PRIMARY KEY,
    "CustomerID" VARCHAR(15) NOT NULL,
    "LoanType" VARCHAR(50),
    "IssueDate" DATE NOT NULL,
    "LoanAmount" NUMERIC(15,2) NOT NULL,
    "InterestRate" NUMERIC(6,2),
    "TermMonths" INTEGER,
    "MaturityDate" DATE,
    "CreditScore" INTEGER,
    "DebtToIncomeRatio" NUMERIC(5,2),
    "PriorDelinquencies" INTEGER,
    "AnnualIncome" NUMERIC(15,2),
    "DefaultProbability" NUMERIC(6,4),
    "DefaultFlag" SMALLINT,
    "LoanStatus" VARCHAR(30),

    CONSTRAINT fk_loans_customer
        FOREIGN KEY ("CustomerID")
        REFERENCES customers ("CustomerID")
);


-- ============================================
-- 5. LOAN PAYMENTS
-- ============================================

CREATE TABLE loan_payments (
    "PaymentID" VARCHAR(15) PRIMARY KEY,
    "LoanID" VARCHAR(15) NOT NULL,
    "PaymentDate" DATE NOT NULL,
    "InstallmentNo" INTEGER,
    "ScheduledPayment" NUMERIC(15,2),
    "AmountPaid" NUMERIC(15,2),
    "PrincipalPaid" NUMERIC(15,2),
    "InterestPaid" NUMERIC(15,2),
    "OutstandingBalance" NUMERIC(15,2),
    "PaymentStatus" VARCHAR(30),

    CONSTRAINT fk_payment_loan
        FOREIGN KEY ("LoanID")
        REFERENCES loans ("LoanID")
);


-- ============================================
-- 6. GENERAL LEDGER
-- ============================================

CREATE TABLE general_ledger (
    "GLLineID" VARCHAR(15) PRIMARY KEY,
    "JournalEntryID" VARCHAR(15) NOT NULL,
    "TransactionDate" DATE NOT NULL,
    "Description" VARCHAR(200),
    "AccountID" INTEGER NOT NULL,
    "Debit" NUMERIC(15,2) NOT NULL DEFAULT 0,
    "Credit" NUMERIC(15,2) NOT NULL DEFAULT 0,
    "DepartmentID" INTEGER NOT NULL,
    "DepartmentName" VARCHAR(100),

    CONSTRAINT fk_gl_account
        FOREIGN KEY ("AccountID")
        REFERENCES chart_of_accounts ("AccountID"),

    CONSTRAINT fk_gl_department
        FOREIGN KEY ("DepartmentID")
        REFERENCES departments ("DepartmentID")
);


-- ============================================
-- 7. BUDGET
-- ============================================

CREATE TABLE budget (
    "BudgetID" VARCHAR(15) PRIMARY KEY,
    "BudgetMonth" DATE NOT NULL,
    "AccountID" INTEGER NOT NULL,
    "AccountName" VARCHAR(150),
    "DepartmentID" INTEGER NOT NULL,
    "DepartmentName" VARCHAR(100),
    "BudgetAmount" NUMERIC(15,2) NOT NULL,
    "BudgetVersion" VARCHAR(30),

    CONSTRAINT fk_budget_account
        FOREIGN KEY ("AccountID")
        REFERENCES chart_of_accounts ("AccountID"),

    CONSTRAINT fk_budget_department
        FOREIGN KEY ("DepartmentID")
        REFERENCES departments ("DepartmentID")
);
--Data Validation steps--
SELECT 'Departments' AS table_name, COUNT(*) FROM departments
UNION ALL
SELECT 'ChartOfAccounts', COUNT(*) FROM chart_of_accounts
UNION ALL
SELECT 'Customers', COUNT(*) FROM customers
UNION ALL
SELECT 'Loans', COUNT(*) FROM loans
UNION ALL
SELECT 'LoanPayments', COUNT(*) FROM loan_payments
UNION ALL
SELECT 'GeneralLedger', COUNT(*) FROM general_ledger
UNION ALL
SELECT 'Budget', COUNT(*) FROM budget;

SELECT l."LoanID", l."CustomerID"
FROM loans l
LEFT JOIN customers c
    ON l."CustomerID" = c."CustomerID"
WHERE c."CustomerID" IS NULL;

--Loan Portfolio Analysis--
--Overall loan KPIs--
SELECT
    COUNT(*) AS total_loans,
    SUM("LoanAmount") AS total_loan_amount,
    AVG("LoanAmount") AS average_loan_amount,
    AVG("InterestRate") AS average_interest_rate
FROM loans;
SELECT
    "LoanType",
    COUNT(*) AS total_loans,
    SUM("LoanAmount") AS total_loan_amount,
    AVG("LoanAmount") AS average_loan_amount
FROM loans
GROUP BY "LoanType"
ORDER BY total_loan_amount DESC;
--Monthly loan issuance trend--
SELECT
    DATE_TRUNC('month', "IssueDate")::DATE AS loan_month,
    COUNT(*) AS total_loans,
    SUM("LoanAmount") AS total_loan_amount
FROM loans
GROUP BY DATE_TRUNC('month', "IssueDate")
ORDER BY loan_month;

--Loan Default & Risk Analysis Overall default rate--
SELECT
    COUNT(*) AS total_loans,
    COUNT(*) FILTER (WHERE "DefaultFlag" = 1) AS defaulted_loans,

    ROUND(
        100.0 * COUNT(*) FILTER (WHERE "DefaultFlag" = 1)
        / NULLIF(COUNT(*), 0),
        2
    ) AS default_rate_percentage

FROM loans;

--Default rate by loan type--
SELECT
    "LoanType",
    COUNT(*) AS total_loans,
    COUNT(*) FILTER (WHERE "DefaultFlag" = 1) AS defaulted_loans,

    ROUND(
        100.0 * COUNT(*) FILTER (WHERE "DefaultFlag" = 1)
        / NULLIF(COUNT(*), 0),
        2
    ) AS default_rate

FROM loans
GROUP BY "LoanType"
ORDER BY default_rate DESC;

--Default rate by credit score category--
SELECT
    CASE
        WHEN "CreditScore" < 580 THEN 'Poor'
        WHEN "CreditScore" < 670 THEN 'Fair'
        WHEN "CreditScore" < 740 THEN 'Good'
        WHEN "CreditScore" < 800 THEN 'Very Good'
        ELSE 'Excellent'
    END AS credit_category,

    COUNT(*) AS total_loans,

    COUNT(*) FILTER (WHERE "DefaultFlag" = 1) AS defaulted_loans,

    ROUND(
        100.0 * COUNT(*) FILTER (WHERE "DefaultFlag" = 1)
        / NULLIF(COUNT(*), 0),
        2
    ) AS default_rate

FROM loans
GROUP BY credit_category
ORDER BY default_rate DESC;

--Defaulted loan exposure--
SELECT
    COUNT(*) AS defaulted_loans,
    SUM("LoanAmount") AS original_defaulted_amount,
    AVG("LoanAmount") AS average_defaulted_amount
FROM loans
WHERE "DefaultFlag" = 1;

--Loan Payment Analysis Payment summary--
SELECT
    COUNT(*) AS total_payments,
    SUM("AmountPaid") AS total_amount_paid,
    SUM("PrincipalPaid") AS total_principal_paid,
    SUM("InterestPaid") AS total_interest_paid
FROM loan_payments;

--Payment trends by month--
SELECT
    DATE_TRUNC('month', "PaymentDate")::DATE AS payment_month,
    SUM("AmountPaid") AS total_paid,
    SUM("PrincipalPaid") AS principal_paid,
    SUM("InterestPaid") AS interest_paid
FROM loan_payments
GROUP BY DATE_TRUNC('month', "PaymentDate")
ORDER BY payment_month;

--Loan-wise outstanding principal--
SELECT
    l."LoanID",
    l."CustomerID",
    l."LoanAmount",

    COALESCE(SUM(p."PrincipalPaid"), 0) AS principal_paid,

    l."LoanAmount" -
    COALESCE(SUM(p."PrincipalPaid"), 0) AS outstanding_principal

FROM loans l

LEFT JOIN loan_payments p
    ON l."LoanID" = p."LoanID"

GROUP BY
    l."LoanID",
    l."CustomerID",
    l."LoanAmount"

ORDER BY outstanding_principal DESC;

--Customer Analytics Customer distribution by state--
SELECT
    "State",
    COUNT(*) AS total_customers,
    AVG("AnnualIncome") AS average_income
FROM customers
GROUP BY "State"
ORDER BY total_customers DESC;

--Customers with multiple loans--
SELECT
    c."CustomerID",
    c."CustomerName",
    COUNT(l."LoanID") AS total_loans,
    SUM(l."LoanAmount") AS total_borrowed

FROM customers c

JOIN loans l
    ON c."CustomerID" = l."CustomerID"

GROUP BY
    c."CustomerID",
    c."CustomerName"

HAVING COUNT(l."LoanID") > 1

ORDER BY total_borrowed DESC;

--General Ledger & Trial Balance General Ledger debit-credit check--
SELECT
    SUM("Debit") AS total_debit,
    SUM("Credit") AS total_credit,
    SUM("Debit") - SUM("Credit") AS difference
FROM general_ledger;

--Trial Balance by account--
SELECT
    gl."AccountID",
    coa."AccountName",
    coa."AccountType",

    SUM(gl."Debit") AS total_debit,
    SUM(gl."Credit") AS total_credit,

    SUM(gl."Debit") - SUM(gl."Credit") AS net_balance

FROM general_ledger gl

JOIN chart_of_accounts coa
    ON gl."AccountID" = coa."AccountID"

GROUP BY
    gl."AccountID",
    coa."AccountName",
    coa."AccountType"

ORDER BY gl."AccountID";

--Monthly General Ledger trend--
SELECT
    DATE_TRUNC('month', "TransactionDate")::DATE AS transaction_month,
    SUM("Debit") AS total_debit,
    SUM("Credit") AS total_credit
FROM general_ledger
GROUP BY DATE_TRUNC('month', "TransactionDate")
ORDER BY transaction_month;

--Budget vs Actual--
WITH actuals AS (

    SELECT
        DATE_TRUNC('month', gl."TransactionDate")::DATE AS actual_month,
        gl."AccountID",
        gl."DepartmentID",

        CASE
            WHEN coa."NormalBalance" = 'Debit'
                THEN SUM(gl."Debit") - SUM(gl."Credit")

            WHEN coa."NormalBalance" = 'Credit'
                THEN SUM(gl."Credit") - SUM(gl."Debit")
        END AS actual_amount

    FROM general_ledger gl

    JOIN chart_of_accounts coa
        ON gl."AccountID" = coa."AccountID"

    GROUP BY
        DATE_TRUNC('month', gl."TransactionDate"),
        gl."AccountID",
        gl."DepartmentID",
        coa."NormalBalance"
)

SELECT
    b."BudgetMonth",
    b."AccountName",
    b."DepartmentName",
    b."BudgetAmount",

    COALESCE(a.actual_amount, 0) AS actual_amount,

    COALESCE(a.actual_amount, 0) - b."BudgetAmount"
        AS variance

FROM budget b

LEFT JOIN actuals a
    ON DATE_TRUNC('month', b."BudgetMonth")::DATE = a.actual_month
    AND b."AccountID" = a."AccountID"
    AND b."DepartmentID" = a."DepartmentID"

ORDER BY
    b."BudgetMonth",
    b."DepartmentName";

--Rank customers by loan amount--
SELECT
    "CustomerID",
    total_loan_amount,

    RANK() OVER (
        ORDER BY total_loan_amount DESC
    ) AS customer_rank

FROM (
    SELECT
        "CustomerID",
        SUM("LoanAmount") AS total_loan_amount
    FROM loans
    GROUP BY "CustomerID"
) customer_summary;

--Monthly loan growth--
WITH monthly_loans AS (

    SELECT
        DATE_TRUNC('month', "IssueDate")::DATE AS loan_month,
        SUM("LoanAmount") AS monthly_amount

    FROM loans

    GROUP BY DATE_TRUNC('month', "IssueDate")

)

SELECT
    loan_month,
    monthly_amount,

    LAG(monthly_amount) OVER (
        ORDER BY loan_month
    ) AS previous_month_amount,

    monthly_amount -
    LAG(monthly_amount) OVER (
        ORDER BY loan_month
    ) AS monthly_change

FROM monthly_loans

ORDER BY loan_month;