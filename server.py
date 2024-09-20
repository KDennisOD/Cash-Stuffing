# server.py
from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import os

from db import db  # Import der SQLAlchemy-Instanz
from models import User, Category, Expense  # Import der Modelle

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ersetze_durch_einen_sicheren_schlüssel')  # Sicherer Schlüssel aus Umgebungsvariablen

# Verwenden eines absoluten Pfades für die Datenbank-URI
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'users.db')
if not os.path.exists(os.path.dirname(db_path)):
    os.makedirs(os.path.dirname(db_path))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
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
        return render_template('index.html', user=user, categories=categories)
    else:
        return redirect(url_for('login'))

# Registrierung
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        if not username or not password:
            return render_template('register.html', error="Bitte geben Sie einen Benutzernamen und ein Passwort ein.")
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Benutzername bereits vergeben.")
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        session['user_id'] = new_user.id
        return redirect(url_for('index'))
    
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Ungültige Anmeldedaten.")
    
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Route zum Hinzufügen einer Kategorie
@app.route('/add_category', methods=['POST'])
def add_category():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401
    
    data = request.json
    name = data.get('name', '').strip()
    allocated_amount = data.get('allocated_amount')
    icon = data.get('icon', 'fas fa-envelope').strip()
    
    if not name or allocated_amount is None:
        return jsonify({'success': False, 'message': 'Ungültige Daten'}), 400
    
    try:
        allocated_amount = float(allocated_amount)
        if allocated_amount < 0:
            raise ValueError
    except ValueError:
        return jsonify({'success': False, 'message': 'Zugewiesener Betrag muss eine positive Zahl sein.'}), 400
    
    new_category = Category(
        user_id=session['user_id'],
        name=name,
        allocated_amount=allocated_amount,
        icon=icon
    )
    db.session.add(new_category)
    db.session.commit()
    
    return jsonify({'success': True, 'category_id': new_category.id})

# Route zum Löschen einer Kategorie
@app.route('/delete_category/<int:category_id>', methods=['GET'])
def delete_category(category_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401
    
    category = Category.query.filter_by(id=category_id, user_id=session['user_id']).first()
    if not category:
        return jsonify({'success': False, 'message': 'Kategorie nicht gefunden'}), 404
    
    # Löschen aller zugehörigen Ausgaben
    Expense.query.filter_by(category_id=category.id).delete()
    
    db.session.delete(category)
    db.session.commit()
    
    return redirect(url_for('index'))

# Route zum Hinzufügen einer Ausgabe
@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401
    
    data = request.json
    category_id = data.get('category_id')
    description = data.get('description', '').strip()
    amount = data.get('amount')
    
    if not category_id or not description or amount is None:
        return jsonify({'success': False, 'message': 'Ungültige Daten'}), 400
    
    category = Category.query.filter_by(id=category_id, user_id=session['user_id']).first()
    if not category:
        return jsonify({'success': False, 'message': 'Kategorie nicht gefunden'}), 404
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'success': False, 'message': 'Betrag muss eine positive Zahl sein.'}), 400
    
    if category.spent_amount + amount > category.allocated_amount:
        return jsonify({'success': False, 'message': 'Der Betrag überschreitet den verfügbaren Betrag in dieser Kategorie.'}), 400
    
    new_expense = Expense(
        category_id=category_id,
        description=description,
        amount=amount
    )
    category.spent_amount += amount
    db.session.add(new_expense)
    db.session.commit()
    
    return jsonify({'success': True, 'expense_id': new_expense.id})

# Route zum Löschen einer Ausgabe
@app.route('/delete_expense/<int:category_id>/<int:expense_id>', methods=['GET'])
def delete_expense(category_id, expense_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401
    
    expense = Expense.query.filter_by(id=expense_id, category_id=category_id).first()
    if not expense:
        return jsonify({'success': False, 'message': 'Ausgabe nicht gefunden'}), 404
    
    category = Category.query.get(category_id)
    if category:
        category.spent_amount -= expense.amount
    
    db.session.delete(expense)
    db.session.commit()
    
    return redirect(url_for('index'))

# Optional: Route für OCR (falls benötigt)
@app.route('/ocr', methods=['POST'])
def ocr():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401
    
    if 'receipt' not in request.files:
        return jsonify({'success': False, 'message': 'Kein Bild hochgeladen'}), 400
    
    file = request.files['receipt']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Kein Bild ausgewählt'}), 400
    
    try:
        img = Image.open(file.stream)
        text = pytesseract.image_to_string(img, lang='de')  # Sprache auf Deutsch setzen
        
        # Beispielhafte Verarbeitung des Textes, um Store Name und Betrag zu extrahieren
        # Dies muss je nach Format der Kassenzettel angepasst werden
        store_name = "Unbekannt"
        amount = 0.0
        
        # Beispielhafte Regex-Extraktion
        import re  # Import innerhalb der Funktion
        store_match = re.search(r'Store\s*:\s*(.*)', text, re.IGNORECASE)
        amount_match = re.search(r'Amount\s*:\s*([0-9.,]+)', text, re.IGNORECASE)
        
        if store_match:
            store_name = store_match.group(1).strip()
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '.')
            try:
                amount = float(amount_str)
            except ValueError:
                amount = 0.0
        
        return jsonify({'success': True, 'storeName': store_name, 'amount': amount})
    
    except Exception as e:
        print(f"OCR Fehler: {e}")
        return jsonify({'success': False, 'message': 'Fehler bei der Verarbeitung des Bildes'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
