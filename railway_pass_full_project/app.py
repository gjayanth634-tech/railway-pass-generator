from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from werkzeug.security import generate_password_hash, check_password_hash
import random
import math
import re
import uuid
import urllib.parse

app = Flask(__name__)
app.secret_key = "railway_secret"

# MongoDB Connection
try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    client.admin.command('ping')  # Attempt to connect to verify server is running
    db = client["railway_pass_system"]
    users = db["users"]
    passes = db["passes"]
    print("Connected to MongoDB successfully!")
except ServerSelectionTimeoutError:
    print("ERROR: Could not connect to MongoDB. Please ensure the 'mongod' service is running.")
    users = None
    passes = None


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        # Check for DB connection
        if users is None:
            return "Database is not connected. Please check the server.", 500

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return render_template("login.html", error="Email and password are required.")

        user = users.find_one({"email": email})

        if user and check_password_hash(user.get("password", ""), password):
            session["user"] = user.get("email")
            return redirect(url_for("home"))
        else:
            error = "Invalid email or password"

    return render_template("login.html", error=error)


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    name = ""
    email = ""
    aadhaar = ""
    mobile = ""

    if request.method == "POST":
        # Defensive coding: check for DB connection first
        if users is None:
            return "Database is not connected. Please check the server.", 500

        # Safely get form data using .get() to avoid crashes on missing fields
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        aadhaar = request.form.get("aadhaar", "").strip()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "").strip()

        # Ensure all fields are submitted
        if not all([name, email, aadhaar, mobile, password]):
            return render_template("register.html", error="All fields are required.", name=name, email=email, aadhaar=aadhaar, mobile=mobile)

        if users.find_one({"email": email}):
            error = "Email already exists!"
            return render_template("register.html", error=error, name=name, email=email, aadhaar=aadhaar, mobile=mobile)

        # Data Inputs: Specific validation for Aadhaar and Mobile
        if not re.match(r"^\d{12}$", aadhaar):
            return render_template("register.html", error="Aadhaar must be exactly 12 digits.", name=name, email=email, aadhaar=aadhaar, mobile=mobile)

        if not re.match(r"^\d{10}$", mobile):
            return render_template("register.html", error="Mobile number must be exactly 10 digits.", name=name, email=email, aadhaar=aadhaar, mobile=mobile)

        result = users.insert_one({
            "name": name,
            "email": email,
            "aadhaar": aadhaar,
            "mobile": mobile,
            "password": generate_password_hash(password),
            "role": "user"  # Set default role for new users
        })
        # Log the successful insertion
        print(f"New user inserted with ID: {result.inserted_id}")

        return redirect(url_for("login"))

    return render_template("register.html", error=error, name=name, email=email, aadhaar=aadhaar, mobile=mobile)


# ---------------- HOME (PASS FORM) ----------------
@app.route("/home", methods=["GET", "POST"])
def home():

    if "user" not in session:
        return redirect(url_for("login"))

    # Check for DB connection
    if users is None:
        return "Database is not connected. Please check the server.", 500

    # Fetch user data to pre-fill the form on GET request
    user_data = users.find_one({"email": session.get("user")}) if users is not None else None

    if request.method == "POST":

        # Safely get form data using .get()
        name = request.form.get("name")
        age = request.form.get("age")
        aadhaar = request.form.get("aadhaar")
        mobile = request.form.get("mobile")
        source = request.form.get("from")
        destination = request.form.get("to")
        pass_type = request.form.get("pass_type")
        train_type = request.form.get("train_type")

        if not all([name, age, aadhaar, mobile, source, destination, pass_type, train_type]):
            return render_template("home.html", error="All fields are required.", user=user_data)

        # Age validation
        if not age.isdigit():
            return render_template("home.html", error="Please enter a valid age.", user=user_data)

        if int(age) < 19:
            return render_template("home.html",
                                   error="Applicants must be 19 years of age or older to qualify for a railway pass.", user=user_data)

        # Data Inputs: Specific validation for Aadhaar and Mobile
        if not re.match(r"^\d{12}$", aadhaar):
            return render_template("home.html", error="Aadhaar must be exactly 12 digits.", user=user_data)

        if not re.match(r"^\d{10}$", mobile):
            return render_template("home.html", error="Mobile number must be exactly 10 digits.", user=user_data)

        if source == destination:
            return render_template("home.html",
                                   error="Departure and Destination cannot be same!", user=user_data)

        # Store values individually
        session["name"] = name
        session["age"] = age
        session["aadhaar"] = aadhaar
        session["mobile"] = mobile
        session["source"] = source
        session["destination"] = destination
        session["pass_type"] = pass_type
        session["train_type"] = train_type

        return redirect(url_for("payment"))

    return render_template("home.html", user=user_data)


# ---------------- PAYMENT ----------------
@app.route("/payment", methods=["GET", "POST"])
def payment():

    if "user" not in session:
        return redirect(url_for("login"))

    # Check if pass details exist in session
    if "name" not in session:
        return redirect(url_for("home"))

    # Determine price based on pass type
    pass_type = session.get("pass_type")
    amount = 0
    if pass_type == "Daily":
        amount = 250
    elif pass_type == "Weekly":
        amount = 550
    elif pass_type == "Monthly":
        amount = 1000
    
    session["amount"] = amount

    if request.method == "POST":
        payment_method = request.form.get("payment")
        if not payment_method:
            return render_template("payment.html", error="Please select a payment method.", amount=amount)

        # Store payment method and create a transaction token to pass to the processing page
        session["payment_method"] = payment_method
        session["transaction_token"] = str(uuid.uuid4())

        return redirect(url_for("process_payment"))

    return render_template("payment.html", amount=amount)


# ---------------- PROCESS PAYMENT (NEW) ----------------
# This route shows a simulated payment screen (e.g., QR code for UPI)
# and then automatically redirects to finalize the payment.
@app.route("/process_payment")
def process_payment():
    if "user" not in session or "transaction_token" not in session:
        return redirect(url_for("login"))

    payment_method = session.get("payment_method")
    token = session.get("transaction_token")
    amount = session.get("amount", 0)
    
    qr_code_url = None
    if payment_method == 'UPI':
        # Construct the UPI string properly
        upi_data = f"upi://pay?pa=example-user@okhdfcbank&pn=Railway Pass&am={amount}.00&cu=INR"
        # Encode the string to be safe for URL
        encoded_data = urllib.parse.quote(upi_data)
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={encoded_data}"

    # This will render the page with the QR code or loader, which then redirects
    return render_template("payment_processing.html", method=payment_method, token=token, amount=amount, qr_code_url=qr_code_url)


# ---------------- FINALIZE PAYMENT (NEW) ----------------
# This is the final step after the simulated payment.
# It validates the transaction, creates the pass, saves it to the DB,
# and clears the session data.
@app.route("/finalize_payment/<token>")
def finalize_payment(token):
    if "user" not in session:
        return redirect(url_for("login"))

    # Security check: validate token to prevent direct access or reuse
    if "transaction_token" not in session or session["transaction_token"] != token:
        # Invalid or expired token, redirect home to be safe
        return redirect(url_for("home"))

    # Check for DB connection
    if passes is None:
        return "Database is not connected. Please check the server.", 500

    pass_number = "RP" + str(random.randint(10000, 99999))

    # Retrieve data from session
    name = session.get("name")
    age = session.get("age")
    aadhaar = session.get("aadhaar")
    mobile = session.get("mobile")
    source = session.get("source")
    destination = session.get("destination")
    pass_type = session.get("pass_type")
    train_type = session.get("train_type")
    payment_method = session.get("payment_method")
    amount = session.get("amount")

    # Store the generated pass in the database
    result = passes.insert_one({
        "pass_number": pass_number, "name": name, "age": age, "aadhaar": aadhaar,
        "mobile": mobile, "source": source, "destination": destination,
        "pass_type": pass_type, "train_type": train_type, "user_email": session.get("user"), "payment_method": payment_method,
        "amount": amount
    })
    print(f"New pass inserted with ID: {result.inserted_id}")

    # Clean up session data after use to prevent re-submission
    for key in ["name", "age", "aadhaar", "mobile", "source", "destination", "pass_type", "train_type", "payment_method", "transaction_token", "amount"]:
        session.pop(key, None)

    return render_template(
        "success.html",
        pass_number=pass_number, name=name, age=age, aadhaar=aadhaar, mobile=mobile, source=source, destination=destination, pass_type=pass_type, train_type=train_type
    )


# ---------------- MY PASSES ----------------
@app.route("/my_passes")
def my_passes():
    if "user" not in session:
        return redirect(url_for("login"))

    # Check for DB connection
    if passes is None:
        return "Database is not connected. Please check the server.", 500

    search_query = request.args.get('search', '')
    user_email = session["user"]
    
    query_filter = {"user_email": user_email}
    if search_query:
        # Using regex for a "contains" search, case-insensitive
        query_filter["pass_number"] = {"$regex": search_query, "$options": "i"}

    # Pagination Logic
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Number of passes per page
    skip = (page - 1) * per_page

    total_passes = passes.count_documents(query_filter)
    total_pages = math.ceil(total_passes / per_page)

    user_passes = list(passes.find(query_filter).skip(skip).limit(per_page))

    return render_template(
        "my_passes.html", passes=user_passes, 
        page=page, total_pages=total_pages,
        search_query=search_query
    )


# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
def admin_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    # Check for DB connection
    if users is None or passes is None:
        return "Database is not connected. Please check the server.", 500

    user = users.find_one({"email": session["user"]})
    if not user or user.get("role") != "admin":
        return "<h1>Unauthorized Access</h1><p>You must be an admin to view this page.</p>", 403

    search_query = request.args.get('search', '')
    
    query_filter = {}
    if search_query:
        # Using regex for a "contains" search, case-insensitive
        query_filter["pass_number"] = {"$regex": search_query, "$options": "i"}
        # Admin can also search by user email
        query_filter = {
            "$or": [
                {"pass_number": {"$regex": search_query, "$options": "i"}},
                {"user_email": {"$regex": search_query, "$options": "i"}}
            ]
        }

    # Pagination Logic
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Show more items on the admin page
    skip = (page - 1) * per_page

    total_passes = passes.count_documents(query_filter)
    total_pages = math.ceil(total_passes / per_page)

    all_passes = list(passes.find(query_filter).sort("_id", -1).skip(skip).limit(per_page))

    return render_template(
        "admin_dashboard.html", passes=all_passes, page=page, total_pages=total_pages,
        search_query=search_query, total_passes=total_passes
    )


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
