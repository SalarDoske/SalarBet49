document.addEventListener('DOMContentLoaded', function() {
    // ١. مێنوی موبایل و خاچ (Menu & Cross)
    const navmob = document.getElementById('navmob-container');
    const cross = document.getElementById('cross');
    const menu = document.getElementById('menu');

    const navClose = () => {
        if (!navmob) return;
        if (navmob.style.display === 'block') {
            navmob.style.display = 'none';
            navmob.style.position = 'static';
        } else {
            navmob.style.display = 'block';
            navmob.style.position = 'fixed';
        }
    };

    if (menu) menu.addEventListener('click', navClose);
    if (cross) cross.addEventListener('click', navClose);

    // ٢. لیستێن زمانان (Languages Dropdown)
    const lang1 = document.getElementById('lang1');
    const lang2 = document.getElementById('lang2');
    const lang3 = document.getElementById('lang3');
    const lang4 = document.getElementById('lang4');

    if (lang1 && lang2) {
        lang1.addEventListener('click', () => {
            lang2.style.display = lang2.style.display === 'block' ? 'none' : 'block';
        });
    }

    if (lang3 && lang4) {
        lang3.addEventListener('click', () => {
            lang4.style.display = lang4.style.display === 'block' ? 'none' : 'block';
        });
    }

    // ٣. مۆدێلێن تۆمارکرن و چوونا ژوورێ (Register & Sign In Modals)
    const regModal = document.getElementById('registerModal');
    const signModal = document.getElementById('signinModal');

    const openReg = document.getElementById('openRegModal') || document.querySelector('.regBtn');
    const openSign = document.getElementById('openSignModal') || document.querySelector('.signBtn');

    const closeReg = document.getElementById('closeRegModal') || document.getElementById('closeModal');
    const closeSign = document.getElementById('closeSignModal');

    if (openReg && regModal) {
        openReg.addEventListener('click', (e) => {
            e.preventDefault();
            regModal.style.display = 'flex';
        });
    }

    if (closeReg && regModal) {
        closeReg.addEventListener('click', () => {
            regModal.style.display = 'none';
        });
    }

    if (openSign && signModal) {
        openSign.addEventListener('click', (e) => {
            e.preventDefault();
            signModal.style.display = 'flex';
        });
    }

    if (closeSign && signModal) {
        closeSign.addEventListener('click', () => {
            signModal.style.display = 'none';
        });
    }

    // داخستنا مۆدێلان دەما ل دەرئەخەی دەوروبەری وان دەدەی
    window.addEventListener('click', (e) => {
        if (regModal && e.target === regModal) regModal.style.display = 'none';
        if (signModal && e.target === signModal) signModal.style.display = 'none';
    });
});
