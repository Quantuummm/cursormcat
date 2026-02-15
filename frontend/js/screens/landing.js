/* ═══════════════════════════════════════════════════════════
   Landing Page — Pre-Login Screen Controller
   Duolingo-inspired layout with cosmic twist
   ═══════════════════════════════════════════════════════════ */

const LandingScreen = (() => {

    async function handleGetStarted() {
        try {
            // Sign in anonymously, then proceed to character select
            const user = await ensureAuth();
            if (user) {
                App.user = user;
                App.db = db;
                showScreen('character-select-screen');
                if (typeof initCharacterSelect === 'function') initCharacterSelect();
            }
        } catch (e) {
            console.error('Sign-in failed:', e);
        }
    }

    async function handleLogin() {
        try {
            // Attempt to sign in, then re-boot to load data
            const user = await ensureAuth();
            if (user) {
                App.user = user;
                App.db = db;
                showScreen('loading-screen');
                // Re-run the data loading portion of boot
                if (typeof boot === 'function') boot();
            }
        } catch (e) {
            console.error('Login failed:', e);
        }
    }

    function init() {
        // Theme toggle
        document.querySelectorAll('.theme-toggle').forEach(btn => {
            btn.addEventListener('click', () => ThemeSystem.toggle());
        });

        // CTA buttons
        document.querySelectorAll('[data-action="get-started"]').forEach(btn => {
            btn.addEventListener('click', handleGetStarted);
        });

        // Login button
        document.querySelectorAll('[data-action="login"]').forEach(btn => {
            btn.addEventListener('click', handleLogin);
        });

        // "I already have an account" link
        document.querySelectorAll('[data-action="existing-account"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                handleLogin();
            });
        });
    }

    return { init };
})();
