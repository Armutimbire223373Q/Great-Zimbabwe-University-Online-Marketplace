//
Initialize
Bootstrap
tooltips
and
popovers

// Get CSRF token from cookie
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

// Set up CSRF token for all AJAX requests
const csrftoken = getCookie('csrftoken');

// Initialize Bootstrap tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    })

    // Auto-scroll chat messages to bottom
    const chatContainer = document.querySelector('.chat-messages');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Handle form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Skip CSRF check for GET forms
            if (form.method.toLowerCase() === 'get') {
                return;
            }

            // Get CSRF token from form or cookie
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]')?.value || csrftoken;
            if (!csrfToken) {
                console.error('CSRF token not found');
                return;
            }

            if (form.dataset.ajax === 'true') {
                e.preventDefault();
                const formData = new FormData(form);
                fetch(form.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    credentials: 'same-origin'
                })
                .then(response => {
                    if (response.ok) {
                        window.location.reload();
                    } else {
                        throw new Error('Network response was not ok');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred. Please try again.');
                });
            } else {
                // For non-AJAX forms, ensure CSRF token is present
                const csrfInput = form.querySelector('[name=csrfmiddlewaretoken]');
                if (!csrfInput) {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'csrfmiddlewaretoken';
                    input.value = csrfToken;
                    form.appendChild(input);
                }
            }
        });
    });
});
