// Staff Management JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize form handlers
    initializeFormHandlers();
    
    // Initialize filters
    initializeFilters();
});

function initializeFormHandlers() {
    const staffForm = document.getElementById('staffForm');
    if (staffForm) {
        staffForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            try {
                const formData = new FormData(this);
                const response = await fetch('/authentication/staff/add/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });

                const data = await response.json();
                
                if (response.ok) {
                    showAlert('success', 'Staff member added successfully');
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addStaffModal'));
                    modal.hide();
                    window.location.reload();
                } else {
                    showAlert('danger', data.message || 'Error adding staff member');
                }
            } catch (error) {
                console.error('Error:', error);
                showAlert('danger', 'An error occurred while adding the staff member');
            }
        });
    }
}

function initializeFilters() {
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', filterStaff);
    }

    // Department filter
    const departmentFilter = document.getElementById('departmentFilter');
    if (departmentFilter) {
        departmentFilter.addEventListener('change', filterStaff);
    }

    // Role filter
    const roleFilter = document.getElementById('roleFilter');
    if (roleFilter) {
        roleFilter.addEventListener('change', filterStaff);
    }
}

function filterStaff() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const department = document.getElementById('departmentFilter').value;
    const role = document.getElementById('roleFilter').value;
    
    const rows = document.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const name = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        const staffDepartment = row.querySelector('td:nth-child(4)').textContent;
        const staffRole = row.querySelector('td:nth-child(3)').textContent;
        
        const matchesSearch = name.includes(searchTerm);
        const matchesDepartment = !department || staffDepartment.includes(department);
        const matchesRole = !role || staffRole.includes(role);
        
        row.style.display = matchesSearch && matchesDepartment && matchesRole ? '' : 'none';
    });
}

function editStaff(staffId) {
    window.location.href = `/authentication/staff/edit/${staffId}/`;
}

function deleteStaff(staffId) {
    const modal = new bootstrap.Modal(document.getElementById('deleteConfirmationModal'));
    modal.show();
    
    document.getElementById('confirmDelete').onclick = async function() {
        try {
            const response = await fetch(`/authentication/staff/delete/${staffId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            
            if (response.ok) {
                window.location.reload();
            } else {
                showAlert('danger', 'Error deleting staff member');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('danger', 'An error occurred while deleting the staff member');
        }
    };
}

// Utility function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Utility function to show alerts
function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}