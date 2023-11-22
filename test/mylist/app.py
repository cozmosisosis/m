import os, logging, sqlite3
from helpers import login_required, get_db, close_db
from flask import Flask, flash, render_template, redirect, session, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'





@app.route('/')
@login_required
def index():

    if 'user_id' in session:
        error = None
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE user_id = ?', (session['user_id'],))

        if user is None:
            error = "Failure retreving user account info please try logging on again"
            flash(error)
            return redirect(url_for('login'))

        db.execute('UPDATE users SET date_last_active = ? WHERE user_id = ?', (datetime.utcnow(), session['user_id']))
        db.commit()
        return render_template("index.html", user=user)

    error = 'login failure, user_id not found in session'
    flash(error)
    return redirect(url_for('login'))
    
        


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error = None

        if username == "" or password == "":
            error = 'Username and or Password was left empty'

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()


        if user is None or not check_password_hash(user['hashed_password'], password):
            error = 'Username and or Password is Incorrect'

        if error is None:

            session.clear()
            session['user_id'] = user['user_id']
            try:
                db.execute('UPDATE users SET date_last_active = ? WHERE user_id = ?', (datetime.utcnow(), user['user_id']))
                db.commit()
                return redirect(url_for('index'))
            except:
                error = 'Failed to update date last active in account info'

        flash(error)
        return redirect(url_for('login'))
    else:
        try:
            if session['user_id'] is not None:
                flash('Logged in!')
                db = get_db()
                db.execute('UPDATE users SET date_last_active = ? WHERE user_id = ?', (datetime.utcnow(), session['user_id']))
                db.commit()
                return redirect(url_for('index'))
        except:
            return render_template('login.html')

        
    
    


@app.route("/logout", methods=['POST', 'GET'])
def logout():
    session.clear()
    flash("Logged out")
    return redirect(url_for('login'))



@app.route("/register", methods=['POST', 'GET'])
def register():

    if request.method == 'GET':
        try:
            if session['user_id'] is not None:
                flash('Must not be logged in to register')
                return redirect(url_for('index'))
        except: pass

        return render_template('register.html')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_email = request.form.get('email',"None")
        password_verification = request.form['password_verification']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required'

        elif not password:
            error = 'Password is required'

        elif not password_verification:
            error = 'Second password is required'

        elif not password == password_verification:
            error = 'Passwords do not match'


        if error is None: 
            try:
                db.execute(
                    'INSERT INTO users (username, hashed_password, user_email, date_created, date_last_active) VALUES (?, ?, ?, ?, ?)',
                    (username, generate_password_hash(password), user_email, datetime.utcnow(), datetime.utcnow())
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            
            else:
                flash('Account created, Please Login!')
                return redirect(url_for('login'))


        flash(error)


        return redirect(url_for('register'))




@app.errorhandler(404)
def page_not_found(error):
    flash('Invalid route')
    return redirect(url_for('index'))