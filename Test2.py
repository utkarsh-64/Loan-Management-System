import streamlit as st
from streamlit_lottie import st_lottie
import requests
import mysql.connector
import pandas as pd
import json

# Database connection function
def create_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='2407',
            database='finalproject'
        )
        if conn.is_connected():
            return conn
    except mysql.connector.Error as e:
        st.error(f"Database connection failed: {e}")
        return None

# Function to load Lottie animation from URL
def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

st.markdown(
    """
    <style>
    [data-testid="stSidebar"]
    {
        background-image: linear-gradient(to top, #dbdcd7 0%, #dddcd7 24%, #e2c9cc 30%, #e7627d 46%, #b8235a 59%, #801357 71%, #3d1635 84%, #1c1a27 100%);
        height: 100vh;  /* Ensure it covers the full height of the viewport */
    }
    </style>
    """, 
    unsafe_allow_html=True
)

# Function to fetch borrower details, loans, and payments
def fetch_borrower_details(borrower_id):
    conn = create_connection()
    if not conn:
        return None, None, None

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM borrower WHERE borrowerid = %s;", (borrower_id,))
    borrower_details = cursor.fetchone()

    if borrower_details is None:
        cursor.close()
        conn.close()
        return None, None, None

    cursor.execute("SELECT * FROM loan WHERE BorrowID = %s;", (borrower_id,))
    loans = cursor.fetchall()

    loan_ids = [loan[0] for loan in loans]
    payments = []
    if loan_ids:
        query = "SELECT * FROM payment WHERE loanid IN (%s)" % ','.join(['%s'] * len(loan_ids))
        cursor.execute(query, loan_ids)
        payments = cursor.fetchall()

    cursor.close()
    conn.close()
    return borrower_details, loans, payments

# Function to fetch lender details and related loans
def fetch_lender_details(lender_name):
    conn = create_connection()
    if not conn:
        return None, None

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lender WHERE lendername = %s;", (lender_name,))
    lender_details = cursor.fetchone()

    cursor.execute("SELECT * FROM loan WHERE lenderid IN (SELECT lenderid FROM lender WHERE lendername = %s);", (lender_name,))
    loans = cursor.fetchall()

    cursor.close()
    conn.close()
    return lender_details, loans

# Function to fetch loan type details and related loans
def fetch_loantype_details(type_of_loan):
    conn = create_connection()
    if not conn:
        return None, None

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM loantype WHERE typeofloan = %s;", (type_of_loan,))
    loantype_details = cursor.fetchone()

    cursor.execute("SELECT * FROM loan WHERE loantypeid IN (SELECT loantypeid FROM loantype WHERE typeofloan = %s);", (type_of_loan,))
    loans = cursor.fetchall()

    cursor.close()
    conn.close()
    return loantype_details, loans

# Function to get lender names and loan types for dropdowns
def get_lender_names():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT lendername FROM lender;")
    lenders = cursor.fetchall()
    cursor.close()
    conn.close()
    return [lender[0] for lender in lenders]

def get_loan_types():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT typeofloan FROM loantype;")
    loan_types = cursor.fetchall()
    cursor.close()
    conn.close()
    return [loan_type[0] for loan_type in loan_types]

def fetch_all_related_data(borrower_id):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)  # Use dictionary cursor to access columns by name
    
    try:
        # Fetch Borrower Details
        cursor.execute("SELECT * FROM borrower WHERE borrowerid = %s;", (borrower_id,))
        borrower_details = cursor.fetchone()
        
        # Fetch Loan Details related to the Borrower
        cursor.execute("SELECT * FROM loan WHERE borrowid = %s;", (borrower_id,))
        loans = cursor.fetchall()
        
        # Check if 'lenderid' exists in each loan and fetch Payment, Lender, and Loan Type details accordingly
        loan_ids = [loan["loanid"] for loan in loans if "loanid" in loan]
        lender_ids = [loan["lenderid"] for loan in loans if "lenderid" in loan]
        loan_type_ids = [loan["loantypeid"] for loan in loans if "loantypeid" in loan]

        # Fetch Payment Details related to the Loans of the Borrower
        if loan_ids:  # Only fetch if there are loans
            format_strings = ','.join(['%s'] * len(loan_ids))
            cursor.execute(f"SELECT * FROM payment WHERE loanid IN ({format_strings});", loan_ids)
            payments = cursor.fetchall()
        else:
            payments = []

        # Fetch Lender Details related to the Borrower’s Loans
        if lender_ids:  # Only fetch if there are lenders
            format_strings = ','.join(['%s'] * len(lender_ids))
            cursor.execute(f"SELECT * FROM lender WHERE lenderid IN ({format_strings});", lender_ids)
            lenders = cursor.fetchall()
        else:
            lenders = []
        
        # Fetch Loan Type Details related to the Borrower’s Loans
        if loan_type_ids:  # Only fetch if there are loan types
            format_strings = ','.join(['%s'] * len(loan_type_ids))
            cursor.execute(f"SELECT * FROM loantype WHERE loantypeid IN ({format_strings});", loan_type_ids)
            loan_types = cursor.fetchall()
        else:
            loan_types = []
        
        return borrower_details, loans, payments, lenders, loan_types

    except mysql.connector.Error as e:
        print(f"Error fetching data: {e}")
        return None, None, None, None, None

    finally:
        cursor.close()
        conn.close()


# Update function to handle updating or inserting borrower-related details in the database
def update_details(borrower_id, data_to_update):
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Update or insert Borrower Information
            borrower_updates = data_to_update.get("borrower", {})
            for field, value in borrower_updates.items():
                if value:
                    cursor.execute(
                        f"UPDATE borrower SET `{field}` = %s WHERE borrowerid = %s;",
                        (value, borrower_id)
                    )

            # Update or insert Loan Information
            for loan_update in data_to_update.get("loan", []):
                loan_id = loan_update.pop("loanid", None)
                if loan_id:
                    for field, value in loan_update.items():
                        if value:
                            cursor.execute(
                                f"UPDATE loan SET `{field}` = %s WHERE loanid = %s;",
                                (value, loan_id)
                            )
                else:
                    # Insert new loan linked to borrower
                    cursor.execute(
                        "INSERT INTO loan (BorrowID, TypeOfLoan, OriginalLoanSize, SegmentOfLoan, Quarters, Years) VALUES (%s, %s, %s, %s, %s, %s);",
                        (borrower_id, loan_update.get("TypeOfLoan"), loan_update.get("OriginalLoanSize"),
                         loan_update.get("SegmentOfLoan"), loan_update.get("Quarters"), loan_update.get("Years"))
                    )

            # Update or insert Payment Information
            for payment_update in data_to_update.get("payment", []):
                payment_id = payment_update.pop("paymentid", None)
                if payment_id:
                    for field, value in payment_update.items():
                        if value:
                            cursor.execute(
                                f"UPDATE payment SET `{field}` = %s WHERE paymentid = %s;",
                                (value, payment_id)
                            )
                else:
                    # Insert new payment linked to loan (or specify a default loan)
                    cursor.execute(
                        "INSERT INTO payment (LoanID, PaymentAmount, outstandingamount) VALUES (%s, %s, %s);",
                        (borrower_id, payment_update.get("PaymentAmount"), payment_update.get("outstandingamount"))
                    )

            # Update or insert Lender Information
            for lender_update in data_to_update.get("lender", []):
                lender_id = lender_update.pop("lenderid", None)
                if lender_id:
                    for field, value in lender_update.items():
                        if value:
                            cursor.execute(
                                f"UPDATE lender SET `{field}` = %s WHERE lenderid = %s;",
                                (value, lender_id)
                            )
                else:
                    # Insert new lender
                    cursor.execute(
                        "INSERT INTO lender (LenderID, LenderName) VALUES (%s, %s);",
                        (lender_update.get("lenderid"), lender_update.get("LenderName"))
                    )

            # Update or insert Loan Type Information
            for loantype_update in data_to_update.get("loantype", []):
                loantype_id = loantype_update.pop("loantypeid", None)
                if loantype_id:
                    for field, value in loantype_update.items():
                        if value:
                            cursor.execute(
                                f"UPDATE loantype SET `{field}` = %s WHERE loantypeid = %s;",
                                (value, loantype_id)
                            )
                else:
                    # Insert new loan type
                    cursor.execute(
                        "INSERT INTO loantype (LoanTypeID, TypeOfLoan) VALUES (%s, %s);",
                        (loantype_update.get("loantypeid"), loantype_update.get("TypeOfLoan"))
                    )

            # Commit all changes
            conn.commit()
            st.success("Records updated successfully.")
        
        except mysql.connector.Error as e:
            st.error(f"Failed to update details: {e}")
        
        finally:
            cursor.close()
            conn.close()


# Enhanced function to update borrower and related details
# Enhanced function to update borrower and related details, with empty inputs available for new entries
def update_entry():
    st.header("Update Borrower and Related Information")
    
    # Input for borrower ID
    borrower_id = st.text_input("Enter Borrower ID to Update Details")
    
    if borrower_id:
        # Fetch all related data
        borrower_details, loans, payments, lenders, loan_types = fetch_all_related_data(borrower_id)
        
        if not borrower_details:
            st.error("No borrower found with this ID.")
            return
        
        # Display Borrower Details for Update
        st.write("### Borrower Details")
        borrower_updates = {}
        for field, value in borrower_details.items():
            borrower_updates[field] = st.text_input(f"Update Borrower {field}", value=value if value else "")
        
        # Loan Details Update Section
        loan_updates = []
        st.write("### Loan Details")
        if loans:
            for loan in loans:
                st.write(f"#### Loan ID: {loan['loanid']}")
                loan_update = {}
                for field, value in loan.items():
                    if field != "loanid":  # Skip primary key field
                        loan_update[field] = st.text_input(f"Update Loan {field}", value=value if value else "")
                loan_update["loanid"] = loan["loanid"]
                loan_updates.append(loan_update)
        else:
            st.info("No loan records found for this borrower. Enter new loan details.")
            loan_update = {
                "loanid": st.text_input("New Loan ID"),
                "TypeOfLoan": st.text_input("New Loan Type"),
                "OriginalLoanSize": st.text_input("Original Loan Size"),
                "SegmentOfLoan": st.text_input("Segment of Loan"),
                "Quarters": st.text_input("Quarters"),
                "Years": st.text_input("Years"),
            }
            loan_updates.append(loan_update)
        
        # Payment Details Update Section
        payment_updates = []
        st.write("### Payment Details")
        if payments:
            for payment in payments:
                st.write(f"#### Payment ID: {payment['paymentid']}")
                payment_update = {}
                for field in ["PaymentAmount", "outstandingamount"]:
                    current_value = payment.get(field, "")
                    payment_update[field] = st.text_input(f"Update Payment {field}", value=current_value)
                payment_update["paymentid"] = payment["paymentid"]
                payment_updates.append(payment_update)
        else:
            st.info("No payment records found for this borrower. Enter new payment details.")
            payment_update = {
                "paymentid": st.text_input("New Payment ID"),
                "PaymentAmount": st.text_input("Payment Amount"),
                "outstandingamount": st.text_input("Outstanding Amount"),
            }
            payment_updates.append(payment_update)
        
        # Lender Details Update Section
        lender_updates = []
        st.write("### Lender Details")
        if lenders:
            for lender in lenders:
                st.write(f"#### Lender ID: {lender['lenderid']}")
                lender_update = {}
                for field, value in lender.items():
                    if field != "lenderid":  # Skip primary key field
                        lender_update[field] = st.text_input(f"Update Lender {field}", value=value if value else "")
                lender_update["lenderid"] = lender["lenderid"]
                lender_updates.append(lender_update)
        else:
            st.info("No lender records found. Enter new lender details.")
            lender_update = {
                "lenderid": st.text_input("New Lender ID"),
                "LenderName": st.text_input("Lender Name"),
            }
            lender_updates.append(lender_update)
        
        # Loan Type Details Update Section
        loantype_updates = []
        st.write("### Loan Type Details")
        if loan_types:
            for loan_type in loan_types:
                st.write(f"#### Loan Type ID: {loan_type['loantypeid']}")
                loantype_update = {}
                for field, value in loan_type.items():
                    if field != "loantypeid":  # Skip primary key field
                        loantype_update[field] = st.text_input(f"Update Loan Type {field}", value=value if value else "")
                loantype_update["loantypeid"] = loan_type["loantypeid"]
                loantype_updates.append(loantype_update)
        else:
            st.info("No loan type records found. Enter new loan type details.")
            loantype_update = {
                "loantypeid": st.text_input("New Loan Type ID"),
                "TypeOfLoan": st.text_input("Type of Loan"),
            }
            loantype_updates.append(loantype_update)
        
        # Submit updated data to database
        if st.button("Submit Updates"):
            # Structure data for update processing
            data_to_update = {
                "borrower": borrower_updates,
                "loan": loan_updates,
                "payment": payment_updates,
                "lender": lender_updates,
                "loantype": loantype_updates
            }
            
            # Call the update details function to apply changes
            update_details(borrower_id, data_to_update)

# Define the path for user data storage
USER_DATA_FILE = "user.user_data.json"

# Load user data from a JSON file
def load_user_data():
    try:
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save user data to a JSON file
def save_user_data(user_data):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(user_data, file)

# Define login and role-based access control
def login():
    st.sidebar.title("Login / Sign Up")

    # Provide option for Login or Sign Up
    action = st.sidebar.radio("Choose an action", ["Login", "Sign Up"])
    role = st.sidebar.radio("Select Role", ["Lender", "Borrower"])

    # Username and password inputs
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    st.title("Loan Management System")
    st.header("Welcome to the Loan Management System")
    st.subheader("Login or Sign Up through the sidebar")
    
    # Add Lottie animation to the homepage
    lottie_home = load_lottie_url("https://lottie.host/acb85db6-aa14-4d88-a96d-2e5647b8c153/uW8obp8Ozc.json")  # Homepage animation URL
    st_lottie(lottie_home, speed=1, width=600, height=400, key="login_lottie")

    # Information about the system
    st.write("""
            **Welcome to the Loan Management System!**

            Our platform is designed to simplify the management of loans, borrowers, lenders, and loan types. Whether you're a financial institution, loan officer, or a borrower, this system provides you with an intuitive interface to manage your loan data effectively.
        """)

    # Load user data from the file
    user_data = load_user_data()

    if action == "Sign Up":
        # Sign-up form
        st.subheader("Sign Up")

        if st.button("Create Account"):
            if username and password:
                # Check if the username already exists
                if username in user_data:
                    st.error("Username already exists. Please choose a different one.")
                else:
                    # Save the new user's details
                    user_data[username] = {"password": password, "role": role}
                    save_user_data(user_data)  # Persist user data in the JSON file
                    st.success("Account created successfully! You can now log in.")
            else:
                st.error("Please fill in both username and password.")

    elif action == "Login":
        # Login form
        if st.button("Login"):
            if username and password:
                # Check if username exists and password matches
                if username in user_data and user_data[username]["password"] == password:
                    role = user_data[username]["role"]
                    st.session_state['role'] = role
                    st.session_state['username'] = username
                    st.success(f"Logged in as {role}")
                    st.rerun()  # Refresh the app to load the selected role options
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Please enter both username and password.")

                
# Function to handle logout
def logout():
    if 'role' in st.session_state:
        del st.session_state['role']
        del st.session_state['username']
        st.success("Logged out successfully")
        st.rerun()  # Refresh the app to show the login page


def check_access(role):
    if 'role' not in st.session_state or st.session_state['role'] != role:
        st.error(f"Access restricted to {role}s only!")
        return False
    return True


# Login and Role Check
if 'role' not in st.session_state:
    login()
else:
    # Sidebar Navigation Options
    if st.session_state['role'] == "Lender":
        option = st.sidebar.radio("Select Option", ["Home", "Search Entries", "Add Entry", "Update Entry", "Delete Entry", "Help", "About Us"])
    elif st.session_state['role'] == "Borrower":
        option = st.sidebar.radio("Select Option", ["Home", "Search Entries", "Help", "About Us"])

    # Logout button
    if st.sidebar.button("Logout"):
        logout()    
    
    # Main Content Based on Selected Option and Role
    if option == "Home":
        st.title("Loan Management System")
        st.header("Welcome to the Loan Management System")
        
        # Add Lottie animation to the homepage
        lottie_home = load_lottie_url("https://lottie.host/73340ce4-2c58-496a-964a-ffcf91c79da5/qCXpIliWTh.json")  # Homepage animation URL
        st_lottie(lottie_home, speed=1, width=600, height=400, key="homepage_lottie")

        st.write("""
            **Welcome to the Loan Management System!**

            Our platform is designed to simplify the management of loans, borrowers, lenders, and loan types. Whether you're a financial institution, loan officer, or a borrower, this system provides you with an intuitive interface to manage your loan data effectively.

            **Key Features:**
            - **Search and View** detailed records of Borrowers, Lenders, Loans, and Loan Types.
            - **Add New Entries** for borrowers, lenders, and loan records with ease.
            - **Update or Delete** existing records to keep your database up-to-date.
            - **View Lender and Loan Type Information** to understand loan options.

            With easy navigation and a user-friendly interface, you can quickly find, add, or modify any loan-related information.

            Get started by selecting an option from the sidebar!
        """)
        
        st.write("Navigate through options in the sidebar to perform various operations. Use Help(from sidebar), if you face any issue or if you are new to the site.")
        
    elif option == "Search Entries":
        st.header("Search Entries")
        # Add Lottie animation to the homepage
        lottie_home = load_lottie_url("https://lottie.host/c7eea75b-ee47-4195-bc24-02407697442e/oQPq4Dah2R.json")  # Homepage animation URL
        st_lottie(lottie_home, speed=1, width=600, height=400, key="search_lottie")

        # Choose what to search
        search_option = st.selectbox("Search By", ["Borrower ID", "Lender Name", "Loan Type", "Loan ID"])

        if search_option == "Borrower ID":
            borrower_id = st.text_input("Enter Borrower ID", "")
            if borrower_id:
                borrower_details, loans, payments = fetch_borrower_details(borrower_id)
                if borrower_details:
                    st.write("Borrower Details:")
                    st.write(pd.DataFrame([borrower_details], columns=["Borrower ID", "Age", "Income", "New to Credit", "Gender"]))

                    if loans:
                        st.write("Related Loan Details:")
                        st.write(pd.DataFrame(loans, columns=["Loan ID", "Borrower ID", "Lender ID", "Loan Type ID", "Original Loan", "Segment of Loan", "Quarter", "Year"]))
                    else:
                        st.info("No loans found for this borrower.")

                    if payments:
                        st.write("Related Payment Details:")
                        st.write(pd.DataFrame(payments, columns=["Payment ID", "Loan ID", "loan type Id","Payment Amount", "Outstanding Amount"]))
                    else:
                        st.info("No payments found for this borrower.")
                else:
                    st.warning("No borrower found with that ID.")

        elif search_option == "Lender Name":
            lender_name = st.selectbox("Select Lender Name", ["NBFC", "PVT Bank", "PSU Bank"])
            if lender_name:
                lender_details, loans = fetch_lender_details(lender_name)
                if lender_details:
                    st.write("Lender Details:")
                    st.write(pd.DataFrame([lender_details], columns=["Lender ID", "Lender Name"]))

                    if loans:
                        st.write("Related Loan Details:")
                        st.write(pd.DataFrame(loans, columns=["Loan ID", "Borrower ID", "Lender ID", "Loan Type ID", "Original Loan", "Segment of Loan", "Quarter", "Year"]))
                    else:
                        st.info("No loans found for this lender.")
                else:
                    st.warning("No lender found with that name.")

        elif search_option == "Loan Type":
            type_of_loan = st.selectbox("Select Type of Loan", ["Commercial Loan", "Microfinance Loan", "Auto Loans", "Credit Card", "Two-Wheeler Loan"])
            if type_of_loan:
                loantype_details, loans = fetch_loantype_details(type_of_loan)
                if loantype_details:
                    st.write("Loan Type Details:")
                    st.write(pd.DataFrame([loantype_details], columns=["Loan Type ID", "Type of Loan"]))

                    if loans:
                        st.write("Related Loan Details:")
                        st.write(pd.DataFrame(loans, columns=["Loan ID", "Borrower ID", "Lender ID", "Loan Type ID", "Original Loan", "Segment of Loan", "Quarter", "Year"]))
                    else:
                        st.info("No loans found for this loan type.")
                else:
                    st.warning("No loan type found with that name.")

        elif search_option == "Loan ID":
            loan_id = st.text_input("Enter Loan ID", "")
            if loan_id:
                conn = create_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM loan WHERE loanid = %s;", (loan_id,))
                    loan_details = cursor.fetchone()
                    
                    cursor.execute("SELECT * FROM payment WHERE loanid = %s;", (loan_id,))
                    payments = cursor.fetchall()
                    
                    cursor.close()
                    conn.close()
                    
                    if loan_details:
                        st.write("Loan Details:")
                        st.write(pd.DataFrame([loan_details], columns=["Loan ID", "Borrower ID", "Lender ID", "Loan Type ID", "Original Loan", "Segment of Loan", "Quarter", "Year"]))

                        if payments:
                            st.write("Related Payment Details:")
                            st.write(pd.DataFrame(payments, columns=["Payment ID", "Loan ID", "Payment Date", "Payment Amount", "Outstanding Amount"]))
                        else:
                            st.info("No payments found for this loan.")
                    else:
                        st.warning("No loan found with that ID.")

                    
    elif option == "Add Entry" and check_access("Lender"):
        st.header("Add New Entry")

        # Split form sections for borrower and loan entries
        with st.form("add_entry_form"):
            
            # Borrower Information Section
            st.subheader("Borrower Information")
            borrower_id = st.text_input("Borrower ID")
            age = st.number_input("Age", min_value=1, value=1)
            income = st.number_input("Income", min_value=0, value=0)
            new_to_credit = st.selectbox("New to Credit", ["Y", "N"])
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])

            # Lender and Loan Type selection dropdowns
            lender_name = st.selectbox("Lender Name", get_lender_names())
            type_of_loan = st.selectbox("Type of Loan", get_loan_types())

            # Loan Information Section
            st.subheader("Loan Information")
            loan_id = st.text_input("Loan ID")
            original_loan = st.number_input("Original Loan Amount", min_value=0, value=0)
            segment_of_loan = st.text_input("Segment of Loan")
            quarter = st.number_input("Quarter", min_value=1, max_value=4, value=1)
            year = st.number_input("Year", min_value=1900, value=2023)

            # Submit button
            submitted = st.form_submit_button("Add Entry")
            if submitted:
                conn = create_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        # Inserting borrower details
                        cursor.execute(
                            """
                            INSERT INTO borrower (borrowerid, age, income, newtocredit, gender) 
                            VALUES (%s, %s, %s, %s, %s);
                            """,
                            (borrower_id, age, income, new_to_credit, gender)
                        )

                        # Fetching lender and loan type IDs
                        cursor.execute("SELECT lenderid FROM lender WHERE lendername = %s;", (lender_name,))
                        lender_id = cursor.fetchone()[0]

                        cursor.execute("SELECT loantypeid FROM loantype WHERE typeofloan = %s;", (type_of_loan,))
                        loan_type_id = cursor.fetchone()[0]

                        # Inserting loan details
                        cursor.execute(
                            """
                            INSERT INTO loan (loanid, borrowid, lenderid, loantypeid, `Original Loan size`, `Segment of Loan`, quarters, years) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                            """,
                            (loan_id, borrower_id, lender_id, loan_type_id, original_loan, segment_of_loan, quarter, year)
                        )

                        # Committing changes to the database
                        conn.commit()
                        st.success("Entry added successfully!")

                    except mysql.connector.Error as e:
                        st.error(f"Failed to add entry: {e}")

                    finally:
                        cursor.close()
                        conn.close()

    
    elif option == "Update Entry" and check_access("Lender"):
        st.header("Update Entry")

        # Add Lottie animation to the homepage
        lottie_home = load_lottie_url("https://lottie.host/0bc8a97c-e221-4969-a1f0-6b9995809671/JyWz93t5es.json")  # Homepage animation URL
        st_lottie(lottie_home, speed=1, width=600, height=400, key="update_lottie")

        # Choose what to update
        update_option = st.selectbox("Update By", ["Borrower ID", "Lender ID", "Loan ID", "Loan Type ID"])

        if update_option == "Borrower ID":
            update_entry()

        elif update_option == "Lender ID":
            lender_id = st.text_input("Enter Lender ID to update", "")
            if lender_id:
                lender_name = st.text_input("New Lender Name", "")
                if st.button("Update Lender"):
                    conn = create_connection()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "UPDATE lender SET lendername = %s WHERE lenderid = %s;", 
                                (lender_name, lender_id)
                            )
                            conn.commit()
                            st.success("Lender updated successfully.")
                        except mysql.connector.Error as e:
                            st.error(f"Failed to update lender: {e}")
                        finally:
                            cursor.close()
                            conn.close()

        elif update_option == "Loan ID":
            loan_id = st.text_input("Enter Loan ID to update", "")
            if loan_id:
                original_loan = st.number_input("New Original Loan Amount", min_value=0, value=0)
                segment_of_loan = st.text_input("New Segment of Loan", "")
                if st.button("Update Loan"):
                    conn = create_connection()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                """
                                UPDATE loan 
                                SET `Original Loan size` = %s, `Segment of Loan` = %s 
                                WHERE loanid = %s;
                                """, 
                                (original_loan, segment_of_loan, loan_id)
                            )
                            conn.commit()
                            st.success("Loan updated successfully.")
                        except mysql.connector.Error as e:
                            st.error(f"Failed to update loan: {e}")
                        finally:
                            cursor.close()
                            conn.close()

        elif update_option == "Loan Type ID":
            loantype_id = st.text_input("Enter Loan Type ID to update", "")
            if loantype_id:
                type_of_loan = st.text_input("New Type of Loan", "")
                if st.button("Update Loan Type"):
                    conn = create_connection()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            cursor.execute(
                                "UPDATE loantype SET typeofloan = %s WHERE loantypeid = %s;", 
                                (type_of_loan, loantype_id)
                            )
                            conn.commit()
                            st.success("Loan type updated successfully.")
                        except mysql.connector.Error as e:
                            st.error(f"Failed to update loan type: {e}")
                        finally:
                            cursor.close()
                            conn.close()
            
    elif option == "Delete Entry" and check_access("Lender"):
        st.header("Delete Entry")

        # Add Lottie animation to the homepage
        lottie_home = load_lottie_url("https://lottie.host/11624765-e71b-4eb5-a3eb-f423cd8c684a/gAhCULY5a9.json")  # Homepage animation URL
        st_lottie(lottie_home, speed=1, width=600, height=400, key="delete_lottie")
        
        # Choose what to delete
        delete_option = st.selectbox("Delete By", ["Borrower ID", "Lender ID", "Loan ID", "Loan Type ID"])

        if delete_option == "Borrower ID":
            borrower_id = st.text_input("Enter Borrower ID to delete", "")
            if st.button("Delete Borrower"):
                conn = create_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("DELETE FROM borrower WHERE borrowerid = %s;", (borrower_id,))
                        cursor.execute("DELETE FROM loan WHERE borrowid = %s;", (borrower_id,))
                        conn.commit()
                        st.success("Borrower deleted successfully.")
                    except mysql.connector.Error as e:
                        st.error(f"Failed to delete borrower: {e}")
                    finally:
                        cursor.close()
                        conn.close()

        elif delete_option == "Lender ID":
            lender_id = st.text_input("Enter Lender ID to delete", "")
            if st.button("Delete Lender"):
                conn = create_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("DELETE FROM lender WHERE lenderid = %s;", (lender_id,))
                        conn.commit()
                        st.success("Lender deleted successfully.")
                    except mysql.connector.Error as e:
                        st.error(f"Failed to delete lender: {e}")
                    finally:
                        cursor.close()
                        conn.close()

        elif delete_option == "Loan ID":
            loan_id = st.text_input("Enter Loan ID to delete", "")
            if st.button("Delete Loan"):
                conn = create_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("DELETE FROM loan WHERE loanid = %s;", (loan_id,))
                        conn.commit()
                        st.success("Loan deleted successfully.")
                    except mysql.connector.Error as e:
                        st.error(f"Failed to delete loan: {e}")
                    finally:
                        cursor.close()
                        conn.close()

        elif delete_option == "Loan Type ID":
            loantype_id = st.text_input("Enter Loan Type ID to delete", "")
            if st.button("Delete Loan Type"):
                conn = create_connection()
                if conn:
                    cursor = conn.cursor()
                    try:
                        cursor.execute("DELETE FROM loantype WHERE loantypeid = %s;", (loantype_id,))
                        conn.commit()
                        st.success("Loan type deleted successfully.")
                    except mysql.connector.Error as e:
                        st.error(f"Failed to delete loan type: {e}")
                    finally:
                        cursor.close()
                        conn.close()


    elif option == "About Us":
        st.header("About Us")
        
        # Add Lottie animation to the About Us page
        lottie_about = load_lottie_url("https://lottie.host/46dadecd-9a72-44e9-832c-f7a2b0439d2e/MWQ2bQuMZd.json")  # About Us animation URL
        st_lottie(lottie_about, speed=1, width=600, height=400, key="aboutus_lottie")
        
        st.write("""
            **Loan Management System**  
            This application is designed to help users manage loan records, including borrowers, lenders, loan types, payments, and other relevant information.  
            The system is user-friendly, allowing you to search, add, update, and delete records easily.  
            Developed to streamline loan management, this tool is perfect for lenders, financial institutions, and loan officers.
        """)

        st.subheader("Contact US")
        # Add Lottie animation to the About Us page
        lottie_about = load_lottie_url("https://lottie.host/ab92b670-e6cb-43ed-a042-2e9e97abf7b7/vtsooseJiq.json")  # About Us animation URL
        st_lottie(lottie_about, speed=1, width=600, height=400, key="contactus_lottie")
        st.write("""
            *Utkarsh Lakhani -23070126064- utkarshlj264@gmail.com*\n
            *Mani Ratna Krishna -23070126071*\n
            *Piyush Mengde -24070126506*\n
        """)
        

# Helper functions remain the same...

    elif option == "Help":
        st.header("Help Section")

        st.write("""
        Welcome to the **Loan Management System Help Section**!  
        This page will guide you on how to use the application effectively.

        ### 1. Home Page
        The home page gives you a brief overview of the app and its functionalities. You can explore the available options from the sidebar.

        ### 2. Search Entries
        Use this section to search for entries in the system. You can search by:
        - **Borrower ID**: Look for specific borrower details.
        - **Lender Name**: Search for loans by lender.
        - **Loan Type**: Find loans based on their type (e.g., Commercial, Microfinance, etc.).
        - **Loan ID**: Look for a specific loan entry by its ID.""")

        # Add Lottie animation to the About Us page
        lottie_about = load_lottie_url("https://lottie.host/f316aa6a-97bc-40c1-9b95-a5d303c1de8a/mnS8F0RQU5.json")  # About Us animation URL
        st_lottie(lottie_about, speed=1, width=600, height=400, key="help_lottie")

        st.write("""
        **Example Borrower ID**: `R9181Z764O`  
        - This ID will help you find a borrower in the system. Simply enter it in the "Search By" > "Borrower ID" option.

        **Example Loan ID**: `NBFCIN000COML127`  
        - Use this loan ID in the "Search By" > "Loan ID" to find specific loan details.

        ### 3. Add Entry
        In this section, you can add new records to the system:
        - **Borrower Information**: Enter details like Borrower ID, Age, Income, Gender, etc.
        - **Loan Information**: Provide details like Loan ID, Lender Name, Loan Type, and Amount.
        - After filling out the form, click on "Add Entry" to submit the data.

        ### 4. Update Entry
        This section allows you to update existing entries in the system:
        - **Borrower ID**: Update borrower details like age, income, etc.
        - **Lender ID**: Update lender name.
        - **Loan ID**: Modify loan details such as the original loan amount and segment.
        - **Loan Type ID**: Update loan type if necessary.

        ### 5. Delete Entry
        Use this section to delete entries from the system by selecting the relevant ID (Borrower ID, Lender ID, Loan ID, or Loan Type ID).

        ### 6. About Us
        This section provides information about the developers and their contributions to the project.

        **Important Tips**:
        - Ensure that all required fields are filled when adding or updating entries.
        - Use the example IDs for reference when searching for entries.
        - If you encounter any issues, contact support through the About Us page.

        We hope this help section guides you through using the Loan Management System. Feel free to explore the other sections and manage your loan data efficiently!
        """)
