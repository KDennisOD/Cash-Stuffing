// static/app.js
// JavaScript-Code für die App

// Initialisierung der Variablen
let totalAmount = 0;
let allocatedAmount = 0;
let totalExpenses = 0;
let categories = [];
let data = {};
let currentMonth;
let currentYear;

// Funktion zur Initialisierung der Datumsauswahl
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

// Rest Ihres bestehenden JavaScript-Codes, inklusive Funktionen für OCR und UI-Updates

// App initialisieren
window.onload = initDateSelectors;
