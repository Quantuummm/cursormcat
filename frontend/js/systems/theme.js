/* ═══════════════════════════════════════════════════════════
   Theme System — Dark/Light Mode Toggle
   DESIGN.md § 8: CSS custom props, localStorage, prefers-color-scheme
   ═══════════════════════════════════════════════════════════ */

const ThemeSystem = (() => {
    const STORAGE_KEY = 'mcat-theme';

    function init() {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            apply(saved);
        } else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
            apply('light');
        } else {
            apply('dark');
        }

        // Listen for OS-level changes
        window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {
            if (!localStorage.getItem(STORAGE_KEY)) {
                apply(e.matches ? 'light' : 'dark');
            }
        });
    }

    function apply(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        updateToggleIcons(theme);
    }

    function toggle() {
        const current = document.documentElement.getAttribute('data-theme') || 'dark';
        const next = current === 'dark' ? 'light' : 'dark';
        localStorage.setItem(STORAGE_KEY, next);
        apply(next);
    }

    function current() {
        return document.documentElement.getAttribute('data-theme') || 'dark';
    }

    function updateToggleIcons(theme) {
        document.querySelectorAll('.theme-toggle').forEach(btn => {
            btn.textContent = theme === 'dark' ? '☀️' : '🌙';
            btn.title = theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
        });
    }

    return { init, toggle, current };
})();
