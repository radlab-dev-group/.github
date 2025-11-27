/* =====================================================
   RadLab.dev - Main JavaScript
   ===================================================== */

(function() {
    'use strict';

    /* =====================================================
       Mobile Navigation Toggle
       ===================================================== */
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
        });

        // Close menu when clicking on a link
        const navLinks = document.querySelectorAll('.nav-menu a');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            }
        });
    }

    /* =====================================================
       Navbar Scroll Effect
       ===================================================== */
    const navbar = document.querySelector('.navbar');
    let lastScrollY = window.scrollY;

    window.addEventListener('scroll', () => {
        if (window.scrollY > lastScrollY && window.scrollY > 100) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }
        lastScrollY = window.scrollY;
    });

    /* =====================================================
       Smooth Scroll for Anchor Links
       ===================================================== */
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));

            if (target) {
                const navbarHeight = navbar.offsetHeight;
                const targetPosition = target.offsetTop - navbarHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    /* =====================================================
       Active Navigation Link on Scroll
       ===================================================== */
    const sections = document.querySelectorAll('section[id]');
    const navMenuLinks = document.querySelectorAll('.nav-menu a[href^="#"]');

    function updateActiveLink() {
        const scrollY = window.scrollY;

        sections.forEach(section => {
            const sectionHeight = section.offsetHeight;
            const sectionTop = section.offsetTop - navbar.offsetHeight - 100;
            const sectionId = section.getAttribute('id');

            if (scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
                navMenuLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${sectionId}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }

    window.addEventListener('scroll', updateActiveLink);

    /* =====================================================
       Intersection Observer for Animations
       ===================================================== */
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe elements for fade-in animation
    const animatedElements = document.querySelectorAll(
        '.service-card, .project-card, .process-step, .blog-card, .stat'
    );

    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });

    /* =====================================================
       Contact Form Handling
       ===================================================== */
    const contactForm = document.querySelector('.contact-form');

    if (contactForm) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(contactForm);
            const data = Object.fromEntries(formData);

            // Get the submit button
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;

            // Show loading state
            submitBtn.textContent = 'Wysyłanie...';
            submitBtn.disabled = true;

            // Simulate form submission (replace with actual endpoint)
            setTimeout(() => {
                // Success message
                submitBtn.textContent = 'Wysłano!';
                submitBtn.style.backgroundColor = 'var(--color-accent-primary)';

                // Reset form
                contactForm.reset();

                // Reset button after 3 seconds
                setTimeout(() => {
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                    submitBtn.style.backgroundColor = '';
                }, 3000);

                // Here you would normally send the data to your server
                console.log('Form data:', data);
            }, 1500);
        });
    }

    /* =====================================================
       Blog Filter (for blog archive page)
       ===================================================== */
    const filterBtns = document.querySelectorAll('.filter-btn');
    const blogCards = document.querySelectorAll('.blog-card');

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const filter = btn.dataset.filter;

            // Update active button
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Filter blog cards
            blogCards.forEach(card => {
                const category = card.querySelector('.blog-category').textContent.toLowerCase();

                if (filter === 'all' || category === filter.toLowerCase()) {
                    card.style.display = 'flex';
                    setTimeout(() => {
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }, 10);
                } else {
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                    setTimeout(() => {
                        card.style.display = 'none';
                    }, 300);
                }
            });
        });
    });

    /* =====================================================
       Hero Stats Counter Animation
       ===================================================== */
    const statNumbers = document.querySelectorAll('.stat-number');

    const animateCounter = (element) => {
        const target = element.textContent;
        const isPercentage = target.includes('%');
        const numericValue = parseInt(target);

        if (isNaN(numericValue)) return;

        const duration = 2000;
        const steps = 60;
        const stepValue = numericValue / steps;
        const stepDuration = duration / steps;
        let current = 0;

        const counter = setInterval(() => {
            current += stepValue;
            if (current >= numericValue) {
                element.textContent = target;
                clearInterval(counter);
            } else {
                element.textContent = Math.floor(current) + (isPercentage ? '%' : '+');
            }
        }, stepDuration);
    };

    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                statsObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    statNumbers.forEach(stat => statsObserver.observe(stat));

    /* =====================================================
       Parallax Effect for Hero Background
       ===================================================== */
    const heroBackground = document.querySelector('.hero-background');

    if (heroBackground) {
        window.addEventListener('scroll', () => {
            const scrolled = window.scrollY;
            const parallaxSpeed = 0.5;
            heroBackground.style.transform = `translateY(${scrolled * parallaxSpeed}px)`;
        });
    }

    /* =====================================================
       Copy to Clipboard for Code Blocks
       ===================================================== */
    const codeBlocks = document.querySelectorAll('pre code');

    codeBlocks.forEach(block => {
        const pre = block.parentElement;
        const button = document.createElement('button');
        button.textContent = 'Kopiuj';
        button.className = 'copy-btn';
        button.style.cssText = `
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            padding: 0.25rem 0.75rem;
            background: var(--color-accent-primary);
            color: white;
            border: none;
            border-radius: var(--radius-sm);
            font-size: 0.875rem;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s;
        `;

        pre.style.position = 'relative';
        pre.appendChild(button);

        pre.addEventListener('mouseenter', () => {
            button.style.opacity = '1';
        });

        pre.addEventListener('mouseleave', () => {
            button.style.opacity = '0';
        });

        button.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(block.textContent);
                button.textContent = 'Skopiowano!';
                setTimeout(() => {
                    button.textContent = 'Kopiuj';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        });
    });

    /* =====================================================
       Dark Mode Toggle (Optional)
       ===================================================== */
    // Uncomment to enable dark mode toggle
    /*
    const darkModeToggle = document.createElement('button');
    darkModeToggle.textContent = '🌙';
    darkModeToggle.className = 'dark-mode-toggle';
    darkModeToggle.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        width: 3rem;
        height: 3rem;
        border-radius: 50%;
        background: var(--color-accent-primary);
        color: white;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        box-shadow: var(--shadow-lg);
        z-index: 1000;
    `;

    document.body.appendChild(darkModeToggle);

    darkModeToggle.addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
        darkModeToggle.textContent = document.body.classList.contains('light-mode') ? '☀️' : '🌙';
    });
    */

    /* =====================================================
       Performance: Lazy Load Images
       ===================================================== */
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));

    /* =====================================================
       Initialize on DOM Ready
       ===================================================== */
    console.log('RadLab.dev initialized');
})();
