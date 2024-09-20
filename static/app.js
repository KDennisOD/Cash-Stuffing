/* static/app.js */

let totalAmount = 0;
let allocatedAmount = 0;
let totalExpenses = 0;
let remainingAmount = 0;
let categories = [];
let data = {};
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
            data = JSON.parse(result.data || '{}');
            const periodData = data[`${currentYear}-${currentMonth}`];
            if (periodData) {
                totalAmount = periodData.totalAmount;
                allocatedAmount = periodData.allocatedAmount;
                totalExpenses = periodData.totalExpenses;
                categories = periodData.categories;
            } else {
                totalAmount = 0;
                allocatedAmount = 0;
                totalExpenses = 0;
                categories = [];
            }
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

// Funktion zum Speichern der Daten auf dem Server
function saveData() {
    data[`${currentYear}-${currentMonth}`] = {
        totalAmount,
        allocatedAmount,
        totalExpenses,
        categories
    };
    fetch('/save_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ data: JSON.stringify(data) })
    })
    .then(response => response.json())
    .then(result => {
        if (!result.success) {
            alert('Fehler beim Speichern der Daten auf dem Server.');
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
    saveData();
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

    if (allocatedAmount + amount > totalAmount) {
        alert('Der Betrag überschreitet den verfügbaren Gesamtbetrag.');
        return;
    }

    let iconClass = 'fas fa-envelope'; // Standard-Icon
    if (categoryIcons[name]) {
        iconClass = categoryIcons[name];
    }

    const category = {
        name: name,
        allocatedAmount: amount,
        expenses: [],
        spentAmount: 0,
        icon: iconClass
    };
    categories.push(category);
    allocatedAmount += amount;

    updateCategoryList();
    updateSummary();

    // Felder zurücksetzen
    selectInput.value = '';
    nameInput.value = '';
    amountInput.value = '';

    saveData();
}

function deleteCategory(index) {
    allocatedAmount -= categories[index].allocatedAmount;
    totalExpenses -= categories[index].spentAmount;
    categories.splice(index, 1);
    updateCategoryList();
    updateSummary();
    saveData();
}

function addExpense(index) {
    const descriptionInput = document.getElementById(`expenseDescription${index}`);
    const amountInput = document.getElementById(`expenseAmount${index}`);

    const description = descriptionInput.value.trim();
    const amount = parseFloat(amountInput.value);

    if (description === '' || isNaN(amount) || amount <= 0) {
        alert('Bitte geben Sie eine gültige Beschreibung und einen gültigen Betrag ein.');
        return;
    }

    const category = categories[index];

    if (category.spentAmount + amount > category.allocatedAmount) {
        alert('Der Betrag überschreitet den in dieser Kategorie verfügbaren Betrag.');
        return;
    }

    const expense = {
        description: description,
        amount: amount
    };

    category.expenses.push(expense);
    category.spentAmount += amount;
    totalExpenses += amount;

    updateCategoryList();
    updateSummary();

    // Felder zurücksetzen
    descriptionInput.value = '';
    amountInput.value = '';

    saveData();
}

function deleteExpense(categoryIndex, expenseIndex) {
    const category = categories[categoryIndex];
    const expenseAmount = category.expenses[expenseIndex].amount;
    category.spentAmount -= expenseAmount;
    totalExpenses -= expenseAmount;

    category.expenses.splice(expenseIndex, 1);

    updateCategoryList();
    updateSummary();
    saveData();
}

function updateCategoryList() {
    const budgetList = document.getElementById('budgetList');
    budgetList.innerHTML = '';

    categories.forEach((category, index) => {
        const li = document.createElement('li');
        li.className = 'budget-item';

        li.innerHTML = `
            <h3>
                <i class="${category.icon}"></i> ${category.name}
                <button class="delete-btn" onclick="deleteCategory(${index})">&times;</button>
            </h3>
            <div class="category-details">
                <p>Zugewiesen: ${category.allocatedAmount.toFixed(2)} €</p>
                <p>Ausgegeben: ${category.spentAmount.toFixed(2)} €</p>
                <p>Verfügbar: ${(category.allocatedAmount - category.spentAmount).toFixed(2)} €</p>
            </div>
            <div class="add-expense-form">
                <input type="text" id="expenseDescription${index}" placeholder="Ausgabenbeschreibung">
                <input type="number" id="expenseAmount${index}" placeholder="Betrag (€)">
                <button onclick="addExpense(${index})">Ausgabe hinzufügen</button>
                <br>
                <label>Kassenzettel scannen:</label>
                <input type="file" accept="image/*" capture="environment" onchange="scanReceipt(event, ${index})">
            </div>
            <ul class="expense-list" id="expenseList${index}">
            </ul>
        `;

        budgetList.appendChild(li);

        updateExpenseList(index);
    });
}

function updateExpenseList(categoryIndex) {
    const category = categories[categoryIndex];
    const expenseList = document.getElementById(`expenseList${categoryIndex}`);
    expenseList.innerHTML = '';

    category.expenses.forEach((expense, expenseIndex) => {
        const li = document.createElement('li');
        li.className = 'expense-item';

        li.innerHTML = `
            <span>${expense.description}: ${expense.amount.toFixed(2)} €</span>
            <button class="expense-delete-btn" onclick="deleteExpense(${categoryIndex}, ${expenseIndex})">&times;</button>
        `;

        expenseList.appendChild(li);
    });
}

function updateSummary() {
    document.getElementById('displayTotalAmount').innerText = totalAmount.toFixed(2) + ' €';
    document.getElementById('allocatedAmount').innerText = allocatedAmount.toFixed(2) + ' €';
    document.getElementById('totalExpenses').innerText = totalExpenses.toFixed(2) + ' €';
    document.getElementById('remainingAmount').innerText = (totalAmount - allocatedAmount).toFixed(2) + ' €';
}

// Aktualisierte Funktion zum Scannen des Kassenzettels
function scanReceipt(event, categoryIndex) {
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

                const category = categories[categoryIndex];

                if (category.spentAmount + amountValue > category.allocatedAmount) {
                    alert('Der Betrag überschreitet den in dieser Kategorie verfügbaren Betrag.');
                    return;
                }

                const expense = {
                    description: description,
                    amount: amountValue
                };

                category.expenses.push(expense);
                category.spentAmount += amountValue;
                totalExpenses += amountValue;

                updateCategoryList();
                updateSummary();
                saveData();
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
