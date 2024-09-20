# server.py
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import pytesseract
from PIL import Image, ImageFilter
import numpy as np
import re
import os

from db import db  # Import der SQLAlchemy-Instanz
from models import User, Category, Expense  # Import der Modelle

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ersetze_durch_sicheren_schlüssel')  # Sicherer Schlüssel aus Umgebungsvariablen

# Verwenden eines absoluten Pfades für die Datenbank-URI
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bcrypt = Bcrypt(app)

db.init_app(app)  # Initialisierung der SQLAlchemy-Instanz mit der Flask-App
migrate = Migrate(app, db)  # Initialisierung von Flask-Migrate

# Route für die Startseite
@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        categories = user.categories if user else []
        return render_template('index.html', categories=categories)
    else:
        return redirect(url_for('login'))

# Route für die Registrierung
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Route für das Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            return 'Ungültige Anmeldedaten', 401
    return render_template('login.html')

# Route für das Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Route zum Abrufen der Budgetdaten
@app.route('/get_data')
def get_data():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401
    user_id = session['user_id']
    user = User.query.get(user_id)
    if user:
        categories = []
        for category in user.categories:
            expenses = [{'id': exp.id, 'description': exp.description, 'amount': exp.amount} for exp in category.expenses]
            categories.append({
                'id': category.id,
                'name': category.name,
                'allocated_amount': category.allocated_amount,
                'spent_amount': category.spent_amount,
                'icon': category.icon,
                'expenses': expenses
            })
        return jsonify({'success': True, 'categories': categories})
    else:
        return jsonify({'success': False, 'message': 'Benutzer nicht gefunden'}), 404

# Route zum Hinzufügen einer Kategorie
@app.route('/add_category', methods=['POST'])
def add_category():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401
    user_id = session['user_id']
    data = request.json
    name = data.get('name')
    allocated_amount = data.get('allocated_amount')
    icon = data.get('icon', 'fas fa-envelope')  # Standard-Icon, falls nicht angegeben

    if not name or allocated_amount is None:
        print("Ungültige Daten empfangen")  # Debugging
        return jsonify({'success': False, 'message': 'Ungültige Daten'}), 400

    category = Category(user_id=user_id, name=name, allocated_amount=allocated_amount, icon=icon)
    db.session.add(category)
    db.session.commit()
    print(f"Added category: {category}")  # Debugging
    return jsonify({'success': True, 'category_id': category.id})

# Route zum Hinzufügen einer Ausgabe
@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401
    user_id = session['user_id']
    data = request.json
    print(f"Received add_expense data: {data}")  # Debugging

    category_id = data.get('category_id')
    description = data.get('description')
    amount = data.get('amount')

    if not category_id or not description or amount is None:
        print("Ungültige Daten empfangen")  # Debugging
        return jsonify({'success': False, 'message': 'Ungültige Daten'}), 400

    category = Category.query.filter_by(id=category_id, user_id=user_id).first()
    if not category:
        print("Kategorie nicht gefunden")  # Debugging
        return jsonify({'success': False, 'message': 'Kategorie nicht gefunden'}), 404

    if category.spent_amount + amount > category.allocated_amount:
        print("Betrag überschreitet verfügbare Menge")  # Debugging
        return jsonify({'success': False, 'message': 'Der Betrag überschreitet den verfügbaren Betrag in dieser Kategorie.'}), 400

    expense = Expense(category_id=category_id, description=description, amount=amount)
    category.spent_amount += amount
    db.session.add(expense)
    db.session.commit()
    print(f"Added expense: {expense}")  # Debugging
    return jsonify({'success': True})

# Route für die OCR-Verarbeitung (unverändert, falls weiterhin benötigt)
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
            # Bildvorverarbeitung
            preprocessed_image = preprocess_image(file.stream)

            # Tesseract-Konfiguration
            custom_config = r'--oem 3 --psm 6'

            # OCR mit Tesseract
            text = pytesseract.image_to_string(preprocessed_image, lang='deu', config=custom_config)

            # Debug: Erkannten Text ausgeben (nur im Debug-Modus)
            if app.debug:
                print("Erkannter Text:")
                print(text)

            # Betrag und Geschäftsname extrahieren
            amount = extract_amount_from_text(text)
            store_name = extract_store_name(text)

            if amount:
                return jsonify({'success': True, 'amount': amount, 'storeName': store_name})
            else:
                return jsonify({'success': False, 'message': 'Kein gültiger Betrag gefunden.'}), 200
        except Exception as e:
            if app.debug:
                print(e)
            return jsonify({'success': False, 'message': 'Fehler bei der Verarbeitung des Bildes.'}), 500
    else:
        return jsonify({'success': False, 'message': 'Ungültiger Dateityp.'}), 400

# Funktion zur Bildvorverarbeitung ohne OpenCV (unverändert)
def preprocess_image(file_stream):
    # Bild öffnen
    image = Image.open(file_stream)

    # In Graustufen konvertieren
    gray = image.convert('L')

    # Rauschunterdrückung mit einem Medianfilter
    gray = gray.filter(ImageFilter.MedianFilter(size=3))

    # Schwellwertsetzung (Binarisierung)
    np_image = np.array(gray)
    threshold = np_image.mean()
    binary = gray.point(lambda x: 0 if x < threshold else 255, '1')

    # Bildskalierung (optional)
    scaled_width = binary.width * 2
    scaled_height = binary.height * 2
    binary = binary.resize((scaled_width, scaled_height), Image.LANCZOS)

    return binary

# Funktion zum Extrahieren des Betrags aus dem erkannten Text (unverändert)
def extract_amount_from_text(text):
    lines = text.split('\n')
    amount = None
    amount_keywords = ['gesamt', 'summe', 'total', 'endbetrag', 'zu zahlen', 'betrag']

    for line in lines:
        lower_line = line.lower()
        if any(keyword in lower_line for keyword in amount_keywords):
            regex = r'(\d+[.,]\d{2})'
            matches = re.findall(regex, line)
            if matches:
                amount_str = matches[-1].replace(',', '.')
                try:
                    amount = float(amount_str)
                    return amount
                except ValueError:
                    continue

    # Fallback, falls kein Betrag gefunden wurde
    regex = r'(\d+[.,]\d{2})'
    matches = re.findall(regex, text)
    if matches:
        amount_str = matches[-1].replace(',', '.')
        try:
            amount = float(amount_str)
            return amount
        except ValueError:
            pass

    return None

# Funktion zum Extrahieren des Geschäftsnames aus dem erkannten Text (unverändert)
def extract_store_name(text):
    lines = text.strip().split('\n')
    possible_names = []
    for line in lines[:10]:
        line = line.strip()
        if line and not any(char.isdigit() for char in line):
            if line.isupper():
                possible_names.append(line)
            else:
                words = line.split()
                capitalized_words = [word for word in words if word and word[0].isupper()]
                if len(capitalized_words) >= len(words) / 2:
                    possible_names.append(line)

    if possible_names:
        return max(possible_names, key=len)
    return 'Unbekanntes Geschäft'

# Erlaubte Dateitypen für den Upload (unverändert)
def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Datenbank erstellen, falls sie nicht existiert
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
