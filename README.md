# Loan Management System

A user-friendly web application built with **Streamlit** for managing loans, borrowers, lenders, loan types, and payments. This system is designed for financial institutions, loan officers, and borrowers to efficiently handle loan-related records with secure role-based access.

---

## 🚀Demo
**Try the application here:** 

https://loan-management-system.streamlit.app/

---
## Features

- **User Authentication**: Secure login and sign-up with role selection (Lender or Borrower).
- **Role-Based Access**: Lenders can add, update, and delete entries. Borrowers can search and view records.
- **Comprehensive Search**: Find records by Borrower ID, Lender Name, Loan Type, or Loan ID.
- **Add, Update, and Delete Entries**: Manage borrowers, loans, payments, lenders, and loan types.
- **Interactive UI**: Modern, animated interface with Lottie animations for a better user experience.
- **Persistent User Data**: User credentials and roles are stored in a local JSON file.
- **MySQL Database Integration**: All data operations are performed on a MySQL backend.

---

## Getting Started

### Prerequisites

- Python 3.8+
- MySQL Server
- The following Python packages:
  - `streamlit`
  - `streamlit-lottie`
  - `mysql-connector-python`
  - `pandas`
  - `requests`

### Installation

1. **Clone the repository**

2. **Install dependencies**

3. **Set up MySQL database:**
   - Create a database named `finalproject`.
   - Create the required tables (`borrower`, `lender`, `loan`, `loantype`, `payment`) as referenced in the code.
   - Update the database connection settings in `Test2.py` if needed (default: user `root`, password `2407`).

4. **Run the application:**
   ```bash
   streamlit run Test2.py
   ```

---

## Usage

### Authentication

- Use the sidebar to **Login** or **Sign Up**.
- Choose your role: **Lender** or **Borrower**.
- Demo credentials are stored in `user.user_data.json`.

### Navigation

- **Home**: Overview and introduction.
- **Search Entries**: Search by Borrower ID, Lender Name, Loan Type, or Loan ID.
- **Add Entry** (Lender only): Add new borrower and loan records.
- **Update Entry** (Lender only): Update borrower, lender, loan, or loan type details.
- **Delete Entry** (Lender only): Remove records by ID.
- **Help**: Step-by-step usage guide and sample IDs.
- **About Us**: Project and developer information.
---

## Database Structure

- **borrower**: Stores borrower details (ID, age, income, credit status, gender).
- **lender**: Stores lender information.
- **loan**: Stores loan records, linked to borrower, lender, and loan type.
- **loantype**: Stores available loan types.
- **payment**: Stores payment records linked to loans.

---

## Contributor:
 - Utkarsh Lakhani - [GitHub](github.com/utkarsh-64)
---

## Notes

- Ensure MySQL server is running and accessible with the credentials provided in the script.
- All required tables must exist in the database before running the app.
- For any issues, refer to the **Help** section in the app or contact the developers via the **About Us** page.

---

## License

This project is for educational purposes. Please contact the authors for reuse or collaboration.
