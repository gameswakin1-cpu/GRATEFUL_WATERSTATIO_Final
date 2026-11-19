/**

 * GRATEFUL WATER STATION - MODERN LOGIN

 * Interactive JavaScript

 */



document.addEventListener('DOMContentLoaded', () => {

    // ========================================

    // INITIALIZE ALL COMPONENTS

    // ========================================

    

    initPasswordToggle();

    initFormValidation();

    initLoadingState();

    initRememberMe();

    initInputAnimations();

    initSocialButtons();

});



// ========================================

// PASSWORD TOGGLE

// ========================================



function initPasswordToggle() {

    const passwordToggle = document.getElementById('passwordToggle');

    const passwordInput = document.getElementById('password');

    

    if (!passwordToggle || !passwordInput) return;

    

    passwordToggle.addEventListener('click', () => {

        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';

        passwordInput.setAttribute('type', type);

        

        // Update icon

        const icon = passwordToggle.querySelector('i');

        icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';

        

        // Add click animation

        passwordToggle.style.transform = 'translateY(-50%) scale(0.9)';

        setTimeout(() => {

            passwordToggle.style.transform = 'translateY(-50%) scale(1)';

        }, 150);

    });

}



// ========================================

// FORM VALIDATION

// ========================================



function initFormValidation() {

    const loginForm = document.getElementById('loginForm');

    const usernameInput = document.getElementById('username');

    const passwordInput = document.getElementById('password');

    

    if (!loginForm) return;

    

    // Real-time validation

    usernameInput.addEventListener('blur', () => validateUsername(usernameInput));

    usernameInput.addEventListener('input', () => clearError(usernameInput));

    

    passwordInput.addEventListener('blur', () => validatePassword(passwordInput));

    passwordInput.addEventListener('input', () => clearError(passwordInput));

    

    // Form submission

    loginForm.addEventListener('submit', (e) => {

        let isValid = true;

        

        // Validate username

        if (!validateUsername(usernameInput)) {

            isValid = false;

        }

        

        // Validate password

        if (!validatePassword(passwordInput)) {

            isValid = false;

        }

        

        if (!isValid) {

            e.preventDefault();

            shakeForm();

        } else {

            // Show loading state

            showLoading();

        }

    });

}



function validateUsername(input) {

    const value = input.value.trim();

    const errorElement = document.getElementById('usernameError');

    const formGroup = input.closest('.form-group');

    

    if (!value) {

        showError(input, errorElement, formGroup, 'Username is required');

        return false;

    }

    

    if (value.length < 3) {

        showError(input, errorElement, formGroup, 'Username must be at least 3 characters');

        return false;

    }

    

    clearError(input, errorElement, formGroup);

    return true;

}



function validatePassword(input) {

    const value = input.value;

    const errorElement = document.getElementById('passwordError');

    const formGroup = input.closest('.form-group');

    

    if (!value) {

        showError(input, errorElement, formGroup, 'Password is required');

        return false;

    }

    

    if (value.length < 6) {

        showError(input, errorElement, formGroup, 'Password must be at least 6 characters');

        return false;

    }

    

    clearError(input, errorElement, formGroup);

    return true;

}



function showError(input, errorElement, formGroup, message) {

    if (errorElement) {

        errorElement.textContent = message;

    }

    if (formGroup) {

        formGroup.classList.add('has-error');

    }

    input.setAttribute('aria-invalid', 'true');

}



function clearError(input, errorElement, formGroup) {

    if (!errorElement) {

        errorElement = document.getElementById(input.id + 'Error');

    }

    if (!formGroup) {

        formGroup = input.closest('.form-group');

    }

    

    if (errorElement) {

        errorElement.textContent = '';

    }

    if (formGroup) {

        formGroup.classList.remove('has-error');

    }

    input.removeAttribute('aria-invalid');

}



function shakeForm() {

    const loginCard = document.querySelector('.login-card');

    if (loginCard) {

        loginCard.classList.add('shake');

        setTimeout(() => {

            loginCard.classList.remove('shake');

        }, 500);

    }

}



// ========================================

// LOADING STATE

// ========================================



function initLoadingState() {

    const loginBtn = document.getElementById('loginBtn');

    

    if (loginBtn) {

        // Store original text

        loginBtn.dataset.originalText = loginBtn.querySelector('.btn-text').textContent;

    }

}



function showLoading() {

    const loginBtn = document.getElementById('loginBtn');

    

    if (loginBtn) {

        loginBtn.classList.add('loading');

        loginBtn.disabled = true;

    }

}



function hideLoading() {

    const loginBtn = document.getElementById('loginBtn');

    

    if (loginBtn) {

        loginBtn.classList.remove('loading');

        loginBtn.disabled = false;

    }

}



// ========================================

// REMEMBER ME FUNCTIONALITY

// ========================================



function initRememberMe() {

    const rememberMe = document.getElementById('rememberMe');

    const usernameInput = document.getElementById('username');

    

    if (!rememberMe || !usernameInput) return;

    

    // Load saved username

    const savedUsername = localStorage.getItem('rememberedUsername');

    if (savedUsername) {

        usernameInput.value = savedUsername;

        rememberMe.checked = true;

    }

    

    // Save username on form submit

    const loginForm = document.getElementById('loginForm');

    loginForm.addEventListener('submit', () => {

        if (rememberMe.checked) {

            localStorage.setItem('rememberedUsername', usernameInput.value.trim());

        } else {

            localStorage.removeItem('rememberedUsername');

        }

    });

}



// ========================================

// INPUT ANIMATIONS

// ========================================



function initInputAnimations() {

    const inputs = document.querySelectorAll('.input-wrapper input');

    

    inputs.forEach(input => {

        // Add focus animation

        input.addEventListener('focus', () => {

            const wrapper = input.closest('.input-wrapper');

            wrapper.style.transform = 'scale(1.02)';

        });

        

        input.addEventListener('blur', () => {

            const wrapper = input.closest('.input-wrapper');

            wrapper.style.transform = 'scale(1)';

        });

    });

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

            showNotification(`${provider} login coming soon!`, 'info');

        });

    });

}



// ========================================

// NOTIFICATION SYSTEM

// ========================================



function showNotification(message, type = 'info') {

    // Remove existing notifications

    const existing = document.querySelector('.login-notification');

    if (existing) existing.remove();

    

    // Create notification

    const notification = document.createElement('div');

    notification.className = `login-notification notification-${type}`;

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

    // Enter key on username or password field submits form

    if (e.key === 'Enter' && (e.target.id === 'username' || e.target.id === 'password')) {

        e.preventDefault();

        const loginForm = document.getElementById('loginForm');

        if (loginForm) {

            // Use requestSubmit for proper form submission with validation

            loginForm.requestSubmit();

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

