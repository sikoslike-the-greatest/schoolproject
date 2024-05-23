from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
import hashlib
import requests
import json

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'
app.static_folder = 'templates/css'

login_manager = LoginManager()
login_manager.init_app(app)

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
        user.id = user_data[1]
        return user
    return None

@app.route('/')
def index():
    page = request.args.get('page', default=1, type=int)
    sort = request.args.get('sort', default='by-relevance')
    sizeValue = request.args.get('size', default='')
    brands = request.args.get('brands', default='')
    api_url = f'http://127.0.0.1:56789/api/products?size={sizeValue}&brands={brands}&sort={sort}&page={page}'
    response = requests.get(api_url)
    if response.status_code == 200:
        products = response.json()
        return render_template('index.html', products=products)
    else:
        return 'Failed to load products from API'

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
            user = load_user(username)
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
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT cart FROM users WHERE username = ?', (current_user.get_id(),))
    cart_json = cursor.fetchone()[0]
    cart = json.loads(cart_json) if cart_json else []

    total_price = sum(int(item['price']) for item in cart)
    
    return render_template('profile.html', username=current_user.get_id(), cart=cart, total_price=total_price)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/product/<path:product_name>')
def product_page(product_name):
    sku = request.args.get('sku')
    api_url = f'http://127.0.0.1:56789/api/product/{product_name}'
    if sku:
        api_url += f'?sku={sku}'
    
    response = requests.get(api_url)
    if response.status_code == 200:
        product_data = response.json()
        return render_template('product.html', product=product_data)
    else:
        return 'Failed to load product from API', 500

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if current_user.is_authenticated:
        size = request.form.get('size')
        product_name = request.form.get('product_name')
        price = request.form.get('price')

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT cart FROM users WHERE username = ?', (current_user.get_id(),))
        cart_json = cursor.fetchone()[0]
        cart = json.loads(cart_json) if cart_json else []

        cart.append({'product_name': product_name, 'size': size, 'price': price})

        cursor.execute('UPDATE users SET cart = ? WHERE username = ?', (json.dumps(cart), current_user.get_id()))
        conn.commit()
        conn.close()

        return redirect(url_for('profile'))
    else:
        return redirect(url_for('login'))


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if current_user.is_authenticated:
        size = request.form.get('size')
        product_name = request.form.get('product_name')

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT cart FROM users WHERE username = ?', (current_user.get_id(),))
        cart_json = cursor.fetchone()[0]
        cart = json.loads(cart_json) if cart_json else []

        # Удаляем товар из корзины
        for item in cart:
            if item['product_name'] == product_name and item['size'] == size:
                cart.remove(item)
                break

        cursor.execute('UPDATE users SET cart = ? WHERE username = ?', (json.dumps(cart), current_user.get_id()))
        conn.commit()
        conn.close()

        return redirect(url_for('profile'))
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
