from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "railway_secret"

client = MongoClient("mongodb://localhost:27017/")
db = client["railway_pass_system"]
users = db["users"]
passes = db["passes"]

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = users.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            session["user"] = user["email"]
            return redirect(url_for("home"))
        else:
            error = "Invalid email or password"

    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]

        if users.find_one({"email": email}):
            return "Email already exists!"

        users.insert_one({
            "name": request.form["name"],
            "email": email,
            "password": generate_password_hash(request.form["password"])
        })
        return redirect("/")
    return render_template("register.html")

@app.route("/home", methods=["GET", "POST"])
def home():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        #  Validation: Prevent same departure and destination
        if request.form["from"] == request.form["to"]:
             return render_template("home.html", error="Departure and Destination cannot be same!")

        session["pass_data"] = request.form.to_dict()
        return redirect("/payment")

    return render_template("home.html")

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':

        name = session.get('name')
        age = session.get('age')
        source = session.get('source')
        destination = session.get('destination')

        import random
        pass_number = "RP" + str(random.randint(10000, 99999))

        return render_template(
            'success.html',
            name=name,
            age=age,
            source=source,
            destination=destination,
            pass_number=pass_number
        )

    return render_template('payment.html')
    @app.route('/success') 
    def success():
        return render_template("success.html")


@app.route('/generate_pass', methods=['POST'])
def generate_pass():

    session['name'] = request.form.get('name')
    session['age'] = request.form.get('age')
    session['source'] = request.form.get('from')
    session['destination'] = request.form.get('to')

    session['pass_number'] = "RP" + str(random.randint(1000, 9999))

    return redirect(url_for('pass_generated'))

@app.route('/pass_generated')
def pass_generated():

    return render_template(
        "pass_generated.html",
        pass_number=session.get('pass_number'),
        name=session.get('name'),
        age=session.get('age'),
        source=session.get('source'),
        destination=session.get('destination')
    )
    return render_template(
    "pass_generated.html",
    pass_number=pass_number,
    name=name,
    age=age,
    source=source,
    destination=destination
    )



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
 




