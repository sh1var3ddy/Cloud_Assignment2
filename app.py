from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3
import os
import hashlib

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_sqlite_db():
    with sqlite3.connect('database.db') as conn:
        print("Opened database successfully")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                address TEXT,
                username TEXT,
                password TEXT
            )
        ''')
        print("Table created successfully")

init_sqlite_db()

@app.template_filter('md5')
def md5_filter(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()

@app.route('/')
def home():
    return redirect(url_for('register'))

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        address = request.form['address']
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            cur.execute('''
                INSERT INTO users (first_name, last_name, email, address, username, password)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (first_name, last_name, email, address, username, password))
            con.commit()
            session['username'] = username
            return redirect(url_for('display'))

    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        con = sqlite3.connect('database.db')
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()
        con.close()

        if user:
            session['username'] = username
            return redirect(url_for('display'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@app.route('/display/', methods=['GET', 'POST'])
def display():
    if 'username' in session:
        username = session['username']
        con = sqlite3.connect('database.db')
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        con.close()
        if user:
            word_count = None
            uploaded_filename = None
            error_message = None
            if request.method == 'POST':
                file = request.files['file']
                if file and file.filename.endswith('.txt'):
                    uploaded_filename = file.filename
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_filename)
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Ensure the upload folder exists
                    file.save(file_path)
                    with open(file_path, 'r') as f:
                        content = f.read()
                        word_count = len(content.split())
                else:
                    error_message = "File must be in .txt format"
            return render_template('display.html', user=user, word_count=word_count, uploaded_filename=uploaded_filename, error_message=error_message)
    return redirect(url_for('login'))

@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    init_sqlite_db()  # Ensure the database is initialized
    app.run(debug=True)
