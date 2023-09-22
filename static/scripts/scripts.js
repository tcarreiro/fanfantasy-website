function divisionsStandingTab() { 
    fetch('/classificacao') 
      .then(response => response.json()) 
      .then(data => console.log(data)) 
      .catch(error => console.error(error)); 
  } 

function overallStandingTab() { 
    fetch('/classificacao') 
      .then(response => response.json()) 
      .then(data => console.log(data)) 
      .catch(error => console.error(error)); 
  } 

/* ======================= toogle icon navbar ======================= */

let menuIcon = document.querySelector('#menu-icon');
let navbar = document.querySelector('.navbar');

menuIcon.onclick = () => {
    menuIcon.classList.toggle('bx-x');
    navbar.classList.toggle('active');
};

const tabs = document.querySelectorAll('.navbar a');
const highlight = document.querySelector('.highlight');
const firstTab = tabs[0];

attHighlight(firstTab);

function attHighlight(activeLink) {
    let leftTab = activeLink.offsetLeft;
    let widthTab = activeLink.offsetWidth;
    
    highlight.style.left = `${leftTab}px`;
    highlight.style.width = `${widthTab}px`;
};

tabs.forEach(tab => {tab.addEventListener("click", attHighlight(this))});

/* ======================= Header active link ======================= */

let sections = document.querySelectorAll('section')
let navLinks = document.querySelectorAll('header nav a')

window.onscroll = () => {
    sections.forEach(sec => {
        let top = window.scrollY;
        let offset = sec.offsetTop - 150;
        let height = sec.offsetHeight;
        let id = sec.getAttribute('id');

        if (top >= offset && top < offset + height) {
            navLinks.forEach(links => {
                links.classList.remove('active');
                document.querySelector('header nav a[href*=' + id +']').classList.add('active');
            });
        };
    });

    /* ======================= toggle icon ======================= */
    menuIcon.classList.remove('bx-x');
    navbar.classList.remove('active');
};

function updateHighlight() {
    navLinks.forEach(link => {
        if (link.classList.contains('active')) {
            attHighlight(link);
        };
    });
    window.requestAnimationFrame(updateHighlight);
};

window.requestAnimationFrame(updateHighlight);

/* ======================= scroll ======================= */

ScrollReveal({
    reset: true,
    distance: '80px',
    duration: 2000,
    delay: 200
});

ScrollReveal().reveal('.home-content, .heading', {origin:'top'});
ScrollReveal().reveal('.home-img, .about-img, .portfolio-box, .contact form', {origin:'bottom'});
ScrollReveal().reveal('.home-content h1', {origin:'left'});
ScrollReveal().reveal('.home-content p, .about-content', {origin:'right'});