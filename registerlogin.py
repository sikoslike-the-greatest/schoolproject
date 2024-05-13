from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
import hashlib

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

# Функция для создания таблицы пользователей
def create_users_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            cart TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Создание таблицы пользователей при запуске приложения
create_users_table()

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        user = User()
        user.id = user_data[1]  # Используем username в качестве идентификатора пользователя
        return user
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()

        if user_data and check_password(user_data[2], password):
            user = load_user(username) # Загружаем пользователя через load_user
            login_user(user)
            conn.close()
            return redirect(url_for('index'))
        else:
            conn.close()
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

def check_password(password_hash, password):
    return hashlib.sha256(password.encode()).hexdigest() == password_hash

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return render_template('register.html', error='Username already exists')

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute('INSERT INTO users (username, password_hash, cart) VALUES (?, ?, ?)', (username, password_hash, ''))
        conn.commit()
        conn.close()

        user = User()
        user.id = username
        login_user(user)
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', username=current_user.id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
