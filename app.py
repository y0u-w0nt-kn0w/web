from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import base64
import os
from jinja2 import Template

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_123')

# -----------------------
# Database Initialization
# -----------------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, testimony TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL, description TEXT)''')

    users = [
        (1, 'john_doe', 'password123', 'user', 'SecureInvest helped me grow my portfolio by 40% in one year!'),
        (2, 'sarah_smith', 'pass456', 'user', 'The most secure investment platform I have ever used.'),
        (3, 'mike_wilson', 'mikepass', 'user', 'Five-star service! Very profitable investments.'),
        (4, 'emily_johnson', 'emilypass', 'user', 'Transparent fees and great support.'),
        (5, 'david_brown', 'david123', 'user', 'Security features are top-notch.'),
        (6, 'lisa_wong', 'lisapass', 'user', 'I trust SecureInvest with my clients portfolios.'),
        (7, 'Backup_user', 'backup123', 'user', 
         'Important: Backup files at backup/backup_2024.sql and backup/server_backup.txt'),
        (99, 't3rm14t0rs@dm1n', 'SuperSecretAdminPass2024!', 'admin', '')
    ]
    
    transactions = [
        (1, 1, 5000.00, 'Initial Investment - Tech Stocks'),
        (2, 1, 250.50, 'Monthly Dividend - AAPL'),
        (3, 1, 1500.00, 'Additional Investment - ETFs'),
        (4, 2, 10000.00, 'Gold Investment - Bullion'),
        (5, 2, 750.00, 'Quarterly Returns'),
        (6, 3, 7500.00, 'Stock Portfolio - Blue Chips'),
        (7, 3, 320.25, 'Monthly Growth'),
        (8, 4, 12000.00, 'Real Estate Fund'),
        (9, 5, 8500.00, 'Cryptocurrency Portfolio'),
        (10, 6, 15000.00, 'Client Managed Funds'),
        (11, 7, 1.00, 'System Maintenance - Backup Verification')
    ]
    
    c.executemany('INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)', users)
    c.executemany('INSERT OR IGNORE INTO transactions VALUES (?,?,?,?)', transactions)
    conn.commit()
    conn.close()

def initialize_app():
    os.makedirs('backup', exist_ok=True)
    
    with open('backup/backup_2024.sql', 'w') as f:
        f.write("""
        -- Database Backup
        -- Admin credentials:
        -- username: t3rm14t0rs@dm1n
        -- password: SuperSecretAdminPass2024!
        """)
    
    with open('backup/server_backup.txt', 'w') as f:
        f.write("""
        Server Config Backup
        Secret Key: flag{S3cur3_1nv3st_App}
        Admin Portal: /admin
        """)
    
    init_db()

initialize_app()

# -----------------------
# Routes
# -----------------------

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT username, testimony FROM users WHERE role='user' AND username!='Backup_user'")
    testimonies = c.fetchall()
    conn.close()
    return render_template('index.html', testimonies=testimonies)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        blocked_chars = ['"', ';', '=', '(', ')', 'union', 'select', '*']
        if any(char in username.lower() for char in blocked_chars):
            return "Blocked characters detected", 403

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        try:
            query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
            c.execute(query)
            user = c.fetchone()

            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                return redirect(url_for('dashboard'))
            else:
                return "Invalid credentials", 401

        except Exception as e:
            return f"Error: {e}", 500

        finally:
            conn.close()

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # -----------------------
    # New IDOR Logic Here:
    # ?MWQ9MTA=
    # -----------------------
    if request.args:
        encoded_key = list(request.args.keys())[0]   # take the first parameter name

        try:
            pad = 4 - (len(encoded_key) % 4)
            if pad != 4:
                encoded_key += "=" * pad

            decoded = base64.b64decode(encoded_key).decode()
            if decoded.startswith("id="):
                user_id = int(decoded.split("=")[1])
        except:
            pass

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()

    c.execute("SELECT * FROM transactions WHERE user_id=?", (user_id,))
    transactions = c.fetchall()
    conn.close()

    if user:
        return render_template('dashboard.html', 
                               user=user, 
                               transactions=transactions, 
                               is_backup_user=(user[1] == "Backup_user"))
    else:
        return "User not found", 404


@app.route('/search', methods=['POST'])
def search_transactions():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    search_term = request.form.get("search", "")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM transactions WHERE description LIKE ? AND user_id=?",
              (f"%{search_term}%", session["user_id"]))
    results = c.fetchall()
    conn.close()

    template_string = f"""
    <h3>Search Results for: {search_term}</h3>
    <div class='results'>
    """

    for result in results:
        template_string += f"<p>${result[2]:.2f} - {result[3]}</p>"

    template_string += "</div>"

    try:
        return Template(template_string).render()
    except:
        return template_string


@app.route('/vulnerable_search', methods=['POST'])
def vulnerable_search():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    search_term = request.form.get("search", "")

    template_code = f"""
    <div class="search-results">
        <h4>Query Analysis</h4>
        <p>Processing query: {search_term}</p>
        <p>Done.</p>
    </div>
    """
    return Template(template_code).render()


@app.route('/admin')
def admin_panel():
    if session.get("role") != "admin":
        return "Access denied", 403
    return render_template("admin.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
