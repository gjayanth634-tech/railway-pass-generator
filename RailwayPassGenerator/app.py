from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'railway_pass_secret_key_2026'

bcrypt = Bcrypt(app)

client = MongoClient('mongodb://localhost:27017/')
db = client['railway_pass_db']

users_collection = db['users']
passes_collection = db['passes']

INDIAN_CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata',
    'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur',
    'Indore', 'Patna', 'Bhopal', 'Ludhiana', 'Coimbatore', 'Mysore',
    'Vijayawada', 'Jodhpur', 'Rajkot', 'Kochi', 'Udaipur', 'Nashik',
    'Faridabad', 'Meerut', 'Prayagraj', 'Varanasi', 'Srinagar', 'Jammu',
    'Chandigarh', 'Dehradun', 'Shimla', 'Guwahati', 'Bhubaneswar', 'Rourkela'
]

TRAINS = [
    {'name': 'Rajdhani Express', 'number': '12450'},
    {'name': 'Shatabdi Express', 'number': '12002'},
    {'name': 'Garib Rath', 'number': '12565'},
    {'name': 'Duronto Express', 'number': '12245'},
    {'name': 'Humsafar Express', 'number': '12596'},
    {'name': 'Howrah Mail', 'number': '13006'},
    {'name': 'Tamil Nadu Express', 'number': '12621'},
    {'name': 'Kerala Express', 'number': '12625'},
    {'name': 'Goa Express', 'number': '12779'},
    {'name': 'Deccan Queen', 'number': '12123'}
]

PASS_PRICES = {
    'daily': 250,
    'weekly': 550,
    'monthly': 1000
}

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('pass_generator'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        aadhar = request.form.get('aadhar')
        dob = request.form.get('dob')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))

        if users_collection.find_one({'email': email}):
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))

        birth_date = datetime.strptime(dob, '%Y-%m-%d')
        age = (datetime.now() - birth_date).days // 365
        
        if age < 18:
            flash('You must be 18 years or older to register!', 'error')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        user_data = {
            'full_name': full_name,
            'email': email,
            'mobile': mobile,
            'aadhar': aadhar,
            'dob': dob,
            'password': hashed_password,
            'created_at': datetime.now()
        }
        
        users_collection.insert_one(user_data)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', cities=INDIAN_CITIES)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = users_collection.find_one({'email': email})
        
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            return redirect(url_for('pass_generator'))
        else:
            flash('Invalid email or password!', 'error')

    return render_template('login.html')

@app.route('/pass_generator', methods=['GET', 'POST'])
def pass_generator():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        pass_type = request.form.get('pass_type')
        from_city = request.form.get('from_city')
        to_city = request.form.get('to_city')
        train_number = request.form.get('train_number')

        price = PASS_PRICES.get(pass_type, 0)
        
        session['pass_data'] = {
            'pass_type': pass_type,
            'from_city': from_city,
            'to_city': to_city,
            'train_number': train_number,
            'price': price
        }
        
        return redirect(url_for('payment'))

    return render_template('pass_generator.html', 
                         cities=INDIAN_CITIES, 
                         trains=TRAINS,
                         prices=PASS_PRICES)

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'user_id' not in session or 'pass_data' not in session:
        return redirect(url_for('pass_generator'))

    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        card_number = request.form.get('card_number')
        upi_id = request.form.get('upi_id')
        wallet_number = request.form.get('wallet_number')

        if payment_method == 'card':
            if not card_number or len(card_number.replace(' ', '')) < 16:
                flash('Please enter a valid card number!', 'error')
                return redirect(url_for('payment'))
        elif payment_method == 'upi':
            if not upi_id:
                flash('Please enter a valid UPI ID!', 'error')
                return redirect(url_for('payment'))
        elif payment_method == 'wallet':
            if not wallet_number:
                flash('Please enter a valid wallet number!', 'error')
                return redirect(url_for('payment'))

        pass_data = session['pass_data']
        
        if pass_data['pass_type'] == 'daily':
            valid_until = datetime.now() + timedelta(days=1)
        elif pass_data['pass_type'] == 'weekly':
            valid_until = datetime.now() + timedelta(days=7)
        else:
            valid_until = datetime.now() + timedelta(days=30)

        pass_record = {
            'user_id': session['user_id'],
            'pass_type': pass_data['pass_type'],
            'from_city': pass_data['from_city'],
            'to_city': pass_data['to_city'],
            'train_number': pass_data['train_number'],
            'price': pass_data['price'],
            'payment_method': payment_method,
            'valid_until': valid_until,
            'created_at': datetime.now(),
            'pass_id': f"RP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

        passes_collection.insert_one(pass_record)
        
        session.pop('pass_data', None)
        flash('Payment successful! Your pass has been generated.', 'success')
        return redirect(url_for('view_pass'))

    return render_template('payment.html', pass_data=session.get('pass_data', {}))

@app.route('/view_pass')
def view_pass():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_passes = list(passes_collection.find({'user_id': session['user_id']}).sort('created_at', -1))
    
    return render_template('view_pass.html', passes=user_passes)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'info')
    return redirect(url_for('login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin123':
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    total_users = users_collection.count_documents({})
    total_passes = passes_collection.count_documents({})
    total_revenue = sum(p.get('price', 0) for p in passes_collection.find({}))
    
    recent_passes = list(passes_collection.find().sort('created_at', -1).limit(10))
    recent_users = list(users_collection.find().sort('created_at', -1).limit(10))
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_passes=total_passes,
                         total_revenue=total_revenue,
                         recent_passes=recent_passes,
                         recent_users=recent_users)

@app.route('/admin/all_passes')
def admin_all_passes():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    all_passes = list(passes_collection.find().sort('created_at', -1))
    return render_template('admin_all_passes.html', passes=all_passes)

@app.route('/admin/all_users')
def admin_all_users():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    all_users = list(users_collection.find().sort('created_at', -1))
    return render_template('admin_all_users.html', users=all_users)

@app.route('/admin/delete_pass/<pass_id>')
def delete_pass(pass_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    passes_collection.delete_one({'pass_id': pass_id})
    flash('Pass deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<user_id>')
def delete_user(user_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    users_collection.delete_one({'_id': ObjectId(user_id)})
    passes_collection.delete_many({'user_id': user_id})
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    flash('Admin logged out successfully!', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
