/* static/app.js */

let totalAmount = 0;
let allocatedAmount = 0;
let totalExpenses = 0;
let remainingAmount = 0;
let categories = [];
let currentMonth = '';
let currentYear = '';

// Zuordnung von Icons zu Kategorien
const categoryIcons = {
    'Miete': 'fas fa-home',
    'Lebensmittel': 'fas fa-apple-alt',
    'Transport': 'fas fa-car',
    'Unterhaltung': 'fas fa-film',
    'Rechnungen': 'fas fa-file-invoice-dollar',
    'Ersparnisse': 'fas fa-piggy-bank',
    'Sonstiges': 'fas fa-box'
};

// Initialisierung der Datumsauswahl
function initDateSelectors() {
    const monthSelect = document.getElementById('monthSelect');
    const yearSelect = document.getElementById('yearSelect');
    const months = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];
    const currentDate = new Date();

    months.forEach((month, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.text = month;
        monthSelect.add(option);
    });
    monthSelect.value = currentDate.getMonth();

    for (let year = currentDate.getFullYear() - 5; year <= currentDate.getFullYear() + 5; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.text = year;
        yearSelect.add(option);
    }
    yearSelect.value = currentDate.getFullYear();

    currentMonth = monthSelect.value;
    currentYear = yearSelect.value;

    loadData();
}

function changePeriod() {
    const monthSelect = document.getElementById('monthSelect');
    const yearSelect = document.getElementById('yearSelect');
    currentMonth = monthSelect.value;
    currentYear = yearSelect.value;
    loadData();
}

// Funktion zum Laden der Daten vom Server
function loadData() {
    fetch('/get_data')
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            categories = result.categories;
            calculateSummary();
            updateCategoryList();
            updateSummary();
        } else {
            alert('Fehler beim Laden der Daten vom Server.');
        }
    })
    .catch(error => {
        console.error('Fehler:', error);
    });
}

// Funktion zum Speichern einer neuen Kategorie auf dem Server
function saveCategory(name, allocated_amount, icon) {
    fetch('/add_category', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, allocated_amount, icon })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // Neue Kategorie wurde erfolgreich hinzugefügt
            loadData();
        } else {
            alert('Fehler beim Hinzufügen der Kategorie: ' + result.message);
        }
    })
    .catch(error => {
        console.error('Fehler:', error);
    });
}

// Funktion zum Speichern einer neuen Ausgabe auf dem Server
function saveExpense(category_id, description, amount) {
    fetch('/add_expense', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ category_id, description, amount })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // Neue Ausgabe wurde erfolgreich hinzugefügt
            loadData();
        } else {
            alert('Fehler beim Hinzufügen der Ausgabe: ' + result.message);
        }
    })
    .catch(error => {
        console.error('Fehler:', error);
    });
}

// Funktionen für die App

function setTotalAmount() {
    const amountInput = document.getElementById('totalAmount');
    totalAmount = parseFloat(amountInput.value);
    if (isNaN(totalAmount) || totalAmount < 0) {
        alert('Bitte geben Sie einen gültigen Gesamtbetrag ein.');
        totalAmount = 0;
    }
    amountInput.value = '';
    updateSummary();
    // Hier könnten Sie den Gesamtbetrag auf dem Server speichern, falls benötigt
}

function addCategory() {
    const selectInput = document.getElementById('categorySelect');
    const nameInput = document.getElementById('categoryName');
    const amountInput = document.getElementById('categoryAmount');

    let name = '';
    if (nameInput.value.trim() !== '') {
        name = nameInput.value.trim();
    } else if (selectInput.value !== '') {
        name = selectInput.value;
    } else {
        alert('Bitte wählen Sie eine Kategorie aus oder geben Sie einen Namen ein.');
        return;
    }

    const amount = parseFloat(amountInput.value);

    if (isNaN(amount) || amount <= 0) {
        alert('Bitte geben Sie einen gültigen Betrag ein.');
        return;
    }

    // Berechnung prüfen
    let totalAllocated = categories.reduce((sum, cat) => sum + cat.allocated_amount, 0);
    if (totalAllocated + amount > totalAmount) {
        alert('Der Betrag überschreitet den verfügbaren Gesamtbetrag.');
        return;
    }

    // Bestimmen des Icons
    let iconClass = 'fas fa-envelope'; // Standard-Icon
    if (categoryIcons[name]) {
        iconClass = categoryIcons[name];
    }

    // Kategorie auf dem Server speichern
    saveCategory(name, amount, iconClass);

    // Felder zurücksetzen
    selectInput.value = '';
    nameInput.value = '';
    amountInput.value = '';
}

function deleteCategory(category_id) {
    // Implementieren Sie eine Route auf dem Server zum Löschen einer Kategorie
    // Diese Funktion muss entsprechend angepasst werden
    alert('Das Löschen von Kategorien ist derzeit nicht implementiert.');
}

function addExpenseUI(category) {
    const expenseList = document.getElementById(`expenseList${category.id}`);
    const expenseDescription = document.getElementById(`expenseDescription${category.id}`);
    const expenseAmount = document.getElementById(`expenseAmount${category.id}`);

    const description = expenseDescription.value.trim();
    const amount = parseFloat(expenseAmount.value);

    if (description === '' || isNaN(amount) || amount <= 0) {
        alert('Bitte geben Sie eine gültige Beschreibung und einen gültigen Betrag ein.');
        return;
    }

    if (category.spent_amount + amount > category.allocated_amount) {
        alert('Der Betrag überschreitet den in dieser Kategorie verfügbaren Betrag.');
        return;
    }

    // Ausgabe auf dem Server speichern
    saveExpense(category.id, description, amount);

    // Felder zurücksetzen
    expenseDescription.value = '';
    expenseAmount.value = '';
}

function deleteExpenseUI(category_id, expense_id) {
    // Implementieren Sie eine Route auf dem Server zum Löschen einer Ausgabe
    // Diese Funktion muss entsprechend angepasst werden
    alert('Das Löschen von Ausgaben ist derzeit nicht implementiert.');
}

function updateCategoryList() {
    const budgetList = document.getElementById('budgetList');
    budgetList.innerHTML = '';

    categories.forEach((category) => {
        const li = document.createElement('li');
        li.className = 'budget-item';

        li.innerHTML = `
            <h3>
                <i class="${category.icon}"></i> ${category.name}
                <button class="delete-btn" onclick="deleteCategory(${category.id})">&times;</button>
            </h3>
            <div class="category-details">
                <p>Zugewiesen: ${category.allocated_amount.toFixed(2)} €</p>
                <p>Ausgegeben: ${category.spent_amount.toFixed(2)} €</p>
                <p>Verfügbar: ${(category.allocated_amount - category.spent_amount).toFixed(2)} €</p>
            </div>
            <div class="add-expense-form">
                <input type="text" id="expenseDescription${category.id}" placeholder="Ausgabenbeschreibung">
                <input type="number" id="expenseAmount${category.id}" placeholder="Betrag (€)" min="0" step="0.01">
                <button onclick="addExpenseUI(${JSON.stringify(category)})">Ausgabe hinzufügen</button>
                <br>
                <label>Kassenzettel scannen:</label>
                <input type="file" accept="image/*" capture="environment" onchange="scanReceipt(event, ${category.id})">
            </div>
            <ul class="expense-list" id="expenseList${category.id}">
                ${category.expenses.map(exp => `
                    <li class="expense-item">
                        <span>${exp.description}: ${exp.amount.toFixed(2)} €</span>
                        <button class="expense-delete-btn" onclick="deleteExpenseUI(${category.id}, ${exp.id})">&times;</button>
                    </li>
                `).join('')}
            </ul>
        `;

        budgetList.appendChild(li);
    });
}

function updateSummary() {
    calculateSummary();
    document.getElementById('displayTotalAmount').innerText = totalAmount.toFixed(2) + ' €';
    document.getElementById('allocatedAmount').innerText = allocatedAmount.toFixed(2) + ' €';
    document.getElementById('totalExpenses').innerText = totalExpenses.toFixed(2) + ' €';
    document.getElementById('remainingAmount').innerText = (totalAmount - allocatedAmount).toFixed(2) + ' €';
}

function calculateSummary() {
    allocatedAmount = categories.reduce((sum, cat) => sum + cat.allocated_amount, 0);
    totalExpenses = categories.reduce((sum, cat) => sum + cat.spent_amount, 0);
    remainingAmount = totalAmount - allocatedAmount;
}

function scanReceipt(event, category_id) {
    const fileInput = event.target;
    const file = fileInput.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('receipt', file);

        showProcessingOverlay();

        fetch('/ocr', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideProcessingOverlay();

            // Zurücksetzen des File Inputs
            fileInput.value = '';

            if (data.success) {
                const amountValue = parseFloat(data.amount);
                const description = data.storeName || 'Kassenzettel';

                if (isNaN(amountValue) || amountValue <= 0) {
                    alert('Kein gültiger Betrag im Kassenzettel gefunden.');
                    return;
                }

                // Finden der Kategorie
                const category = categories.find(cat => cat.id === category_id);
                if (!category) {
                    alert('Kategorie nicht gefunden.');
                    return;
                }

                if (category.spent_amount + amountValue > category.allocated_amount) {
                    alert('Der Betrag überschreitet den in dieser Kategorie verfügbaren Betrag.');
                    return;
                }

                // Ausgabe auf dem Server speichern
                saveExpense(category.id, description, amountValue);
            } else {
                alert('Fehler beim Verarbeiten des Kassenzettels: ' + data.message);
            }
        })
        .catch(error => {
            hideProcessingOverlay();
            console.error('Fehler:', error);
            alert('Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.');
        });
    }
}

// Aktualisierte Funktion zum Anzeigen des Overlays
function showProcessingOverlay() {
    const overlay = document.getElementById('processingOverlay');
    overlay.style.display = 'flex';
}

// Aktualisierte Funktion zum Verbergen des Overlays
function hideProcessingOverlay() {
    const overlay = document.getElementById('processingOverlay');
    overlay.style.display = 'none';
}

// Hinzufügen der Logout-Funktion
function logout() {
    window.location.href = '/logout';
}

// App initialisieren
window.onload = initDateSelectors;
