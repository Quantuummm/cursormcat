/**
 * MCAT Mastery — TTS Playback System
 * 
 * Handles Text-to-Speech playback with two modes:
 * 1. Cloud Audio: Pre-generated MP3 files from Phase 10 (production)
 * 2. Browser TTS: Web Speech API fallback (development)
 * 
 * Routes each text segment to the correct character voice based on speaker_id.
 */

const TTS = {
    mode: 'browser',  // 'cloud' | 'browser'
    audioElement: null,
    speaking: false,
    queue: [],
    voiceConfig: null,
    onComplete: null,
};

// ─── Initialization ─────────────────────────────────────────

/**
 * Initialize TTS system.
 * @param {object} voiceConfig - Voice assignments from game-data.js
 * @param {string} mode - 'cloud' for pre-generated audio, 'browser' for Web Speech API
 */
function initTTS(voiceConfig, mode = 'browser') {
    TTS.voiceConfig = voiceConfig;
    TTS.mode = mode;
    TTS.audioElement = new Audio();
    TTS.audioElement.addEventListener('ended', _onAudioEnd);
    
    // Pre-warm browser TTS voices
    if (mode === 'browser' && 'speechSynthesis' in window) {
        speechSynthesis.getVoices();
    }
    
    console.log(`🔊 TTS initialized (${mode} mode)`);
}

// ─── Public API ─────────────────────────────────────────────

/**
 * Speak a text segment with the appropriate character voice.
 * @param {string} text - The narrator_text to speak
 * @param {string} speakerId - lyra, specialist, grimble, etc.
 * @param {string} audioPath - Path to pre-generated audio file (cloud mode)
 * @returns {Promise} Resolves when speech completes
 */
function speak(text, speakerId = 'lyra', audioPath = null) {
    return new Promise((resolve) => {
        if (TTS.mode === 'cloud' && audioPath) {
            _playCloudAudio(audioPath, resolve);
        } else {
            _playBrowserTTS(text, speakerId, resolve);
        }
    });
}

/**
 * Queue multiple segments for sequential playback.
 * @param {Array} segments - Array of {text, speakerId, audioPath}
 */
async function speakSequence(segments) {
    for (const seg of segments) {
        await speak(seg.text, seg.speakerId, seg.audioPath);
    }
}

/**
 * Stop all current and queued speech.
 */
function stopSpeaking() {
    TTS.speaking = false;
    TTS.queue = [];
    
    if (TTS.audioElement) {
        TTS.audioElement.pause();
        TTS.audioElement.currentTime = 0;
    }
    
    if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
    }
}

/**
 * Check if currently speaking.
 */
function isSpeaking() {
    return TTS.speaking;
}

// ─── Cloud Audio Mode ───────────────────────────────────────

function _playCloudAudio(audioPath, onComplete) {
    TTS.speaking = true;
    TTS.onComplete = onComplete;
    
    TTS.audioElement.src = audioPath;
    TTS.audioElement.play().catch(e => {
        console.warn('Cloud audio failed, falling back to browser TTS:', e);
        // Could fall back to browser TTS here
        TTS.speaking = false;
        onComplete();
    });
}

function _onAudioEnd() {
    TTS.speaking = false;
    if (TTS.onComplete) {
        TTS.onComplete();
        TTS.onComplete = null;
    }
}

// ─── Browser TTS Mode ───────────────────────────────────────

function _playBrowserTTS(text, speakerId, onComplete) {
    if (!('speechSynthesis' in window)) {
        console.warn('Speech synthesis not supported');
        onComplete();
        return;
    }
    
    // Clean text: remove [PAUSE] markers, convert to natural pauses
    const cleanText = text
        .replace(/\[PAUSE \d+s\]/g, '...')
        .replace(/\[PAUSE\]/g, '...');
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // Apply character-specific voice settings
    const voiceParams = _getBrowserVoiceParams(speakerId);
    utterance.rate = voiceParams.rate;
    utterance.pitch = voiceParams.pitch;
    utterance.volume = 1.0;
    
    // Try to find a good voice
    const voices = speechSynthesis.getVoices();
    const preferred = voices.find(v => v.lang === 'en-US' && v.name.includes('Google'));
    if (preferred) utterance.voice = preferred;
    
    TTS.speaking = true;
    
    utterance.onend = () => {
        TTS.speaking = false;
        onComplete();
    };
    
    utterance.onerror = () => {
        TTS.speaking = false;
        onComplete();
    };
    
    speechSynthesis.speak(utterance);
}

/**
 * Map speaker_id to browser TTS voice parameters.
 * Approximate the Cloud voice characteristics.
 */
function _getBrowserVoiceParams(speakerId) {
    const params = {
        lyra:       { rate: 1.05, pitch: 1.1 },  // Warm, slightly higher
        grimble:    { rate: 0.9,  pitch: 0.8 },   // Slower, deeper
        specialist: { rate: 1.0,  pitch: 1.0 },   // Neutral
        
        // Individual specialists
        dr_kade:    { rate: 1.0,  pitch: 1.0 },
        dr_vale:    { rate: 1.05, pitch: 1.05 },
        dr_calder:  { rate: 1.1,  pitch: 1.1 },
        dr_finch:   { rate: 1.0,  pitch: 1.05 },
        cmdr_voss:  { rate: 0.95, pitch: 0.95 },
        dr_solomon: { rate: 0.95, pitch: 1.0 },
        prof_rhee:  { rate: 1.0,  pitch: 1.0 },
    };
    
    return params[speakerId] || params.specialist;
}

// ─── Exports ────────────────────────────────────────────────
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initTTS, speak, speakSequence, stopSpeaking, isSpeaking,
    };
}
