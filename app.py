from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import base64
import os
from jinja2 import Template

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_123')

# Initialize database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, testimony TEXT)''')
    
    # Create transactions table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL, description TEXT)''')
    
    # Insert sample data - More users including Backup_user
    users = [
        (1, 'john_doe', 'password123', 'user', 'SecureInvest helped me grow my portfolio by 40% in just one year! Absolutely amazing service.'),
        (2, 'sarah_smith', 'pass456', 'user', 'The most secure investment platform I have ever used. My assets feel completely protected.'),
        (3, 'mike_wilson', 'mikepass', 'user', 'Five-star service! My investments have never been safer or more profitable.'),
        (4, 'emily_johnson', 'emilypass', 'user', 'Transparent fees and excellent customer support. Highly recommended for serious investors.'),
        (5, 'david_brown', 'david123', 'user', 'Switched from my previous broker and never looked back. The security features are top-notch.'),
        (6, 'lisa_wong', 'lisapass', 'user', 'As a financial advisor, I trust SecureInvest with my clients portfolios. Professional and reliable.'),
        (7, 'Backup_user', 'backup123', 'user', 'Important: System backup information is stored in backup/backup_2024.sql and backup/server_backup.txt for recovery purposes.'),
        (8, 'admin', 'SuperSecretAdminPass2024!', 'admin', '')
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
    
    try:
        c.executemany('INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)', users)
        c.executemany('INSERT OR IGNORE INTO transactions VALUES (?,?,?,?)', transactions)
        conn.commit()
    except:
        pass
    
    conn.close()

# Initialize database and backup files when app starts
def initialize_app():
    # Create backup directory and files
    os.makedirs('backup', exist_ok=True)
    
    with open('backup/backup_2024.sql', 'w') as f:
        f.write("""
        -- Database Backup
        -- Admin credentials: 
        -- username: admin
        -- password: SuperSecretAdminPass2024!
        
        CREATE TABLE users (id INT, username TEXT, password TEXT, role TEXT);
        INSERT INTO users VALUES (4, 'admin', 'SuperSecretAdminPass2024!', 'admin');
        """)
    
    with open('backup/server_backup.txt', 'w') as f:
        f.write("""
        Server Configuration Backup
        Database Name: secure_investments_db
        Secret Key: flag{S3cur3_1nv3st_App}
        Admin Portal: /admin
        """)
    
    # Initialize database
    init_db()

# Call initialization
initialize_app()

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Exclude Backup_user from testimonies on index page
    c.execute("SELECT username, testimony FROM users WHERE role = 'user' AND username != 'Backup_user'")
    testimonies = c.fetchall()
    conn.close()
    return render_template('index.html', testimonies=testimonies)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Basic character filtering (but vulnerable to specific payloads)
        blocked_chars = ['"', ';', '=', '(', ')', 'union', 'select', '*']
        
        if any(char in username.lower() for char in blocked_chars):
            return "Blocked characters detected", 403
        
        # SQL Injection vulnerability - only works with known usernames and '--
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        try:
            # Vulnerable query
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
            return f"Error: {str(e)}", 500
        finally:
            conn.close()
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = request.args.get('id')
    if user_id:
        try:
            # IDOR vulnerability - encoded ID parameter
            user_id = int(base64.b64decode(user_id).decode('utf-8').split('=')[1])
        except:
            user_id = session['user_id']
    else:
        user_id = session['user_id']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get user info
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    
    # Get transactions
    c.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
    transactions = c.fetchall()
    
    conn.close()
    
    if user:
        # Check if this is Backup_user to show special message
        is_backup_user = user[1] == 'Backup_user'
        return render_template('dashboard.html', user=user, transactions=transactions, is_backup_user=is_backup_user)
    else:
        return "User not found", 404

@app.route('/search', methods=['POST'])
def search_transactions():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    search_term = request.form.get('search', '')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Safe parameterized query to avoid SQL injection here
    c.execute("SELECT * FROM transactions WHERE description LIKE ? AND user_id = ?", 
              (f'%{search_term}%', session['user_id']))
    results = c.fetchall()
    conn.close()
    
    # VULNERABLE: Direct template injection in the response
    template_string = f"""
    <h3>Search Results for: {search_term}</h3>
    <div class='results'>
    """
    
    # Add results to template string
    for result in results:
        template_string += f"<p>${result[2]:.2f} - {result[3]}</p>"
    
    template_string += "</div>"
    
    # This is where SSTI happens - rendering user input as template
    try:
        t = Template(template_string)
        return t.render()
    except Exception as e:
        # If template rendering fails, return plain text
        return template_string

# Add a dedicated SSTI endpoint that doesn't touch the database
@app.route('/vulnerable_search', methods=['POST'])
def vulnerable_search():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    search_term = request.form.get('search', '')
    
    # This endpoint is purely for SSTI - no database operations
    template_code = f"""
    <div class="search-results">
        <h4>Query Analysis Results</h4>
        <p>Processing your query: {search_term}</p>
        <div class="analysis">
            <p>Query processed successfully. Found relevant results for: {search_term}</p>
        </div>
    </div>
    """
    
    # Direct template rendering with user input - SSTI vulnerability here
    return Template(template_code).render()

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session or session.get('role') != 'admin':
        return "Access denied", 403
    
    return render_template('admin.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
