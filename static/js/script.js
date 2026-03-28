document.addEventListener('DOMContentLoaded', function() {
    initPasswordStrength();
    initPasswordToggle();
    initPaymentMethod();
    initFormValidation();
    initDOBValidation();
    initCardFormatting();
});

function initPasswordStrength() {
    const passwordInput = document.getElementById('password');
    const strengthBar = document.querySelector('.strength-bar');
    
    if (passwordInput && strengthBar) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            let strength = 0;
            
            if (password.length >= 6) strength++;
            if (password.length >= 10) strength++;
            if (/[A-Z]/.test(password)) strength++;
            if (/[0-9]/.test(password)) strength++;
            if (/[^A-Za-z0-9]/.test(password)) strength++;
            
            strengthBar.className = 'strength-bar';
            if (password.length > 0) {
                if (strength <= 2) strengthBar.classList.add('weak');
                else if (strength <= 3) strengthBar.classList.add('medium');
                else strengthBar.classList.add('strong');
            }
        });
    }
}

function initPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.toggle-password');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input');
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });
}

function initPaymentMethod() {
    const paymentOptions = document.querySelectorAll('input[name="payment_method"]');
    const paymentSections = document.querySelectorAll('.payment-section');
    
    paymentOptions.forEach(option => {
        option.addEventListener('change', function() {
            paymentSections.forEach(section => section.classList.remove('active'));
            
            const selectedSection = document.querySelector(`.${this.value}-section`);
            if (selectedSection) {
                selectedSection.classList.add('active');
            }
        });
    });
}

function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            showError(input, 'This field is required');
        } else {
            clearError(input);
        }
    });
    
    return isValid;
}

function showError(input, message) {
    input.style.borderColor = '#e74c3c';
    
    let errorElement = input.parentElement.querySelector('.error-message');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.style.color = '#e74c3c';
        errorElement.style.fontSize = '0.8rem';
        errorElement.style.marginTop = '5px';
        input.parentElement.appendChild(errorElement);
    }
    errorElement.textContent = message;
}

function clearError(input) {
    input.style.borderColor = '#e0e0e0';
    const errorElement = input.parentElement.querySelector('.error-message');
    if (errorElement) {
        errorElement.remove();
    }
}

function initDOBValidation() {
    const dobInput = document.getElementById('dob');
    
    if (dobInput) {
        const today = new Date();
        const maxDate = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate());
        dobInput.max = maxDate.toISOString().split('T')[0];
        
        const minDate = new Date(today.getFullYear() - 100, today.getMonth(), today.getDate());
        dobInput.min = minDate.toISOString().split('T')[0];
    }
}

function initCardFormatting() {
    const cardNumber = document.getElementById('card_number');
    const expiry = document.getElementById('expiry');
    
    if (cardNumber) {
        cardNumber.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.replace(/(\d{4})/g, '$1 ').trim();
            e.target.value = value.substring(0, 19);
        });
    }
    
    if (expiry) {
        expiry.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.substring(0, 2) + '/' + value.substring(2, 4);
            }
            e.target.value = value;
        });
    }
    
    const mobileInput = document.getElementById('mobile');
    if (mobileInput) {
        mobileInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
    }
    
    const aadharInput = document.getElementById('aadhar');
    if (aadharInput) {
        aadharInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
    }
}

document.querySelectorAll('.pass-type-card').forEach(card => {
    card.addEventListener('click', function() {
        document.querySelectorAll('.pass-type-card').forEach(c => {
            c.querySelector('.pass-type-content').style.background = '#fff';
        });
        this.querySelector('.pass-type-content').style.background = 'rgba(231, 76, 60, 0.05)';
    });
});

document.querySelectorAll('.payment-option').forEach(option => {
    option.addEventListener('click', function() {
        document.querySelectorAll('.payment-option').forEach(o => {
            o.querySelector('.payment-card').style.background = '#fff';
        });
        this.querySelector('.payment-card').style.background = 'rgba(231, 76, 60, 0.05)';
    });
});
