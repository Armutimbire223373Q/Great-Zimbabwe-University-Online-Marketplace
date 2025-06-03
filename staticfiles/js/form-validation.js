// Form validation functions
const validators = {
    // Price validation
    validatePrice: (value) => {
        const price = parseFloat(value);
        if (isNaN(price) || price <= 0) {
            return 'Price must be greater than zero';
        }
        if (!/^\d+(\.\d{1,2})?$/.test(value)) {
            return 'Price must have at most 2 decimal places';
        }
        return '';
    },

    // Phone number validation
    validatePhone: (value) => {
        if (!/^\+263[7-8][0-9]{8}$/.test(value)) {
            return 'Please enter a valid Zimbabwe phone number (e.g., +263771234567)';
        }
        return '';
    },

    // Image validation
    validateImage: (file) => {
        if (!file) return '';
        
        // Check file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            return 'Image size must be no more than 5MB';
        }
        
        // Check file type
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            return 'Only JPEG, PNG and GIF images are allowed';
        }
        
        return '';
    },

    // Title validation
    validateTitle: (value) => {
        if (value.length < 5 || value.length > 100) {
            return 'Title must be between 5 and 100 characters';
        }
        if (!/^[a-zA-Z0-9\s\-_.,!?()]+$/.test(value)) {
            return 'Title contains invalid characters';
        }
        return '';
    },

    // Description validation
    validateDescription: (value) => {
        if (value.length < 20 || value.length > 2000) {
            return 'Description must be between 20 and 2000 characters';
        }
        return '';
    },

    // Meetup time validation
    validateMeetupTime: (value) => {
        const meetupTime = new Date(value);
        const now = new Date();
        if (meetupTime <= now) {
            return 'Meetup time must be in the future';
        }
        return '';
    }
};

// Form validation handler
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const errors = {};
            
            // Validate all form fields
            form.querySelectorAll('[data-validate]').forEach(field => {
                const validations = field.dataset.validate.split(' ');
                let fieldErrors = [];
                
                validations.forEach(validation => {
                    if (validators[validation]) {
                        const error = validators[validation](field.value);
                        if (error) fieldErrors.push(error);
                    }
                });
                
                if (fieldErrors.length > 0) {
                    isValid = false;
                    errors[field.name] = fieldErrors;
                    
                    // Add error class to field
                    field.classList.add('is-invalid');
                    
                    // Create or update error message
                    let errorDiv = field.nextElementSibling;
                    if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
                        errorDiv = document.createElement('div');
                        errorDiv.className = 'invalid-feedback';
                        field.parentNode.insertBefore(errorDiv, field.nextSibling);
                    }
                    errorDiv.textContent = fieldErrors[0];
                } else {
                    field.classList.remove('is-invalid');
                    field.classList.add('is-valid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                // Show error messages
                Object.keys(errors).forEach(fieldName => {
                    const field = form.querySelector(`[name="${fieldName}"]`);
                    if (field) {
                        field.focus();
                        return;
                    }
                });
            }
        });
        
        // Real-time validation on input
        form.querySelectorAll('[data-validate]').forEach(field => {
            field.addEventListener('input', function() {
                const validations = this.dataset.validate.split(' ');
                let hasError = false;
                
                validations.forEach(validation => {
                    if (validators[validation]) {
                        const error = validators[validation](this.value);
                        if (error) hasError = true;
                    }
                });
                
                if (hasError) {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        });
    });
});

// Image preview handler
document.addEventListener('DOMContentLoaded', function() {
    const imageInputs = document.querySelectorAll('input[type="file"][accept="image/*"]');
    
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const error = validators.validateImage(file);
                if (error) {
                    this.value = '';
                    alert(error);
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.querySelector(`#${input.id}-preview`);
                    if (preview) {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    });
}); 