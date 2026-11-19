/* ============================================
   MODERN LANDING PAGE - JAVASCRIPT
   ============================================ */

// Mobile Navigation Toggle
const hamburger = document.getElementById('hamburger');
const navMenu = document.getElementById('navMenu');
const navLinks = document.querySelectorAll('.nav-link');

hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    navMenu.classList.toggle('active');
});

// Close mobile menu when clicking on a link
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
    });
});

// Sticky Navbar Background Change
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Smooth Scroll Reveal Animation
const revealElements = () => {
    const elements = document.querySelectorAll('.feature-card, .stat-card, .advantage-item, .testimonial-card, .info-item');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('show');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    elements.forEach(element => {
        element.classList.add('scroll-reveal');
        observer.observe(element);
    });
};

// Initialize Reveal Animation
document.addEventListener('DOMContentLoaded', revealElements);

// Testimonials Slider
let currentTestimonial = 0;
const testimonialsContainer = document.getElementById('testimonialsContainer');
const testimonialCards = testimonialsContainer.querySelectorAll('.testimonial-card');
const totalTestimonials = testimonialCards.length;

const moveTestimonial = (direction) => {
    currentTestimonial += direction;
    
    if (currentTestimonial >= totalTestimonials) {
        currentTestimonial = 0;
    } else if (currentTestimonial < 0) {
        currentTestimonial = totalTestimonials - 1;
    }
    
    const offset = -currentTestimonial * 100;
    testimonialsContainer.style.transform = `translateX(${offset}%)`;
};

// Auto-scroll testimonials every 6 seconds
setInterval(() => {
    moveTestimonial(1);
}, 6000);

// Contact Form Submission
const contactForm = document.getElementById('contactForm');

if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const formData = {
            name: contactForm.children[0].children[0].value,
            email: contactForm.children[1].children[0].value,
            message: contactForm.children[2].children[0].value
        };
        
        // Validate form
        if (!formData.name || !formData.email || !formData.message) {
            showNotification('Please fill in all fields', 'error');
            return;
        }
        
        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            showNotification('Please enter a valid email', 'error');
            return;
        }
        
        // Log form data (in production, send to server)
        console.log('Form submitted:', formData);
        
        showNotification('Message sent successfully! We\'ll get back to you soon.', 'success');
        contactForm.reset();
    });
}

// Notification System
const showNotification = (message, type = 'info') => {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
        z-index: 9999;
        animation: slideInRight 0.3s ease-out;
        font-weight: 500;
    `;
    
    document.body.appendChild(notification);
    
    // Remove notification after 4 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
};

// Add animation styles dynamically
const addAnimationStyles = () => {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideOutRight {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100px);
            }
        }
    `;
    document.head.appendChild(style);
};

addAnimationStyles();

// Counter Animation for Stats
const animateCounters = () => {
    const statNumbers = document.querySelectorAll('.stat-number');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const finalValue = element.textContent;
                
                // Extract numeric value
                let numericValue = parseInt(finalValue);
                let suffix = finalValue.replace(/[0-9]/g, '');
                
                if (!isNaN(numericValue)) {
                    let currentValue = 0;
                    const increment = Math.ceil(numericValue / 50);
                    
                    const counter = setInterval(() => {
                        currentValue += increment;
                        if (currentValue >= numericValue) {
                            element.textContent = finalValue;
                            clearInterval(counter);
                        } else {
                            element.textContent = currentValue + suffix;
                        }
                    }, 30);
                }
                
                observer.unobserve(element);
            }
        });
    }, {
        threshold: 0.5
    });
    
    statNumbers.forEach(number => observer.observe(number));
};

document.addEventListener('DOMContentLoaded', animateCounters);

// Parallax Effect
const parallaxEffect = () => {
    const heroBg = document.querySelector('.hero-background');
    
    window.addEventListener('scroll', () => {
        const scrollY = window.scrollY;
        if (heroBg) {
            heroBg.style.transform = `translateY(${scrollY * 0.5}px)`;
        }
    });
};

parallaxEffect();

// Lazy Loading for Images (if added in future)
const lazyLoadImages = () => {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    observer.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img.lazy').forEach(img => imageObserver.observe(img));
    }
};

document.addEventListener('DOMContentLoaded', lazyLoadImages);

// Smooth Scroll Navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#') {
            e.preventDefault();
            const element = document.querySelector(href);
            if (element) {
                element.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// Add scroll class to feature cards on hover
document.querySelectorAll('.feature-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.cursor = 'pointer';
    });
});

// Keyboard Navigation for Testimonials
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') {
        moveTestimonial(-1);
    } else if (e.key === 'ArrowRight') {
        moveTestimonial(1);
    }
});

// Add ripple effect to buttons
const addRippleEffect = () => {
    const buttons = document.querySelectorAll('.btn, .testimonials-btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                background: rgba(255, 255, 255, 0.5);
                border-radius: 50%;
                left: ${x}px;
                top: ${y}px;
                pointer-events: none;
                animation: ripple 0.6s ease-out;
            `;
            
            if (!this.style.position || this.style.position === 'static') {
                this.style.position = 'relative';
                this.style.overflow = 'hidden';
            }
            
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });
};

const addRippleStyles = () => {
    if (!document.querySelector('style[data-ripple]')) {
        const style = document.createElement('style');
        style.setAttribute('data-ripple', 'true');
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    addRippleStyles();
    addRippleEffect();
});

// Dark Mode Detection (Optional)
const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

if (prefersDarkScheme.matches) {
    // Optional: Add dark mode styles
    console.log('Dark mode preferred by user');
}

// Performance Optimization - Debounce scroll events
const debounce = (func, delay) => {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
};

// Optimize scroll event handler
const optimizedScroll = debounce(() => {
    const scrollY = window.scrollY;
    if (scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
}, 10);

// Use optimized scroll handler
window.addEventListener('scroll', optimizedScroll, { passive: true });

// Page visibility optimization
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Pause animations if page is hidden
        document.querySelectorAll('[style*="animation"]').forEach(el => {
            el.style.animationPlayState = 'paused';
        });
    } else {
        // Resume animations when page is visible
        document.querySelectorAll('[style*="animation"]').forEach(el => {
            el.style.animationPlayState = 'running';
        });
    }
});

// Add loading state to buttons
document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('click', function() {
        if (this.id !== 'contactForm' && this !== contactForm) {
            const originalText = this.textContent;
            this.textContent = 'Processing...';
            this.disabled = true;
            
            setTimeout(() => {
                this.textContent = originalText;
                this.disabled = false;
            }, 1000);
        }
    });
});

// Console welcome message
console.log('%cWelcome to Modern Landing Page!', 'color: #6366f1; font-size: 16px; font-weight: bold;');
console.log('%cBuilt with HTML, CSS, and JavaScript\nMade with ❤️', 'color: #10b981; font-size: 12px;');

// Initialize all features
document.addEventListener('DOMContentLoaded', () => {
    console.log('All features initialized successfully!');
});
