/* ═══════════════════════════════════════════════════════════
   Galaxy Shimmer — Ambient Background Particle System
   DESIGN.md § 6: 50-100 particles, 0.1-0.3px/frame drift,
   0.1-0.4 opacity, ~10% visual intensity
   ═══════════════════════════════════════════════════════════ */

const GalaxyShimmer = (() => {
    let canvas, ctx;
    let particles = [];
    let animId = null;
    let lastTime = 0;
    const FPS = 30;
    const FRAME_INTERVAL = 1000 / FPS;
    const PARTICLE_COUNT = 70;

    function init() {
        canvas = document.getElementById('galaxy-canvas');
        if (!canvas) return;
        ctx = canvas.getContext('2d');
        resize();
        createParticles();
        window.addEventListener('resize', resize);
        start();
    }

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    function createParticles() {
        particles = [];
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                size: Math.random() * 1.5 + 0.5,
                opacity: Math.random() * 0.3 + 0.1,
                dx: (Math.random() - 0.5) * 0.2,
                dy: (Math.random() - 0.5) * 0.15,
                pulseSpeed: Math.random() * 0.002 + 0.001,
                pulsePhase: Math.random() * Math.PI * 2,
                baseOpacity: 0,
            });
            particles[i].baseOpacity = particles[i].opacity;
        }
    }

    function isLightMode() {
        return document.documentElement.getAttribute('data-theme') === 'light';
    }

    function draw(timestamp) {
        animId = requestAnimationFrame(draw);

        const delta = timestamp - lastTime;
        if (delta < FRAME_INTERVAL) return;
        lastTime = timestamp - (delta % FRAME_INTERVAL);

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const light = isLightMode();
        const r = light ? 0 : 255;
        const g = light ? 0 : 255;
        const b = light ? 30 : 255;

        for (const p of particles) {
            // Move
            p.x += p.dx;
            p.y += p.dy;

            // Wrap around edges
            if (p.x < -5) p.x = canvas.width + 5;
            if (p.x > canvas.width + 5) p.x = -5;
            if (p.y < -5) p.y = canvas.height + 5;
            if (p.y > canvas.height + 5) p.y = -5;

            // Pulse opacity
            p.opacity = p.baseOpacity + Math.sin(timestamp * p.pulseSpeed + p.pulsePhase) * 0.15;
            p.opacity = Math.max(0.05, Math.min(0.5, p.opacity));

            // Draw
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${p.opacity})`;
            ctx.fill();
        }
    }

    function start() {
        if (animId) return;
        animId = requestAnimationFrame(draw);
    }

    function stop() {
        if (animId) {
            cancelAnimationFrame(animId);
            animId = null;
        }
    }

    function destroy() {
        stop();
        window.removeEventListener('resize', resize);
        particles = [];
    }

    return { init, start, stop, destroy };
})();
