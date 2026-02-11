/**
 * MCAT Mastery — Firebase Configuration
 * 
 * Initialize Firebase, expose db and auth references.
 * Replace the config values with your project's credentials.
 */

const firebaseConfig = {
    apiKey:            "YOUR_API_KEY",
    authDomain:        "YOUR_PROJECT.firebaseapp.com",
    projectId:         "YOUR_PROJECT_ID",
    storageBucket:     "YOUR_PROJECT.appspot.com",
    messagingSenderId: "000000000000",
    appId:             "YOUR_APP_ID",
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
