document.addEventListener("DOMContentLoaded", function () {
    // Load Header
    loadComponent("header-placeholder", "components/header.html");

    // Load Footer
    loadComponent("footer-placeholder", "components/footer.html");

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

async function loadComponent(elementId, filePath) {
    try {
        const response = await fetch(filePath);
        if (response.ok) {
            const content = await response.text();
            document.getElementById(elementId).innerHTML = content;
            
            // Update year in footer after loading
            if (elementId === 'footer-placeholder') {
                const yearElement = document.getElementById("year");
                if (yearElement) {
                    yearElement.textContent = new Date().getFullYear();
                }
            }
            
            // Re-highlight active link based on current URL
            if (elementId === 'header-placeholder') {
                setActiveLink();
            }
        } else {
            console.error(`Error loading ${filePath}: ${response.statusText}`);
        }
    } catch (error) {
        console.error(`Error loading ${filePath}:`, error);
    }
}

function setActiveLink() {
    const currentPath = window.location.pathname.split("/").pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (linkPath === currentPath) {
            link.classList.add('active');
        }
    });
}
