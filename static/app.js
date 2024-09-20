// static/app.js

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM vollständig geladen.");
    initDateSelectors();
    initAddCategoryForm();
    // Weitere Initialisierungen können hier hinzugefügt werden
});

// Funktion zur Initialisierung der Date-Selectors (falls vorhanden)
function initDateSelectors() {
    const dateSelectors = document.querySelectorAll('.date-selector');
    console.log('Gefundene date-selector Elemente:', dateSelectors);
    
    if (dateSelectors.length === 0) {
        console.warn('Keine Elemente mit der Klasse .date-selector gefunden.');
        return;
    }
    
    dateSelectors.forEach(selector => {
        if (selector) {
            console.log('Füge Event Listener zu:', selector);
            selector.addEventListener('change', function(event) {
                // Ihre Logik hier, z.B. Filterung von Ausgaben basierend auf dem Datum
                console.log('Date selector geändert:', event.target.value);
            });
        } else {
            console.warn('Ein date-selector Element ist null.');
        }
    });
}

// Funktion zur Initialisierung des Add Category Formulars
function initAddCategoryForm() {
    const addCategoryForm = document.getElementById('addCategoryForm');
    if (addCategoryForm) {
        console.log('Füge Event Listener zum Add Category Form hinzu.');
        addCategoryForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const name = document.getElementById('categoryName').value.trim();
            const allocatedAmount = parseFloat(document.getElementById('categoryAmount').value);
            const icon = document.getElementById('categoryIcon').value.trim() || 'fas fa-envelope';
            
            console.log(`Kategorie hinzufügen: Name=${name}, Betrag=${allocatedAmount}, Icon=${icon}`);
            
            if (name === '' || isNaN(allocatedAmount) || allocatedAmount < 0) {
                alert('Bitte geben Sie einen gültigen Namen und einen positiven Betrag ein.');
                return;
            }
            
            fetch('/add_category', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, allocated_amount: allocatedAmount, icon })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Kategorie erfolgreich hinzugefügt');
                    window.location.reload();
                } else {
                    alert('Fehler beim Hinzufügen der Kategorie: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Fehler:', error);
                alert('Ein unerwarteter Fehler ist aufgetreten.');
            });
        });
    } else {
        console.warn('Add Category Form nicht gefunden.');
    }
}

// Funktion zum Hinzufügen einer Ausgabe
function addExpenseUI(category_id) {
    const expenseDescription = document.getElementById(`expenseDescription${category_id}`);
    const expenseAmount = document.getElementById(`expenseAmount${category_id}`);

    if (!expenseDescription || !expenseAmount) {
        console.error('Ausgabe-Formularelemente nicht gefunden.');
        alert('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
        return;
    }

    const description = expenseDescription.value.trim();
    const amount = parseFloat(expenseAmount.value);

    console.log(`Ausgabe hinzufügen: Kategorie-ID=${category_id}, Beschreibung=${description}, Betrag=${amount}`);
    
    if (description === '' || isNaN(amount) || amount <= 0) {
        alert('Bitte geben Sie eine gültige Beschreibung und einen gültigen Betrag ein.');
        return;
    }

    fetch('/add_expense', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ category_id, description, amount })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Ausgabe erfolgreich hinzugefügt');
            window.location.reload();
        } else {
            alert('Fehler beim Hinzufügen der Ausgabe: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Fehler:', error);
        alert('Ein unerwarteter Fehler ist aufgetreten.');
    });
}

// Funktion zum Löschen einer Ausgabe
function deleteExpenseUI(category_id, expense_id) {
    if (confirm('Sind Sie sicher, dass Sie diese Ausgabe löschen möchten?')) {
        console.log(`Lösche Ausgabe: Kategorie-ID=${category_id}, Ausgabe-ID=${expense_id}`);
        window.location.href = `/delete_expense/${category_id}/${expense_id}`;
    }
}

// Optional: Funktion zum Scannen von Kassenzetteln mit OCR (Falls implementiert)
function scanReceipt(event, category_id) {
    const file = event.target.files[0];
    if (!file) {
        return;
    }

    const formData = new FormData();
    formData.append('receipt', file);

    // Optional: Implementieren Sie eine Route `/ocr` in Ihrem server.py, um das Bild zu verarbeiten
    fetch('/ocr', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const descriptionField = document.getElementById(`expenseDescription${category_id}`);
            const amountField = document.getElementById(`expenseAmount${category_id}`);
            descriptionField.value = data.storeName || 'Kassenzettel';
            amountField.value = data.amount || '';
            console.log('Kassenzettel gescannt und Felder aktualisiert.');
        } else {
            alert('Fehler beim Scannen des Kassenzettels: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Fehler:', error);
        alert('Ein unerwarteter Fehler ist aufgetreten.');
    });
}
