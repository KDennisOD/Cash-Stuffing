from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import pytesseract
from PIL import Image, ImageFilter
import numpy as np
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Ersetze dies durch einen sicheren Schlüssel
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Oder dein gewünschtes Datenbanksystem
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

# Datenbankmodell für Benutzer
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

# Datenbankmodell für die Budgetdaten
class BudgetData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Text, nullable=False)

# Route für die Startseite
@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('index.html')
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
            return 'Ungültige Anmeldedaten'
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
    budget_data = BudgetData.query.filter_by(user_id=user_id).first()
    if budget_data:
        return jsonify({'success': True, 'data': budget_data.data})
    else:
        return jsonify({'success': True, 'data': '{}'})
    
# Route zum Speichern der Budgetdaten
@app.route('/save_data', methods=['POST'])
def save_data():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401
    user_id = session['user_id']
    data = request.json.get('data')
    budget_data = BudgetData.query.filter_by(user_id=user_id).first()
    if budget_data:
        budget_data.data = data
    else:
        budget_data = BudgetData(user_id=user_id, data=data)
        db.session.add(budget_data)
    db.session.commit()
    return jsonify({'success': True})

# Funktion zur Bildvorverarbeitung ohne OpenCV
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

# Funktion zum Extrahieren des Betrags aus dem erkannten Text
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

# Funktion zum Extrahieren des Geschäftsnames aus dem erkannten Text
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

# Erlaubte Dateitypen für den Upload
def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Route für die OCR-Verarbeitung
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

            # Debug: Erkannten Text ausgeben
            print("Erkannter Text:")
            print(text)

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

# Datenbank erstellen, falls sie nicht existiert
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
