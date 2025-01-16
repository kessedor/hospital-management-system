document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap modals
    var modals = document.querySelectorAll('.modal');
    modals.forEach(function(modal) {
        new bootstrap.Modal(modal);
    });

    // Initialize form handlers
    initializeFormHandlers();
    
    // Initialize search and filters
    initializeSearchAndFilters();
});

// Form submission handlers
function initializeFormHandlers() {
    // Add Item Form
    const itemForm = document.getElementById('itemForm');
    if (itemForm) {
        itemForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('Form submitted');
            
            // Add form validation
            if (!this.checkValidity()) {
                e.stopPropagation();
                this.classList.add('was-validated');
                return;
            }
            
            try {
                const formData = new FormData(this);
                const submitBtn = this.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                
                const response = await fetch(window.INVENTORY.urls.addItem, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': window.INVENTORY.csrfToken
                    }
                });

                const data = await response.json();
                console.log('Response:', data);

                if (response.ok) {
                    // Add new item to table without reload
                    if (data.item) {
                        const tbody = document.querySelector('table tbody');
                        const noItemsRow = tbody.querySelector('tr td[colspan="7"]');
                        
                        if (noItemsRow) {
                            tbody.innerHTML = createItemRow(data.item);
                        } else {
                            tbody.insertAdjacentHTML('afterbegin', createItemRow(data.item));
                        }
                        
                        // Update statistics
                        updateStatistics(data.stats);
                    }
                    
                    showAlert('success', 'Item added successfully!');
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addItemModal'));
                    modal.hide();
                    this.reset();
                    this.classList.remove('was-validated');
                } else {
                    showAlert('danger', data.message || 'Error adding item');
                }
            } catch (error) {
                console.error('Error:', error);
                showAlert('danger', 'An error occurred while adding the item');
            } finally {
                submitBtn.disabled = false;
            }
        });
    }

    // Stock Update Form
    const stockUpdateForm = document.getElementById('stockUpdateForm');
    if (stockUpdateForm) {
        stockUpdateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const itemId = this.dataset.itemId;
            submitForm(this, `${window.INVENTORY.urls.updateStock}${itemId}/`, 'updateStockModal');
        });
    }

    // Delete Item Form
    const deleteItemForm = document.getElementById('deleteItemForm');
    if (deleteItemForm) {
        deleteItemForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const itemId = this.dataset.itemId;
            submitForm(this, `${window.INVENTORY.urls.deleteItem}${itemId}/`, 'deleteConfirmationModal');
        });
    }
}

// Generic form submission function
async function submitForm(form, url, modalId) {
    try {
        const formData = new FormData(form);
        
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': window.INVENTORY.csrfToken
            }
        });

        const data = await response.json();

        if (response.ok) {
            showAlert('success', 'Operation completed successfully!');
            
            const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
            modal.hide();

            refreshInventoryStats();
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showAlert('danger', data.message || 'An error occurred');
        }
    } catch (error) {
        showAlert('danger', 'An error occurred while processing your request');
        console.error('Error:', error);
    }
}

// Button click handlers
function editItem(button) {
    const form = document.getElementById('itemForm');
    const modal = new bootstrap.Modal(document.getElementById('addItemModal'));
    
    const itemData = {
        id: button.dataset.id,
        name: button.dataset.name,
        category: button.dataset.category,
        quantity: button.dataset.quantity,
        unit: button.dataset.unit,
        minimum_stock: button.dataset.minimumStock,
        unit_price: button.dataset.unitPrice,
        expiry_date: button.dataset.expiryDate,
        description: button.dataset.description,
        storage_location: button.dataset.storageLocation,
        supplier_info: button.dataset.supplierInfo
    };
    
    form.dataset.itemId = itemData.id;
    form.action = `${window.INVENTORY.urls.editItem}${itemData.id}/`;
    
    // Populate form fields
    Object.keys(itemData).forEach(key => {
        const input = form.querySelector(`[name=${key}]`);
        if (input) {
            input.value = itemData[key] || '';
        }
    });
    
    document.getElementById('itemModalTitle').textContent = 'Edit Item';
    modal.show();
}

function updateStock(itemId) {
    const form = document.getElementById('stockUpdateForm');
    const modal = new bootstrap.Modal(document.getElementById('updateStockModal'));
    
    form.dataset.itemId = itemId;
    form.action = `${window.INVENTORY.urls.updateStock}${itemId}/`;
    form.reset();
    
    modal.show();
}

function deleteItem(itemId) {
    const form = document.getElementById('deleteItemForm');
    const modal = new bootstrap.Modal(document.getElementById('deleteConfirmationModal'));
    
    form.dataset.itemId = itemId;
    form.action = `${window.INVENTORY.urls.deleteItem}${itemId}/`;
    modal.show();
}

function createItemRow(item) {
    return `
        <tr>
            <td>
                <div class="d-flex flex-column">
                    <span class="fw-medium">${item.name}</span>
                    <small class="text-muted d-none d-md-block">ID: ${item.id}</small>
                </div>
            </td>
            <td data-category-id="${item.category.id}">${item.category.name}</td>
            <td>${item.quantity}</td>
            <td>${item.unit}</td>
            <td>
                <span class="badge bg-${item.status_class}">${item.status}</span>
            </td>
            <td>${item.updated_at}</td>
            <td class="text-end">
                <div class="btn-group">
                    <button class="btn btn-sm btn-outline-primary" onclick="editItem(${item.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-success" onclick="updateStock(${item.id})">
                        <i class="fas fa-boxes"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteItem(${item.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>`;
}

function updateStatistics(stats) {
    if (stats) {
        document.querySelector('.total-items').textContent = stats.total_items;
        document.querySelector('.low-stock').textContent = stats.low_stock;
        document.querySelector('.categories-count').textContent = stats.categories_count;
        document.querySelector('.expired').textContent = stats.expired;
    }
}

function initializeSearchAndFilters() {
    // Your existing search and filter code
}

function showAlert(type, message) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>`;
    document.querySelector('.container-fluid').insertAdjacentHTML('afterbegin', alertHtml);
}

function refreshInventoryStats() {
    // Your existing refresh stats code
}