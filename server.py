# server.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import pytesseract
from PIL import Image
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Ersetze dies durch einen sicheren Schlüssel

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cash_stuffing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Importiere Modelle nach der Initialisierung von db, um Zirkularimporte zu vermeiden
from models import User, Data

# Routen für die Benutzerregistrierung und -anmeldung
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Registrierungsformular verarbeiten
        username = request.form['username']
        password = request.form['password']
        # Überprüfe, ob der Benutzername bereits existiert
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error='Benutzername bereits vergeben.')
        # Passwort hashen
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        # Neuen Benutzer erstellen
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Anmeldeformular verarbeiten
        username = request.form['username']
        password = request.form['password']
        # Benutzer authentifizieren
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            # Anmeldung erfolgreich
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            # Anmeldung fehlgeschlagen
            return render_template('login.html', error='Ungültiger Benutzername oder Passwort.')
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Hauptseite der App
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

# API-Endpunkte zum Laden und Speichern von Daten
@app.route('/get_data', methods=['GET'])
def get_data():
    if 'user_id' not in session:
        return jsonify({'error': 'Nicht autorisiert'}), 401
    user_id = session['user_id']
    data = Data.query.filter_by(user_id=user_id).first()
    if data:
        return jsonify({'success': True, 'data': data.content})
    else:
        return jsonify({'success': True, 'data': {}})

@app.route('/save_data', methods=['POST'])
def save_data():
    if 'user_id' not in session:
        return jsonify({'error': 'Nicht autorisiert'}), 401
    user_id = session['user_id']
    content = request.json.get('data')
    data = Data.query.filter_by(user_id=user_id).first()
    if data:
        data.content = content
    else:
        data = Data(user_id=user_id, content=content)
        db.session.add(data)
    db.session.commit()
    return jsonify({'success': True})

# OCR-Verarbeitung
@app.route('/ocr', methods=['POST'])
def ocr():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401
    if 'receipt' not in request.files:
        return jsonify({'success': False, 'message': 'Keine Datei hochgeladen.'}), 400

    file = request.files['receipt']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Keine Datei ausgewählt.'}), 400

    if file and allowed_file(file.filename):
        try:
            image = Image.open(file.stream)
            text = pytesseract.image_to_string(image, lang='deu')

            # Betrag und Geschäftsname extrahieren
            amount = extract_amount_from_text(text)
            store_name = extract_store_name(text)

            if amount:
                response = {'success': True, 'amount': amount}
                if store_name:
                    response['storeName'] = store_name
                return jsonify(response)
            else:
                return jsonify({'success': False, 'message': 'Kein gültiger Betrag gefunden.'}), 200
        except Exception as e:
            print(e)
            return jsonify({'success': False, 'message': 'Fehler bei der Verarbeitung des Bildes.'}), 500
    else:
        return jsonify({'success': False, 'message': 'Ungültiger Dateityp.'}), 400

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg'}
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions

def extract_amount_from_text(text):
    regex = r'(\d+[\.,]\d{2})'
    matches = re.findall(regex, text)
    if matches:
        amount_str = matches[-1]
        amount_str = amount_str.replace(',', '.')
        try:
            amount = float(amount_str)
            return amount
        except ValueError:
            return None
    return None

def extract_store_name(text):
    lines = text.strip().split('\n')
    for line in lines[:5]:
        line = line.strip()
        if line and not any(char.isdigit() for char in line):
            return line
    return None

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5000)
