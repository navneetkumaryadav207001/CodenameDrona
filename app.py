from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my name is navneet'  # Use a strong secret key
bcrypt = Bcrypt(app)

# Initialize database
def init_db():
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.rout('/login')
def login():
    return render_template('login.html')

@app.route('/login_post', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

    if user and bcrypt.check_password_hash(user[0], password):
        session['username'] = username
        flash('Login successful!', 'success')
        return redirect(url_for('welcome'))
    flash('Invalid credentials', 'danger')
    return redirect(url_for('index'))

@app.route('/welcome')
def welcome():
    if 'username' not in session:
        return redirect(url_for('index'))
    return f'Welcome to the protected area, {session["username"]}!'

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('index'))
    except sqlite3.IntegrityError:
        flash('Username already exists', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # HTTPS for local testing; use a real certificate for production
