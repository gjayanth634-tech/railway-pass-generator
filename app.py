from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "railway_secret"

client = MongoClient("mongodb://localhost:27017/")
db = client["railway_pass"]
users = db["users"]

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        users.insert_one({
            "name": request.form["name"],
            "email": request.form["email"],
            "password": request.form["password"]
        })
        return redirect("/")
    return render_template("register.html")

@app.route("/login", methods=["POST"])
def login_user():
    user = users.find_one({
        "email": request.form["email"],
        "password": request.form["password"]
    })
    if user:
        session["user"] = user["name"]
        return redirect("/dashboard")
    return "Invalid Credentials"

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", user=session.get("user"))

@app.route("/payment")
def payment():
    return render_template("payment.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

