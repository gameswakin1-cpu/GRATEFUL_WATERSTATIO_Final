/**
 * GRATEFUL WATER STATION - MODERN REGISTER
 * Interactive JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    // ========================================
    // INITIALIZE ALL COMPONENTS
    // ========================================
    
    initPasswordToggles();
    initPasswordStrength();
    initPasswordMatch();
    initFormValidation();
    initLoadingState();
    initSocialButtons();
    initInputAnimations();
});

// ========================================
// PASSWORD TOGGLES
// ========================================

function initPasswordToggles() {
    const password1Toggle = document.getElementById('password1Toggle');
    const password2Toggle = document.getElementById('password2Toggle');
    const password1Input = document.getElementById('password1');
    const password2Input = document.getElementById('password2');
    
    if (password1Toggle && password1Input) {
        password1Toggle.addEventListener('click', () => {
            togglePassword(password1Input, password1Toggle);
        });
    }
    
    if (password2Toggle && password2Input) {
        password2Toggle.addEventListener('click', () => {
            togglePassword(password2Input, password2Toggle);
        });
    }
}

function togglePassword(input, toggle) {
    const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
    input.setAttribute('type', type);
    
    // Update icon
    const icon = toggle.querySelector('i');
    icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
    
    // Add click animation
    toggle.style.transform = 'translateY(-50%) scale(0.9)';
    setTimeout(() => {
        toggle.style.transform = 'translateY(-50%) scale(1)';
    }, 150);
}

// ========================================
// PASSWORD STRENGTH INDICATOR
// ========================================

function initPasswordStrength() {
    const passwordInput = document.getElementById('password1');
    const strengthFill = document.getElementById('strengthFill');
    const strengthText = document.getElementById('strengthText');
    
    if (!passwordInput || !strengthFill || !strengthText) return;
    
    passwordInput.addEventListener('input', (e) => {
        const password = e.target.value;
        const strength = calculatePasswordStrength(password);
        updateStrengthIndicator(strength, strengthFill, strengthText);
    });
}

function calculatePasswordStrength(password) {
    let score = 0;
    
    if (!password) return 0;
    
    // Length check
    if (password.length >= 8) score += 1;
    if (password.length >= 12) score += 1;
    
    // Character variety checks
    if (/[a-z]/.test(password)) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^a-zA-Z0-9]/.test(password)) score += 1;
    
    // Normalize score to 0-4 range
    if (score <= 2) return 1; // Weak
    if (score <= 3) return 2; // Fair
    if (score <= 5) return 3; // Good
    return 4; // Strong
}

function updateStrengthIndicator(strength, fillElement, textElement) {
    // Remove all strength classes
    fillElement.className = 'strength-fill';
    textElement.className = 'strength-text';
    
    const strengthLabels = {
        0: 'Enter password',
        1: 'Weak',
        2: 'Fair',
        3: 'Good',
        4: 'Strong'
    };
    
    const strengthClasses = {
        0: '',
        1: 'weak',
        2: 'fair',
        3: 'good',
        4: 'strong'
    };
    
    if (strength > 0) {
        fillElement.classList.add(strengthClasses[strength]);
    }
    
    textElement.textContent = strengthLabels[strength];
    textElement.classList.add(strengthClasses[strength]);
}

// ========================================
// PASSWORD MATCH CHECKER
// ========================================

function initPasswordMatch() {
    const password1 = document.getElementById('password1');
    const password2 = document.getElementById('password2');
    const matchError = document.getElementById('passwordMatchError');
    
    if (!password1 || !password2 || !matchError) return;
    
    password2.addEventListener('input', () => {
        if (password2.value && password1.value !== password2.value) {
            matchError.textContent = 'Passwords do not match';
            password2.closest('.form-group').classList.add('has-error');
        } else {
            matchError.textContent = '';
            password2.closest('.form-group').classList.remove('has-error');
        }
    });
    
    password1.addEventListener('input', () => {
        if (password2.value && password1.value === password2.value) {
            matchError.textContent = '';
            password2.closest('.form-group').classList.remove('has-error');
        }
    });
}

// ========================================
// FORM VALIDATION
// ========================================

function initFormValidation() {
    const registerForm = document.getElementById('registerForm');
    const termsCheckbox = document.getElementById('termsCheckbox');
    
    if (!registerForm) return;
    
    // Real-time validation for inputs
    const inputs = registerForm.querySelectorAll('input[required], textarea[required]');
    inputs.forEach(input => {
        input.addEventListener('blur', () => validateField(input));
        input.addEventListener('input', () => clearFieldError(input));
    });
    
    // Email validation
    const emailInput = document.getElementById('email');
    if (emailInput) {
        emailInput.addEventListener('blur', () => validateEmail(emailInput));
    }
    
    // Phone validation
    const phoneInput = document.getElementById('phone_number');
    if (phoneInput) {
        phoneInput.addEventListener('blur', () => validatePhone(phoneInput));
    }
    
    // Form submission
    registerForm.addEventListener('submit', (e) => {
        let isValid = true;
        
        // Validate all required fields
        inputs.forEach(input => {
            if (!validateField(input)) {
                isValid = false;
            }
        });
        
        // Validate email
        if (emailInput && !validateEmail(emailInput)) {
            isValid = false;
        }
        
        // Validate phone
        if (phoneInput && !validatePhone(phoneInput)) {
            isValid = false;
        }
        
        // Validate passwords match
        const password1 = document.getElementById('password1');
        const password2 = document.getElementById('password2');
        if (password1 && password2 && password1.value !== password2.value) {
            showFieldError(password2, 'Passwords do not match');
            isValid = false;
        }
        
        // Validate terms checkbox
        if (termsCheckbox && !termsCheckbox.checked) {
            const termsError = document.getElementById('termsError');
            if (termsError) {
                termsError.textContent = 'You must agree to the Terms of Service and Privacy Policy';
            }
            isValid = false;
        } else if (termsCheckbox) {
            const termsError = document.getElementById('termsError');
            if (termsError) {
                termsError.textContent = '';
            }
        }
        
        if (!isValid) {
            e.preventDefault();
            shakeCard();
            
            // Scroll to first error
            const firstError = registerForm.querySelector('.has-error');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        } else {
            showLoading();
        }
    });
    
    // Terms checkbox change handler
    if (termsCheckbox) {
        termsCheckbox.addEventListener('change', () => {
            const termsError = document.getElementById('termsError');
            if (termsCheckbox.checked && termsError) {
                termsError.textContent = '';
            }
        });
    }
}

function validateField(input) {
    const value = input.value.trim();
    const formGroup = input.closest('.form-group');
    
    if (!value) {
        showFieldError(input, 'This field is required');
        return false;
    }
    
    // Minimum length for username
    if (input.id === 'username' && value.length < 3) {
        showFieldError(input, 'Username must be at least 3 characters');
        return false;
    }
    
    // Minimum length for password
    if (input.id === 'password1' && value.length < 8) {
        showFieldError(input, 'Password must be at least 8 characters');
        return false;
    }
    
    clearFieldError(input);
    return true;
}

function validateEmail(input) {
    const value = input.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!value) {
        showFieldError(input, 'Email is required');
        return false;
    }
    
    if (!emailRegex.test(value)) {
        showFieldError(input, 'Please enter a valid email address');
        return false;
    }
    
    clearFieldError(input);
    return true;
}

function validatePhone(input) {
    const value = input.value.trim();
    // Basic phone validation - at least 10 digits
    const phoneRegex = /^[\d\s\-\+\(\)\.]{10,}$/;
    
    if (!value) {
        showFieldError(input, 'Phone number is required');
        return false;
    }
    
    if (!phoneRegex.test(value)) {
        showFieldError(input, 'Please enter a valid phone number');
        return false;
    }
    
    clearFieldError(input);
    return true;
}

function showFieldError(input, message) {
    const formGroup = input.closest('.form-group');
    let errorElement = formGroup.querySelector('.error-message');
    
    // Create error element if it doesn't exist
    if (!errorElement) {
        errorElement = document.createElement('span');
        errorElement.className = 'error-message';
        formGroup.appendChild(errorElement);
    }
    
    errorElement.textContent = message;
    formGroup.classList.add('has-error');
    input.setAttribute('aria-invalid', 'true');
}

function clearFieldError(input) {
    const formGroup = input.closest('.form-group');
    if (!formGroup) return;
    
    const errorElement = formGroup.querySelector('.error-message');
    if (errorElement) {
        errorElement.textContent = '';
    }
    
    formGroup.classList.remove('has-error');
    input.removeAttribute('aria-invalid');
}

function shakeCard() {
    const registerCard = document.querySelector('.register-card');
    if (registerCard) {
        registerCard.classList.add('shake');
        setTimeout(() => {
            registerCard.classList.remove('shake');
        }, 500);
    }
}

// ========================================
// LOADING STATE
// ========================================

function initLoadingState() {
    const registerBtn = document.getElementById('registerBtn');
    
    if (registerBtn) {
        // Store original text
        registerBtn.dataset.originalText = registerBtn.querySelector('.btn-text').textContent;
    }
}

function showLoading() {
    const registerBtn = document.getElementById('registerBtn');
    
    if (registerBtn) {
        registerBtn.classList.add('loading');
        registerBtn.disabled = true;
    }
}

function hideLoading() {
    const registerBtn = document.getElementById('registerBtn');
    
    if (registerBtn) {
        registerBtn.classList.remove('loading');
        registerBtn.disabled = false;
    }
}

// ========================================
// SOCIAL BUTTONS
// ========================================

function initSocialButtons() {
    const socialButtons = document.querySelectorAll('.social-btn');
    
    socialButtons.forEach(btn => {
        const isLiveLink = btn.tagName === 'A' && btn.getAttribute('href');
        if (isLiveLink) {
            return;
        }

        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Show coming soon notification
            const provider = btn.dataset.provider || (this.classList.contains('google-btn') ? 'Google' : 'Facebook');
            showNotification(`${provider} sign up coming soon!`, 'info');
        });
    });
}

// ========================================
// INPUT ANIMATIONS
// ========================================

function initInputAnimations() {
    const inputs = document.querySelectorAll('.input-wrapper input, .input-wrapper textarea');
    
    inputs.forEach(input => {
        // Add focus animation
        input.addEventListener('focus', () => {
            const wrapper = input.closest('.input-wrapper');
            wrapper.style.transform = 'scale(1.01)';
        });
        
        input.addEventListener('blur', () => {
            const wrapper = input.closest('.input-wrapper');
            wrapper.style.transform = 'scale(1)';
        });
    });
}

// ========================================
// NOTIFICATION SYSTEM
// ========================================

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.register-notification');
    if (existing) existing.remove();
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `register-notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        left: 50%;
        transform: translateX(-50%) translateY(-20px);
        background: ${type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : '#0ea5e9'};
        color: white;
        padding: 14px 24px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 500;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        z-index: 10000;
        opacity: 0;
        transition: all 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    requestAnimationFrame(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(-50%) translateY(0)';
    });
    
    // Auto remove
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(-50%) translateY(-20px)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ========================================
// KEYBOARD NAVIGATION
// ========================================

document.addEventListener('keydown', (e) => {
    // Enter key on last field submits form
    if (e.key === 'Enter' && e.target.id === 'password2') {
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.dispatchEvent(new Event('submit'));
        }
    }
});

// ========================================
// PRELOAD OPTIMIZATION
// ========================================

// Add loaded class to body when everything is ready
window.addEventListener('load', () => {
    document.body.classList.add('loaded');
});
