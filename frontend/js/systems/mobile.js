/**
 * MCAT Mastery — Mobile Native Integration
 * 
 * Provides native capabilities when running inside Capacitor (iOS/Android).
 * Gracefully no-ops when running in browser.
 */

const Mobile = {
    isNative: false,
    platform: 'web',

    async init() {
        // Detect Capacitor environment
        if (window.Capacitor && window.Capacitor.isNativePlatform()) {
            this.isNative = true;
            this.platform = window.Capacitor.getPlatform(); // 'ios' | 'android'
            console.log(`[Mobile] Running on ${this.platform}`);
            await this._setupNative();
        } else {
            console.log('[Mobile] Running in browser');
        }
    },

    async _setupNative() {
        try {
            // Status bar — dark content on dark background
            const { StatusBar } = await import('https://esm.sh/@capacitor/status-bar');
            if (StatusBar) {
                await StatusBar.setStyle({ style: 'Dark' });
                await StatusBar.setBackgroundColor({ color: '#0D1117' });
            }
        } catch (e) {
            console.warn('[Mobile] StatusBar not available:', e.message);
        }

        try {
            // Hide splash screen after app loads
            const { SplashScreen } = await import('https://esm.sh/@capacitor/splash-screen');
            if (SplashScreen) {
                await SplashScreen.hide();
            }
        } catch (e) {
            console.warn('[Mobile] SplashScreen not available:', e.message);
        }

        try {
            // Keyboard adjustments
            const { Keyboard } = await import('https://esm.sh/@capacitor/keyboard');
            if (Keyboard) {
                Keyboard.addListener('keyboardWillShow', (info) => {
                    document.body.style.paddingBottom = `${info.keyboardHeight}px`;
                });
                Keyboard.addListener('keyboardWillHide', () => {
                    document.body.style.paddingBottom = '0px';
                });
            }
        } catch (e) {
            console.warn('[Mobile] Keyboard not available:', e.message);
        }
    },

    /**
     * Trigger haptic feedback on native platforms.
     * @param {'light'|'medium'|'heavy'} style
     */
    async haptic(style = 'light') {
        if (!this.isNative) return;
        try {
            const { Haptics, ImpactStyle } = await import('https://esm.sh/@capacitor/haptics');
            const styleMap = {
                light: ImpactStyle.Light,
                medium: ImpactStyle.Medium,
                heavy: ImpactStyle.Heavy,
            };
            await Haptics.impact({ style: styleMap[style] || ImpactStyle.Light });
        } catch (e) {
            // Silently fail
        }
    },

    /**
     * Haptic notification feedback.
     * @param {'success'|'warning'|'error'} type
     */
    async hapticNotification(type = 'success') {
        if (!this.isNative) return;
        try {
            const { Haptics, NotificationType } = await import('https://esm.sh/@capacitor/haptics');
            const typeMap = {
                success: NotificationType.Success,
                warning: NotificationType.Warning,
                error: NotificationType.Error,
            };
            await Haptics.notification({ type: typeMap[type] || NotificationType.Success });
        } catch (e) {
            // Silently fail
        }
    },

    /**
     * Store data natively (faster than localStorage on native).
     */
    async setPreference(key, value) {
        if (!this.isNative) {
            localStorage.setItem(key, JSON.stringify(value));
            return;
        }
        try {
            const { Preferences } = await import('https://esm.sh/@capacitor/preferences');
            await Preferences.set({ key, value: JSON.stringify(value) });
        } catch (e) {
            localStorage.setItem(key, JSON.stringify(value));
        }
    },

    async getPreference(key) {
        if (!this.isNative) {
            const v = localStorage.getItem(key);
            return v ? JSON.parse(v) : null;
        }
        try {
            const { Preferences } = await import('https://esm.sh/@capacitor/preferences');
            const { value } = await Preferences.get({ key });
            return value ? JSON.parse(value) : null;
        } catch (e) {
            const v = localStorage.getItem(key);
            return v ? JSON.parse(v) : null;
        }
    },
};
