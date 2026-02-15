/**
 * MCAT Mastery — Firebase Configuration
 * 
 * NOTE: Credentials are now being handled securely.
 * For local development, ensure these are placeholder values in tracked files.
 */

const firebaseConfig = {
    apiKey:            "REPLACED_WITH_ENV_VARIABLE",
    authDomain:        "gen-lang-client-0005785057.firebaseapp.com",
    projectId:         "gen-lang-client-0005785057",
    storageBucket:     "gen-lang-client-0005785057.firebasestorage.app",
    messagingSenderId: "1009890177702",
    appId:             "1:1009890177702:web:7bbecb45aeae1bea41fa67",
};

// In a real production build, these would be injected via environment variables.
// For now, we are removing the hardcoded key from the tracked file.
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // If you need the key locally for development, you can manually set it here 
    // or use a local dev server that injects it.
}

firebase.initializeApp(firebaseConfig);

const db   = firebase.firestore();
const auth = firebase.auth();

// Enable offline persistence
db.enablePersistence({ synchronizeTabs: true }).catch(err => {
    if (err.code === 'failed-precondition') {
        console.warn('Firestore persistence unavailable: multiple tabs open');
    } else if (err.code === 'unimplemented') {
        console.warn('Firestore persistence not supported in this browser');
    }
});

/**
 * Sign in anonymously — every player gets a uid without account creation.
 * Can be upgraded to email/Google sign-in later.
 */
async function ensureAuth() {
    if (auth.currentUser) return auth.currentUser;
    
    try {
        const cred = await auth.signInAnonymously();
        console.log('Signed in:', cred.user.uid);
        return cred.user;
    } catch (e) {
        console.error('Auth failed:', e);
        return null;
    }
}
