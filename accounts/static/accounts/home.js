/**
 * GRATEFUL WATER STATION - LANDING PAGE
 * Premium Interactive JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    // ========================================
    // INITIALIZATION
    // ========================================
    
    initNavigation();
    initScrollReveal();
    initCounters();
    initTestimonialSlider();
    initContactForm();
    initScrollToTop();
    initSmoothScroll();
});

// ========================================
// NAVIGATION
// ========================================

function initNavigation() {
    const navbar = document.getElementById('navbar');
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    const navLinks = document.querySelectorAll('.nav-link');
    let previousScrollY = window.scrollY;
    let scrollDirectionDistance = 0;
    
    // Sticky navbar on scroll
    window.addEventListener('scroll', () => {
        const currentScrollY = Math.max(window.scrollY, 0);
        if (currentScrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        if (!window.matchMedia('(max-width: 768px)').matches) {
            navbar.classList.remove('nav-hidden');
            scrollDirectionDistance = 0;
            previousScrollY = currentScrollY;
            return;
        }

        if (currentScrollY <= 50 || navMenu?.classList.contains('active')) {
            navbar.classList.remove('nav-hidden');
            scrollDirectionDistance = 0;
        } else {
            const scrollDelta = currentScrollY - previousScrollY;
            scrollDirectionDistance = Math.sign(scrollDelta) === Math.sign(scrollDirectionDistance)
                ? scrollDirectionDistance + scrollDelta
                : scrollDelta;

            if (scrollDirectionDistance > 8 && currentScrollY > 100) {
                navbar.classList.add('nav-hidden');
                scrollDirectionDistance = 0;
            } else if (scrollDirectionDistance < -8) {
                navbar.classList.remove('nav-hidden');
                scrollDirectionDistance = 0;
            }
        }

        previousScrollY = currentScrollY;
    }, { passive: true });
    
    // Mobile menu toggle
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
            if (navMenu.classList.contains('active')) {
                navbar.classList.remove('nav-hidden');
            }
            document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
        });
        
        // Close menu on link click
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
    }
    
    // Keep the Home, About, and Contact links in sync with their page sections.
    const sectionLinks = Array.from(navLinks).filter(link =>
        ['#home', '#about', '#contact'].includes(link.getAttribute('href'))
    );
    const sections = sectionLinks
        .map(link => document.querySelector(link.getAttribute('href')))
        .filter(Boolean);

    function updateActiveSection() {
        const activationLine = (navbar?.offsetHeight || 0) + 80;
        let activeSection = sections[0];

        sections.forEach(section => {
            if (section.getBoundingClientRect().top <= activationLine) {
                activeSection = section;
            }
        });

        sectionLinks.forEach(link => {
            link.classList.toggle('active', link.getAttribute('href') === `#${activeSection?.id}`);
        });
    }

    window.addEventListener('scroll', updateActiveSection, { passive: true });
    window.addEventListener('resize', updateActiveSection);
    updateActiveSection();
}

// ========================================
// SCROLL REVEAL ANIMATIONS
// ========================================

function initScrollReveal() {
    const revealElements = document.querySelectorAll('[data-reveal]');
    
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                // Add staggered delay for elements in the same container
                const container = entry.target.closest('[data-reveal-group]') || entry.target.parentElement;
                const siblings = container.querySelectorAll('[data-reveal]');
                const siblingIndex = Array.from(siblings).indexOf(entry.target);
                
                setTimeout(() => {
                    entry.target.classList.add('revealed');
                }, siblingIndex * 100);
                
                revealObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    revealElements.forEach(el => revealObserver.observe(el));
}

// ========================================
// ANIMATED COUNTERS
// ========================================

function initCounters() {
    const counters = document.querySelectorAll('[data-count]');
    
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.getAttribute('data-count'));
                const duration = 2000; // 2 seconds
                const startTime = performance.now();
                
                const updateCounter = (currentTime) => {
                    const elapsed = currentTime - startTime;
                    const progress = Math.min(elapsed / duration, 1);
                    
                    // Easing function - ease out quart
                    const easeOutQuart = 1 - Math.pow(1 - progress, 4);
                    
                    const current = Math.floor(easeOutQuart * target);
                    counter.textContent = formatNumber(current);
                    
                    if (progress < 1) {
                        requestAnimationFrame(updateCounter);
                    } else {
                        counter.textContent = formatNumber(target);
                    }
                };
                
                requestAnimationFrame(updateCounter);
                counterObserver.unobserve(counter);
            }
        });
    }, { threshold: 0.5 });
    
    counters.forEach(counter => counterObserver.observe(counter));
}

function formatNumber(num) {
    if (num >= 1000) {
        return num.toLocaleString();
    }
    return num;
}

// ========================================
// TESTIMONIAL SLIDER
// ========================================

function initTestimonialSlider() {
    const slider = document.querySelector('.testimonials-slider');
    if (!slider) return;
    
    const track = slider.querySelector('.testimonials-track');
    const cards = slider.querySelectorAll('.testimonial-card');
    const prevBtn = slider.querySelector('.slider-btn.prev');
    const nextBtn = slider.querySelector('.slider-btn.next');
    const dots = slider.querySelectorAll('.dot');
    
    let currentIndex = 0;
    const totalSlides = cards.length;
    let autoplayInterval;
    
    // Calculate cards per view based on screen width
    function getCardsPerView() {
        if (window.innerWidth >= 992) return 3;
        if (window.innerWidth >= 768) return 2;
        return 1;
    }
    
    function getMaxIndex() {
        return Math.max(0, totalSlides - getCardsPerView());
    }
    
    function goToSlide(index) {
        const maxIndex = getMaxIndex();
        currentIndex = Math.max(0, Math.min(index, maxIndex));
        
        const cardWidth = cards[0].offsetWidth + 24; // Including gap
        const offset = currentIndex * cardWidth;
        
        track.style.transform = `translateX(-${offset}px)`;
        
        // Update dots
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === currentIndex);
        });
    }
    
    function nextSlide() {
        const maxIndex = getMaxIndex();
        if (currentIndex < maxIndex) {
            goToSlide(currentIndex + 1);
        } else {
            goToSlide(0);
        }
    }
    
    function prevSlide() {
        if (currentIndex > 0) {
            goToSlide(currentIndex - 1);
        } else {
            goToSlide(getMaxIndex());
        }
    }
    
    function startAutoplay() {
        autoplayInterval = setInterval(nextSlide, 5000);
    }
    
    function stopAutoplay() {
        clearInterval(autoplayInterval);
    }
    
    // Event listeners
    if (prevBtn) prevBtn.addEventListener('click', () => {
        prevSlide();
        stopAutoplay();
        startAutoplay();
    });
    
    if (nextBtn) nextBtn.addEventListener('click', () => {
        nextSlide();
        stopAutoplay();
        startAutoplay();
    });
    
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            goToSlide(index);
            stopAutoplay();
            startAutoplay();
        });
    });
    
    // Pause autoplay on hover
    slider.addEventListener('mouseenter', stopAutoplay);
    slider.addEventListener('mouseleave', startAutoplay);
    
    // Handle resize
    window.addEventListener('resize', () => {
        goToSlide(currentIndex);
    });
    
    // Start autoplay
    startAutoplay();
    
    // Touch/swipe support
    let touchStartX = 0;
    let touchEndX = 0;
    
    track.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    
    track.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, { passive: true });
    
    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;
        
        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                nextSlide();
            } else {
                prevSlide();
            }
            stopAutoplay();
            startAutoplay();
        }
    }
}

// ========================================
// CONTACT FORM
// ========================================

function initContactForm() {
    const form = document.getElementById('contactForm');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        submitBtn.disabled = true;

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {'X-Requested-With': 'XMLHttpRequest'},
            });
            const result = await response.json();

            if (!response.ok || !result.success) {
                throw new Error(result.message || 'Unable to send your message.');
            }

            submitBtn.innerHTML = '<i class="fas fa-check"></i> Message Sent!';
            showNotification(result.message, 'success');
            form.reset();
        } catch (error) {
            showNotification(error.message, 'error');
        } finally {
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 2500);
        }
    });
    
    // Input focus effects
    const inputs = form.querySelectorAll('input, textarea');
    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            input.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', () => {
            input.parentElement.classList.remove('focused');
        });
    });
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 24px;
        background: ${type === 'success' ? '#22c55e' : '#0ea5e9'};
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 500;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// ========================================
// SCROLL TO TOP
// ========================================

function initScrollToTop() {
    const scrollTopBtn = document.getElementById('scrollTop');
    if (!scrollTopBtn) return;
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 500) {
            scrollTopBtn.classList.add('visible');
        } else {
            scrollTopBtn.classList.remove('visible');
        }
    }, { passive: true });
    
    scrollTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// ========================================
// SMOOTH SCROLL
// ========================================

function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                
                const navbarHeight = document.getElementById('navbar').offsetHeight;
                const targetPosition = targetElement.offsetTop - navbarHeight - 20;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// ========================================
// ADDITIONAL ANIMATIONS
// ========================================

// Parallax effect for hero orbs
window.addEventListener('scroll', () => {
    const scrolled = window.scrollY;
    const orbs = document.querySelectorAll('.gradient-orb');
    
    orbs.forEach((orb, index) => {
        const speed = 0.1 + (index * 0.05);
        orb.style.transform = `translateY(${scrolled * speed}px)`;
    });
}, { passive: true });

// Add animation keyframes dynamically
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

// ========================================
// PERFORMANCE OPTIMIZATIONS
// ========================================

// Lazy load images
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                }
                imageObserver.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

// Preload critical resources
const preloadLinks = [
    { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
    { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossOrigin: true }
];

preloadLinks.forEach(({ rel, href, crossOrigin }) => {
    const link = document.createElement('link');
    link.rel = rel;
    link.href = href;
    if (crossOrigin) link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
});
