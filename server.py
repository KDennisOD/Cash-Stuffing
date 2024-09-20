from flask import Flask, request, jsonify
import pytesseract
from PIL import Image
import numpy as np
import cv2
import re

app = Flask(__name__)

def preprocess_image(file_stream):
    # Bild aus dem Dateistream lesen
    file_bytes = np.asarray(bytearray(file_stream.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # In Graustufen konvertieren
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Rauschunterdrückung mittels Gaußscher Weichzeichnung
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Schwellwertsetzung (Otsu's Methode)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Morphologische Operationen
    kernel = np.ones((1, 1), np.uint8)
    img_dilated = cv2.dilate(thresh, kernel, iterations=1)
    img_eroded = cv2.erode(img_dilated, kernel, iterations=1)

    # Entzerrung (Bild begradigen)
    coords = np.column_stack(np.where(img_eroded > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = img_eroded.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    img_rotated = cv2.warpAffine(img_eroded, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # Skalierung
    img_resized = cv2.resize(img_rotated, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # In PIL-Image konvertieren
    preprocessed_image = Image.fromarray(img_resized)

    return preprocessed_image

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
                capitalized_words = [word for word in words if word[0].isupper()]
                if len(capitalized_words) >= len(words) / 2:
                    possible_names.append(line)

    if possible_names:
        return max(possible_names, key=len)
    return 'Unbekanntes Geschäft'

@app.route('/ocr', methods=['POST'])
def ocr():
    if 'receipt' not in request.files:
        return jsonify({'success': False, 'message': 'Keine Datei hochgeladen.'}), 400

    file = request.files['receipt']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Keine Datei ausgewählt.'}), 400

    if file and allowed_file(file.filename):
        try:
            preprocessed_image = preprocess_image(file.stream)
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(preprocessed_image, lang='deu', config=custom_config)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
