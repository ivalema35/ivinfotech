// ─── Component Prefetch ────────────────────────────────────────────────────
// Start fetching IMMEDIATELY when the script is parsed — before DOMContentLoaded.
// Combined with <link rel="preload">, these requests fire at the earliest possible moment.
const _componentCache = {
    header: fetch('components/header.html').then(r => r.ok ? r.text() : Promise.reject(r.statusText)),
    footer: fetch('components/footer.html').then(r => r.ok ? r.text() : Promise.reject(r.statusText))
};

document.addEventListener("DOMContentLoaded", async function () {
    // ─── Inject Components in Parallel ──────────────────────────────────────
    // By the time DOM is ready the fetches are already in-flight (or done).
    try {
        const [headerContent, footerContent] = await Promise.all([
            _componentCache.header,
            _componentCache.footer
        ]);

        const headerEl = document.getElementById('header-placeholder');
        if (headerEl) {
            headerEl.innerHTML = headerContent;
            setActiveLink();
        }

        const footerEl = document.getElementById('footer-placeholder');
        if (footerEl) {
            footerEl.innerHTML = footerContent;
            const yearElement = document.getElementById('year');
            if (yearElement) yearElement.textContent = new Date().getFullYear();
        }
    } catch (error) {
        console.error('Component loading failed:', error);
    }

    // Initialize AOS
    AOS.init({
        duration: 800,
        easing: 'ease-in-out',
        once: true,
        mirror: false
    });

    if (typeof Swiper !== 'undefined') {
        new Swiper('.testimonial-swiper', {
            slidesPerView: 3,
            spaceBetween: 24,
            loop: true,
            autoplay: {
                delay: 3500,
                disableOnInteraction: false
            },
            pagination: {
                el: '.testimonial-swiper .swiper-pagination',
                clickable: true
            },
            breakpoints: {
                0: {
                    slidesPerView: 1
                },
                768: {
                    slidesPerView: 2
                },
                992: {
                    slidesPerView: 3
                }
            }
        });
    }

    const navbar = document.querySelector('.navbar');
    if (navbar) {
        const toggleNavbarShadow = () => {
            if (window.scrollY > 10) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        };

        toggleNavbarShadow();
        window.addEventListener('scroll', toggleNavbarShadow);
    }

    const coreTabs = document.querySelectorAll('.core-tabs .nav-link');
    if (coreTabs.length && typeof bootstrap !== 'undefined') {
        coreTabs.forEach((tab) => {
            tab.addEventListener('mouseenter', () => {
                const tabInstance = bootstrap.Tab.getOrCreateInstance(tab);
                tabInstance.show();
            });
        });
    }

    // Lottie Player is now handled by the web component automatically
    // No need for manual initialization
});

function setActiveLink() {
    const currentPath = window.location.pathname.split('/').pop() || 'index';

    // Check all nav-links and dropdown-items
    const allLinks = document.querySelectorAll('.navbar-nav .nav-link, .dropdown-menu .dropdown-item');

    allLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href === currentPath) {
            link.classList.add('active');

            // If it's a dropdown item, also activate the parent dropdown toggle
            const parentDropdown = link.closest('.nav-item.dropdown');
            if (parentDropdown) {
                const parentToggle = parentDropdown.querySelector(':scope > .nav-link');
                if (parentToggle) {
                    parentToggle.classList.add('active');
                }
            }
        }
    });
}

// Legacy helper kept for any inline page-specific calls — wraps the cache.
async function loadComponent(elementId, filePath) {
    try {
        const response = await fetch(filePath);
        if (response.ok) {
            const content = await response.text();
            const el = document.getElementById(elementId);
            if (el) el.innerHTML = content;
        } else {
            console.error(`Error loading ${filePath}: ${response.statusText}`);
        }
    } catch (error) {
        console.error(`Error loading ${filePath}:`, error);
    }
}
