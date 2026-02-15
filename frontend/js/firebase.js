/**
 * MCAT Mastery — Firebase Configuration
 * 
 * Initialize Firebase, expose db and auth references.
 * Replace the config values with your project's credentials.
 */

const firebaseConfig = {
    apiKey:            "AIzaSyA1RnGs2GWOVu8RH-6sG4ek-ycyvAv51C8",
    authDomain:        "gen-lang-client-0005785057.firebaseapp.com",
    projectId:         "gen-lang-client-0005785057",
    storageBucket:     "gen-lang-client-0005785057.firebasestorage.app",
    messagingSenderId: "1009890177702",
    appId:             "1:1009890177702:web:7bbecb45aeae1bea41fa67",
};

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
