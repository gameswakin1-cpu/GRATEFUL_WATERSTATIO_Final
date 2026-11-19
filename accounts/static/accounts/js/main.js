// Modal functionality
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    // Password match validation for registration forms
    const password1 = document.getElementById('password1');
    const password2 = document.getElementById('password2');
    
    if (password1 && password2) {
        password2.addEventListener('input', function() {
            if (password1.value !== password2.value) {
                password2.setCustomValidity('Passwords do not match');
            } else {
                password2.setCustomValidity('');
            }
        });
    }
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.display = 'none';
        }, 5000);
    });
    
    // Status update forms for riders
    const statusForms = document.querySelectorAll('.status-update-form');
    statusForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update status badge
                    const statusBadge = this.closest('.delivery-item').querySelector('.status-badge');
                    statusBadge.textContent = data.new_status;
                    statusBadge.className = `status-badge ${data.new_status}`;
                    
                    // Show success message
                    showNotification('Status updated successfully!', 'success');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Error updating status', 'error');
            });
        });
    });
});

// Notification function
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.textContent = message;
    
    const container = document.querySelector('.main-content');
    if (container) {
        container.insertBefore(notification, container.firstChild);
    }
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Search functionality for tables
function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toUpperCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        const cells = rows[i].getElementsByTagName('td');
        let found = false;
        
        for (let j = 0; j < cells.length; j++) {
            const cell = cells[j];
            if (cell) {
                const textValue = cell.textContent || cell.innerText;
                if (textValue.toUpperCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
        }
        
        rows[i].style.display = found ? '' : 'none';
    }
}

// Export table to CSV
function exportToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    for (let i = 0; i < rows.length; i++) {
        const row = [];
        const cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            let data = cols[j].innerText.replace(/,/g, '');
            row.push(data);
        }
        
        csv.push(row.join(','));
    }
    
    const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

// Dashboard charts (if Chart.js is included)
function initializeCharts() {
    if (typeof Chart !== 'undefined') {
        // Orders chart
        const ordersCtx = document.getElementById('ordersChart');
        if (ordersCtx) {
            new Chart(ordersCtx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Orders',
                        data: [12, 19, 3, 5, 2, 3],
                        borderColor: '#3498db',
                        tension: 0.1
                    }]
                }
            });
        }
        
        // Revenue chart
        const revenueCtx = document.getElementById('revenueChart');
        if (revenueCtx) {
            new Chart(revenueCtx, {
                type: 'bar',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Revenue',
                        data: [12000, 19000, 3000, 5000, 2000, 3000],
                        backgroundColor: '#27ae60'
                    }]
                }
            });
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    
    // Add search inputs to tables
    const tables = document.querySelectorAll('.data-table');
    tables.forEach((table, index) => {
        if (table.id) {
            const searchDiv = document.createElement('div');
            searchDiv.className = 'table-search';
            searchDiv.innerHTML = `
                <input type="text" 
                       id="search-${table.id}" 
                       placeholder="Search..." 
                       onkeyup="searchTable('search-${table.id}', '${table.id}')"
                       class="search-input">
            `;
            table.parentNode.insertBefore(searchDiv, table);
        }
    });
});